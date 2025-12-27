from datetime import datetime, timedelta, timezone
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, responses, status

from app.users.auth import authenticate_user, create_access_token, create_refresh_token, get_password_hash
from app.users.dao import ProfileDAO, UserDAO
from app.users.dependencies import get_current_user, get_current_user_by_refresh
from app.users.schemas import SUserAuth, SUserRegister
from app.config import settings
from app.users.models import Users


router = APIRouter(prefix="/auth", tags=["auth & users"])

@router.post("/register")
async def register_user(request: Request, user_data: SUserRegister):
    existing_user = await UserDAO.find_one_or_none(email=user_data.email)
    if existing_user:
        raise HTTPException(status_code=500)
    hashed_password = get_password_hash(password=user_data.password)
    await UserDAO.add(email=user_data.email, hashed_password=hashed_password, is_active=True)
    
    user = await UserDAO.find_one_or_none(email=user_data.email)
    
    await ProfileDAO.add(user_id = user.id, fullname=user_data.fullname, username=user_data.username, birthdate=user_data.birthdate)
    
    #блок автоматической авторизации
    
    profile = await ProfileDAO.find_one_or_none(user_id=user.id)

    refresh_jti = secrets.token_urlsafe(16) # Генерируем уникальный ID сессии
    expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    expire_at = datetime.now(timezone.utc) + timedelta(days=expire_days)
    
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id), "jti": refresh_jti})
    
    await UserDAO.update_session_data(
        user_id=user.id,
        jti=refresh_jti,
        ip=request.client.host, # Получаем IP клиента
        expires_at=expire_at
    )

    response = responses.JSONResponse(
        status_code=status.HTTP_201_CREATED, 
        content={
            "user":{
                "id": int(user.id),
                "email": str(user.email),
                "username": str(user_data.username),
                "fullname": str(user_data.fullname),
                "role": profile.role.value if profile.role else "user",
                "imgSrc": str(profile.imgSrc) if profile.imgSrc else None
            }
        }
    )

    # Access Token: доступен всему приложению
    response.set_cookie(
        key="user_access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=900
    )

    # Refresh Token: доступен ТОЛЬКО эндпоинту обновления
    response.set_cookie(
        key="user_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/auth/refresh", # Ограничиваем путь для безопасности
        max_age=expire_days * 24 * 3600
    )

    return response


@router.post("/login")
async def login_user(request: Request, user_data: SUserAuth):
    user = await authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    profile = await ProfileDAO.find_one_or_none(user_id=user.id)

    refresh_jti = secrets.token_urlsafe(16) # Генерируем уникальный ID сессии
    expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    expire_at = datetime.now(timezone.utc) + timedelta(days=expire_days)
    
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id), "jti": refresh_jti})
    


    await UserDAO.update_session_data(
        user_id=user.id,
        jti=refresh_jti,
        ip=request.client.host, # Получаем IP клиента
        expires_at=expire_at
    )

    response = responses.JSONResponse(
        status_code=status.HTTP_201_CREATED, 
        content={
            "user":{
                "id": int(user.id),
                "email": str(user.email),
                "username": str(profile.username),
                "fullname": str(profile.fullname),
                "role": profile.role.value if profile.role else "user",
                "imgSrc": str(profile.imgSrc) if profile.imgSrc else None
            }
        }
    )

    # Access Token: доступен всему приложению
    response.set_cookie(
        key="user_access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=900
    )

    # Refresh Token: доступен ТОЛЬКО эндпоинту обновления
    response.set_cookie(
        key="user_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/auth/refresh", # Ограничиваем путь для безопасности
        max_age=expire_days * 24 * 3600
    )

    return response

@router.post("/logout")
async def logout_user(
    response: responses.JSONResponse, # Используем для возможности очистки кук
    user: Users = Depends(get_current_user) # Используем зависимость для проверки прав
):
    # 1. Сброс сессии в базе данных через DAO
    # Мы обнуляем jti, IP и срок годности, тем самым аннулируя токен
    await UserDAO.reset_session(user.id)

    # 2. Формируем ответ
    response = responses.JSONResponse(content={"message": "Вы успешно вышли из системы"})

    # 3. Удаление кук на стороне браузера
    # Мы устанавливаем значение в пустую строку и время жизни в 0
    response.delete_cookie(
        key="user_access_token",
        path="/",
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    response.delete_cookie(
        key="user_refresh_token",
        path="/auth/refresh", # Важно: путь должен совпадать с тем, что был при login
        httponly=True,
        secure=True,
        samesite="lax"
    )

    return response

@router.post("/refresh")
async def refresh_token(
    request: Request,
    # Зависимость уже проверила IP, JTI и срок годности в БД
    user: Users = Depends(get_current_user_by_refresh)
):
    # 1. Подготовка данных для новой сессии
    new_jti = secrets.token_urlsafe(16)
    expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    expire_at = datetime.now(timezone.utc) + timedelta(days=expire_days)
    
    # 2. Генерация новой пары токенов
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={
        "sub": str(user.id),
        "jti": new_jti
    })

    # 3. Обновление сессии в БД (Token Rotation)
    # Старый jti затирается новым, что делает старый Refresh-токен бесполезным
    await UserDAO.update_session_data(
        user_id=user.id,
        jti=new_jti,
        ip=request.client.host,
        expires_at=expire_at
    )

    # 4. Формирование ответа и установка новых кук
    content = {
        "user_access_token": new_access_token,
        "token_type": "bearer",
    }
    response = responses.JSONResponse(content=content)

    # Обновляем Access-куку
    response.set_cookie(
        key="user_access_token",
        value=new_access_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=3600
    )

    # Обновляем Refresh-куку (с новым токеном и путем)
    response.set_cookie(
        key="user_refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/auth/refresh",
        max_age=expire_days * 24 * 3600
    )

    return response

@router.get("/me")
async def get_user_info(
    request: Request,
    user: Users = Depends(get_current_user)
):
    print(request.cookies)

    profile = await ProfileDAO.find_by_id(user.id)

    response = responses.JSONResponse(
        status_code=status.HTTP_201_CREATED, 
        content={
            "user":{
                "id": int(user.id),
                "email": str(user.email),
                "username": str(profile.username),
                "fullname": str(profile.fullname),
                "role": profile.role.value if profile.role else "user",
                "imgSrc": str(profile.imgSrc) if profile.imgSrc else None
            }
        }
    )

    return response
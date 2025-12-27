from datetime import date, datetime, timezone
from sqlalchemy import update
from app.dao.base import BaseDAO
from app.users.models import Users, Profiles
from app.database import async_session_maker

class UserDAO(BaseDAO):
    model = Users

    @classmethod
    async def reset_session(cls, user_id: int):
        """
        'Удаляет' сессию, обнуляя поля токена в таблице Users.
        """
        async with async_session_maker() as session:
            query = (
                update(cls.model)
                .where(cls.model.id == user_id)
                .values(
                    current_refresh_jti=None,
                    expires_at=None,
                    last_ip=None
                )
            )
            await session.execute(query)
            await session.commit()
    
    @classmethod
    async def update_jwt(cls, user_id: int, jwt: str):
        """
        Обновляет поле last_jti для конкретного пользователя.
        """
        async with async_session_maker() as session:
            # Создаем запрос на обновление по ID пользователя
            query = (
                update(cls.model)
                .where(cls.model.id == user_id)
                .values(current_refresh_jti=jwt)
            )
            await session.execute(query)
            await session.commit()
    
    @classmethod
    async def update_session_data(cls, user_id: int, jti: str, ip: str, expires_at: datetime):
        async with async_session_maker() as session:
            # Обновляем поля сессии для конкретного пользователя
            query = (
                update(cls.model)
                .where(cls.model.id == user_id)
                .values(
                    current_refresh_jti=jti,
                    last_ip=ip,
                    expires_at=expires_at,
                    last_login_at=datetime.now(timezone.utc) 
                )
            )
            await session.execute(query)
            await session.commit()

class ProfileDAO(BaseDAO):
    model = Profiles

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.users.router import router as router_users

app = FastAPI()

origins_regex = r"http://(localhost|127\.0\.0\.1|192\.168\.1\.10|26\.57\.119\.85|26\.248\.104\.117)(:\d+)?"

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=origins_regex,             # Разрешить запросы с любых адресов
    allow_credentials=True,
    allow_methods=["*"],             # Разрешить все методы (GET, POST, и т.д.)
    allow_headers=["*"],             # Разрешить все заголовки
)

app.include_router(router_users)
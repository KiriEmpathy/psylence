from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_HOST: str
    DB_LOCATION: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    algorithm: str

    class Config:
        env_file = ".env"
    
settings = Settings()
DATABASE_URL = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}-{settings.DB_LOCATION}:{settings.DB_PORT}/{settings.DB_NAME}"
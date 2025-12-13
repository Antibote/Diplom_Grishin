from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from dotenv import load_dotenv
import os

# Определяем окружение
environment = os.getenv("ENVIRONMENT", "local")

if environment == "docker":
    load_dotenv(".env.docker")
else:
    load_dotenv(".env")

DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

print(f"Подключение к БД: {os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}")
print(f"Окружение: {environment}")

engine = create_async_engine(DATABASE_URL)
new_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

from app.database import async_session_maker
from sqlalchemy import insert, select, update

class BaseDAO:
    model = None
    
    @classmethod
    async def find_by_id(cls, model_id: int):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(id=model_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    @classmethod
    async def find_one_or_none(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    @classmethod
    async def find_all(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalars().all()
    
    @classmethod
    async def add(cls, **data):
        async with async_session_maker() as session:
            query = insert(cls.model).values(**data)
            await session.execute(query)
            await session.commit()
    
    @classmethod
    async def clear_by_filter(cls, fields_to_clear: list[str], **filter_by):
        async with async_session_maker() as session:
            for field in fields_to_clear:
                if not hasattr(cls, field):
                    raise AttributeError(f"Модель {cls.__name__} не имеет поля {field}")
            values_to_update = {field: None for field in fields_to_clear}
            query = update(cls).filter_by(**filter_by).values(values_to_update)
            await session.execute(query)
            await session.commit()

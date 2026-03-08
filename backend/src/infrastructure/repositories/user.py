from typing import Any
from pydantic import UUID5

from src.infrastructure.utils.password import hash_password
from src.core.domain.user import UserIn
from src.core.repositories.iuser import IUserRepository
from src.db import database, user_table
class UserRepository(IUserRepository):

    async def register_user(self, user: UserIn) -> Any | None:
        if await self.get_by_email(user.email):
            return None
        user.password = hash_password(user.password)
        query = user_table.insert().values(**user.model_dump())
        new_user_uuid = await database.execute(query)
        return await self.get_by_uuid(new_user_uuid)

    async def get_by_uuid(self, uuid: UUID5) -> Any | None:
        query = user_table \
            .select() \
            .where(user_table.c.id == uuid)
        user = await database.fetch_one(query)
        return user

    async def get_by_email(self, email: str) -> Any | None:
        query = user_table \
            .select() \
            .where(user_table.c.email == email)
        user = await database.fetch_one(query)
        return user

    async def get_all(self) -> list[Any]:
        query = user_table.select()
        users = await database.fetch_all(query)
        return users

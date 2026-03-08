from abc import ABC, abstractmethod
from typing import Any
from pydantic import UUID4

from src.core.domain.user import UserIn

class IUserRepository(ABC):
    @abstractmethod
    async def register_user(self, user: UserIn) -> Any | None:
        pass

    @abstractmethod
    async def get_by_uuid(self, uuid: UUID4) -> Any | None:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Any | None:
        pass

    @abstractmethod
    async def get_all(self) -> list[Any]:
        pass

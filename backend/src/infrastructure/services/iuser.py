from abc import ABC, abstractmethod
from pydantic import UUID4

from src.core.domain.user import UserIn
from src.infrastructure.dto.user import UserDTO
from src.infrastructure.dto.token import TokenDTO

class IUserService(ABC):
    @abstractmethod
    async def register_user(self, user: UserIn) -> UserDTO | None:
        pass

    @abstractmethod
    async def authenticate_user(self, user: UserIn) -> TokenDTO | None:
        pass

    @abstractmethod
    async def get_by_uuid(self, uuid: UUID4) -> UserDTO | None:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> UserDTO | None:
        pass

    @abstractmethod
    async def get_all(self) -> list[UserDTO]:
        pass

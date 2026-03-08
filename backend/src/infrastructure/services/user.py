from pydantic import UUID4

from src.core.domain.user import UserIn
from src.core.repositories.iuser import IUserRepository
from src.infrastructure.dto.user import UserDTO
from src.infrastructure.dto.token import TokenDTO
from src.infrastructure.services.iuser import IUserService
from src.infrastructure.utils.password import verify_password
from src.infrastructure.utils.token import generate_user_token


class UserService(IUserService):

    _repository: IUserRepository

    def __init__(self, repository: IUserRepository) -> None:
        self._repository = repository

    async def register_user(self, user: UserIn) -> UserDTO | None:
        return await self._repository.register_user(user)

    async def authenticate_user(self, user: UserIn) -> TokenDTO | None:
        if user_data := await self._repository.get_by_email(user.email):
            if verify_password(user.password, user_data.password):
                token_details = generate_user_token(user_data.id)
                return TokenDTO(token_type="Bearer", **token_details)
            return None

        return None

    async def get_by_uuid(self, uuid: UUID4) -> UserDTO | None:
        return await self._repository.get_by_uuid(uuid)

    async def get_by_email(self, email: str) -> UserDTO | None:
        return await self._repository.get_by_email(email)

    async def get_all(self) -> list[UserDTO]:
        users = await self._repository.get_all()

        return [UserDTO.model_validate(user, from_attributes=True) for user in users]

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, HTTPException

from src.container import Container
from src.core.domain.user import UserIn
from src.infrastructure.dto.token import TokenDTO
from src.infrastructure.dto.user import UserDTO
from src.infrastructure.services.iuser import IUserService

router = APIRouter()


@router.post("/register", response_model=UserDTO, status_code=201)
@inject
async def register_user(
    user: UserIn,
    service: IUserService = Depends(Provide[Container.user_service]),
) -> dict:
    if new_user := await service.register_user(user):
        return UserDTO(**dict(new_user))

    raise HTTPException(
        status_code=400,
        detail="The user with provided e-mail already exists",
    )


@router.post("/token", response_model=TokenDTO, status_code=200)
@inject
async def authenticate_user(
    user: UserIn,
    service: IUserService = Depends(Provide[Container.user_service]),
) -> dict:
    if token_details := await service.authenticate_user(user):
        print("user confirmed")
        return token_details

    raise HTTPException(
        status_code=401,
        detail="Provided incorrect credentials",
    )


@router.get("/users", response_model=list[UserDTO], status_code=200)
@inject
async def get_all_users(
    service: IUserService = Depends(Provide[Container.user_service]),
) -> list[UserDTO]:
    return await service.get_all()

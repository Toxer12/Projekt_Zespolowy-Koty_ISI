from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Factory, Singleton

from src.infrastructure.repositories.user import UserRepository

from src.infrastructure.services.user import UserService

class Container(DeclarativeContainer):
    user_repository = Singleton(UserRepository)

    user_service = Factory(
        UserService,
        repository = user_repository,
    )
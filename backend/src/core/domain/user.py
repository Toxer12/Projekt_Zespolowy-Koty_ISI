from pydantic import BaseModel, ConfigDict, UUID1


class UserIn(BaseModel):
    email: str
    password: str


class User(UserIn):
    id: UUID1

    model_config = ConfigDict(from_attributes=True, extra="ignore")

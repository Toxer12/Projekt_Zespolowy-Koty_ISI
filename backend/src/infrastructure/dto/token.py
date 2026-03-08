from datetime import datetime
from pydantic import BaseModel, ConfigDict

class TokenDTO(BaseModel):
    token_type: str
    user_token: str
    expires: datetime
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

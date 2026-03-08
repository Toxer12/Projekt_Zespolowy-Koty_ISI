from datetime import datetime, timedelta, timezone
from jose import jwt
from pydantic import UUID4
from src.infrastructure.utils.consts import (
    EXPIRATION_MINUTES,
    ALGORITHM,
    SECRET_KEY,
)

def generate_user_token(user_uuid: UUID4) -> dict:
    expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRATION_MINUTES)
    jwt_data = {"sub": str(user_uuid), "exp": expire, "type": "confirmation"}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return {"user_token": encoded_jwt, "expires": expire}

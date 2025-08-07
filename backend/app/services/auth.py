from datetime import datetime, timedelta
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlalchemy import select            # ← add this line

from ..core.config import get_settings
from ..db.models import SessionLocal, User


settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")


async def get_user_by_email(email: str) -> User | None:
    async with SessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == email)  # type: ignore
        )
        return result.scalar_one_or_none()


def _hash_pw(raw_pw: str) -> str:
    return bcrypt.hashpw(raw_pw.encode(), bcrypt.gensalt()).decode()


def _verify_pw(raw_pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(raw_pw.encode(), hashed.encode())


def _create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(days=7),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


async def authenticate(email: str, password: str) -> str:
    user = await get_user_by_email(email)
    if not user or not _verify_pw(password, user.hashed_pw):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return _create_token(user.id)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    async with SessionLocal() as db:
        user = await db.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return user


def get_current_admin(user=Depends(get_current_user)):
    if not user.is_admin:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

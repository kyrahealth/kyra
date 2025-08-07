from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional

from ...services.auth import authenticate, _hash_pw, get_user_by_email, get_current_user
from ...db.models import SessionLocal, User

router = APIRouter()


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginOut)
async def login(body: LoginIn):
    token = await authenticate(body.email, body.password)
    return {"access_token": token}


class RegisterIn(LoginIn):
    full_name: str | None = None
    date_of_birth: str | None = None
    gender: str | None = None
    sex: str | None = None
    country: str | None = None
    address: str | None = None
    ethnic_group: str | None = None
    long_term_conditions: str | None = None
    medications: str | None = None
    consent_to_data_storage: bool = False


@router.post("/register")
async def register(body: RegisterIn):
    existing = await get_user_by_email(body.email)
    if existing:
        return {"detail": "User exists"}

    async with SessionLocal() as db:
        user_kwargs = dict(email=body.email, hashed_pw=_hash_pw(body.password))
        if body.consent_to_data_storage:
            user_kwargs.update(
                full_name=body.full_name,
                date_of_birth=body.date_of_birth,
                gender=body.gender,
                sex=body.sex,
                country=body.country,
                address=body.address,
                ethnic_group=body.ethnic_group,
                long_term_conditions=body.long_term_conditions,
                medications=body.medications,
                consent_to_data_storage=True
            )
        else:
            user_kwargs["consent_to_data_storage"] = False
        db.add(User(**user_kwargs))
        await db.commit()
    return {"detail": "ok"}


@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {
        "email": user.email,
        "is_admin": user.is_admin,
        # "full_name": user.full_name,
        # "date_of_birth": user.date_of_birth,
        # "gender": user.gender,
        # "sex": user.sex,
        # "country": user.country,
        # "address": user.address,
        # "ethnic_group": user.ethnic_group,
        # "long_term_conditions": user.long_term_conditions,
        # "medications": user.medications,
        # "consent_to_data_storage": user.consent_to_data_storage,
        # "id": user.id,
    }


class UserUpdateIn(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    sex: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    ethnic_group: Optional[str] = None
    long_term_conditions: Optional[str] = None
    medications: Optional[str] = None
    consent_to_data_storage: Optional[bool] = None
    password: Optional[str] = None

@router.put("/me")
async def update_me(body: UserUpdateIn, user=Depends(get_current_user)):
    async with SessionLocal() as db:
        db_user = await db.get(User, user.id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        update_fields = body.dict(exclude_unset=True)
        if "password" in update_fields:
            db_user.hashed_pw = _hash_pw(update_fields.pop("password"))
        for k, v in update_fields.items():
            setattr(db_user, k, v)
        await db.commit()
        await db.refresh(db_user)
        return {
            "email": db_user.email,
            "is_admin": db_user.is_admin,
            "full_name": db_user.full_name,
            "date_of_birth": db_user.date_of_birth,
            "gender": db_user.gender,
            "sex": db_user.sex,
            "country": db_user.country,
            "address": db_user.address,
            "ethnic_group": db_user.ethnic_group,
            "long_term_conditions": db_user.long_term_conditions,
            "medications": db_user.medications,
            "consent_to_data_storage": db_user.consent_to_data_storage,
            "id": db_user.id,
        }

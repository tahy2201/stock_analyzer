from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies import get_current_user
from app.api.dependencies.db import DBSession
from app.shared.database import models
from app.shared.utils.security import hash_password, validate_password_policy, verify_password

router = APIRouter(prefix="/api/users", tags=["users"])


class ProfileUpdateRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=100)


class PasswordUpdateRequest(BaseModel):
    current_password: str
    new_password: str


class UserResponse(BaseModel):
    id: int
    login_id: str
    display_name: str
    role: str
    status: str

    model_config = ConfigDict(from_attributes=True)


@router.put("/me", response_model=UserResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    db: DBSession,
    current_user: models.User = Depends(get_current_user),
):
    current_user.display_name = payload.display_name
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/password")
def change_password(
    payload: PasswordUpdateRequest,
    db: DBSession,
    current_user: models.User = Depends(get_current_user),
):
    is_valid, msg = validate_password_policy(payload.new_password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    # verify current password
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="現在のパスワードが違います")

    current_user.password_hash = hash_password(payload.new_password)
    db.add(current_user)
    db.commit()
    return {"message": "password updated"}

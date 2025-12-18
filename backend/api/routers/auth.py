from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from api.dependencies import get_current_user
from api.dependencies.db import DBSession
from shared.database import models
from shared.utils.security import (
    generate_token,
    hash_password,
    validate_password_policy,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    login_id: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    id: int
    login_id: str
    display_name: str
    role: str
    status: str
    last_login_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class RegisterFromInviteRequest(BaseModel):
    token: str
    login_id: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)
    display_name: Optional[str] = None


@router.post("/login", response_model=UserResponse)
def login(request: Request, payload: LoginRequest, db: DBSession):
    user = db.query(models.User).filter(models.User.login_id == payload.login_id).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="IDまたはパスワードが不正です")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="アカウントが有効ではありません")

    request.session["user_id"] = user.id
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "logged out"}


@router.get("/me", response_model=UserResponse)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.post("/register", response_model=UserResponse)
def register_from_invite(
    request: Request,
    payload: RegisterFromInviteRequest,
    db: DBSession,
):
    is_valid, msg = validate_password_policy(payload.password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    invite = (
        db.query(models.Invite)
        .filter(models.Invite.token == payload.token)
        .first()
    )
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="招待が存在しません")

    if invite.used_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="招待は既に使用されています")
    if invite.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="招待は失効しています")
    if invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="招待の有効期限が切れています")

    # login_idユニークチェック（既存ユーザーと衝突しないこと）
    existing = db.query(models.User).filter(models.User.login_id == payload.login_id).first()
    if existing and existing.id != invite.provisional_user_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="このIDは既に使用されています")

    # 仮ユーザーが無い場合は作成（保険）
    if invite.provisional_user_id:
        user = db.get(models.User, invite.provisional_user_id)
    else:
        provisional_login = f"invite_{generate_token(4)}"
        user = models.User(
            login_id=provisional_login,
            display_name="招待中",
            role=invite.role,
            status="pending",
            password_hash=hash_password(generate_token(4)),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        invite.provisional_user_id = user.id

    # 本登録
    user.login_id = payload.login_id
    user.display_name = payload.display_name or payload.login_id
    user.password_hash = hash_password(payload.password)
    user.status = "active"
    user.role = invite.role
    invite.used_at = datetime.now(timezone.utc)
    db.add_all([user, invite])
    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id
    return user

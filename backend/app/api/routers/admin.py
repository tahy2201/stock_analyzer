from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies import get_current_admin
from app.api.dependencies.db import DBSession
from app.shared.database import models
from app.shared.utils.security import generate_token, hash_password, validate_password_policy

router = APIRouter(prefix="/api/admin", tags=["admin"])


class UserListResponse(BaseModel):
    id: int
    login_id: str
    display_name: str
    role: str
    status: str
    created_at: datetime
    last_login_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class InviteCreateRequest(BaseModel):
    role: str = Field("user", pattern="^(admin|user)$")


class InviteResponse(BaseModel):
    token: str
    expires_at: datetime
    role: str
    provisional_user_id: int


class PasswordResetRequest(BaseModel):
    new_password: str


@router.get("/users", response_model=list[UserListResponse])
def list_users(
    db: DBSession,
    current_admin=Depends(get_current_admin),
):
    users = db.query(models.User).order_by(models.User.id.asc()).all()
    return users


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: DBSession,
    current_admin=Depends(get_current_admin),
):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ユーザーが存在しません")
    if user.id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="自分自身は削除できません")
    db.delete(user)
    db.commit()
    return {"message": "deleted"}


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: int,
    payload: PasswordResetRequest,
    db: DBSession,
    current_admin=Depends(get_current_admin),
):
    is_valid, msg = validate_password_policy(payload.new_password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ユーザーが存在しません")
    user.password_hash = hash_password(payload.new_password)
    db.add(user)
    db.commit()
    return {"message": "password reset"}


@router.post("/invites", response_model=InviteResponse)
def create_invite(
    payload: InviteCreateRequest,
    db: DBSession,
    current_admin=Depends(get_current_admin),
):
    token = generate_token(32)
    placeholder_login = f"invite_{token[:8]}"
    provisional_user = models.User(
        login_id=placeholder_login,
        display_name="招待中",
        role=payload.role,
        status="pending",
        password_hash=hash_password(generate_token(4)),
    )
    db.add(provisional_user)
    db.commit()
    db.refresh(provisional_user)

    invite = models.Invite(
        token=token,
        role=payload.role,
        issued_by=current_admin.id,
        provisional_user_id=provisional_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.post("/invites/{token}/reissue", response_model=InviteResponse)
def reissue_invite(
    token: str,
    db: DBSession,
    current_admin=Depends(get_current_admin),
):
    invite = db.get(models.Invite, token)
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="招待が見つかりません")
    if invite.used_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="使用済みの招待は再発行できません")

    new_token = generate_token(32)
    invite.token = new_token
    invite.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    invite.revoked_at = None
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.post("/invites/{token}/revoke")
def revoke_invite(
    token: str,
    db: DBSession,
    current_admin=Depends(get_current_admin),
):
    invite = db.get(models.Invite, token)
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="招待が見つかりません")
    if invite.used_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="使用済みの招待は失効できません")
    invite.revoked_at = datetime.now(timezone.utc)
    db.add(invite)
    db.commit()
    return {"message": "revoked"}

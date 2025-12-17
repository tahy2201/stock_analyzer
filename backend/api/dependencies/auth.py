from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from shared.database.session import get_db
from shared.database import models


def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> models.User:
    user_id: Optional[int] = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ログインが必要です")

    user = db.get(models.User, user_id)
    if not user:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="無効なセッションです")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="アカウントが有効ではありません")
    return user


def get_current_admin(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="管理者権限が必要です")
    return current_user


def touch_last_login(user: models.User, db: Session) -> None:
    user.last_login_at = datetime.utcnow()
    db.add(user)
    db.commit()

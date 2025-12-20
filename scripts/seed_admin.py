"""
テスト/初期管理者ユーザーを挿入するユーティリティスクリプト。

使い方例:
    uv run python scripts/seed_admin.py --login admin --password YOUR_PASSWORD --display 管理者 --role admin

デフォルト:
    login_id=admin, password=YOUR_PASSWORD, display_name=管理者, role=admin

同じ login_id が存在する場合は何もしません。上書きしたい場合は --force を指定してください。
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def setup_import_path() -> None:
    """backend モジュールをインポートできるように sys.path を調整する。"""
    repo_root = Path(__file__).resolve().parents[1]
    backend_path = repo_root / "backend"
    sys.path.insert(0, str(backend_path))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed admin/test user into the database.")
    parser.add_argument("--login", default="admin", help="login_id to insert")
    parser.add_argument("--password", default="YOUR_PASSWORD", help="password (plaintext)")
    parser.add_argument("--display", default="管理者", help="display name")
    parser.add_argument(
        "--role",
        choices=["admin", "user"],
        default="admin",
        help="user role",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="update password/display/role if the login_id already exists",
    )
    return parser.parse_args()


def main() -> None:
    setup_import_path()

    from shared.database.session import SessionLocal  # type: ignore  # noqa: WPS433
    from shared.database import models  # type: ignore  # noqa: WPS433
    from shared.utils.security import hash_password  # type: ignore  # noqa: WPS433
    from sqlalchemy import select  # type: ignore  # noqa: WPS433

    args = parse_args()

    db = SessionLocal()
    try:
        existing = (
            db.execute(select(models.User).where(models.User.login_id == args.login))
            .scalar_one_or_none()
        )
        if existing and not args.force:
            print(f"exists: id={existing.id}, login_id={existing.login_id} (no changes)")
            return

        if existing and args.force:
            user = existing
            action = "updated"
        else:
            user = models.User(login_id=args.login)
            action = "created"
            db.add(user)

        user.display_name = args.display
        user.role = args.role
        user.status = "active"
        user.password_hash = hash_password(args.password)

        db.commit()
        db.refresh(user)
        print(f"{action}: id={user.id}, login_id={user.login_id}, role={user.role}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

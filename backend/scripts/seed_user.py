"""
テスト/初期ユーザーを挿入するユーティリティスクリプト。

使い方:
    # デフォルト（管理者と一般ユーザーの両方を作成）
    uv run python backend/scripts/seed_user.py

    # 任意のユーザーを作成
    uv run python backend/scripts/seed_user.py --login john --password YOUR_PASSWORD --display "John Doe" --role user

    # 既存ユーザーの上書き更新
    uv run python backend/scripts/seed_user.py --login admin --password YOUR_PASSWORD --force
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


def setup_import_path() -> None:
    """backend モジュールをインポートできるように sys.path を調整する。"""
    # backend/scripts/ から backend/ へ (親の親)
    backend_path = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(backend_path))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed user(s) into the database. By default, creates both admin and test users.",
        epilog="""
Examples:
  # Create default users (admin + testuser)
  %(prog)s

  # Create custom admin user
  %(prog)s --login admin --password YOUR_PASSWORD --display Admin --role admin

  # Create custom regular user
  %(prog)s --login john --password YOUR_PASSWORD --display "John Doe" --role user

  # Update existing user
  %(prog)s --login admin --password YOUR_PASSWORD --force
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--login", help="login_id to insert (if not specified, creates default users)")
    parser.add_argument("--password", help="password in plaintext")
    parser.add_argument("--display", help="display name")
    parser.add_argument(
        "--role",
        choices=["admin", "user"],
        help="user role: admin or user",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="update password/display/role if the login_id already exists",
    )
    return parser.parse_args()


def create_user(db, models, hash_password, login_id: str, password: str, display_name: str, role: str, force: bool = False) -> None:
    """ユーザーを作成または更新する。"""
    from sqlalchemy import select

    existing = db.execute(select(models.User).where(models.User.login_id == login_id)).scalar_one_or_none()

    if existing and not force:
        print(f"  exists: id={existing.id}, login_id={existing.login_id}, role={existing.role} (no changes)")
        return

    if existing and force:
        user = existing
        action = "updated"
    else:
        user = models.User(login_id=login_id)
        action = "created"
        db.add(user)

    user.display_name = display_name
    user.role = role
    user.status = "active"
    user.password_hash = hash_password(password)

    db.commit()
    db.refresh(user)
    print(f"  {action}: id={user.id}, login_id={user.login_id}, role={user.role}, display={user.display_name}")


def main() -> None:
    setup_import_path()

    # Load environment variables from .env
    from dotenv import load_dotenv
    repo_root = Path(__file__).resolve().parent.parent.parent
    env_file = repo_root / ".env"
    load_dotenv(dotenv_path=env_file)

    from shared.database.session import SessionLocal  # type: ignore  # noqa: WPS433
    from shared.database import models  # type: ignore  # noqa: WPS433
    from shared.utils.security import hash_password  # type: ignore  # noqa: WPS433

    args = parse_args()
    db = SessionLocal()

    try:
        # 引数が指定されている場合は単一ユーザー作成
        if args.login:
            if not args.password:
                print("Error: --password is required when --login is specified")
                sys.exit(1)

            display_name = args.display or args.login
            role = args.role or "user"

            print(f"Creating user '{args.login}'...")
            create_user(db, models, hash_password, args.login, args.password, display_name, role, args.force)

        # 引数なしの場合はデフォルトユーザー2つを作成
        else:
            print("Creating default users (admin + testuser)...")

            # 環境変数からパスワードを取得
            admin_password = os.getenv("SEED_ADMIN_PASSWORD")
            test_password = os.getenv("SEED_TEST_PASSWORD")

            if not admin_password or not test_password:
                print("Error: SEED_ADMIN_PASSWORD and SEED_TEST_PASSWORD must be set in .env")
                print("Please add the following to .env:")
                print("  SEED_ADMIN_PASSWORD=your_admin_password")
                print("  SEED_TEST_PASSWORD=your_test_password")
                sys.exit(1)

            create_user(db, models, hash_password, "admin", admin_password, "Admin", "admin", args.force)
            create_user(db, models, hash_password, "testuser", test_password, "Test User", "user", args.force)
            print("\nDefault users created successfully!")
            print("  admin: ***** (role: admin)")
            print("  testuser: ***** (role: user)")

    finally:
        db.close()


if __name__ == "__main__":
    main()

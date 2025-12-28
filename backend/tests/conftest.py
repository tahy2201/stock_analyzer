import os
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
from pytest import TempPathFactory
from sqlalchemy.orm import Session

from shared.database import models
from shared.database.session import SessionLocal, engine


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory: TempPathFactory) -> Path:
    """一時SQLite DBを用意してDATABASE_PATHに差し替え。"""
    db_dir = tmp_path_factory.mktemp("db")
    db_path = db_dir / "test.db"
    os.environ["DATABASE_PATH"] = str(db_path)
    return db_path


@pytest.fixture(scope="session")
def db_engine_session(test_db_path: Path) -> Iterator[tuple]:
    """テスト用エンジン/SessionLocalを初期化し、メタデータを管理。"""
    models.Base.metadata.create_all(bind=engine)
    yield engine, SessionLocal
    models.Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_db(db_engine_session):
    """テストごとにクリーンなテーブル状態へリセット。"""
    engine, _ = db_engine_session
    from shared.database import models

    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session(db_engine_session) -> Session:
    """SQLAlchemyセッションを提供。"""
    _, SessionLocal = db_engine_session
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def app(test_db_path):
    """FastAPIアプリ本体。"""
    from api.main import app

    return app


@pytest_asyncio.fixture
async def client(app):
    """ASGIクライアント（Cookieを保持）。"""
    import httpx

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as ac:
        yield ac


@pytest.fixture
def create_user(db_session) -> Callable:
    """テスト用ユーザーを作成するヘルパー。"""
    from shared.database import models
    from shared.utils.security import hash_password

    def _create_user(
        login_id: str,
        password: str,
        role: str = "user",
        status: str = "active",
        display_name: str | None = None,
    ) -> models.User:
        user = models.User(
            login_id=login_id,
            display_name=display_name or login_id,
            role=role,
            status=status,
            password_hash=hash_password(password),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _create_user

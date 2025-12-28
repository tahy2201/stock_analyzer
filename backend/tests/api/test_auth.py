import pytest


@pytest.mark.asyncio
async def test_login_success(client, create_user):
    create_user(login_id="alice", password="Passw0rd!", role="user", status="active")

    res = await client.post("/api/auth/login", json={"login_id": "alice", "password": "Passw0rd!"})
    assert res.status_code == 200
    data = res.json()
    assert data["login_id"] == "alice"
    assert data["role"] == "user"

    # セッション継続確認
    me = await client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["login_id"] == "alice"


@pytest.mark.asyncio
async def test_login_wrong_password(client, create_user):
    create_user(login_id="bob", password="Correct123", role="user", status="active")

    res = await client.post("/api/auth/login", json={"login_id": "bob", "password": "Wrong123"})
    assert res.status_code == 401
    assert "不正" in res.json()["detail"]

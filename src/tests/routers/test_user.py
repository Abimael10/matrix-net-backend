import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.usefixtures("db")

async def register_user(
    async_client: AsyncClient, 
    email: str, 
    password: str
):
    return await async_client.post(
        "/api/register",
        json= {
            "email": email,
            "password": password
        }
    )

@pytest.mark.anyio
async def test_register_user(async_client: AsyncClient):

    response = await register_user(
        async_client, 
        "test@example.com", 
        "12345"
    )

    assert response.status_code == 201
    assert "User created" in response.json()["detail"]

@pytest.mark.anyio
async def test_register_user_already_exists(
    async_client: AsyncClient, registered_user: dict
):
    response = await register_user(
        async_client, 
        registered_user["email"], 
        registered_user["password"]
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

@pytest.mark.anyio
async def test_login_user_not_exists(async_client: AsyncClient):
    response = await async_client.post(
        "/api/token",
        data={
            "username": "email@email.com",
            "password": "1234tired."
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 401

@pytest.mark.anyio
async def test_login_registered_user(
    async_client: AsyncClient,
    registered_user: dict  # Now users are auto-confirmed, so this test should succeed
):
    response = await async_client.post(
        "/api/token",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"]
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200  # Now succeeds because users are auto-confirmed

@pytest.mark.anyio
async def test_login_confirmed_user(async_client: AsyncClient, confirmed_user: dict):
    response = await async_client.post(
        "/api/token",
        data={
            "username": confirmed_user["email"],
            "password": confirmed_user["password"]
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200

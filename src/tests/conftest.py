from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src.db import database, user_table
from src.main import app
#from src.routers.post import comment_table, post_table

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture
def client() -> Generator:
   yield TestClient(app)

@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator:
    await database.connect()
    yield
    await database.disconnect()

@pytest.fixture()
async def async_client() -> AsyncGenerator:
    """A client for making asynchronous requests to the app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

@pytest.fixture()
async def registered_user(async_client: AsyncClient) -> dict:
    user_details = {"email": "test@example.net", "password": "1234"}
    await async_client.post("/api/register", json=user_details)

    query = user_table.select().where(user_table.c.email == user_details["email"])

    user = await database.fetch_one(query)

    user_details["id"] = user.id

    return user_details

@pytest.fixture()
async def logged_in_token(async_client: AsyncClient, registered_user: dict) -> str:
    response = await async_client.post("/api/token", json=registered_user)

    return response.json()["access_token"]
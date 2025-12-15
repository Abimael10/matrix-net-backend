from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src.db import database, user_table, post_table, comment_table, likes_table
from src.main import app
#from src.routers.post import comment_table, post_table

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture()
def client() -> Generator:
   yield TestClient(app)

@pytest.fixture()
async def db(request) -> AsyncGenerator:
    """
    DB fixture for integration/API tests. Opt-in via @pytest.mark.usefixtures("db")
    or module-level pytestmark. Skipped for pure unit tests.
    """
    if request.node.get_closest_marker("no_db"):
        yield
        return
    await database.connect()
    # Ensure a clean database state before each test
    # Delete in child-to-parent order to satisfy foreign key constraints
    await database.execute(likes_table.delete())
    await database.execute(comment_table.delete())
    await database.execute(post_table.delete())
    await database.execute(user_table.delete())

    # Reset SQLite autoincrement sequences if using SQLite
    try:
        await database.execute(
            "DELETE FROM sqlite_sequence WHERE name IN ('users','posts','likes','comments')"
        )
    except Exception:
        # Ignore for non-SQLite databases
        pass
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
async def confirmed_user(registered_user: dict) -> dict:
    query = (
        user_table.update()
        .where(user_table.c.email == registered_user["email"])
        .values(confirmed=True)
    )
    await database.execute(query)

    return registered_user

@pytest.fixture()
async def logged_in_token(async_client: AsyncClient, confirmed_user: dict) -> str:
    response = await async_client.post("/api/token", json=confirmed_user)

    return response.json()["access_token"]

#@pytest.fixture(autouse=True)
#def mock_httpx_client(mocker):
#    mocked_client = mocker.patch("src.tasks.httpx.AsyncClient")
#
#    mocked_async_client = Mock()
#    response = Response(status_code=200, content="", request=Request("POST", "//"))
#    mocked_async_client.post = AsyncMock(return_value=response)
#    mocked_client.return_value.__aenter__.return_value = mocked_async_client

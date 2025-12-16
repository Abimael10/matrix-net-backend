from typing import AsyncGenerator, Generator
import os

# Force test configuration for all imports
#os.environ.setdefault("ENV", "test")
# Use a file-backed DB so async/sync connections share the same schema/data
#os.environ.setdefault("TEST_DATABASE_URI", "sqlite:///./test.db")

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src import security
from src.db import SessionLocal, user_table, post_table, comment_table, likes_table
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
    Uses synchronous SQLAlchemy session for cleanup to avoid async driver issues.
    """
    if request.node.get_closest_marker("no_db"):
        yield
        return
    with SessionLocal() as session:
        session.execute(likes_table.delete())
        session.execute(comment_table.delete())
        session.execute(post_table.delete())
        session.execute(user_table.delete())
        session.commit()
    yield

@pytest.fixture()
async def async_client() -> AsyncGenerator:
    """A client for making asynchronous requests to the app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver", timeout=5.0) as ac:
        yield ac


@pytest.fixture(scope="session", autouse=True)
def patch_security_db_access():
    """
    Patch security helpers to rely on synchronous SQLAlchemy queries instead of the async
    `databases` client, which can hang in this environment.
    """

    from types import SimpleNamespace

    def _to_user(row):
        return SimpleNamespace(**dict(row)) if row else None

    def _fetch_user_by_email(email: str):
        with SessionLocal() as session:
            row = session.execute(user_table.select().where(user_table.c.email == email)).mappings().first()
            return _to_user(row)

    def _fetch_user_by_username(username: str):
        with SessionLocal() as session:
            row = session.execute(user_table.select().where(user_table.c.username == username)).mappings().first()
            return _to_user(row)

    async def get_user_by_email(email: str):
        row = _fetch_user_by_email(email)
        return row

    async def get_user_by_username(username: str):
        row = _fetch_user_by_username(username)
        return row

    async def authenticate_user(email: str, password: str):
        user = _fetch_user_by_email(email)
        if not user or not security.verify_password(password, user.password):
            raise security.create_credentials_exception("Invalid email or password")
        return user

    async def get_user(email: str):
        return await get_user_by_email(email)

    security.get_user_by_email = get_user_by_email  # type: ignore[assignment]
    security.get_user_by_username = get_user_by_username  # type: ignore[assignment]
    security.authenticate_user = authenticate_user  # type: ignore[assignment]
    security.get_user = get_user  # type: ignore[assignment]

@pytest.fixture()
async def registered_user(async_client: AsyncClient) -> dict:
    user_details = {"email": "test@example.net", "password": "1234"}
    response = await async_client.post("/api/register", json=user_details)
    assert response.status_code == 201, response.text

    with SessionLocal() as session:
        row = session.execute(user_table.select().where(user_table.c.email == user_details["email"])).mappings().first()
        user_details["id"] = row["id"]

    return user_details

@pytest.fixture()
async def confirmed_user(registered_user: dict) -> dict:
    with SessionLocal() as session:
        session.execute(
            user_table.update()
            .where(user_table.c.email == registered_user["email"])
            .values(confirmed=True)
        )
        session.commit()

    return registered_user

@pytest.fixture()
async def logged_in_token(async_client: AsyncClient, confirmed_user: dict) -> str:
    response = await async_client.post(
        "/api/token",
        data={"username": confirmed_user["email"], "password": confirmed_user["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    return response.json()["access_token"]

#@pytest.fixture(autouse=True)
#def mock_httpx_client(mocker):
#    mocked_client = mocker.patch("src.tasks.httpx.AsyncClient")
#
#    mocked_async_client = Mock()
#    response = Response(status_code=200, content="", request=Request("POST", "//"))
#    mocked_async_client.post = AsyncMock(return_value=response)
#    mocked_client.return_value.__aenter__.return_value = mocked_async_client

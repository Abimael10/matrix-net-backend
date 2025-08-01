from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src.db import database
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
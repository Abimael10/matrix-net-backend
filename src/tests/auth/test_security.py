import pytest
from jose import jwt

from src import security

def test_access_token_expire_minutes():
    assert security.access_token_expire_minutes() == 30

def test_create_access_token():
    token = security.create_access_token("email@email.com")
    assert {"sub": "email@email.com"}.items() <= jwt.decode(
        token, key=security.KEY, algorithms=[security.ALGORITHM]
    ).items()

@pytest.mark.anyio
async def test_get_user(registered_user: dict):
    user = await security.get_user(registered_user["email"])

    assert user.email == registered_user["email"]

@pytest.mark.anyio
async def test_get_user_not_found():
    user = await security.get_user("test@example.com")

    assert user is None

@pytest.mark.anyio
async def test_authenticate_user(registered_user: dict):
    user = await security.authenticate_user(
        registered_user["email"], registered_user["password"]
    )
    assert user.email == registered_user["email"]

@pytest.mark.anyio
async def test_authenticate_user_not_found():
    with pytest.raises(security.HTTPException):
        await security.authenticate_user("testblabla@email.com", "1234.")

@pytest.mark.anyio
async def test_authenticate_user_with_wrong_password(registered_user: dict):
    with pytest.raises(security.HTTPException):
        await security.authenticate_user(registered_user["email"], "wrong password")

@pytest.mark.anyio
async def test_get_current_user(registered_user: dict):
    token = security.create_access_token(registered_user["email"])
    user = await security.get_current_user(token)

    assert user.email == registered_user["email"]

@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    with pytest.raises(security.HTTPException):
        await security.get_current_user("Invalid token")
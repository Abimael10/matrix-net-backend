import datetime
import logging
from typing import Annotated, Literal

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

from passlib.context import CryptContext
from src.config import config
from jose import jwt, ExpiredSignatureError, JWTError

from src.db import database, user_table

logger = logging.getLogger(__name__)

KEY = config.SECRET_KEY
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"])

def create_credentials_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )

def access_token_expire_minutes() -> int:
    return 30 #30 minutes

def refresh_token_expire_days() -> int:
    return 10080  # 7 days

def create_access_token(email: str):
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "access"}
    encoded_jwt = jwt.encode(jwt_data, KEY, algorithm = ALGORITHM)

    return encoded_jwt

def create_refresh_token(email: str):
    """Create a refresh token with longer expiration"""
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        days=refresh_token_expire_days()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "refresh"}
    encoded_jwt = jwt.encode(jwt_data, KEY, algorithm = ALGORITHM)

    return encoded_jwt

def get_subject_for_token_type(
    token: str, type: Literal["access", "refresh"]
) -> str:
    try:
        payload = jwt.decode(token, key=KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError as e:
        raise create_credentials_exception("Token has expired") from e
    except JWTError as e:
        raise create_credentials_exception("Invalid token") from e

    email = payload.get("sub")
    if email is None:
        raise create_credentials_exception("Token is missing 'sub' field")

    token_type = payload.get("type")
    if token_type is None or token_type != type:
        raise create_credentials_exception(
            f"Token has incorrect type, expected '{type}'"
        )

    return email

def get_password_hash(password: str) -> str:
    # bcrypt has a 72-byte limit; truncate to prevent errors
    password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(password_bytes)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt has a 72-byte limit; truncate to match hashing behavior
    password_bytes = plain_password.encode('utf-8')[:72]
    return pwd_context.verify(password_bytes, hashed_password)

async def get_user_by_email(email: str):
    logger.info(f"Fetching user from database for email: {email}")
    query = user_table.select().where(user_table.c.email == email)
    result = await database.fetch_one(query)

    if result:
        logger.info(f"User found for email {email}: user_id={result.id}")
        return result
    else:
        logger.info(f"No user found for email {email}")
        return None

async def get_user(email: str):
    """Compatibility helper used in tests."""
    return await get_user_by_email(email)

async def get_user_by_username(username: str):
    logger.info(f"Fetching user from database for username: {username}")
    query = user_table.select().where(user_table.c.username == username)
    result = await database.fetch_one(query)

    if result:
        logger.info(f"User found for username {username}: user_id={result.id}")
        return result
    else:
        logger.info(f"No user found for username {username}")
        return None

async def authenticate_user(email: str, password: str):
    user = await get_user_by_email(email)

    if not user:
        raise create_credentials_exception("Invalid email or password")

    if not verify_password(password, user.password):
        raise create_credentials_exception("Invalid email or password")

    # No email confirmation required - all registered users are automatically confirmed
    return user

#Adding the dependency injection to reduce the amount of code related to adding this scheme
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    email = get_subject_for_token_type(token, "access")
    
    user = await get_user_by_email(email=email)
    if user is None:
        raise create_credentials_exception("Could not find user for this token")
    
    return user

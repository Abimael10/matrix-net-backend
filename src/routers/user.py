import logging
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Request, Depends

from src.models.user import UserI, UserLogin
from src.security import (
    get_password_hash,
    get_user_by_email,
    get_user_by_username,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_confirmation_token,
    get_subject_for_token_type,
    get_current_user,
)
from src.auth_tasks.send_confirm_email import send_email

from src.db import database, user_table

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/api/register", status_code=201)
async def register_user(user: UserI, request: Request):
    if await get_user_by_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists",
        )
    if await get_user_by_username(user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    hashed_password = get_password_hash(user.password)
    # This is wrong, I will handle hashing the password later after tests
    query = user_table.insert().values(
        username=user.username, 
        email=user.email, 
        password=hashed_password
        )

    await database.execute(query)

    # Generate confirmation token and send email
    confirmation_token = create_confirmation_token(user.email)
    confirmation_link = f"{request.url_for('confirm_email', token=confirmation_token)}"

    # Basic HTML email body
    email_body = f"""
    <h1>Email Confirmation</h1>
    <p>Please click the link below to confirm your email address:</p>
    <a href="{confirmation_link}">Confirm Email</a>
    """

    send_email(
        subject="Sentinel - Email Confirmation", recipient=user.email, body=email_body
    )

    return {"detail": "User created. A confirmation email has been sent."}


@router.post("/api/token")
async def login(user: UserLogin):
    user = await authenticate_user(user.email, user.password)
    access_token = create_access_token(user.email)
    refresh_token = create_refresh_token(user.email)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/api/token/refresh/")
async def refresh_token(refresh_data: dict):
    """
    Refresh access token using refresh token
    """
    refresh_token = refresh_data.get("refresh")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token is required"
        )

    try:
        # Validate refresh token and get email
        email = get_subject_for_token_type(refresh_token, "refresh")

        # Check if user still exists and is confirmed
        user = await get_user_by_email(email)
        if not user or not user.confirmed:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # Create new access token
        new_access_token = create_access_token(email)

        return {"access": new_access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )


@router.get("/api/user/me/")
async def get_current_user_info(
    current_user: Annotated[UserI, Depends(get_current_user)],
):
    """
    Get current authenticated user information
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "confirmed": current_user.confirmed,
    }


@router.get("/api/confirm/{token}")
async def confirm_email(token: str):
    email = get_subject_for_token_type(token, "confirmation")
    query = (
        user_table.update().where(user_table.c.email == email).values(confirmed=True)
    )

    await database.execute(query)
    return {"detail": "User confirmed. You may close this window."}

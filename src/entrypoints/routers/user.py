import logging
from typing import Annotated

import sqlalchemy
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from src.db import database, user_table
from src.entrypoints.schemas.user import UserI, UserLogin, UserProfileUpdate, UserRegister
from src.entrypoints.schemas.user_settings import ChangePasswordRequest, DeleteAccountRequest
from src import security
from src.security import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_subject_for_token_type,
    get_user_by_email,
)
from src.domain import commands, exceptions
from src.views import users as user_views
from src.bootstrap import bootstrap

router = APIRouter()

logger = logging.getLogger(__name__)


def get_bus(request: Request):
    # Use global helper for now
    from src.bootstrap import get_message_bus
    return get_message_bus()


@router.post("/api/register", status_code=201)
async def register_user(user: UserRegister, request: Request, background_tasks: BackgroundTasks):
    bus = get_bus(request)
    cmd = commands.RegisterUser(
        email=user.email,
        username=user.username,
        password=user.password,
        bio=user.bio,
        location=getattr(user, "location", None),
        avatar_url=user.avatar_url,
    )
    try:
        bus.handle(cmd)
    except exceptions.UserExists as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"detail": "User created successfully. No email verification required."}


@router.post("/api/token")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Token issuer for both JSON clients and OAuth2 password flow (form-encoded).
    - JSON: {"email": "...", "password": "..."}
    - Form: username/password (Swagger OAuth2 password flow)
    """
    login_email = None
    login_password = None

    # Prefer JSON if sent
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            payload = await request.json()
            login_email = payload.get("email") or payload.get("username")
            login_password = payload.get("password")
        except Exception:
            login_email = login_password = None

    # Fallback to form (Swagger)
    if not login_email or not login_password:
        login_email = form_data.username
        login_password = form_data.password

    if not login_email or not login_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email/username and password are required",
        )

    user_db = await authenticate_user(login_email, login_password)
    access_token = create_access_token(user_db.email)
    refresh_token = create_refresh_token(user_db.email)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/api/token/refresh/")
async def refresh_token(refresh_data: dict):
    """
    Refresh access token using refresh token.
    Expected payload: {"refresh_token": "<token>"}.
    """
    refresh_token_value = refresh_data.get("refresh_token")
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required (payload key: 'refresh_token')",
        )

    try:
        # Validate refresh token and get email
        email = get_subject_for_token_type(refresh_token_value, "refresh")

        # Check if user still exists
        user = await get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # Create new access token
        new_access_token = create_access_token(email)

        return {"access_token": new_access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )


@router.get("/api/user/me/")
async def get_current_user_info(
    request: Request,
    current_user: Annotated[UserI, Depends(get_current_user)],
):
    profile = await user_views.get_profile_with_stats(current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


@router.patch("/api/user/me/", status_code=200)
async def update_current_user_profile(
    request: Request,
    payload: UserProfileUpdate,
    current_user: Annotated[UserI, Depends(get_current_user)],
):
    bus = get_bus(request)
    cmd = commands.UpdateProfile(
        user_id=current_user.id,
        bio=payload.bio if "bio" in payload.model_fields_set else None,
        location=payload.location if "location" in payload.model_fields_set else None,
        avatar_url=None,
    )
    if all(v is None for v in (cmd.bio, cmd.location, cmd.avatar_url)):
        return {"detail": "No fields to update"}
    bus.handle(cmd)
    profile = await user_views.get_profile_with_stats(current_user.id)
    return profile




@router.get("/api/admin/database-info")
async def get_database_info():
    """
    Shows database connection info and current state.
    WARNING: Secure this endpoint in production!
    """
    from src.config import config

    # Count users
    user_count_query = sqlalchemy.select(sqlalchemy.func.count()).select_from(user_table)
    user_count = await database.fetch_val(user_count_query)

    # Get database URI (sanitized)
    db_uri = config.DATABASE_URI
    if db_uri:
        # Hide password in connection string
        if '@' in db_uri and ':' in db_uri:
            parts = db_uri.split('@')
            credentials = parts[0].split('//')[-1]
            if ':' in credentials:
                user_part = credentials.split(':')[0]
                sanitized = db_uri.replace(credentials, f"{user_part}:****")
            else:
                sanitized = db_uri
        else:
            sanitized = db_uri
    else:
        sanitized = "Not configured"

    return {
        "database_uri": sanitized,
        "total_users": user_count,
        "is_connected": database.is_connected,
    }


# User settings models
@router.delete("/api/user", status_code=204)
async def delete_account(
    request: Request,
    payload: DeleteAccountRequest,
    current_user: Annotated[UserI, Depends(get_current_user)],
):
    bus = get_bus(request)
    # Optionally verify password before deletion
    if payload.password:
        user = await authenticate_user(current_user.email, payload.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid password")

    cmd = commands.DeleteAccount(user_id=current_user.id, verify_password_hash=None)
    bus.handle(cmd)
    return


@router.post("/api/user/change-password", status_code=200)
async def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    current_user: Annotated[UserI, Depends(get_current_user)],
):
    # Verify old password
    user = await authenticate_user(current_user.email, payload.old_password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid old password")
    bus = get_bus(request)
    new_hash = security.get_password_hash(payload.new_password)
    cmd = commands.ChangePassword(user_id=current_user.id, new_password_hash=new_hash)
    bus.handle(cmd)
    logger.info(f"Password changed for user_id={current_user.id}")
    return {"detail": "Password changed successfully."}

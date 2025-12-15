import logging
from typing import Annotated

import sqlalchemy
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from src.db import database, likes_table, post_table, user_table
from src.models.user import UserI, UserLogin, UserProfileUpdate, UserRegister
from src.models.user_settings import ChangePasswordRequest, DeleteAccountRequest
from src.security import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_password_hash,
    get_subject_for_token_type,
    get_user_by_email,
    get_user_by_username,
)

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/api/register", status_code=201)
async def register_user(user: UserRegister, background_tasks: BackgroundTasks):
    logger.info(f"=== REGISTRATION START === Email: {user.email}")

    # Check if user already exists by email
    existing_user = await get_user_by_email(user.email)
    logger.info(f"get_user_by_email returned: {existing_user} (type: {type(existing_user)})")

    if existing_user is not None:
        logger.error(f"REGISTRATION BLOCKED: email {user.email} already exists (user_id: {existing_user.id})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists",
        )

    logger.info(f"Email {user.email} is available - proceeding with registration")

    # If username is provided, ensure it is unique; else derive from email
    if user.username:
        existing_username = await get_user_by_username(user.username)
        if existing_username is not None:
            logger.error(f"REGISTRATION BLOCKED: username {user.username} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )
        username = user.username
    else:
        # Derive a default username from the email local-part
        base_username = user.email.split("@")[0]
        candidate = base_username
        suffix = 1
        # Ensure uniqueness by appending numeric suffix if needed
        check_username = await get_user_by_username(candidate)
        while check_username is not None:
            suffix += 1
            candidate = f"{base_username}{suffix}"
            check_username = await get_user_by_username(candidate)
        username = candidate

    logger.info(f"Username '{username}' is available - creating user")

    hashed_password = get_password_hash(user.password)
    query = user_table.insert().values(
        username=username,
        email=user.email,
        password=hashed_password,
        bio=user.bio,
        location=getattr(user, "location", None),
        avatar_url=user.avatar_url,
        confirmed=True,  # Auto-confirm users - no email verification required
    )

    user_id = await database.execute(query)
    logger.info(f"User created successfully with ID: {user_id}, email: {user.email}")

    return {"detail": "User created successfully. No email verification required."}


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

        # Check if user still exists
        user = await get_user_by_email(email)
        if not user:
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
    # Compute aggregate fields
    posts_count_query = (
        sqlalchemy.select(sqlalchemy.func.count())
        .select_from(post_table)
        .where(post_table.c.user_id == current_user.id)
    )
    likes_received_query = (
        sqlalchemy.select(sqlalchemy.func.count())
        .select_from(
            likes_table.join(post_table, likes_table.c.post_id == post_table.c.id)
        )
        .where(post_table.c.user_id == current_user.id)
    )
    posts_count = await database.fetch_val(posts_count_query) or 0
    likes_received = await database.fetch_val(likes_received_query) or 0
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "confirmed": current_user.confirmed,
        "bio": current_user.bio,
        "location": current_user.location,
        "avatar_url": current_user.avatar_url,
        "created_at": current_user.created_at,
        "posts_count": posts_count,
        "likes_received": likes_received,
    }


@router.patch("/api/user/me/", status_code=200)
async def update_current_user_profile(
    payload: UserProfileUpdate,
    current_user: Annotated[UserI, Depends(get_current_user)],
):
    # Only include fields explicitly provided (allow clearing by sending empty/whitespace)
    update_data = {}
    if "bio" in payload.model_fields_set:
        update_data["bio"] = payload.bio
    if "location" in payload.model_fields_set:
        update_data["location"] = payload.location

    if not update_data:
        return {"detail": "No fields to update"}

    query = (
        user_table.update()
        .where(user_table.c.id == current_user.id)
        .values(**update_data)
    )
    await database.execute(query)

    # Reuse the same response shape as get_current_user_info for consistency
    # Fetch aggregates
    posts_count_query = (
        sqlalchemy.select(sqlalchemy.func.count())
        .select_from(post_table)
        .where(post_table.c.user_id == current_user.id)
    )
    likes_received_query = (
        sqlalchemy.select(sqlalchemy.func.count())
        .select_from(
            likes_table.join(post_table, likes_table.c.post_id == post_table.c.id)
        )
        .where(post_table.c.user_id == current_user.id)
    )
    posts_count = await database.fetch_val(posts_count_query) or 0
    likes_received = await database.fetch_val(likes_received_query) or 0

    # Fetch fresh user row
    refreshed = await database.fetch_one(
        user_table.select().where(user_table.c.id == current_user.id)
    )
    return {
        "id": refreshed.id,
        "username": refreshed.username,
        "email": refreshed.email,
        "confirmed": refreshed.confirmed,
        "bio": refreshed.bio,
        "location": refreshed.location,
        "avatar_url": refreshed.avatar_url,
        "created_at": refreshed.created_at,
        "posts_count": posts_count,
        "likes_received": likes_received,
    }




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
    payload: DeleteAccountRequest,
    current_user: Annotated[UserI, Depends(get_current_user)],
):
    # Optionally verify password before deletion
    if payload.password:
        user = await authenticate_user(current_user.email, payload.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid password")

    # Delete user and all related data in a transaction (posts, likes, comments, user)
    from src.db import comment_table

    async with database.transaction():
        # 1. Delete all comments made by the user (prevents orphaned comments)
        await database.execute(
            comment_table.delete().where(comment_table.c.user_id == current_user.id)
        )
        # 2. Delete all likes made by the user
        await database.execute(
            likes_table.delete().where(likes_table.c.user_id == current_user.id)
        )
        # 3. Delete all comments and likes on the user's posts, then the posts
        user_posts = await database.fetch_all(
            post_table.select().where(post_table.c.user_id == current_user.id)
        )
        for post in user_posts:
            # Delete comments on each post (prevents orphaned comments if post id reused)
            await database.execute(
                comment_table.delete().where(comment_table.c.post_id == post.id)
            )
            # Delete likes on each post
            await database.execute(
                likes_table.delete().where(likes_table.c.post_id == post.id)
            )
        # 4. Delete all posts made by the user
        await database.execute(
            post_table.delete().where(post_table.c.user_id == current_user.id)
        )
        # 5. Finally, delete the user
        await database.execute(
            user_table.delete().where(user_table.c.id == current_user.id)
        )
    # 6. Invalidate all tokens/sessions for this user (OWASP A7)
    # TODO: Implement token/session invalidation if using JWT or session store
    return


@router.post("/api/user/change-password", status_code=200)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: Annotated[UserI, Depends(get_current_user)],
):
    # Verify old password
    user = await authenticate_user(current_user.email, payload.old_password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid old password")
    # Hash and update new password
    new_hashed = get_password_hash(payload.new_password)
    await database.execute(
        user_table.update()
        .where(user_table.c.id == current_user.id)
        .values(password=new_hashed)
    )
    # Invalidate all other sessions/tokens for this user
    # TODO: Implement token/session invalidation if using JWT or session store
    # Log the password change event (no sensitive data)
    logger.info(f"Password changed for user_id={current_user.id}")
    return {"detail": "Password changed successfully."}

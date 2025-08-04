import logging
from fastapi import APIRouter, HTTPException, status, Request

from src.models.user import UserI
from src.security import (
    get_password_hash, 
    get_user, 
    authenticate_user, 
    create_access_token,
    create_confirmation_token,
    get_subject_for_token_type
)
from src.auth_tasks.send_confirm_email import send_email 

from src.db import database, user_table

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/api/register", status_code=201)
async def register_user(user: UserI, request: Request):
    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists"
        )
    hashed_password = get_password_hash(user.password)
    #This is wrong, I will handle hashing the password later after tests
    query = user_table.insert().values(email=user.email, password=hashed_password)

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
        subject="Sentinel - Email Confirmation",
        recipient=user.email,
        body=email_body
    )

    return {"detail": "User created. A confirmation email has been sent."}

@router.post("/api/token")
async def login(user: UserI):
    user = await authenticate_user(user.email, user.password)
    access_token = create_access_token(user.email)

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/api/confirm/{token}")
async def confirm_email(token: str):
    email = get_subject_for_token_type(token, "confirmation")
    query = (
        user_table.update().where(user_table.c.email == email).values(confirmed=True)
    )

    await database.execute(query)
    return {"detail": "User confirmed"}
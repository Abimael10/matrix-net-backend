import logging
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exception_handlers import http_exception_handler

#Keeping sentry off while testing and developing since it will create so many issues
import sentry_sdk

#from src.config import config
from src.config import config
from src.db import database
from src.log_config import configure_logging

from src.routers.post import router as post_router
from src.routers.user import router as user_router
from src.routers.upload import router as upload_router

sentry_sdk.init(
    dsn=config.SENTRY_DSN,
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

#Only use these middleware in dev, for PROD remember to change to the client domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://abimael.site", "https://matrix-frontend-lkr9.onrender.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)

app.add_middleware(CorrelationIdMiddleware)

app.include_router(post_router)
app.include_router(user_router)
app.include_router(upload_router)

@app.exception_handler(HTTPException)
async def http_exception_handle_logging(request, exc):
    logger.error(f"HTTPException: {exc.status_code} {exc.detail}")
    return await http_exception_handler(request, exc)

#This will the endopoint to test the sentry issues connection, normally it would
#create a 500 server error which is likely what we want and then track it in
#its dashboard, our initial test was successful so we comment it out.
#@app.get("/api/sentry-debug")
#async def trigger_error():
#    division_by_zero = 1 / 0
#    return division_by_zero

@app.get("/")
async def root():
    return {"message": "Server is running"}

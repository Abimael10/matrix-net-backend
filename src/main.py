import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from fastapi.exception_handlers import http_exception_handler

from src.db import database
from src.log_config import configure_logging
from src.routers.post import router as post_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

app.include_router(post_router)

@app.exception_handler(HTTPException)
async def http_exception_handle_logging(request, exc):
    logger.error(f"HTTPException: {exc.status_code} {exc.detail}")
    return await http_exception_handler(request, exc)

@app.get("/")
async def root():
    return {"message": "Server is running"}
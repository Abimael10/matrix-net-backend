from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.db import database
from src.routers.post import router as post_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

app.include_router(post_router)

@app.get("/")
async def root():
    return {"message": "Server is running"}
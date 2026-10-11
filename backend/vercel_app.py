"""Vercel entrypoint for the API mounted alongside the frontend at /api."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.main import app as backend_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Mounted applications do not receive lifespan events automatically.
    async with backend_app.router.lifespan_context(backend_app):
        yield


app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)
app.mount("/api", backend_app)

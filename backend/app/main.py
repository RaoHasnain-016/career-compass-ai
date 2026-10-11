import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import text

from app.database import Base, engine

# Import models so SQLAlchemy can register all tables
from app.models import (
    User,
    StudentProfile,
    Career,
    Recommendation,
    RoadmapStage,
    LearningResource,
    SavedCareer,
    ChatMessage,
    VideoResource,
)

from app.routes import (
    auth_routes,
    profile_routes,
    career_routes,
    recommendation_routes,
    resource_routes,
    roadmap_routes,
    chatbot_routes,
    saved_career_routes,
    admin_routes,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cloud deployments restore/migrate the database once, outside requests.
    default_auto_create = "false" if os.getenv("VERCEL") == "1" else "true"
    if os.getenv("DATABASE_AUTO_CREATE", default_auto_create).lower() == "true":
        Base.metadata.create_all(bind=engine)
        apply_startup_schema_patches()
    yield


app = FastAPI(
    title="Career Compass AI API",
    description="FastAPI backend for Career Compass AI",
    version="1.0.0",
    lifespan=lifespan,
)

LOCAL_DEV_ORIGIN_REGEX = (
    r"^http://("
    r"localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|"
    r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"192\.168\.\d{1,3}\.\d{1,3}|"
    r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}"
    r"):\d+$"
)


def apply_startup_schema_patches():
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE student_profiles
                ALTER COLUMN study_preference TYPE TEXT
                """
            )
        )


# CORS setup for React/Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_origin_regex=LOCAL_DEV_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    if os.getenv("VERCEL") != "1" and FRONTEND_INDEX.is_file():
        return FileResponse(FRONTEND_INDEX)

    return {
        "message": "Career Compass AI backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.get("/db-test")
def db_test():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return {
                "database": "connected",
                "result": result.scalar(),
            }
    except Exception:
        raise HTTPException(status_code=503, detail="Database is unavailable.") from None


# Register API routes
app.include_router(auth_routes.router)
app.include_router(profile_routes.router)
app.include_router(career_routes.router)
app.include_router(recommendation_routes.router)
app.include_router(resource_routes.router)
app.include_router(roadmap_routes.router)
app.include_router(chatbot_routes.router)
app.include_router(saved_career_routes.router)
app.include_router(admin_routes.router)


# In production, serve the React build from this same FastAPI origin. This
# keeps browser API requests same-origin and also supports React Router URLs.
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str):
    if os.getenv("VERCEL") == "1" or not FRONTEND_INDEX.is_file():
        raise HTTPException(status_code=404, detail="Not Found")

    requested_file = (FRONTEND_DIST / full_path).resolve()
    try:
        requested_file.relative_to(FRONTEND_DIST.resolve())
    except ValueError:
        raise HTTPException(status_code=404, detail="Not Found")

    if requested_file.is_file():
        return FileResponse(requested_file)

    # Unknown non-API paths belong to the React SPA; React Router handles them.
    return FileResponse(FRONTEND_INDEX)

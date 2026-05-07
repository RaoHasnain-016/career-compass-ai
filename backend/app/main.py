from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


app = FastAPI(
    title="Career Compass AI API",
    description="FastAPI backend for Career Compass AI",
    version="1.0.0",
)

LOCAL_DEV_ORIGIN_REGEX = (
    r"^http://("
    r"localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|"
    r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"192\.168\.\d{1,3}\.\d{1,3}|"
    r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}"
    r"):\d+$"
)


# Create tables automatically from models
Base.metadata.create_all(bind=engine)


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


apply_startup_schema_patches()


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
    except Exception as e:
        return {
            "database": "not connected",
            "error": str(e),
        }


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

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    if os.getenv("VERCEL") == "1":
        raise ValueError("Set DATABASE_URL to your hosted PostgreSQL connection string.")
    DATABASE_URL = "postgresql://postgres:password@localhost:5432/career_compass_ai"

# Some providers use the older URI scheme; SQLAlchemy requires postgresql.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine_options = {"pool_pre_ping": True, "connect_args": {"connect_timeout": 10}}
if os.getenv("VERCEL") == "1":
    # Use the database provider's pooled URL. Do not retain idle connections
    # independently in every serverless instance.
    engine_options["poolclass"] = NullPool

engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

if os.getenv("ENV", "development") == "development":
    env_path = Path(__file__).resolve().parents[1] / ".env" 
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Set it in backend/.env for development or via 'liara env:set' in production."
    )


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,    
    future=True
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


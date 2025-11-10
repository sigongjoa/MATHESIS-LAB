from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.app.core.config import settings

# Use psycopg2 for PostgreSQL connection
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
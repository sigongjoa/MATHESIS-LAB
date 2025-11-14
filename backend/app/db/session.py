from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from backend.app.core.config import settings

# Use the DATABASE_URL from settings, which will now point to PostgreSQL
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    print(f"--- get_db: Session created: {id(db)}")
    try:
        yield db
    finally:
        print(f"--- get_db: Session closed: {id(db)}")
        db.close()
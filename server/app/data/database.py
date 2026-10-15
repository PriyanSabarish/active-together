from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from app.config import settings
import logging
import os
load_dotenv()  # This explicitly forces python to read the .env file
logging.basicConfig()
# Not INFO: that logs every SQL statement with its bound values, which would put the
# coordinates of every search in the logs.
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# prediction_service/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
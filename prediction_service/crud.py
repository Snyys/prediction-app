# prediction_service/crud.py
from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional
from datetime import datetime


def get_prediction(db: Session, prediction_id: int) -> Optional[models.Prediction]:
    return db.query(models.Prediction).filter(models.Prediction.id == prediction_id).first()


def get_user_predictions(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Prediction]:
    return db.query(models.Prediction).filter(
        models.Prediction.user_id == user_id
    ).offset(skip).limit(limit).all()


def get_expired_predictions(db: Session) -> List[models.Prediction]:
    return db.query(models.Prediction).filter(
        models.Prediction.due_date <= datetime.utcnow(),
        models.Prediction.status == "pending"
    ).all()


def create_prediction(db: Session, prediction: schemas.PredictionCreate, user_id: int) -> models.Prediction:
    db_prediction = models.Prediction(
        **prediction.dict(),
        user_id=user_id
    )
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    return db_prediction


def update_prediction_status(
    db: Session,
    prediction_id: int,
    status: str
) -> Optional[models.Prediction]:
    db_prediction = get_prediction(db, prediction_id)
    if db_prediction:
        db_prediction.status = status
        db_prediction.checked_at = datetime.utcnow()
        db.commit()
        db.refresh(db_prediction)
    return db_prediction

def delete_prediction(db: Session, prediction_id: int) -> bool:
    db_prediction = get_prediction(db, prediction_id)
    if db_prediction:
        db.delete(db_prediction)
        db.commit()
        return True
    return False
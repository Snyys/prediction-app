# prediction_service/main.py
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from . import crud, models, schemas, tasks
from .database import get_db, engine
from auth_service.dependencies import get_current_user
from auth_service.schemas import UserResponse
import asyncio

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Prediction Service", version="1.0.0")


@app.post("/predictions/", response_model=schemas.PredictionResponse)
def create_prediction(
        prediction: schemas.PredictionCreate,
        db: Session = Depends(get_db),
        current_user: UserResponse = Depends(get_current_user)
):
    return crud.create_prediction(db=db, prediction=prediction, user_id=current_user.id)


@app.get("/predictions/", response_model=list[schemas.PredictionResponse])
def read_predictions(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: UserResponse = Depends(get_current_user)
):
    predictions = crud.get_user_predictions(db, user_id=current_user.id, skip=skip, limit=limit)
    return predictions


@app.get("/predictions/{prediction_id}", response_model=schemas.PredictionResponse)
def read_prediction(
        prediction_id: int,
        db: Session = Depends(get_db),
        current_user: UserResponse = Depends(get_current_user)
):
    db_prediction = crud.get_prediction(db, prediction_id=prediction_id)
    if db_prediction is None:
        raise HTTPException(status_code=404, detail="Prediction not found")

    if db_prediction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return db_prediction


@app.delete("/predictions/{prediction_id}")
def delete_prediction(
        prediction_id: int,
        db: Session = Depends(get_db),
        current_user: UserResponse = Depends(get_current_user)
):
    db_prediction = crud.get_prediction(db, prediction_id=prediction_id)
    if db_prediction is None:
        raise HTTPException(status_code=404, detail="Prediction not found")

    if db_prediction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    success = crud.delete_prediction(db, prediction_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prediction not found")

    return {"message": "Prediction deleted successfully"}


@app.post("/predictions/check-expired")
async def check_expired_predictions(background_tasks: BackgroundTasks):
    """Запуск проверки истекших предсказаний"""
    background_tasks.add_task(run_prediction_check)
    return {"status": "check_started"}


async def run_prediction_check():
    """Запуск проверки предсказаний"""
    checker = tasks.PredictionChecker()
    checker.check_expired_predictions()


@app.get("/health")
def health_check():
    return {"status": "healthy"}
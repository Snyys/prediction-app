from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import List

import models
import schemas
from database import engine, get_db, Base
from init_db import init_database
from security import (
    get_password_hash,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from dependencies import get_current_active_user

# Инициализируем базу данных
init_database()

app = FastAPI(
    title="Prediction App API",
    version="1.0.0",
    description="API для системы предсказаний с системой наград",
    docs_url="/docs",
    redoc_url="/redoc"
)


# API Endpoints
@app.get("/")
def read_root():
    return {"message": "Prediction App API Gateway"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        db_status = "connected"
    except:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "service": "api-gateway",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }


# Аутентификация
@app.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@app.post("/login", response_model=schemas.Token)
def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# Защищенные endpoints
@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user


@app.post("/predictions", response_model=schemas.PredictionResponse)
def create_prediction(
        prediction: schemas.PredictionCreate,
        current_user: models.User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    db_prediction = models.Prediction(
        title=prediction.title,
        description=prediction.description,
        user_id=current_user.id,
        predicted_date=prediction.predicted_date,
        expiration_date=prediction.expiration_date,
        confidence_level=prediction.confidence_level
    )

    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)

    return db_prediction


@app.get("/predictions", response_model=List[schemas.PredictionResponse])
def get_predictions(
        current_user: models.User = Depends(get_current_active_user),
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    predictions = db.query(models.Prediction).filter(
        models.Prediction.user_id == current_user.id
    ).offset(skip).limit(limit).all()

    return predictions


@app.put("/predictions/{prediction_id}/verify")
def verify_prediction(
        prediction_id: int,
        is_correct: bool,
        current_user: models.User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    prediction = db.query(models.Prediction).filter(
        models.Prediction.id == prediction_id,
        models.Prediction.user_id == current_user.id
    ).first()

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )

    prediction.status = "success" if is_correct else "failed"
    prediction.result = is_correct
    prediction.verified_at = datetime.utcnow()

    if is_correct:
        current_user.points += 100

    db.commit()

    return {
        "status": "verified",
        "prediction_id": prediction_id,
        "result": is_correct,
        "points_awarded": 100 if is_correct else 0
    }


@app.get("/rewards", response_model=List[schemas.RewardResponse])
def get_rewards(
        current_user: models.User = Depends(get_current_active_user),
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    rewards = db.query(models.Reward).filter(
        models.Reward.is_active == True
    ).offset(skip).limit(limit).all()

    return rewards


@app.post("/rewards/{reward_id}/redeem")
def redeem_reward(
        reward_id: int,
        current_user: models.User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    reward = db.query(models.Reward).filter(models.Reward.id == reward_id).first()

    if not reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found"
        )

    if current_user.points < reward.points_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not enough points. Required: {reward.points_required}, Available: {current_user.points}"
        )

    current_user.points -= reward.points_required
    db.commit()

    return {
        "reward_id": reward_id,
        "reward_name": reward.name,
        "points_spent": reward.points_required,
        "remaining_points": current_user.points
    }


@app.get("/stats")
def get_stats(
        current_user: models.User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    total_predictions = db.query(models.Prediction).filter(
        models.Prediction.user_id == current_user.id
    ).count()

    pending_predictions = db.query(models.Prediction).filter(
        models.Prediction.user_id == current_user.id,
        models.Prediction.status == "pending"
    ).count()

    successful_predictions = db.query(models.Prediction).filter(
        models.Prediction.user_id == current_user.id,
        models.Prediction.status == "success"
    ).count()

    return {
        "user_points": current_user.points,
        "total_predictions": total_predictions,
        "pending_predictions": pending_predictions,
        "successful_predictions": successful_predictions,
        "success_rate": successful_predictions / total_predictions if total_predictions > 0 else 0
    }


# Создаем тестовые награды при запуске
@app.on_event("startup")
def create_default_rewards():
    db = next(get_db())

    existing_rewards = db.query(models.Reward).count()
    if existing_rewards == 0:
        default_rewards = [
            models.Reward(
                name="Новичок предсказатель",
                description="Первое успешное предсказание",
                points_required=100
            ),
            models.Reward(
                name="Эксперт предсказаний",
                description="5 успешных предсказаний",
                points_required=500
            ),
            models.Reward(
                name="Мастер предвидения",
                description="10 успешных предсказаний",
                points_required=1000
            ),
        ]

        for reward in default_rewards:
            db.add(reward)

        db.commit()
        print("Default rewards created!")
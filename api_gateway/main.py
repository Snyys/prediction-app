# prediction_app/api_gateway/main.py - ОБНОВЛЯЕМ

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import List, Optional

import models
import schemas
import crud
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


# Существующие endpoints (register, login, health) остаются без изменений
# ... [остается тот же код что был ранее] ...

# РАСШИРЕННЫЕ ENDPOINTS ДЛЯ ПРЕДСКАЗАНИЙ

@app.get("/predictions/{prediction_id}", response_model=schemas.PredictionResponse)
def get_prediction(
        prediction_id: int,
        current_user: models.User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Получить конкретное предсказание"""
    prediction = crud.get_prediction(db, prediction_id)

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )

    if prediction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return prediction


@app.put("/predictions/{prediction_id}", response_model=schemas.PredictionResponse)
def update_prediction(
        prediction_id: int,
        prediction_update: schemas.PredictionUpdate,
        current_user: models.User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Обновить предсказание"""
    prediction = crud.get_prediction(db, prediction_id)

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )

    if prediction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    if prediction.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only update pending predictions"
        )

    return crud.update_prediction(db, prediction_id, prediction_update)


@app.delete("/predictions/{prediction_id}")
def delete_prediction(
        prediction_id: int,
        current_user: models.User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Удалить предсказание"""
    prediction = crud.get_prediction(db, prediction_id)

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )

    if prediction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    crud.delete_prediction(db, prediction_id)

    return {"message": "Prediction deleted successfully"}


@app.get("/predictions/filter/status", response_model=List[schemas.PredictionResponse])
def get_predictions_by_status(
        status: schemas.PredictionStatus = Query(..., description="Filter by status"),
        current_user: models.User = Depends(get_current_active_user),
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """Получить предсказания по статусу"""
    predictions = db.query(models.Prediction).filter(
        models.Prediction.user_id == current_user.id,
        models.Prediction.status == status.value
    ).offset(skip).limit(limit).all()

    return predictions


# РАСШИРЕННЫЕ ENDPOINTS ДЛЯ НАГРАД

@app.get("/rewards/my", response_model=List[schemas.UserRewardResponse])
def get_my_rewards(
        current_user: models.User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Получить мои полученные награды"""
    user_rewards = crud.get_user_rewards(db, current_user.id)

    # Добавляем название награды в ответ
    result = []
    for user_reward in user_rewards:
        reward_data = schemas.UserRewardResponse.from_orm(user_reward)
        reward_data.reward_name = user_reward.reward.name
        result.append(reward_data)

    return result


@app.get("/rewards/available", response_model=List[schemas.RewardResponse])
def get_available_rewards(
        current_user: models.User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Получить доступные для получения награды"""
    user_stats = crud.get_user_stats(db, current_user.id)
    all_rewards = crud.get_available_rewards(db)
    user_rewards = crud.get_user_rewards(db, current_user.id)
    awarded_reward_ids = [ur.reward_id for ur in user_rewards]

    # Фильтруем награды которые пользователь еще не получил
    available_rewards = [
        reward for reward in all_rewards
        if reward.id not in awarded_reward_ids
    ]

    return available_rewards


# СТАТИСТИКА И АНАЛИТИКА

@app.get("/stats/detailed", response_model=schemas.UserStats)
def get_detailed_stats(
        current_user: models.User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Получить детальную статистику"""
    return crud.get_user_stats(db, current_user.id)


@app.get("/analytics/success-rate")
def get_success_rate_analytics(
        current_user: models.User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Аналитика успешности предсказаний по времени"""
    # Группируем по месяцам
    monthly_stats = db.execute("""
        SELECT 
            DATE_TRUNC('month', created_at) as month,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
            AVG(confidence_level) as avg_confidence
        FROM predictions 
        WHERE user_id = :user_id
        GROUP BY DATE_TRUNC('month', created_at)
        ORDER BY month
    """, {"user_id": current_user.id}).fetchall()

    return [
        {
            "month": row[0].strftime("%Y-%m"),
            "total_predictions": row[1],
            "successful_predictions": row[2],
            "success_rate": row[2] / row[1] if row[1] > 0 else 0,
            "average_confidence": float(row[3]) if row[3] else 0
        }
        for row in monthly_stats
    ]


# АДМИН ENDPOINTS

@app.get("/admin/predictions", response_model=List[schemas.PredictionResponse])
def get_all_predictions_admin(
        current_user: models.User = Depends(get_current_active_user),
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """Админ: получить все предсказания (только для админов)"""
    if current_user.username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    predictions = db.query(models.Prediction).offset(skip).limit(limit).all()
    return predictions


@app.get("/admin/users/stats")
def get_all_users_stats(
        current_user: models.User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Админ: статистика всех пользователей"""
    if current_user.username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    users = crud.get_users(db)
    stats = []

    for user in users:
        user_stats = crud.get_user_stats(db, user.id)
        stats.append({
            "user_id": user.id,
            "username": user.username,
            **user_stats.dict()
        })

    return stats


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
            models.Reward(
                name="Оракул",
                description="20 успешных предсказаний",
                points_required=2000
            )
        ]

        for reward in default_rewards:
            db.add(reward)

        db.commit()
        print("Default rewards created!")
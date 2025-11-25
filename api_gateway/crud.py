# prediction_app/api_gateway/crud.py - НОВЫЙ ФАЙЛ

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import models
import schemas


# CRUD для пользователей
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def update_user_points(db: Session, user_id: int, points: int):
    user = get_user(db, user_id)
    if user:
        user.points += points
        db.commit()
        db.refresh(user)
    return user


# CRUD для предсказаний
def get_prediction(db: Session, prediction_id: int):
    return db.query(models.Prediction).filter(models.Prediction.id == prediction_id).first()


def get_predictions_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Prediction).filter(
        models.Prediction.user_id == user_id
    ).offset(skip).limit(limit).all()


def get_pending_predictions(db: Session):
    return db.query(models.Prediction).filter(
        models.Prediction.status == "pending"
    ).all()


def create_prediction(db: Session, prediction: schemas.PredictionCreate, user_id: int):
    db_prediction = models.Prediction(
        **prediction.dict(),
        user_id=user_id
    )
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    return db_prediction


def update_prediction(db: Session, prediction_id: int, prediction_update: schemas.PredictionUpdate):
    db_prediction = get_prediction(db, prediction_id)
    if db_prediction:
        update_data = prediction_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_prediction, field, value)
        db.commit()
        db.refresh(db_prediction)
    return db_prediction


def delete_prediction(db: Session, prediction_id: int):
    db_prediction = get_prediction(db, prediction_id)
    if db_prediction:
        db.delete(db_prediction)
        db.commit()
    return db_prediction


def verify_prediction(db: Session, prediction_id: int, is_correct: bool):
    prediction = get_prediction(db, prediction_id)
    if prediction:
        prediction.status = "success" if is_correct else "failed"
        prediction.result = is_correct
        prediction.verified_at = datetime.utcnow()

        if is_correct:
            prediction.user.points += 100
            # Проверяем и выдаем награды
            check_and_award_rewards(db, prediction.user_id)

        db.commit()
        db.refresh(prediction)
    return prediction


# CRUD для наград
def get_reward(db: Session, reward_id: int):
    return db.query(models.Reward).filter(models.Reward.id == reward_id).first()


def get_available_rewards(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Reward).filter(
        models.Reward.is_active == True
    ).offset(skip).limit(limit).all()


def create_user_reward(db: Session, user_id: int, reward_id: int):
    reward = get_reward(db, reward_id)
    user_reward = models.UserReward(
        user_id=user_id,
        reward_id=reward_id,
        points_awarded=reward.points_required
    )
    db.add(user_reward)
    db.commit()
    db.refresh(user_reward)
    return user_reward


def get_user_rewards(db: Session, user_id: int):
    return db.query(models.UserReward).filter(
        models.UserReward.user_id == user_id
    ).all()


# Бизнес-логика
def check_and_award_rewards(db: Session, user_id: int):
    """Проверяет и выдает награды пользователю"""
    user = get_user(db, user_id)
    if not user:
        return

    # Получаем статистику пользователя
    successful_predictions = db.query(models.Prediction).filter(
        models.Prediction.user_id == user_id,
        models.Prediction.status == "success"
    ).count()

    # Проверяем условия для наград
    available_rewards = get_available_rewards(db)
    user_rewards = get_user_rewards(db, user_id)
    awarded_reward_ids = [ur.reward_id for ur in user_rewards]

    for reward in available_rewards:
        if reward.id in awarded_reward_ids:
            continue

        # Условия для выдачи наград
        if reward.name == "Новичок предсказатель" and successful_predictions >= 1:
            create_user_reward(db, user_id, reward.id)
        elif reward.name == "Эксперт предсказаний" and successful_predictions >= 5:
            create_user_reward(db, user_id, reward.id)
        elif reward.name == "Мастер предвидения" and successful_predictions >= 10:
            create_user_reward(db, user_id, reward.id)
        elif reward.name == "Оракул" and successful_predictions >= 20:
            create_user_reward(db, user_id, reward.id)


def get_user_stats(db: Session, user_id: int) -> schemas.UserStats:
    """Получает статистику пользователя"""
    total_predictions = db.query(models.Prediction).filter(
        models.Prediction.user_id == user_id
    ).count()

    successful_predictions = db.query(models.Prediction).filter(
        models.Prediction.user_id == user_id,
        models.Prediction.status == "success"
    ).count()

    pending_predictions = db.query(models.Prediction).filter(
        models.Prediction.user_id == user_id,
        models.Prediction.status == "pending"
    ).count()

    user = get_user(db, user_id)
    available_rewards = len([
        r for r in get_available_rewards(db)
        if successful_predictions >= get_required_successes(r.name)
    ])

    return schemas.UserStats(
        total_predictions=total_predictions,
        successful_predictions=successful_predictions,
        pending_predictions=pending_predictions,
        success_rate=successful_predictions / total_predictions if total_predictions > 0 else 0,
        total_points=user.points if user else 0,
        available_rewards=available_rewards
    )


def get_required_successes(reward_name: str) -> int:
    """Возвращает количество успешных предсказаний для получения награды"""
    requirements = {
        "Новичок предсказатель": 1,
        "Эксперт предсказаний": 5,
        "Мастер предвидения": 10,
        "Оракул": 20
    }
    return requirements.get(reward_name, 999)
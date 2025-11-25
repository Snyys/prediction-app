from sqlalchemy.orm import Session
import models, schemas
from typing import Optional


def get_reward_rule(db: Session, rule_name: str) -> Optional[models.RewardRule]:
    return db.query(models.RewardRule).filter(
        models.RewardRule.rule_name == rule_name,
        models.RewardRule.is_active == True
    ).first()


def get_user_balance(db: Session, user_id: int) -> Optional[models.UserBalance]:
    return db.query(models.UserBalance).filter(models.UserBalance.user_id == user_id).first()


def create_user_balance(db: Session, user_id: int) -> models.UserBalance:
    db_balance = models.UserBalance(user_id=user_id)
    db.add(db_balance)
    db.commit()
    db.refresh(db_balance)
    return db_balance


def update_user_balance(db: Session, user_id: int, points: int) -> models.UserBalance:
    balance = get_user_balance(db, user_id)
    if not balance:
        balance = create_user_balance(db, user_id)

    balance.total_points += points
    balance.available_points += points
    db.commit()
    db.refresh(balance)
    return balance


def create_user_reward(
        db: Session,
        user_id: int,
        prediction_id: int,
        points: int,
        award_type: str,
        description: str
) -> models.UserReward:
    # Проверяем, не выдавалась ли уже награда за это предсказание
    existing_reward = db.query(models.UserReward).filter(
        models.UserReward.prediction_id == prediction_id
    ).first()

    if existing_reward:
        return existing_reward

    db_reward = models.UserReward(
        user_id=user_id,
        prediction_id=prediction_id,
        points_awarded=points,
        award_type=award_type,
        description=description,
        is_claimed=True
    )
    db.add(db_reward)
    db.commit()
    db.refresh(db_reward)

    # Обновляем баланс пользователя
    update_user_balance(db, user_id, points)

    return db_reward
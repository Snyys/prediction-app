from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import models, schemas, crud
import SessionLocal, engine
import requests
import os
import json

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Reward Service", version="1.0.0")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/rewards/award-prediction")
async def award_prediction_success(
        award_data: schemas.AwardPredictionRequest,
        db: Session = Depends(get_db)
):
    """Выдача награды за сбывшееся предсказание"""
    try:
        rule = crud.get_reward_rule(db, "prediction_success")
        if not rule:
            raise HTTPException(status_code=500, detail="Reward rule not configured")

        description = f"Предсказание сбылось: '{award_data.prediction_text}'"

        reward = crud.create_user_reward(
            db=db,
            user_id=award_data.user_id,
            prediction_id=award_data.prediction_id,
            points=rule.points,
            award_type="prediction_success",
            description=description
        )

        return {
            "status": "success",
            "points_awarded": rule.points,
            "new_balance": crud.get_user_balance(db, award_data.user_id).available_points,
            "reward_id": reward.id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rewards/balance/{user_id}")
async def get_user_balance(user_id: int, db: Session = Depends(get_db)):
    """Получение баланса пользователя"""
    balance = crud.get_user_balance(db, user_id)
    if not balance:
        balance = crud.create_user_balance(db, user_id)

    return schemas.UserBalanceResponse(
        user_id=balance.user_id,
        total_points=balance.total_points,
        available_points=balance.available_points,
        level=balance.level,
        streak_days=balance.streak_days
    )


@app.post("/rewards/init-rules")
async def initialize_reward_rules(db: Session = Depends(get_db)):
    """Инициализация стандартных правил наград"""
    rules_data = [
        {
            "rule_name": "prediction_success",
            "points": 100,
            "description": "Награда за сбывшееся предсказание",
            "conditions": "{}"
        },
        {
            "rule_name": "prediction_streak_3",
            "points": 50,
            "description": "Бонус за серию из 3 сбывшихся предсказаний",
            "conditions": '{"streak_days": 3}'
        },
        {
            "rule_name": "prediction_streak_7",
            "points": 150,
            "description": "Бонус за серию из 7 сбывшихся предсказаний",
            "conditions": '{"streak_days": 7}'
        }
    ]

    for rule_data in rules_data:
        existing_rule = crud.get_reward_rule(db, rule_data["rule_name"])
        if not existing_rule:
            db_rule = models.RewardRule(**rule_data)
            db.add(db_rule)

    db.commit()
    return {"status": "rules_initialized"}
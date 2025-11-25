# prediction_service/tasks.py
import redis
from sqlalchemy.orm import Session
from . import crud, models
from .database import SessionLocal
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_client = redis.Redis(host='redis', port=6379, db=0)


class PredictionChecker:
    def __init__(self):
        self.db = SessionLocal()

    def check_expired_predictions(self):
        """Проверка предсказаний, у которых истек срок"""
        try:
            expired_predictions = crud.get_expired_predictions(self.db)
            logger.info(f"Found {len(expired_predictions)} expired predictions")

            for prediction in expired_predictions:
                self.evaluate_prediction(prediction)

        except Exception as e:
            logger.error(f"Error checking predictions: {e}")
        finally:
            self.db.close()

    def evaluate_prediction(self, prediction):
        """Оценка сбылось ли предсказание"""
        try:
            # Временная логика - случайное определение
            import random
            is_fulfilled = random.choice([True, False])

            status = "fulfilled" if is_fulfilled else "failed"
            crud.update_prediction_status(self.db, prediction.id, status)

            # Если сбылось - награждаем пользователя
            if is_fulfilled:
                self.award_user(prediction)

            logger.info(f"Prediction {prediction.id} evaluated as {status}")

        except Exception as e:
            logger.error(f"Error evaluating prediction {prediction.id}: {e}")

    def award_user(self, prediction):
        """Выдача награды пользователю"""
        try:
            reward_service_url = "http://reward_service:8001/rewards/award-prediction"

            award_data = {
                "user_id": prediction.user_id,
                "prediction_id": prediction.id,
                "prediction_text": prediction.prediction_text
            }

            response = requests.post(reward_service_url, json=award_data)

            if response.status_code == 200:
                logger.info(f"User {prediction.user_id} awarded for prediction {prediction.id}")
            else:
                logger.error(f"Failed to award user: {response.text}")

        except Exception as e:
            logger.error(f"Error awarding user: {e}")
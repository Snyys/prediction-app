# api_gateway/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import jwt
from typing import Optional

app = FastAPI(title="Prediction App API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация сервисов
SERVICES = {
    "auth": "http://auth_service:8000",
    "predictions": "http://prediction_service:8002",
    "rewards": "http://reward_service:8001"
}


async def verify_token(token: str) -> dict:
    """Верификация JWT токена"""
    try:
        # Отправляем токен в сервис аутентификации для проверки
        auth_response = requests.get(
            f"{SERVICES['auth']}/auth/verify-token",
            headers={"Authorization": f"Bearer {token}"}
        )

        if auth_response.status_code == 200:
            return auth_response.json()
        else:
            raise HTTPException(status_code=401, detail="Invalid token")

    except Exception as e:
        raise HTTPException(status_code=401, detail="Token verification failed")


@app.get("/user/predictions")
async def get_user_predictions(token: str):
    """Получение предсказаний пользователя через gateway"""
    user_data = await verify_token(token)

    # Перенаправляем запрос в prediction service
    response = requests.get(
        f"{SERVICES['predictions']}/predictions/user/{user_data['user_id']}",
        headers={"Authorization": f"Bearer {token}"}
    )

    return response.json()


@app.get("/user/rewards")
async def get_user_rewards(token: str):
    """Получение наград пользователя через gateway"""
    user_data = await verify_token(token)

    response = requests.get(
        f"{SERVICES['rewards']}/rewards/balance/{user_data['user_id']}",
        headers={"Authorization": f"Bearer {token}"}
    )

    return response.json()
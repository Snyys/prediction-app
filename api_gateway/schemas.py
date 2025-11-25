# prediction_app/api_gateway/schemas.py - ДОБАВЛЯЕМ К СУЩЕСТВУЮЩИМ

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enum для статусов предсказаний
class PredictionStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    EXPIRED = "expired"


# Обновляем Prediction схемы
class PredictionBase(BaseModel):
    title: str
    description: str
    predicted_date: datetime
    expiration_date: datetime
    confidence_level: float = 0.5

    @validator('confidence_level')
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Confidence level must be between 0 and 1')
        return v

    @validator('expiration_date')
    def validate_expiration_date(cls, v, values):
        if 'predicted_date' in values and v <= values['predicted_date']:
            raise ValueError('Expiration date must be after predicted date')
        return v


class PredictionCreate(PredictionBase):
    pass


class PredictionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    confidence_level: Optional[float] = None


class PredictionResponse(PredictionBase):
    id: int
    user_id: int
    status: str
    result: Optional[bool] = None
    created_at: datetime
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Схемы для пользователей
class UserStats(BaseModel):
    total_predictions: int
    successful_predictions: int
    pending_predictions: int
    success_rate: float
    total_points: int
    available_rewards: int


# Схемы для системы наград
class UserRewardBase(BaseModel):
    user_id: int
    reward_id: int
    points_awarded: int


class UserRewardResponse(UserRewardBase):
    id: int
    awarded_at: datetime
    reward_name: str

    class Config:
        from_attributes = True
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    points: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Prediction Schemas
class PredictionBase(BaseModel):
    title: str
    description: str
    predicted_date: datetime
    expiration_date: datetime
    confidence_level: float = 0.5


class PredictionCreate(PredictionBase):
    pass


class PredictionResponse(PredictionBase):
    id: int
    user_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# Reward Schemas
class RewardBase(BaseModel):
    name: str
    description: str
    points_required: int


class RewardResponse(RewardBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
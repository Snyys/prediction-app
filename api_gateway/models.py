# prediction_app/api_gateway/models.py - ДОБАВЛЯЕМ К СУЩЕСТВУЮЩИМ

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


# Обновляем модель User
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    points = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связь с предсказаниями
    predictions = relationship("Prediction", back_populates="user")


# Обновляем модель Prediction
class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    predicted_date = Column(DateTime, nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    confidence_level = Column(Float, default=0.5)
    status = Column(String(20), default="pending")
    result = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    verified_at = Column(DateTime)

    # Связь с пользователем
    user = relationship("User", back_populates="predictions")


# Новая модель для наград пользователей
class UserReward(Base):
    __tablename__ = "user_rewards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reward_id = Column(Integer, ForeignKey("rewards.id"), nullable=False)
    points_awarded = Column(Integer, nullable=False)
    awarded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    user = relationship("User")
    reward = relationship("Reward")


# Существующая модель Reward остается без изменений
class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    points_required = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
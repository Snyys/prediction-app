from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class UserReward(Base):
    __tablename__ = "user_rewards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    prediction_id = Column(Integer, index=True)
    points_awarded = Column(Integer, default=0)
    award_type = Column(String(50))  # 'prediction_success', 'streak', 'achievement'
    description = Column(Text)
    awarded_at = Column(DateTime(timezone=True), server_default=func.now())
    is_claimed = Column(Boolean, default=False)


class RewardRule(Base):
    __tablename__ = "reward_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), unique=True)
    points = Column(Integer)
    description = Column(String(500))
    conditions = Column(Text)  # JSON условия для награды
    is_active = Column(Boolean, default=True)


class UserBalance(Base):
    __tablename__ = "user_balances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    total_points = Column(Integer, default=0)
    available_points = Column(Integer, default=0)
    level = Column(Integer, default=1)
    streak_days = Column(Integer, default=0)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
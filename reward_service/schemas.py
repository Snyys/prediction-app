from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class RewardRuleBase(BaseModel):
    rule_name: str
    points: int
    description: str
    conditions: Optional[str] = None


class UserRewardBase(BaseModel):
    user_id: int
    prediction_id: int
    points_awarded: int
    award_type: str
    description: str


class UserBalanceResponse(BaseModel):
    user_id: int
    total_points: int
    available_points: int
    level: int
    streak_days: int


class AwardPredictionRequest(BaseModel):
    user_id: int
    prediction_id: int
    prediction_text: str
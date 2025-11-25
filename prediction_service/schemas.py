# prediction_service/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PredictionBase(BaseModel):
    prediction_text: str
    due_date: datetime


class PredictionCreate(PredictionBase):
    pass


class PredictionResponse(PredictionBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    checked_at: Optional[datetime]

    class Config:
        from_attributes = True


class PredictionUpdate(BaseModel):
    status: Optional[str] = None
    checked_at: Optional[datetime] = None
from pydantic import BaseModel, validator, EmailStr, constr
from datetime import datetime
from enum import Enum
from typing import Optional
import re
from html import escape

class FeedbackType(str, Enum):
    suggestion = "suggestion"
    problem = "problem"
    complaint = "complaint"
    other = "other"

class FeedbackBase(BaseModel):
    feedback_type: FeedbackType
    full_name: constr(min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[constr(max_length=20)] = None
    message: constr(min_length=10, max_length=1000)
    order_number: Optional[constr(max_length=20)] = None

    @validator('phone')
    def validate_phone(cls, v):
        if v is None:
            return v
        # Экранирование HTML
        v = escape(v)
        # Проверка формата телефона
        if not re.match(r'^\+?[\d\s\-()]+$', v):
            raise ValueError('Некорректный формат телефона')
        # Проверка длины (5-20 символов)
        cleaned = re.sub(r'[^\d+]', '', v)
        if len(cleaned) < 5 or len(cleaned) > 15:
            raise ValueError('Телефон должен содержать от 5 до 15 цифр')
        return v

    @validator('full_name', 'message', 'order_number')
    def escape_html(cls, v):
        if v is None:
            return v
        return escape(v)

class FeedbackCreate(FeedbackBase):
    pass

class Feedback(FeedbackBase):
    id: int
    created_at: datetime
    file_path: Optional[str]

    class Config:
        orm_mode = True
        from_attributes = True
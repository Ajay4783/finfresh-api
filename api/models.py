from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional
from enum import Enum

# --- Auth Models ---
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# --- Transaction Models ---
class TransactionType(str, Enum):
    income = "income"
    expense = "expense"
    investment = "investment"
    debt = "debt"

class TransactionCreate(BaseModel):
    type: TransactionType
    category: str
    amount: float = Field(gt=0)
    date: date
    description: Optional[str] = None
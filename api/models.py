from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str
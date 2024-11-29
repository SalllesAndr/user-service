from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    user_id: str
    isStudent: bool
    email: EmailStr
    username: str

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserUpdate(BaseModel):
    isStudent: Optional[bool] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

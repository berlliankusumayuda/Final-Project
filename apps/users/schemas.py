from ninja import Schema
from pydantic import EmailStr
from typing import Optional


class RegisterIn(Schema):
    username: str
    email: EmailStr
    password: str
    role: str = "student"
    first_name: str = ""
    last_name: str = ""


class LoginIn(Schema):
    username: str
    password: str


class TokenOut(Schema):
    access: str
    refresh: str


class UserOut(Schema):
    id: int
    username: str
    email: str
    role: str
    first_name: str
    last_name: str
    bio: str


class UserUpdateIn(Schema):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None


class MessageOut(Schema):
    message: str

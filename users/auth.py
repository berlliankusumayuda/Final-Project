from ninja import Router, Schema
from django.contrib.auth import authenticate
from django.conf import settings
import jwt
from users.models import User
from django.shortcuts import get_object_or_404

api = Router()

class TokenOut(Schema):
    access: str

class LoginIn(Schema):
    username: str
    password: str

@api.post('login', response=TokenOut)
def login(request, data: LoginIn):
    user = authenticate(username=data.username, password=data.password)
    if not user:
        from ninja.errors import HttpError
        raise HttpError(401, 'Invalid credentials')
    payload = {'user_id': user.id, 'role': user.role}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')
    return {'access': token}

# Simple helper
def get_user_from_token(token: str):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
        return User.objects.get(id=payload['user_id'])
    except Exception:
        return None

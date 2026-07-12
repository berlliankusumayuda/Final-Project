from ninja import Router
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .schemas import RegisterIn, LoginIn, TokenOut, UserOut, UserUpdateIn, MessageOut
from typing import List

User = get_user_model()
router = Router()


@router.post("/register", response=UserOut, auth=None, summary="Register a new user")
def register(request, payload: RegisterIn):
    if User.objects.filter(username=payload.username).exists():
        from ninja.errors import HttpError
        raise HttpError(400, "Username already exists")
    if payload.role not in ["student", "instructor"]:
        payload.role = "student"
    user = User.objects.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password,
        role=payload.role,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        first_name=user.first_name,
        last_name=user.last_name,
        bio=user.bio,
    )


@router.post("/login", response=TokenOut, auth=None, summary="Login and get JWT tokens")
def login(request, payload: LoginIn):
    from ninja.errors import HttpError
    user = authenticate(username=payload.username, password=payload.password)
    if not user:
        raise HttpError(401, "Invalid credentials")
    refresh = RefreshToken.for_user(user)
    return TokenOut(access=str(refresh.access_token), refresh=str(refresh))


@router.post("/refresh", response=TokenOut, auth=None, summary="Refresh access token")
def refresh_token(request, refresh: str):
    from ninja.errors import HttpError
    try:
        token = RefreshToken(refresh)
        return TokenOut(access=str(token.access_token), refresh=str(token))
    except Exception:
        raise HttpError(401, "Invalid refresh token")


@router.get("/me", response=UserOut, summary="Get current user profile")
def me(request):
    u = request.auth
    return UserOut(
        id=u.id, username=u.username, email=u.email, role=u.role,
        first_name=u.first_name, last_name=u.last_name, bio=u.bio,
    )


@router.put("/me", response=UserOut, summary="Update current user profile")
def update_me(request, payload: UserUpdateIn):
    u = request.auth
    if payload.first_name is not None:
        u.first_name = payload.first_name
    if payload.last_name is not None:
        u.last_name = payload.last_name
    if payload.bio is not None:
        u.bio = payload.bio
    u.save()
    return UserOut(
        id=u.id, username=u.username, email=u.email, role=u.role,
        first_name=u.first_name, last_name=u.last_name, bio=u.bio,
    )


@router.get("/users", response=List[UserOut], summary="[Admin] List all users")
def list_users(request):
    from ninja.errors import HttpError
    if not request.auth.is_admin():
        raise HttpError(403, "Admin only")
    users = User.objects.all()
    return [UserOut(id=u.id, username=u.username, email=u.email, role=u.role,
                    first_name=u.first_name, last_name=u.last_name, bio=u.bio) for u in users]

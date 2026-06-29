from ninja.errors import HttpError
from ninja.security import HttpBearer
from users.auth import get_user_from_token

class TokenAuth(HttpBearer):
    def authenticate(self, request, token):
        user = get_user_from_token(token)
        if not user:
            raise HttpError(401, 'Invalid or expired token')
        return user

def require_role(user, roles):
    if user.role not in roles:
        from ninja.errors import HttpError
        raise HttpError(403, 'Permission denied')

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from ninja import NinjaAPI
from ninja.security import HttpBearer
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()


class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            user = User.objects.get(id=user_id, is_active=True)
            request.user = user
            return user
        except Exception:
            return None


auth = JWTAuth()

api = NinjaAPI(
    title="Simple LMS API",
    version="1.0.0",
    description="Simple Learning Management System - Extended Backend with Assessment & Certificate",
    auth=auth,
)

from apps.users.api import router as users_router
from apps.courses.api import router as courses_router
from apps.assessments.api import router as assessments_router
from apps.certificates.api import router as certificates_router

api.add_router("/auth", users_router, tags=["Authentication"])
api.add_router("/courses", courses_router, tags=["Courses"])
api.add_router("/assessments", assessments_router, tags=["Assessments"])
api.add_router("/certificates", certificates_router, tags=["Certificates"])

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

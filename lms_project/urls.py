from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from users.auth import api as auth_api
from courses.api import api as courses_api
api = NinjaAPI(title='LMS API')
api.add_router('/auth/', auth_api)
api.add_router('/courses/', courses_api)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api.urls),
]

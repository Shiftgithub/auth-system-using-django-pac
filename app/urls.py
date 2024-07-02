from .views import *
from django.urls import path, include

urlpatterns = [
    path("auth/", include("django.contrib.auth.urls")),
    path("", dashboard, name="dashboard"),
    path("auth/registration/", registration, name="registration"),
]

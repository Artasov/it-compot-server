from django.urls import path

from apps.endpoints.controllers.base import endpoints

urlpatterns = [
    path('', endpoints, name='endpoints'),
]

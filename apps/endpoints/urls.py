from django.urls import path

from endpoints.controllers.base import endpoints

urlpatterns = [
    path('', endpoints, name='endpoints'),
]

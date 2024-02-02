from django.urls import path

from tools.api import get_forming_groups

# app_name = 'tools'

urlpatterns = [
    path('get_forming_groups/',
         get_forming_groups,
         name='get_forming_groups'),
]

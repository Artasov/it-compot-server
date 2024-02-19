from django.urls import path

from .views import create_short_link, redirect_to_full_link

urlpatterns = [
    path('create_short_link/', create_short_link, name='create_short_link'),
    path('r/<str:short_code>/', redirect_to_full_link, name='redirect_to_full_link'),
]

from django.urls import path, re_path
from .views import create_short_link_controller, redirect_to_full_link

urlpatterns = [
    path('create_short_link/', create_short_link_controller, name='create_short_link'),
    re_path(r'^r/(?P<short_code>\w+)/.*$', redirect_to_full_link, name='redirect_to_full_link'),
]
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from Core.views import menu, health_test

urlpatterns = [
    path('health_test/', health_test),
    path('admin/', admin.site.urls),
    path('', menu),
    path('tools/', include(('tools.urls', 'tools'), namespace='tools')),
    path('api/v1/tools/', include('tools.urls_api')),

    # На удаление, так как есть tools/teachers_salary/
    path('teachers_salary/',
         RedirectView.as_view(pattern_name='tools:teachers_salary'),
         name='old_teachers_salary_redirect'),
]

if settings.DEV:
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]

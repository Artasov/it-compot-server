from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from apps.Core.views import menu, health_test, stupid_auth, signout

urlpatterns = [
    path('health_test/', health_test),
    path('admin/', admin.site.urls),
    path('', menu, name='menu'),
    path('', include(('apps.link_shorter.urls', 'apps.link_shorter'), namespace='link_shorter')),
    path('tools/', include(('apps.tools.urls', 'apps.tools'), namespace='tools')),
    path('api/v1/tools/', include(('apps.tools.urls_api', 'apps.tools'), namespace='tools-api')),
    path('api/v1/transcribe/', include(('apps.transcribe.urls_api', 'apps.transcribe'), namespace='transcribe-api')),
    path('login/', stupid_auth, name='stupid_auth'),
    path('signout/', signout, name='signout'),

    # На удаление, так как есть tools/teachers_salary/
    path('teachers_salary/',
         RedirectView.as_view(pattern_name='tools:teachers_salary'),
         name='old_teachers_salary_redirect'),

    path('endpoints/', include('endpoints.urls')),
]

if settings.DEV:
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]

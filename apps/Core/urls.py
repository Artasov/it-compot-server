from django.conf import settings
from django.contrib import admin
from django.urls import path, include

from apps.Core.views import (
    menu, health_test, stupid_auth,
    signout, delete_expired_cache,
    delete_all_cache
)

urlpatterns = [
    path('health_test/', health_test),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('delete_expired_cache/', delete_expired_cache),
    path('delete_all_cache/', delete_all_cache),

    path('', menu, name='menu'),
    path('', include(('apps.link_shorter.urls', 'apps.link_shorter'), namespace='link_shorter')),
    path('tools/', include(('apps.tools.urls', 'apps.tools'), namespace='tools')),
    path('api/v1/tools/', include(('apps.tools.urls_api', 'apps.tools'), namespace='tools-api')),
    path('api/v1/transcribe/', include(('apps.transcribe.urls_api', 'apps.transcribe'), namespace='transcribe-api')),
    path('login/', stupid_auth, name='stupid_auth'),
    path('signout/', signout, name='signout'),

    path('endpoints/', include('apps.endpoints.urls')),
]

if settings.DEV:
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]

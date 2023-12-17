from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from Core.views import menu

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', menu),
    path('tools/', include(('tools.urls', 'tools'), namespace='tools')),

    # На удаление, так как есть tools/teachers_salary/
    path('teachers_salary/',
         RedirectView.as_view(pattern_name='tools:teachers_salary'),
         name='old_teachers_salary_redirect'),
]

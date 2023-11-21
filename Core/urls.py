from django.contrib import admin
from django.urls import path

from Core.views import teacher_salary

urlpatterns = [
    path('admin/', admin.site.urls),
    path('teachers_salary/', teacher_salary, name='teachers_salary')
]

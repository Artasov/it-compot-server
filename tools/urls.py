from django.urls import path

from tools.views import teacher_salary, parse_teachers_schedule_ui, join_to_group

# app_name = 'tools'

urlpatterns = [
    path('teachers_salary/', teacher_salary,
         name='teachers_salary'),
    path('parse_teachers_schedule/', parse_teachers_schedule_ui,
         name='parse_teachers_schedule'),
    path('join_to_group/', join_to_group,
         name='join_to_group'),
]

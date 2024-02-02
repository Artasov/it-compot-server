from django.urls import path

from tools.api import get_forming_groups, student_to_group, get_is_student_on_discipline

# app_name = 'tools'

urlpatterns = [
    path('get_forming_groups/',
         get_forming_groups,
         name='get_forming_groups'),
    path('student_to_group/',
         student_to_group,
         name='student_to_group'),
    path('get_is_student_on_discipline/',
         get_is_student_on_discipline,
         name='get_is_student_on_discipline'),
]

from django.urls import path

from tools.api import (
    get_is_student_in_group_on_discipline,
    build_link_for_join_to_forming_group,
    get_forming_groups_for_join,
    student_to_forming_group,
    send_nothing_fit,
)

urlpatterns = [
    path('get_forming_groups_for_join/',
         get_forming_groups_for_join,
         name='get_forming_groups_for_join'),
    path('student_to_forming_group/',
         student_to_forming_group,
         name='student_to_forming_group'),
    path('get_is_student_in_group_on_discipline/',
         get_is_student_in_group_on_discipline,
         name='get_is_student_in_group_on_discipline'),
    path('send_nothing_fit/',
         send_nothing_fit,
         name='send_nothing_fit'),
    path('build_link_for_join_to_forming_group/',
         build_link_for_join_to_forming_group,
         name='build_link_for_join_to_forming_group'),
]

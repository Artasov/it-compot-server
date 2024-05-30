from django.urls import path

from apps.tools.views import (
    teacher_salary,
    join_to_forming_group,
    teacher_set_lesson_report,
    daily_teacher_schedule_by_interval_gsheet_export, get_lasts_themes_for_unit_student
)

urlpatterns = [
    path('lesson_report/', teacher_set_lesson_report,
         name='lesson_report'),
    path('teachers_salary/', teacher_salary,
         name='teachers_salary'),
    path('parse_teachers_schedule/', daily_teacher_schedule_by_interval_gsheet_export,
         name='daily_teacher_schedule_by_interval_gsheet_export'),
    path('join_to_forming_group/', join_to_forming_group,
         name='join_to_forming_group'),
    # Удалить
    path('get_lasts_themes_for_unit_student/', get_lasts_themes_for_unit_student,
         name='get_lasts_themes_for_unit_student'),
]

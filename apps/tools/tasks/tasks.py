import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from django.conf import settings

from apps.tools.services.lesson_report.funcs import upload_lasts_themes_for_unit_student, send_lesson_report

log = logging.getLogger('base')


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 120})
def upload_lasts_themes_task():
    if 'code-academy' in settings.DOMAIN_URL:
        async_to_sync(upload_lasts_themes_for_unit_student)()
    else:
        print("DOMAIN NOT IS code-academy TASK NOT STARTED")


@shared_task()
def process_lesson_report_task(
        ed_unit_id,
        day_date,
        theme_number,
        theme_name,
        lesson_completion_percentage,
        students_comments,
        type_ed_unit,
        user_email,
        growth_points,
        what_was_positive,
        satisfaction_rate,
        self_feeling_rate,
        students_feeling_rate,
        other_general_questions,
):
    send_lesson_report(
        ed_unit_id=ed_unit_id,
        day_date=day_date,
        theme_number=theme_number,
        theme_name=theme_name,
        lesson_completion_percentage=lesson_completion_percentage,
        students_comments=students_comments,
        type_ed_unit=type_ed_unit,
        user_email=user_email,
        growth_points=growth_points,
        what_was_positive=what_was_positive,
        satisfaction_rate=satisfaction_rate,
        self_feeling_rate=self_feeling_rate,
        students_feeling_rate=students_feeling_rate,
        other_general_questions=other_general_questions,
    )
    return {'success': True}

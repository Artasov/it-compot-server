import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from django.conf import settings

from apps.tools.services.lesson_report.funcs import upload_lasts_themes_for_unit_student, send_gs_lesson_report
from modules.hollihop.classes.custom_hollihop import CustomHHApiV2Manager, SetCommentError
from modules.pickler import PicklerNotFoundDumpFile

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
        username
):
    from apps.tools.api import pickler
    HHManager = CustomHHApiV2Manager()
    try:
        teacher_name = pickler.cache(f'{username}_full_teacher_name')
    except PicklerNotFoundDumpFile:
        teacher_name = HHManager.get_full_teacher_name_by_email(user_email)
        pickler.cache(f'{username}_full_teacher_name', teacher_name, 24 * 60 * 60 * 4)

    for student_comment in students_comments:
        try:
            HHManager.set_comment_for_student_ed_unit(
                ed_unit_id=ed_unit_id,
                student_client_id=student_comment['ClientId'],
                date=day_date,
                passed=student_comment['Pass'],
                description=f'* {theme_number}{". " if theme_number else ""}{theme_name}\n'
                            f'* Завершено на: {lesson_completion_percentage}%\n'
                            f'* {student_comment["Description"]}'
            )
            send_gs_lesson_report(
                teacher_name=teacher_name,
                type_ed_unit=type_ed_unit,
                ed_unit_id=ed_unit_id,
                student_name=student_comment['StudentName'],
                student_amo_id=student_comment['StudentAmoId'],
                student_client_id=student_comment['ClientId'],
                date=day_date,
                description=f'* {theme_number}. {theme_name}\n'
                            f'* Завершено на: {lesson_completion_percentage}%\n'
                            f'* {student_comment["Description"]}'
            )
        except SetCommentError:
            return {'success': False, 'error': 'Ошибка при добавлении комментария в HH'}
    pickler.delete(f'{username}_lessons')
    return {'success': True}

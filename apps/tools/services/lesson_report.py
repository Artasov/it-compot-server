from django.conf import settings

from service.tools.gsheet.classes.gsheetsclient import GSDocument


async def send_gs_lesson_report(
        teacher_name: str,
        type_ed_unit: str,
        ed_unit_id: int,
        student_name: str,
        student_client_id: int,
        date: str,
        description: str):
    sheet_name = 'Lesson Comments'
    doc = GSDocument(settings.GSDOCID_UPLOAD_BY_LESSON)
    doc.append_row(
        row=(
            teacher_name, ed_unit_id,
            student_name, date,
            description,
            f'https://it-school.t8s.ru/Learner/{type_ed_unit}/{ed_unit_id}/',
            # f'https://it-school.t8s.ru/Profile/{student_client_id}/'
        ),
        sheet_name=sheet_name
    )
    doc.auto_resize_last_row(sheet_name)

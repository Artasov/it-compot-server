import re
from datetime import datetime, timedelta
from pprint import pprint
from typing import TypedDict

from django.conf import settings

from modules.gsheet.classes.gsheetsclient import GSDocument, GSFormatOptions
from modules.hollihop.classes.custom_hollihop import CustomHHApiV2Manager, SetCommentError
from modules.pickler import PicklerNotFoundDumpFile, PicklerLoadError


class LessonComment(TypedDict):
    number: int
    theme: str
    finish_percent: int | None
    add_info: str


async def send_lesson_report(
        ed_unit_id,
        day_date,
        theme_number,
        theme_name,
        lesson_completion_percentage,
        students_comments,
        type_ed_unit,
        user_email,
        username,
):
    from apps.tools.api import pickler
    HHManager = CustomHHApiV2Manager()
    try:
        teacher_name = pickler.cache(f'{username}_full_teacher_name')
    except (PicklerNotFoundDumpFile, PicklerLoadError):
        teacher_name = await HHManager.get_full_teacher_name_by_email(user_email)
        pickler.cache(f'{username}_full_teacher_name', teacher_name, 24 * 60 * 60 * 4)

    for student_comment in students_comments:
        try:
            await HHManager.set_comment_for_student_ed_unit(
                ed_unit_id=ed_unit_id,
                student_client_id=student_comment['ClientId'],
                date=day_date,
                passed=student_comment['Pass'],
                description=f'* {theme_number}{". " if theme_number else ""}{theme_name}\n'
                            f'* Завершено на: {lesson_completion_percentage}%\n'
                            f'* {student_comment["Description"]}'
            )
            await send_gs_lesson_report(
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


def parse_lesson_comment(comment: str) -> LessonComment | None:
    pattern = re.compile(
        r'\*\s*(\d+)\.\s*\).*? (.*?)\s*(?:\*\s*Завершено на:\s*(\d+)%\s*\*\s*(.*))?\s*\*',
        re.DOTALL
    )
    match = pattern.search(comment)

    if not match:
        return None

    number = int(match.group(1))
    theme = match.group(2).strip()
    finish_percent = int(match.group(3)) if match.group(3) else None
    add_info = match.group(4).strip() if match.group(4) else ""

    return LessonComment(number=number, theme=theme, finish_percent=finish_percent, add_info=add_info)


def get_module_by_lesson_number(lesson_number: int, discipline) -> str:
    doc = GSDocument(settings.GSDOCID_COURSES_RESUME)
    return doc.get_cell(lesson_number + 2, 4, discipline)


def get_module_for_autumn_by_lesson_number(lesson_number: int, discipline) -> str:
    doc = GSDocument(settings.GSDOCID_COURSES_RESUME)
    return doc.get_cell(lesson_number + 2, 6, discipline)


async def send_gs_lesson_report(
        teacher_name: str,
        type_ed_unit: str,
        ed_unit_id: int,
        student_name: str,
        student_amo_id: int,
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
            f'https://itbestonlineschool.amocrm.ru/leads/detail/{student_amo_id}/',
            student_amo_id,
            student_client_id
        ),
        sheet_name=sheet_name
    )
    doc.auto_resize_last_row(sheet_name)


def calculate_age(birth_date_str):
    birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
    today = datetime.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age


def get_last_conducted_lesson_description(days):
    today = datetime.today().date()
    last_conducted_lesson = None

    for day in days:
        lesson_date = datetime.strptime(day['Date'], '%Y-%m-%d').date()
        if lesson_date <= today and not day['Pass']:
            if 'Description' in day:
                if last_conducted_lesson is None or lesson_date > last_conducted_lesson['Date']:
                    last_conducted_lesson = {'Date': lesson_date, 'Description': day['Description']}

    if last_conducted_lesson:
        return last_conducted_lesson['Description']
    else:
        return None


def get_latest_unit_student(unit_students):
    grouped = {}
    for ustudent in unit_students:
        key = (ustudent['StudentClientId'], ustudent['EdUnitDiscipline'])
        if key not in grouped:
            grouped[key] = ustudent
        else:
            current_days = [day for day in grouped[key]['Days'] if not day['Pass']]
            new_days = [day for day in ustudent['Days'] if not day['Pass']]

            if current_days and new_days:
                current_last_date = max(datetime.strptime(day['Date'], '%Y-%m-%d') for day in current_days)
                new_last_date = max(datetime.strptime(day['Date'], '%Y-%m-%d') for day in new_days)

                if new_last_date > current_last_date:
                    grouped[key] = ustudent
            elif new_days:
                grouped[key] = ustudent

    return list(grouped.values())


async def upload_lasts_themes_for_unit_student():
    HHManager = CustomHHApiV2Manager()
    now = datetime.now()
    unit_students = await HHManager.getEdUnitStudents(
        queryDays=True,
        dateFrom=(now - timedelta(days=200)).strftime('%Y-%m-%d'),
        dateTo=now.strftime('%Y-%m-%d'),
        maxTake=16000
    )

    pprint('------------------')
    pprint('unit_students')
    print(len(unit_students))
    pprint('------------------')

    students = await HHManager.getStudents(maxTake=12000)

    pprint('------------------')
    pprint('students')
    print(len(students))
    pprint('------------------')

    student_dict = {student['ClientId']: student for student in students}

    not_found_counter = 0
    for unit_student in unit_students:
        student_client_id = unit_student['StudentClientId']
        if student_client_id in student_dict:
            unit_student['Student'] = student_dict[student_client_id]
        else:
            unit_student['Student'] = None
            not_found_counter += 1
    print(f'Не найдено совпадений с {not_found_counter} ClientId')

    unit_students = get_latest_unit_student(unit_students)

    doc = GSDocument(settings.GSDOCID_UPLOAD_BY_LAST_THEMES[0])
    doc.clear_sheet(settings.GSDOCID_UPLOAD_BY_LAST_THEMES[1])
    sheet_data = [(
        'Student Name',
        'Amo ID',
        'Amo Link',
        'HH Link',
        'Time Zone',
        'Birthday / Age',
        'Discipline',
        'Last Theme',
        'Student Level',
        'Формат из Amo индивид / группа',
        'Баланс в HH',
        'Статус Amo ученики без паузы и закрытых',
        'Доп. поле - готовность к лагерю (новое поле создаст ира данные будут подтягиваться из анкеты)',
        'Если индивид, то в какие дни (доп. поле)',
        'Интенсив 2 недели, даты (доп поле)',
        'Мероприятия',
        'Столбцы для комментов ОЗР',
    )]
    for ustudent in unit_students:
        if ustudent['Student'] is None:
            sheet_data.append((ustudent['StudentName'], 'Не найдено совпадений с ClientId'), )
            continue

        amo_id = HHManager.get_student_or_student_unit_extra_field_value(ustudent, 'id ученика')

        if 'Birthday' in ustudent["Student"]:
            birth_date_age_row = f'{ustudent["Student"]["Birthday"]} / {calculate_age(ustudent["Student"]["Birthday"])}'
        else:
            birth_date_age_row = 'Не указано'

        sheet_data.append((
            ustudent['StudentName'],
            amo_id,
            f'=ГИПЕРССЫЛКА("https://itbestonlineschool.amocrm.ru/leads/detail/{amo_id}/"; "Amo")',
            f'=ГИПЕРССЫЛКА("https://it-school.t8s.ru/{"Profile"}/{ustudent["Student"]["Id"]}/"; "HolliHop")',
            '',
            birth_date_age_row,
            ustudent['EdUnitDiscipline'],
            get_last_conducted_lesson_description(ustudent['Days']),
            ustudent['EdUnitLevel']
        ))

    doc.update_sheet(sheet_name=settings.GSDOCID_UPLOAD_BY_LAST_THEMES[1], values=sheet_data)
    format_options_header = GSFormatOptions(
        background_color={'red': 0.3, 'green': 0.5, 'blue': 1},
        text_color={'red': 1.0, 'green': 1.0, 'blue': 1.0},
        font_size=16,
        bold=True,
        vertical_alignment='MIDDLE',
        horizontal_alignment='CENTER',
        wrap_strategy='WRAP'
    )
    doc.format_range(0, 0, settings.GSDOCID_UPLOAD_BY_LAST_THEMES[1], format_options_header, 1, )
    print('SUCCESSFULLY Uploaded last themes to google sheet')

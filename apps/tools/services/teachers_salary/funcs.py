import pandas as pd

from service.hollihop.funcs.teachers_salary import get_teacher_salary_by_email


async def fetch_teacher_lessons_data_by_email(email) -> list[dict]:
    """
    Получает данные об уроках учителя по его электронной почте.

    @param email: Электронная почта учителя для поиска уроков.
    @return: Список словарей, каждый из которых содержит информацию об отдельном уроке.
             Пример:
             [
                 {'gid': '1', 'title': 'Математика', 'discipline': 'Математика', 'level': '5', 'type': 'Лекция',
                  'student': 'Иван Иванов', 'date': '2024-02-01', 'skip': 'FALSE', 'duration': '45',
                  'start_date': '2024-02-01', 'end_date': '2024-02-01', 'teacher': 'Елена Петровна', 'money': '1500'},
                 ...
             ]
    """
    teacher_month_lessons_rows = await get_teacher_salary_by_email(email)

    teacher_month_lessons = []
    for info in teacher_month_lessons_rows:
        # pprint(info)
        info = info[0] if isinstance(info[0], list) else info
        teacher_month_lessons.append({
            'gid': info[0], 'title': info[1], 'discipline': info[2], 'level': info[3],
            'type': info[4], 'student': info[5], 'date': info[6], 'skip': info[7],
            'duration': info[8], 'start_date': info[9], 'end_date': info[10],
            'teacher': info[11], 'money': info[12],
        })
    return teacher_month_lessons


async def filter_and_aggregate_teacher_lessons(teacher_month_lessons) -> tuple[list[dict], int]:
    """
    Фильтрует и агрегирует данные уроков учителя, подсчитывая общую зарплату
    на основе данных из 'fetch_teacher_lessons_data_by_email'

    @param teacher_month_lessons: Список словарей с данными об уроках.
    @return: Кортеж(len=2), содержащий отфильтрованные и агрегированные данные уроков и сумму зарплаты.
             Пример:
             ([{'gid': '1', 'title': 'Математика', 'discipline': 'Математика', 'level': '5', 'type': 'Лекция',
                'student': 'Иван Иванов', 'date': '2024-02-01', 'skip': 'FALSE', 'duration': '45',
                'start_date': '2024-02-01', 'end_date': '2024-02-01', 'teacher': 'Елена Петровна', 'money': '1500'},
               ...],
              4500)  # Сумма зарплаты
    """
    teacher_month_lessons_df = pd.DataFrame(teacher_month_lessons)
    teacher_month_lessons_df['duration'] = pd.to_numeric(teacher_month_lessons_df['duration'], errors='coerce')
    grouped_lessons = teacher_month_lessons_df.groupby(['gid', 'date', 'discipline', 'type'])
    filtered_lessons = grouped_lessons.filter(lambda x: not ((x['skip'] == 'TRUE') & (x['duration'] == 0)).all())
    teacher_month_lessons = filtered_lessons.to_dict('records')

    sum_salary = sum(int(lesson['money']) for lesson in teacher_month_lessons if lesson.get('money').isdigit())

    return teacher_month_lessons, sum_salary

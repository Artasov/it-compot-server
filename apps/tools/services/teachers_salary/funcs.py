from pprint import pprint

import pandas as pd

from modules.hollihop.funcs.teachers_salary import get_teacher_salary_by_email


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
        info = info[0] if isinstance(info[0], list) else info
        # if info[11] == '#N/A':
        #     continue
        teacher_month_lessons.append({
            'gid': info[0], 'title': info[1], 'discipline': info[2], 'level': info[3],
            'type': info[4], 'student': info[5], 'date': info[6], 'skip': info[7],
            'duration': info[8], 'start_date': info[9], 'end_date': info[10],
            'teacher': info[11], 'money': info[12],
        })
    return teacher_month_lessons


async def filter_and_aggregate_teacher_lessons(teacher_month_lessons) -> dict:
    """
    Фильтрует и агрегирует данные уроков учителя, подсчитывая общую зарплату
    на основе данных из 'fetch_teacher_lessons_data_by_email', группируя по месяцам.

    @param teacher_month_lessons: Список словарей с данными об уроках.
    @return: Словарь, где ключи - это месяцы, а значения - объекты со списком уроков и суммой зарплаты.
    """
    if not teacher_month_lessons:
        return {}
    # Создаем DataFrame из списка уроков
    lessons_df = pd.DataFrame(teacher_month_lessons)

    # Преобразование дат с учетом разных форматов
    def parse_date(date_str):
        for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                return pd.to_datetime(date_str, format=fmt)
            except ValueError:
                continue
        raise ValueError("no valid date format found")

    lessons_df['date'] = lessons_df['date'].apply(parse_date)
    lessons_df['month'] = lessons_df['date'].dt.to_period('M')

    # Преобразуем duration и money в числовой формат
    lessons_df['duration'] = pd.to_numeric(lessons_df['duration'], errors='coerce')
    lessons_df['money'] = pd.to_numeric(lessons_df['money'], errors='coerce')

    # Фильтрация уроков
    # lessons_df = lessons_df[~((lessons_df['skip'] == 'TRUE') & (lessons_df['duration'] == 0))]

    # Группировка данных по месяцам
    result = {}
    for month, group in lessons_df.groupby('month'):
        # Суммирование зарплаты за месяц
        total_money = group['money'].sum()

        # Список уроков в этом месяце
        month_lessons = group.to_dict('records')

        # Сохранение результатов в словарь
        result[str(month)] = {
            'lessons': month_lessons,
            'total_money': total_money
        }
    return result

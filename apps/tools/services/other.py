import pandas as pd
from django.conf import settings

from modules.gsheet.classes.gsheetsclient import GSDocument


async def get_course_themes(course_name) -> list[str] | None:
    """
    Получает список тем для курса через гугл таблицу 'Резюме курсов'
    @param course_name: Имя курса.
    @return: Список тем строками, если курс существует, иначе None
    """
    doc = GSDocument(settings.GSDOCID_COURSES_RESUME)
    sheets_names = doc.get_sheets_titles()

    matched_sheet_name = next((name for name in sheets_names if course_name in name), None)
    if not matched_sheet_name:
        return None

    course_sheet = pd.DataFrame(doc.get_sheet_as_list(matched_sheet_name))
    res = course_sheet.iloc[2:, 1:].astype(str).values.tolist()
    return res

from config.settings import TABLE_TEACHERS_SALARY
from service.hollihop.classes.custom_hollihop import CustomHHApiV2Manager
from service.hollihop.classes.exeptions import TeacherNotFound
from service.tools.gsheet.classes.gspread_client import GSDocumentGSpread


async def get_teacher_salary_by_email(email: str) -> list:
    """
    Get EdUnit completed for teacher by email.
    @param email: Teacher email address
    @return: List of teacher with completed lessons by email
    """
    teacher_target = None
    teachers_active = await CustomHHApiV2Manager().get_active_teachers()
    for teacher in teachers_active:
        if teacher['EMail'] == email:
            teacher_target = teacher
            break

    if teacher_target is None:
        raise TeacherNotFound

    teacher_target_full_name = f"{teacher_target['LastName']} {teacher_target['FirstName']} {teacher_target['MiddleName']}"

    # doc = GSDocument(settings.GSDOCID_TEACHERS_SALARY)
    # teacher_salary = doc.get_sheet_as_df('выгрузка')
    # # Первые две строки бесполезны
    # teacher_salary = teacher_salary.iloc[1:, :].astype(str).values.tolist()

    teacher_salary = GSDocumentGSpread(doc_id=TABLE_TEACHERS_SALARY[0]).get_sheet_as_list('выгрузка')
    teacher_salary = teacher_salary[1:]
    target_salary_stats = []
    for row in teacher_salary:
        if row[11].strip() == teacher_target_full_name.strip():
            target_salary_stats.append(row)
    return target_salary_stats

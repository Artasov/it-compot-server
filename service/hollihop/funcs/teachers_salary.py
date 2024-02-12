from config.settings import TABLE_TEACHERS_SALARY
from service.hollihop.classes.custom_hollihop import CustomHHApiV2Manager
from service.hollihop.classes.exeptions import TeacherNotFound
from service.hollihop.funcs.gsheet2csv import download_google_sheet_as_csv


async def get_teachers_salary():
    """
    Just downloaded GoogleSheet data with teacher salary.
    @return: GSheet table data.
    """
    return await download_google_sheet_as_csv(
        spreadsheet_id=TABLE_TEACHERS_SALARY[0],
        gid=TABLE_TEACHERS_SALARY[1]
    )


async def get_teacher_salary_by_email(email: str) -> list:
    """
    Get EdUnit completed for teacher by email.
    @param email: Teacher email address
    @return: List of teacher with completed lessons by email
    """
    teacher_target = None
    teachers_active = await CustomHHApiV2Manager().getActiveTeachers()
    for teacher in teachers_active:
        if teacher['EMail'] == email:
            teacher_target = teacher
            break

    if teacher_target is None:
        raise TeacherNotFound

    teacher_target_full_name = f"{teacher_target['LastName']} {teacher_target['FirstName']} {teacher_target['MiddleName']}"

    teacher_salary = await get_teachers_salary()
    teacher_salary = teacher_salary[1:]

    target_salary_stats = [teacher_salary[0:1]]
    for row in teacher_salary:
        if row[11].strip() == teacher_target_full_name.strip():
            target_salary_stats.append(row)
    return target_salary_stats

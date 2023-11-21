from config.settings import TABLE_TEACHERS_SALARY
from service.hollihop.classes.custom_hollihop import CustomHHApiV2Manager
from service.hollihop.classes.exeptions import TeacherNotFound
from service.hollihop.funcs.gsheet2csv import download_google_sheet_as_csv


def get_teachers_salary():
    return download_google_sheet_as_csv(
        spreadsheet_id=TABLE_TEACHERS_SALARY[0],
        gid=TABLE_TEACHERS_SALARY[1]
    )


def get_teacher_salary_by_email(email: str) -> list:
    # get teacher by email
    teacher_target = None
    teachers_active = CustomHHApiV2Manager().getActiveTeachers()

    for teacher in teachers_active:
        if teacher['EMail'] == email:
            teacher_target = teacher
            break

    if teacher_target is None:
        raise TeacherNotFound

    teacher_target_full_name = f"{teacher_target['LastName']} {teacher_target['FirstName']} {teacher_target['MiddleName']}"

    teacher_salary = get_teachers_salary()[1:]

    target_salary_stats = [teacher_salary[0:1]]
    for row in teacher_salary:
        if row[11].strip() == teacher_target_full_name.strip():
            target_salary_stats.append(row)
    return target_salary_stats


def get_teacher_salary_by_email_as_csv(email: str):
    target_salary_stats = get_teacher_salary_by_email(email)


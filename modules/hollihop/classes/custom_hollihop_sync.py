from modules.hollihop.classes.custom_hollihop import SetCommentError
from modules.hollihop.classes.hollihop_sync import HolliHopApiV2SyncManager


class CustomHHApiV2SyncManager(HolliHopApiV2SyncManager):

    def set_comment_for_student_ed_unit(self, ed_unit_id: int, student_client_id: int, date: str, passed: bool,
                                        description: str) -> None:
        """
        date: Строка формата YYYY-MM-DD
        """
        first_pass = not passed
        second_pass = passed

        self.setStudentPasses(like_array=[{
            'Date': date,
            'EdUnitId': ed_unit_id,
            'StudentClientId': student_client_id,
            'Pass': first_pass
        }])

        result = self.setStudentPasses(like_array=[{
            'Date': date,
            'EdUnitId': ed_unit_id,
            'StudentClientId': student_client_id,
            'Description': description,
            'Pass': second_pass
        }])

        if not result.get('success'):
            raise SetCommentError('Ошибка при добавлении комментария')

    def get_teacher_by_email(self, email):
        teachers = self.getTeachers()
        for teacher in teachers:
            if teacher['EMail'].lower() == email.lower():
                return teacher

    def get_full_teacher_name_by_email(self, email):
        teacher = self.get_teacher_by_email(email)
        if teacher:
            return f'{teacher["LastName"]} {teacher["FirstName"]} {teacher["MiddleName"]}'
        return None

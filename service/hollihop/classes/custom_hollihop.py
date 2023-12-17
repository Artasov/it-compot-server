from service.hollihop.classes.hollihop import HolliHopApiV2Manager


class CustomHHApiV2Manager(HolliHopApiV2Manager):
    def getActiveTeachers(self):
        teachers = self.getTeachers(take=10000)
        active_teachers = []

        if teachers is not None:
            for teacher in teachers:
                # Проверяем, что у преподавателя есть статус и он не равен "уволен"
                if teacher.get('Status', '').lower() != 'уволен':
                    active_teachers.append(teacher)

        return active_teachers

    def get_short_names_teachers(self) -> list:
        all_teachers = self.getActiveTeachers()
        short_names_teachers = []
        for teacher in all_teachers:
            try:
                last_name = teacher['LastName']
            except KeyError:
                last_name = ''

            try:
                first_name_short = teacher['FirstName'][0]
            except KeyError:
                first_name_short = ''
            try:
                middle_name_short = teacher['MiddleName'][0]
            except KeyError:
                middle_name_short = ''
            fio = ''
            if last_name:
                fio += last_name
            if first_name_short:
                fio += f' {first_name_short}.'
            if middle_name_short:
                fio += f' {middle_name_short}.'
            if fio:
                short_names_teachers.append(fio)
        return short_names_teachers

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

from django.http import HttpResponse
from django.shortcuts import render

from core.error_messages import TEACHER_EMAIL_NOT_FOUND
from core.forms.teachers_salary import GetTeacherSalaryForm
from service.common.common import create_virtual_csv
from service.hollihop.classes.exeptions import TeacherNotFound
from service.hollihop.funcs.teachers_salary import get_teacher_salary_by_email


def teacher_salary(request):
    form = GetTeacherSalaryForm(request.POST or None)
    if form.is_valid():
        email = form.cleaned_data['email']
        try:
            teacher_salary_rows = get_teacher_salary_by_email(email)
            sum_salary = 0
            for i, row in enumerate(teacher_salary_rows):
                if i == 0:
                    continue
                sum_salary += int(row[-1])

            return render(request, 'core/other/teachers_salary_result.html', {
                'teacher_salary_rows': teacher_salary_rows,
                'sum_salary': sum_salary,
                'email': email
            })
        except TeacherNotFound:
            form.add_error(None, TEACHER_EMAIL_NOT_FOUND)
    return render(request, 'core/other/teachers_salary.html', {'form': form})

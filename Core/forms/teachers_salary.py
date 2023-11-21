from django import forms

from config.settings import TEACHER_SALARY_PASSWORD
from Core.error_messages import TEACHER_EMAIL_NOT_FOUND, TEACHER_SALARY_PASSWORD_WRONG


class GetTeacherSalaryForm(forms.Form):
    email = forms.CharField(
        label='HH Email',
        min_length=4,
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'HH Email'}))
    password = forms.CharField(
        label='Password',
        min_length=4,
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data['password']
        if password != TEACHER_SALARY_PASSWORD:
            raise forms.ValidationError(TEACHER_SALARY_PASSWORD_WRONG)
        return cleaned_data
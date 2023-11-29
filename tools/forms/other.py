from django import forms


class LoadHHTeachersScheduleXLSXForm(forms.Form):
    gsheet_id = forms.CharField(
        label='GSheet ID',
        min_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'GSheet ID'}))
    file = forms.FileField(
        label='HH teachers schedule .xlsx',
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

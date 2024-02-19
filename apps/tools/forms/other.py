from django import forms


class LoadHHTeachersScheduleXLSXForm(forms.Form):
    gdoc_id = forms.CharField(
        label='Doc ID',
        min_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Doc ID'}))
    new_glist_name = forms.CharField(
        label='New list name',
        min_length=2,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'New list name'}))
    file = forms.FileField(
        label='HH teachers schedule .xlsx',
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

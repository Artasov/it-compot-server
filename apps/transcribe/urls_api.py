from django.urls import path

from transcribe.api import transcribe_lead_call

urlpatterns = [
    path('transcribe_lead_call/', transcribe_lead_call, name='transcribe_lead_call'),
]

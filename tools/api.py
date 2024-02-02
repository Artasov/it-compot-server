from asgiref.sync import async_to_sync
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from service.hollihop.classes.custom_hollihop import CustomHHApiV2Manager


class FormingGroupParamsSerializer(serializers.Serializer):
    level = serializers.CharField(max_length=200)
    discipline = serializers.CharField(max_length=400)
    age = serializers.IntegerField()


@api_view(('GET',))
def get_forming_groups(request):
    serializer = FormingGroupParamsSerializer(data=request.GET)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data = serializer.validated_data

    HHManager = CustomHHApiV2Manager()
    groups_available = async_to_sync(HHManager.get_forming_groups)(
        level=data.get('level'),
        discipline=data.get('discipline'),
        age=data.get('age')
    )
    groups_result = []
    for group in groups_available:
        groups_result.append({
            'Id': group['Id'],
            'Type': group['Type'],
            'Discipline': group['Discipline'],
            'StudentsCount': group['StudentsCount'],
            'Vacancies': group['Vacancies'],
            'ScheduleItems': group['ScheduleItems'],
            'OfficeTimeZone': group['OfficeTimeZone'],
        })
    return Response(groups_result, status=status.HTTP_200_OK)

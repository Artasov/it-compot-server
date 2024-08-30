from adrf.serializers import Serializer as AsyncSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from modules.hollihop.consts import amo_hh_levels_map, amo_hh_disciplines_map


class FormingGroupParamsSerializer(AsyncSerializer):
    student_full_name = serializers.CharField(max_length=400, required=False)
    email = serializers.EmailField(required=False)
    tel = serializers.CharField(max_length=14, required=False)
    level = serializers.CharField(max_length=200, required=False)
    discipline = serializers.CharField(max_length=400)
    age = serializers.IntegerField(required=False)



class StudentToGroupSerializer(AsyncSerializer):
    group_id = serializers.IntegerField()
    student_id = serializers.IntegerField()
    client_tz = serializers.IntegerField()
    join_type = serializers.CharField(max_length=50)


class StudentAlreadyStudyingOnDisciplineSerializer(AsyncSerializer):
    student_id = serializers.IntegerField()
    discipline = serializers.CharField(max_length=400)


class SendNothingFitSerializer(AsyncSerializer):
    msg = serializers.CharField(max_length=1000)
    student_id = serializers.IntegerField()
    join_type = serializers.CharField(max_length=50)


class AddHhPaymentByAmoSerializer(AsyncSerializer):
    student_id = serializers.IntegerField()  # id ученика
    currency = serializers.CharField(max_length=50, default='Рубль')  # валюта
    sum = serializers.IntegerField()  # сумма
    payment_type = serializers.CharField(max_length=50)  # вид платежа
    course = serializers.CharField(max_length=150)  # курс для комментария


class BuildLinkForJoinToFormingGroupSerializer(AsyncSerializer):
    level = serializers.CharField(max_length=200)
    discipline = serializers.CharField(max_length=400)
    age = serializers.IntegerField()
    student_id = serializers.IntegerField()

    def validate(self, data):
        level_map = dict(amo_hh_levels_map)
        data['level'] = level_map.get(data['level'], None)
        discipline_map = dict(amo_hh_disciplines_map)
        data['discipline'] = discipline_map.get(data['discipline'], None)
        if not all((data['level'], data['discipline'])):
            missing_fields = []
            if not data['level']:
                missing_fields.append('level')
            if not data['discipline']:
                missing_fields.append('discipline')
            raise ValidationError(
                detail=f"Unable to map provided "
                       f"{' and '.join(missing_fields)}"
                       f" to HH platform. Check the input values."
            )
        return data

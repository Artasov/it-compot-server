from adrf.serializers import Serializer as AsyncSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from tools.services.signup_group.const import amo_hh_levels_map, amo_hh_disciplines_map


class FormingGroupParamsSerializer(AsyncSerializer):
    level = serializers.CharField(max_length=200)
    discipline = serializers.CharField(max_length=400)
    age = serializers.IntegerField()


class StudentToGroupSerializer(AsyncSerializer):
    group_id = serializers.IntegerField()
    student_id = serializers.IntegerField()


class StudentAlreadyStudyingOnDisciplineSerializer(AsyncSerializer):
    student_id = serializers.IntegerField()
    discipline = serializers.CharField(max_length=400)


class SendNothingFitSerializer(AsyncSerializer):
    msg = serializers.CharField(max_length=1000)
    student_id = serializers.IntegerField()


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

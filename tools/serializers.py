from adrf.serializers import Serializer as AsyncSerializer
from rest_framework import serializers


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

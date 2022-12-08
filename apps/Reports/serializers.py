from datetime import datetime

from django.db.models import Model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from Reports.models import Reports


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reports
        exclude = ('is_delete', "create_user", "deleted_time")
        extra_kwargs = {
            'updated_time': {"format": "%Y-%m-%d %H:%M:%S"},
            'created_time': {"format": "%Y-%m-%d %H:%M:%S"},
            'update_user': {"required": False},
            'name': {"required": False}
        }

    def create(self, validated_data):
        """
        将创建用户的信息添加到validated_data中
        :param validated_data:
        :return:
        """

        validated_data['create_user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        将更新用户的信息添加到validated_data中
        :param instance:
        :param validated_data:
        :return:
        """
        validated_data['update_user'] = self.context['request'].user
        return super().update(instance, validated_data)

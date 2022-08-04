from datetime import datetime

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from Projects.models import Projects
from TestCasesDiretorys.models import TestcaseDirectory
from TestCasesDiretorys.serializers import TestCaseDirectorySerializer


class ProjectSerializers(serializers.ModelSerializer):
    # 使用从表的序列化器类作为主表的关联字段进行输出
    testcase_directory = TestCaseDirectorySerializer(label='用例目录', help_text='用例目录', many=True, read_only=True)

    class Meta:
        model = Projects
        exclude = ('created_time', 'updated_time', 'is_delete', "create_user", "update_user", "deleted_time")

        extra_kwargs = {
            'name': {
                'required': True,
                'validators': [UniqueValidator(queryset=Projects.objects.all(), message='项目名称不能重复')],
            },
            'owner': {'required': False},
            'app': {'required': False},
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
        # 将当前用户设置为更新用户
        validated_data['update_user'] = self.context['request'].user.username
        return super().update(instance, validated_data)

from datetime import datetime

from django.db.models import Model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from Projects.models import Projects
from TestCasesDiretorys.models import TestcaseDirectory
from TestCasesDiretorys.serializers import TestCaseDirectorySerializer


class ProjectSerializers(serializers.ModelSerializer):
    # 使用从表的序列化器类作为主表的关联字段进行输出
    testcase_directory = TestCaseDirectorySerializer(label='用例目录', help_text='用例目录', many=True, read_only=True)

    # testcase_directory = serializers.PrimaryKeyRelatedField(label='父目录', help_text='父目录',
    #                                                         queryset=TestcaseDirectory.objects.all().filter(
    #                                                             is_delete=False))

    class Meta:
        model = Projects
        exclude = ('is_delete', "create_user", "update_user", "deleted_time")

        extra_kwargs = {
            'name': {
                'required': True,  # 必填
                'error_messages': {'required': '项目名称不能为空', 'blank': '项目名称不能为空', 'null': '项目名称不能为空'}
            },
            'owner': {'error_messages': {'required': '项目负责人不能为空', 'blank': '项目负责人不能为空', 'null': '项目负责人不能为空'}},
            'app': {'required': False},
            'type': {'error_messages': {'required': '项目类型不能为空', 'blank': '项目类型不能为空', 'null': '项目类型不能为空'}},
            'version': {'error_messages': {'required': '项目版本不能为空', 'blank': '项目版本不能为空', 'null': '项目版本不能为空'}},
            'updated_time': {'format': '%Y-%m-%d %H:%M:%S', 'read_only': True},
            'created_time': {'format': '%Y-%m-%d %H:%M:%S', 'read_only': True},
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

    def to_representation(self, instance):
        text = super().to_representation(instance)
        testcase_directorys = text.get('testcase_directory')
        for testcase_directory in testcase_directorys:
            pop_id = TestcaseDirectory.objects.filter(id=testcase_directory.get('id'), is_delete=True)
            if pop_id:
                testcase_directory.clear()

        return text

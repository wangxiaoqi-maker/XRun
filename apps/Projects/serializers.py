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

    def validate(self, attrs):
        # 校验项目名称不能重复
        names = Projects.objects.filter(name=attrs.get('name'), is_delete=False)  # 第二个调用
        if names:
            # 当筛选的模型类不为空时，数据库中的主键id和传入需要更新的主键id是否一致，若一致则可以更新，不一致则抛出异常
            if self.context['request'].data.get('id') != str(names.first().id) and attrs.get(
                    'name') == names.first().name:
                raise serializers.ValidationError({"message": "项目名称已存在", "success": True})
        return attrs

    def to_representation(self, instance):
        """
        过滤已被物理删除的目录
        """
        instances = super().to_representation(instance)
        testcase_directorys = instances.get('testcase_directory')
        if testcase_directorys:
            for testcase_directory in testcase_directorys:
                clear_id = TestcaseDirectory.objects.filter(id=testcase_directory.get('id'), is_delete=True)
                if clear_id:
                    testcase_directory.clear()
        return instances

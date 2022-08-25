from django.db.models import QuerySet
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from Interfaces.serializers import InterfaceSeralizers
from Projects.models import Projects
from TestCasesDiretorys.models import TestcaseDirectory


class TestCaseDirectorySerializer(serializers.ModelSerializer):
    # parent_directory = serializers.PrimaryKeyRelatedField(label='父目录', help_text='父目录',
    #                                                       queryset=TestcaseDirectory.objects.all())
    # 使用从表的序列化器类作为主表的关联字段进行输出
    interfaces = InterfaceSeralizers(label='目录所属接口信息', help_text='目录所属接口信息', many=True, read_only=True)

    class Meta:
        model = TestcaseDirectory
        fields = ('id', 'name', 'projects', 'parent', 'interfaces', 'desc')
        extra_kwargs = {
            'parent': {'required': False},
            'id': {'error_messages': {'required': '目录id不能为空', 'blank': '目录id不能为空', 'null': '目录id不能为空'}},
            'projects': {'error_messages': {'required': '目录所属项目不能为空', 'blank': '目录所属项目不能为空', 'null': '目录所属项目不能为空'}},
        }

    def create(self, validated_data):
        """
        不同项目下可以创建相同目录名称
        同项目下不同目录级别可以创建相同目录名称
        :param validated_data:
        :return:
        """

        validated_data['create_user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        调用update方法时将该用户设置为最后修改人
        :param instance:
        :param validated_data:
        :return:
        """
        validated_data['update_user'] = self.context['request'].user.username
        return super().update(instance, validated_data)

    def validate(self, attrs: dict) -> dict:
        # 判断项目是否存在
        projects: QuerySet[Projects] = Projects.objects.filter(id=attrs.get('projects').id,
                                                               is_delete=False)
        if not projects:
            raise serializers.ValidationError('项目不存在')
        # 校验目录名称不能重复
        name = attrs.get('name')
        parent = attrs.get('parent')
        projects = attrs.get('projects')
        if parent:
            # 同项目下不同目录级别可以创建相同目录名称
            directorys = TestcaseDirectory.objects.filter(name=name, parent=parent, projects=projects,
                                                          is_delete=False)
            parent_directory = TestcaseDirectory.objects.filter(id=parent.id, is_delete=False)
            if not parent_directory:
                raise serializers.ValidationError('父目录不存在')
        else:
            # 不同项目下可以创建相同目录名称
            directorys: QuerySet[TestcaseDirectory] = TestcaseDirectory.objects.filter(name=name, projects=projects,
                                                                                       is_delete=False)
        if directorys:
            raise serializers.ValidationError('目录名称已存在')
        return attrs

    def validate_projects(self, value):
        """
        校验项目是否存在
        :param value:
        :return:
        """
        projects: QuerySet[Projects] = Projects.objects.filter(id=value.id, is_delete=False)
        if not projects:
            raise serializers.ValidationError('项目不存在')
        return value

    def to_representation(self, instance):
        """
        过滤目录下被逻辑删除的接口信息
        """
        ret = super().to_representation(instance)
        ret['interfaces'] = InterfaceSeralizers(instance.interfaces.filter(is_delete=False), many=True).data
        return ret

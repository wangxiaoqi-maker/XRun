from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from Interfaces.serializers import InterfaceSeralizers
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
        duplicate_name = TestcaseDirectory.objects.filter(name=validated_data['name'],
                                                          projects=validated_data['projects'],
                                                          parent_id=validated_data.get('parent'),
                                                          is_delete=False)
        if duplicate_name:
            # 判断是否是同一个目录
            raise serializers.ValidationError({"code": "400", "message": "目录名称已存在", "success": False})
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

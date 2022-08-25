from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from Interfaces.models import Interfaces
from TestCasesDiretorys.models import TestcaseDirectory


class InterfaceSeralizers(serializers.ModelSerializer):
    class Meta:
        model = Interfaces
        exclude = ('is_delete', "create_user", "update_user", "deleted_time")
        extra_kwargs = {
            "updated_time": {
                "read_only": True,
                "format": "%Y-%m-%d %H:%M:%S"
            },
            "created_time": {
                "read_only": True,
                "format": "%Y-%m-%d %H:%M:%S"},
            'name': {
                'required': True,  # 必填
                'error_messages': {'required': '接口名称不能为空', 'blank': '接口名称不能为空', 'null': '接口名称不能为空'}
            },
            'url': {'required': True,
                    'error_messages': {'required': '接口url不能为空', 'blank': '接口url不能为空', 'null': '接口url不能为空'}},
            'request_method': {'required': True,
                               'error_messages': {'required': '请求方法不能为空', 'blank': '请求方法不能为空', 'null': '请求方法不能为空'}},
            'body_type': {'required': True,
                          'error_messages': {'required': '请求体类型不能为空', 'blank': '请求体类型不能为空', 'null': '请求体类型不能为空'}},
            'directory': {'error_messages': {'required': '接口所属目录不能为空', 'blank': '接口所属目录不能为空', 'null': '接口所属目录不能为空'}}

        }

    def create(self, validated_data):
        """
        将当前用户设置为创建用户
        """

        validated_data['create_user'] = self.context['request'].user.username
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        将当前用户设置为最后修改用户
        """
        validated_data['update_user'] = self.context['request'].user.username
        return super().update(instance, validated_data)

    def validate(self, attrs):
        duplicate_directory = TestcaseDirectory.objects.filter(id=attrs.get('directory').id,
                                                               is_delete=False).exists()
        if not duplicate_directory:
            # 判断目录是否存在
            raise serializers.ValidationError({"code": "400", "message": "目录不存在", "success": False})
        # 校验在创建接口时，不同的目录下可以创建相同的接口名称
        names = Interfaces.objects.filter(name=attrs.get('name'), is_delete=False,
                                          directory=attrs.get('directory').id)  # 第二个调用
        if names:
            # 当筛选的模型类不为空时，数据库中的主键id和传入需要更新的主键id是否一致，若一致则可以更新，不一致则抛出异常
            if self.context['request'].data.get('id') != str(names.first().id) and attrs.get(
                    'name') == names.first().name and attrs.get('directory') == names.first().directory:
                raise serializers.ValidationError({"message": "接口名称已存在", "success": True})
        return attrs

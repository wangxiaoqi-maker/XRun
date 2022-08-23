from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from Interfaces.models import Interfaces


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
        names = Interfaces.objects.filter(name=attrs.get('name'), is_delete=False)  # 第二个调用
        if names:
            if attrs.get('id') == str(names.first().id):
                return attrs
            raise serializers.ValidationError({"message": "接口名称已存在", "success": True})
        return attrs

from rest_framework import serializers, validators
from rest_framework.validators import UniqueValidator

from Configs.models import Config


class ConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = Config
        fields = 'name', 'base_url', 'desc , created_time', 'update_time'
        extra_kwargs = {
            'name': {"required": True,
                     "error_messages": {"required": "配置名称不能为空", "blank": "配置名称不能为空", "null": "配置名称不能为空"}},
            'base_url': {"required": True,
                         "error_messages": {"required": "公共url不能为空", "blank": "公共url不能为空", "null": "公共url不能为空"}},
            'created_time': {'read_only': True, 'format': '%Y-%m-%d %H:%M:%S'},
            'update_time': {'read_only': True, 'format': '%Y-%m-%d %H:%M:%S'},
        }

    def create(self, validated_data):
        validated_data["create_user"] = self.context["request"].user.username
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["update_user"] = self.context["request"].user.username
        return super().update(instance, validated_data)

    def validate(self, attrs):
        names = Config.objects.filter(name=attrs.get('name'), is_delete=False)  # 第二个调用
        if names:
            if attrs.get('id') == str(names.first().id):
                return attrs
            raise serializers.ValidationError({"message": "配置名称已存在", "success": True})
        return attrs

    def to_internal_value(self, data):
        path = self.context['request'].path  # post方法第一个调用
        return data

    def to_representation(self, instance):
        return super().to_representation(instance)  # get方法第一个调用

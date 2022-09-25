from rest_framework import serializers

from Configs.models import Config
from Interfaces.models import Interfaces
from Interfaces.serializers import InterfaceSeralizers
from Projects.models import Projects
from TestSuit.models import TestSuit


class CaseListSerializers(serializers.ModelSerializer):
    id = serializers.IntegerField(label='用例id', help_text='用例id')
    name = serializers.CharField(label='用例名称', help_text='用例名称', max_length=200, min_length=2, )
    request_method = serializers.CharField(label='请求方法', help_text='请求方法', max_length=200, min_length=2, )
    url = serializers.CharField(label='请求地址', help_text='请求地址', max_length=200, min_length=2, )
    is_delete = serializers.BooleanField(label='是否删除', help_text='是否删除')

    class Meta:
        model = Interfaces
        fields = ('id', 'name', 'request_method', 'url', 'is_delete')


class TestSuitSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestSuit
        exclude = ('is_delete', "create_user", "update_user", "deleted_time")
        extra_kwargs = {'name': {'required': True,
                                 'error_messages': {'required': '套件名称不能为空', 'blank': '套件名称不能为空', 'null': '套件名称不能为空'}},
                        'project': {'required': True,
                                    'error_messages': {'required': '项目不能为空', 'blank': '项目不能为空', 'null': '项目不能为空'}},
                        'case_list': {'required': False},
                        'env': {'required': True,
                                'error_messages': {'required': '环境不能为空', 'blank': '环境不能为空', 'null': '环境不能为空'}},
                        'priority': {'required': False},
                        'created_time': {'format': '%Y-%m-%d %H:%M:%S'},
                        'updated_time': {'format': '%Y-%m-%d %H:%M:%S'},
                        }

    def create(self, validated_data):
        """
        重写create方法，实现套件创建时自动添加创建人
        :param validated_data:
        :return:
        """
        validated_data['create_user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        重写update方法，实现套件更新时自动添加更新人
        :param instance:
        :param validated_data:
        :return:
        """
        validated_data['update_user'] = self.context['request'].user
        return super().update(instance, validated_data)

    def validate(self, attrs):
        """
        校验在不同项目下可以创建相同的套件名称
        """
        project = Projects.objects.filter(id=attrs.get('project').id, is_delete=False).first()
        env = Config.objects.filter(id=attrs.get('env').id, is_delete=False).first()
        # case_list = attrs.get('case_list')
        # if case_list:
        #     for i in case_list:
        #         case = Interfaces.objects.filter(id=i.id, is_delete=False).first()
        #         if not case:
        #             raise serializers.ValidationError('用例不存在')
        if not project:
            raise serializers.ValidationError('项目不存在')
        if not env:
            raise serializers.ValidationError('环境不存在')
        if attrs.get('name'):
            if TestSuit.objects.filter(name=attrs['name'], project=attrs['project'].id, is_delete=False).exists():
                raise serializers.ValidationError('该项目下已存在相同名称的套件')
        return attrs

    def to_representation(self, instance):
        """
        过滤case_list中已被删除的用例
        """
        ret = super().to_representation(instance)
        ret['case_list'] = CaseListSerializers(instance.case_list.filter(is_delete=False), many=True).data
        return ret

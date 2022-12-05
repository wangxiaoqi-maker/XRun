from rest_framework import serializers

from Configs.models import Config
from Interfaces.models import Interfaces
from Interfaces.serializers import InterfaceSeralizers
from Projects.models import Projects
from TestSuit.models import TestSuit, TestCaseStep


class CaseListSerializers(serializers.ModelSerializer):
    id = serializers.IntegerField(label='用例id', help_text='用例id')
    name = serializers.CharField(label='用例名称', help_text='用例名称', max_length=200, min_length=2, )
    request_method = serializers.CharField(label='请求方法', help_text='请求方法', max_length=200, min_length=2, )
    url = serializers.CharField(label='请求地址', help_text='请求地址', max_length=200, min_length=2, )
    is_delete = serializers.BooleanField(label='是否删除', help_text='是否删除')
    status = serializers.CharField(label='测试结果', help_text='测试结果', max_length=200, min_length=1, )
    response = serializers.CharField(label='响应结果', help_text='响应结果', max_length=200, min_length=1, )
    request_type = serializers.CharField(label='请求类型', help_text='请求类型', max_length=200, min_length=1, )
    request_headers = serializers.CharField(label='请求头', help_text='请求头', max_length=200, min_length=1, )
    body = serializers.CharField(label='请求体', help_text='请求体', max_length=100000, min_length=1, )
    body_type = serializers.CharField(label='请求体类型', help_text='请求体类型', max_length=200, min_length=1, )
    assert_list = serializers.CharField(label='断言', help_text='断言', max_length=200, min_length=1, )
    out_params = serializers.CharField(label='提取参数', help_text='提取参数', max_length=200, min_length=1, )
    case_type = serializers.CharField(label='用例类型', help_text='用例类型', max_length=200, min_length=1, )

    class Meta:
        model = Interfaces
        fields = (
            'id', 'name', 'request_method', 'url', 'is_delete', 'status', 'response', 'request_type', 'request_headers',
            'body', 'body_type', 'assert_list', 'out_params', 'case_type')
        extra_kwargs = {"updated_time": {'format': '%Y-%m-%d %H:%M:%S'}}


class TestSuitSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestSuit
        exclude = ('is_delete', "create_user", "deleted_time")
        extra_kwargs = {'name': {'required': True,
                                 'error_messages': {'required': '套件名称不能为空', 'blank': '套件名称不能为空', 'null': '套件名称不能为空'}},
                        'project': {'required': True,
                                    'error_messages': {'required': '项目不能为空', 'blank': '项目不能为空', 'null': '项目不能为空'}},
                        'priority': {'required': False},
                        'created_time': {'format': '%Y-%m-%d %H:%M:%S'},
                        'updated_time': {'format': '%Y-%m-%d %H:%M:%S'},
                        'update_user': {'required': False},
                        'case_tag': {'required': True},
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
        validated_data['update_user'] = self.context['request'].user.username
        return super().update(instance, validated_data)

    def validate(self, attrs):
        """
        1.校验在不同项目下可以创建相同的套件名称
        2.校验在同一项目下套件名称不能重复
        3.校验环境是否存在
        4.当更新时，同一个套件名称可以重复
        """
        project = Projects.objects.filter(id=attrs.get('project').id, is_delete=False).first()
        # env = Config.objects.filter(id=attrs.get('env').id, is_delete=False).first()
        if not project:
            raise serializers.ValidationError('项目不存在')
        # if not env:
        #     raise serializers.ValidationError('环境不存在')
        if attrs.get('name'):
            if self.instance:
                if TestSuit.objects.filter(name=attrs.get('name'), project=project, is_delete=False).exclude(
                        id=self.instance.id).exists():
                    raise serializers.ValidationError('套件名称已存在')
            else:
                if TestSuit.objects.filter(name=attrs.get('name'), project=project, is_delete=False).exists():
                    raise serializers.ValidationError('套件名称已存在')
        return attrs

    def to_representation(self, instance):
        """
        重写to_representation方法，实现返回某个套件下的所有步骤
        """
        ret = super().to_representation(instance)
        ret['case_list'] = TestCaseStepSerializer(TestCaseStep.objects.filter(testsuit_id=instance.id), many=True).data
        return ret


class TestCaseStepSerializer(serializers.ModelSerializer):
    """
    用例步骤序列化器
    """
    case_list = serializers.ListSerializer(child=serializers.IntegerField(), required=True, allow_null=True,
                                           write_only=True)

    class Meta:
        model = TestCaseStep
        exclude = ('is_delete', "create_user", "deleted_time")
        extra_kwargs = {
            'update_user': {'required': False},
            'updated_time': {'format': '%Y-%m-%d %H:%M:%S'},
            'created_time': {'format': '%Y-%m-%d %H:%M:%S'},
            "interface": {'required': False},
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
        validated_data['update_user'] = self.context['request'].user.username
        return super().update(instance, validated_data)

    def validate(self, attrs):
        """
        1. 判断case_id的用例是否存在且不能为空
        2. 循环拿出case_id的用例，插入到TestSuitStep中
        """
        case_list = attrs.get('case_list')
        if case_list:
            for case_id in case_list:
                case = Interfaces.objects.filter(id=case_id, is_delete=False).first()
                if not case:
                    raise serializers.ValidationError('用例不存在')
                else:
                    # 判断是否是最后一个case_id
                    if case_list.index(case_id) == len(case_list) - 1:
                        attrs['interface'] = case
                        attrs.pop('case_list')
                        return attrs
                    else:
                        TestCaseStep.objects.create(testsuit=attrs.get("testsuit").id,
                                                    interface=case,
                                                    execution_order=attrs.get("execution_order"),
                                                    create_user=self.context['request'].user)
        return attrs

    def to_representation(self, instance):
        """
        将用一个套件下的所有用例组装到一个列表中返回
        """
        ret = super().to_representation(instance)
        # 已删除的用例不返回
        if instance.interface.is_delete:
            ret['case_step'] = []
        else:
            ret['case_step'] = CaseListSerializers(instance.interface).data
        return ret

from rest_framework import serializers

from Interfaces.models import Interfaces


class SendHttpRequestSeralizer(serializers.ModelSerializer):
    """
    发送http请求的序列化器
    """
    # 发送请求的接口地址
    url = serializers.CharField(max_length=10000, label='接口地址', help_text='接口地址', required=True,
                                error_messages={'required': '接口地址不能为空'})
    # 发送请求的接口请求方式
    request_method = serializers.CharField(max_length=10, label='接口请求方式', help_text='接口请求方式', required=True,
                                           error_messages={'required': '接口请求方式不能为空'})
    # 发送请求的接口请求头
    request_headers = serializers.CharField(max_length=10000, label='接口请求头', help_text='接口请求头', required=False)
    # 发送请求的接口请求体
    body = serializers.CharField(max_length=100000, label='接口请求体', help_text='接口请求', required=False)
    # 发送请求的接口请求体类型
    body_type = serializers.CharField(max_length=10, label='接口请求体类型', help_text='接口请求体类型', required=True,
                                      error_messages={'required': '接口请求体类型不能为空'})
    # 接口的响应结果
    response = serializers.JSONField(label='接口响应结果', help_text='接口响应结果', read_only=True)
    # 断言列表
    assert_list = serializers.CharField(max_length=10000, label='断言列表', help_text='断言列表', required=False)

    class Meta:
        model = Interfaces
        fields = ('url', 'request_method', 'request_headers', 'body', 'body_type', 'response', 'assert_list')
        extra_kwargs = {'response': {'read_only': True},
                        'headers': {'required': False},
                        }


class RunCaseSeralizer(serializers.ModelSerializer):
    """
    执行用例的序列化器
    """
    # 用例id
    case_id = serializers.ListSerializer(label='用例id', help_text='用例id', required=True,
                                         child=serializers.IntegerField(), error_messages={'required': '用例id不能为空'})
    env = serializers.CharField(max_length=100, label='环境', help_text='环境', required=True,
                                error_messages={'required': '环境不能为空', 'blank': '环境不能为空', 'null': '环境不能为空'})
    suite_id = serializers.CharField(max_length=100, label='测试套件', help_text='测试套件', required=True,
                                     error_messages={'required': '测试套件不能为空', 'blank': '测试套件不能为空', 'null': '测试套件不能为空'})

    class Meta:
        model = Interfaces
        fields = ('case_id', 'env', 'suite_id')

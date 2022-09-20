from typing import Dict

from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler
from rest_framework.views import Response
from rest_framework.utils.serializer_helpers import ReturnDict
from rest_framework import status


def custom_handler(err: ValidationError, context: dict):
    """
    自定义异常处理
    将仅针对由引发的异常生成的响应调用异常处理程序。不会用于视图直接返回的任何响应
    """
    # 先调用REST framework默认的异常处理方法获得标准错误响应对
    response = exception_handler(err, context)
    # 循环取出第一个错误提示信息
    try:
        for index, value in enumerate(response.data):
            if index == 0:
                key = value
                if key == 'code':
                    value = response.data['message']
                else:
                    value = response.data[key]

                if isinstance(value, str):
                    message = value
                else:
                    message = value[0]
        # 判断是否有自定义的异常的字段

        if response is None:
            # print(exc)    #错误原因   还可以做更详细的原因，通过判断exc信息类型
            # print(context)  #错误信息
            return Response({
                'message': '网络超时'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, exception=True)

        else:
            print('123 = %s - %s - %s' % (context['view'], context['request'].method, err))
            return Response({
                'message': message,
            }, status=response.status_code, exception=True)
    except Exception:
        return Response({
            'message': str(err),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, exception=True)


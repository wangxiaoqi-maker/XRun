# 导入控制返回的JSON格式的类
from rest_framework import status
from rest_framework.renderers import JSONRenderer


class CustomRenderer(JSONRenderer):
    # 重构render方法
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if renderer_context:
            # 响应的信息，成功和错误的都是这个
            # 成功和异常响应的信息，异常信息在前面自定义异常处理中已经处理为{'message': 'error'}这种格式

            # 如果返回的data为字典类型，则添加code和message字段
            if isinstance(data, dict):
                # 响应信息中有message和code这两个key，则获取响应信息中的message和code，并且将原本data中的这两个key删除，放在自定义响应信息里
                # 响应信息中没有则将msg内容改为操作成功 code改为请求的状态码
                msg = data.pop('message', '操作成功')
                code = data.pop('code', renderer_context["response"].status_code)
                if data.get('success') is not None:
                    success = data.pop('success')
                elif renderer_context["response"].status_code == status.HTTP_200_OK or renderer_context[
                    "response"].status_code == status.HTTP_201_CREATED or renderer_context[
                    "response"].status_code == status.HTTP_204_NO_CONTENT:
                    success = True
                else:
                    success = False
            else:
                msg = '操作失败'
                code = renderer_context["response"].status_code
                success = False

            # 重新构建返回的JSON字典
            for key in data:
                # 判断是否有自定义的异常的字段
                if key == 'message':
                    msg = data[key]
                    data = {}
                    code = 0
            # 自定义返回的格式
            ret = {
                'code': code,
                'message': msg,
                'success': success,
                'data': data,
            }
            # 返回JSON数据
            return super().render(ret, accepted_media_type, renderer_context)
        else:
            return super().render(data, accepted_media_type, renderer_context)

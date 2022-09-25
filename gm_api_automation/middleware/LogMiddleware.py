import time
import json

from django.utils.deprecation import MiddlewareMixin

from gm_api_automation.Utils.loguru_util import logger

log = logger


class OpLogs(MiddlewareMixin):
    __exclude_urls = ['index/']  # 定义不需要记录日志的url名单

    def __init__(self, *args):
        super().__init__(*args)

        self.start_time = None  # 开始时间
        self.end_time = None  # 响应时间
        self.data = {}  # dict数据

    def process_request(self, request):
        """
        请求进入
        :param request: 请求对象
        :return:
        """

        self.start_time = time.time()  # 开始时间
        re_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())  # 请求时间（北京）

        # 请求IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # 如果有代理，获取真实IP
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # 请求方法
        method = request.method

        # 请求参数
        if method == "GET":
            content = request.GET
        else:
            content = json.loads(request.body)
        self.data.update(
            {
                'time': re_time,  # 请求时间
                'url': request.path,  # 请求url
                'method': method,  # 请求方法
                'ip': ip,  # 请求IP
                'body': content,  # 请求参数
                'user': request.user,  # 操作人(需修改)，网站登录用户
                "protocol": request.scheme  # 请求协议
                # 're_user': 'AnonymousUser'  # 匿名操作用户测试
            }
        )

    def process_response(self, request, response):
        """
        响应返回
        :param request: 请求对象
        :param response: 响应对象
        :return: response
        """
        # 请求url在 exclude_urls中，直接return，不保存操作日志记录
        for url in self.__exclude_urls:
            if url in self.data.get('url'):
                return response

        # 获取响应数据字符串(多用于API, 返回JSON字符串)
        rp_response = response.content.decode()
        self.data['response'] = rp_response
        self.data['user'] = request.user

        # 耗时
        self.end_time = time.time()  # 响应时间
        access_time = self.end_time - self.start_time
        self.data['access_time'] = round(access_time * 1000)  # 耗时毫秒/ms

        # 耗时大于3s的请求,单独记录 (可将时间阈值设置在settings中,实现可配置化)
        if self.data.get('access_time') > 6 * 1000:
            log.info(f"耗时大于6秒的日志：{self.data}")  # 超时操作日志记录

        if self.data.get("method") == "get" or self.data.get("method") == "GET":
            # path = (self.data.get('protocol')) + (str(request).replace("WSGIRequest:", "").replace("GET", "").replace(
            #         '<', "").replace('>', ""))
            log.info(
                f"{request}")
        else:
            log.info(f"POST {self.data.get('protocol')}://{self.data.get('ip')}{self.data.get('url')}")
            log.info(f"请求参数: {self.data.get('body')}")
            log.info(f"响应信息: {self.data.get('response')}")

        return response

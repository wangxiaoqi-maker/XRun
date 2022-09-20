import datetime
import json
import time
from json import JSONDecodeError

import requests
from aiohttp import FormData


class Request(object):

    def __init__(self, url, session=False, **kwargs):
        self.url = url
        self.session = session
        self.kwargs = kwargs
        if self.session:
            self.client = requests.session()
            return
        self.client = requests

    @staticmethod
    def get_elapsed(timer: datetime.timedelta):
        """
        获取请求耗时
        """
        if timer.seconds > 0:
            return f"{timer.seconds}.{timer.microseconds // 1000}s"
        return f"{timer.microseconds // 100}ms"

    @staticmethod
    def get_headers(**kwargs):
        """
        [{"name":"Authorization","value":"Bearer eyJ0eXAiOiJKV1Qi","_type":"String","required":true,"restrict":"","desc":"token值","status":"String"}]
        :param kwargs: 请求头参数
        :return: 请求头
        """
        header = {}
        headers = kwargs.get("headers")
        if headers:
            try:
                headers = json.loads(headers)
            except JSONDecodeError:
                raise Exception("headers格式错误")
            for h in headers:
                if h.get("name") and h.get("value"):
                    header[h.get("name")] = h.get("value")
                else:
                    header = {}
        return header

    @staticmethod
    def get_body(**kwargs):
        """
        获取请求体
        :param kwargs: 请求参数
        :return: 请求体
        """
        body = kwargs.get("body")
        if body:
            try:
                return json.loads(body)
            except JSONDecodeError:
                raise Exception("json格式错误")
            except TypeError:
                return body
        return {}

    def get_form_data(self, **kwargs):
        """
        '[{\"name\":\"file\",\"value\":\"excel.xlsx\",\"_type\":\"file\",\"required\":true,\"restrict\":\"\",\"description\":\"id值\"},{\"name\":\"result\",\"value\":\"111\",\"_type\":\"text\",\"required\":true,\"restrict\":\"\",\"description\":\"result值\"}]'
        :param kwargs: 请求参数
        如果是files格式则取到的是文件名，如果是data格式则组装成字典 格式为{'files': 'excel.xlsx', 'data': {'inter': '222'}}
        :return: {'files': 'excel.xlsx', 'data': {'inter': '222'}}
        """
        data = self.kwargs.get("body")
        form_data = {}
        datas = {}
        if data:
            try:
                data = json.loads(data)
            except JSONDecodeError:
                raise Exception("json格式错误")
            for d in data:
                if d.get("_type") == 'file':
                    form_data['files'] = d.get('value')
                if d.get("_type") == 'text':
                    datas[d.get('name')] = d.get('value')
            form_data['data'] = datas
        return form_data

    def request(self, method: str, body_type: str = "json", **kwargs):
        """
        :param method: 请求方法
        :param body_type: 请求体类型
        :param kwargs: 请求参数
        :return: 响应体
        """
        status_code = 0
        elapsed = "-1ms"
        headers = self.get_headers(**kwargs)
        start = time.time()
        try:
            if body_type == "json":
                body = self.get_body(**kwargs)
                response = self.client.request(method, self.url, json=body, headers=headers)
            elif body_type == "params":
                response = self.client.request(method, self.url, headers=headers)
            elif body_type == "form_data":
                body = self.get_form_data(**kwargs)
                if body:
                    if body.get("files"):
                        if body.get("data"):
                            response = self.client.request(method, self.url, files=body.get("files"),
                                                           data=body.get("data"), headers=headers)
                        else:
                            response = self.client.request(method, self.url, files=body.get("files"),
                                                           headers=headers)
                    else:
                        response = self.client.request(method, self.url, data=body.get("data"), headers=headers)
            else:
                response = self.client.request(method, self.url, headers=headers, **kwargs, timeout=30)
            status_code = response.status_code
            cost = "%.0fms" % ((time.time() - start) * 1000)
            data = self.get_resp(response)
            if status_code != 200:
                return Request.collect(False, self.kwargs.get("body"), status_code, data, response.headers,
                                       response.request.headers, elapsed=cost)
            return Request.collect(True, self.kwargs.get("body"), 200, data, response.headers,
                                   response.request.headers, elapsed=cost,
                                   cookies=response.cookies)
        except Exception as e:
            return Request.collect(False, self.kwargs.get("data"), status_code, msg=str(e), elapsed=elapsed)

    @staticmethod
    def get_resp(resp):
        """
        获取响应体
        :param resp: 响应体
        :return: 响应体
        """
        try:
            data = resp.json()
            # 说明是json格式
            return data
            # return json.dumps(data, ensure_ascii=False, indent=4), True
        except JSONDecodeError:
            data = resp.text
            # 说明不是json格式，我们不做loads操作了
            return data

    @staticmethod
    def get_request_data(body):
        """
        获取请求体
        :param body: 请求体
        :return: 请求体
        """
        request_body = body
        if isinstance(body, bytes):
            request_body = request_body.decode()
        if isinstance(body, FormData):
            request_body = str(body)
        if isinstance(request_body, str):
            return json.loads(body)
        if request_body is None:
            return {}
        return json.dumps(request_body, ensure_ascii=False, indent=4)

    @staticmethod
    def collect(status, request_data, status_code=200, response=None, response_headers=None,
                request_headers=None, cookies=None, elapsed=None, msg="success", **kwargs):
        """
        收集http返回数据
        :param status: 请求状态
        :param request_data: 请求入参
        :param status_code: 状态码
        :param response: 响应数据
        :param response_headers: 返回header
        :param request_headers:  请求header
        :param cookies:  cookie
        :param elapsed: 耗时
        :param msg: 报错信息
        :return:
        """
        request_headers = {k: v for k, v in request_headers.items()} if request_headers is not None else {}
        response_headers = {k: v for k, v in response_headers.items()} if response_headers is not None else {}
        cookies = {k: v for k, v in cookies.items()} if cookies is not None else {}
        return {
            "status": status, "response": response, "status_code": status_code,
            "request_data": Request.get_request_data(request_data),
            "response_headers": response_headers, "request_headers": request_headers,
            "msg": msg, "cost": elapsed, "cookies": cookies, **kwargs,
        }


if __name__ == '__main__':
    url = "https://gmjk-hcm-test.nhf.cn/api/gm-health-steward-platform/healthSteward/user/wjjGmOpenToken/login"
    method = "post"
    bodys = """{
    "loginAccount": "17621525387",
    "loginKey": "541925",
    "loginType": "1",
    "landingSource": 7
}"""
    header1 = {
        "token": "Bearer eyJhbGciOiJIUzUxMiJ9.eyJwaG9uZSI6IjE3NjIxNTI1Mzg3IiwiZXhwVGltZSI6MjU5MjAwMDAwMCwiYWNjb3VudE5vIjoiR00yMDIyMDUyMDA5NTYyNjAwMDAwMDAzMDUiLCJyb2xlQ29kZSI6IkhXUjAwMDA0MyIsInRlbmFudElkIjpudWxsLCJlbXBsb3llZUlkIjpudWxsLCJwbGF0VHlwZSI6IjciLCJ1c2VyTmFtZSI6IueOi-Wui-aWhyIsImV4cCI6MTY2NDUwMzkwNSwidXNlcklkIjo0Mzd9.xCpeIhH4POoSn47y_7T1Xs2IYzxm29Z7W6wSkKXiQhk0EYJ7D9st4yoh0hYndvferFeowHKAkR4gkh3n7hC80w"}

    header2 = '[{\"name\":\"file\",\"value\":\"excel.xlsx\",\"_type\":\"file\",\"required\":true,\"restrict\":\"\",\"description\":\"id值\"},{\"name\":\"result\",\"value\":\"111\",\"_type\":\"text\",\"required\":true,\"restrict\":\"\",\"description\":\"result值\"},{\"name\":\"inter\",\"value\":\"222\",\"_type\":\"text\",\"required\":true,\"restrict\":\"\",\"description\":\"result值\"}]'

    print(Request(url, body=bodys).get_form_data(body=header2))

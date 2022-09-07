from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from Executed.serializers import SendHttpRequestSeralizer, RunCaseSeralizer
from Interfaces.models import Interfaces
from gm_api_automation.core.executor import Executor
from gm_api_automation.core.paramters_parse.jsonpath_parser import JSONPathParser
from gm_api_automation.middleware.HttpClient import Request


class SendHttpRequestView(ModelViewSet):
    queryset = Interfaces.objects.all()
    serializer_class = SendHttpRequestSeralizer
    permission_classes = [IsAuthenticated]

    def run_http_request(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = request.data.get('url')
        method = request.data.get('request_method')
        bodys = request.data.get('body')
        headers = request.data.get('request_headers')
        body_type = request.data.get('body_type')
        data = Request(url, body=bodys).request(method=method, body_type=body_type, headers=headers, body=bodys)
        actual = JSONPathParser().parse_assert(data, request.data.get('assert_list'))
        message = Executor().my_assert(actual, True)
        return Response(message)

    def run_case(self, request):
        case_id = request.data.get('case_id')
        if case_id is None or case_id == '':
            return Response({'message': '用例id不能为空', 'success': False})
        case = self.queryset.filter(id=case_id).first()
        if not case:
            return Response({'message': '用例不存在', 'success': False})
        # serializer = RunCaseSeralizer(data=case_id)
        # serializer.is_valid(raise_exception=True)
        url = case.url
        method = case.request_method
        bodys = case.body
        headers = case.request_headers
        body_type = case.body_type
        assert_list = case.assert_list
        data = Request(url, body=bodys).request(method=method, body_type=body_type, headers=headers, body=bodys)
        actual = JSONPathParser().parse_assert(data, assert_list)
        message = Executor().my_assert(actual, True)
        return Response(message)

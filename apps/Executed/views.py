from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from Executed.serializers import SendHttpRequestSeralizer, RunCaseSeralizer
from Interfaces.models import Interfaces
from gm_api_automation.core.executor import Executor, Data
from gm_api_automation.core.paramters_parse.jsonpath_parser import JSONPathParser
from gm_api_automation.core.run_case import parse_case, ParametrizedTestCase, ExecutorTest, add_cases
from gm_api_automation.core.suit import unittest_run_case
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
        assert_list = request.data.get('assert_list')
        if assert_list:
            actual = JSONPathParser().parse_assert(data, request.data.get('assert_list'))
            message = Executor().my_assert(actual, True)
            data['asserts'] = message
        return Response(data)

    def run_case(self, request):
        serializer = RunCaseSeralizer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case_id = request.data.get('case_id')
        if case_id is None or case_id == []:
            return Response({'message': '用例id不能为空', 'success': False})
        cases = parse_case(self.queryset, case_id)
        add_cases(cases)
        message = unittest_run_case()
        return Response(message)

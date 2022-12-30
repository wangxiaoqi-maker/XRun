import json

from django.http import HttpRequest
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from Executed.serializers import SendHttpRequestSeralizer, RunCaseSeralizer
from Interfaces.models import Interfaces
from Reports.views import ReportsView
from TestSuit.models import TestCaseStep
from gm_api_automation.core.executor import Executor, Data, ExecutorTest
from gm_api_automation.core.paramters_parse.jsonpath_parser import JSONPathParser
from gm_api_automation.core.run_case import parse_case, ParametrizedTestCase
from gm_api_automation.core.suit import unittest_run_case
from gm_api_automation.middleware.HttpClient import Request


class SendHttpRequestView(ModelViewSet):
    queryset = Interfaces.objects.all()
    case_step_queryset = TestCaseStep.objects.all()
    serializer_class = SendHttpRequestSeralizer
    permission_classes = [IsAuthenticated]

    def run_http_request(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cases = Executor().replace_single_interface_params(request.data)
        url = cases.get('url')
        method = cases.get('request_method')
        bodys = cases.get('body')
        headers = cases.get('request_headers')
        body_type = cases.get('body_type')
        data = Request(url, body=bodys).request(method=method, body_type=body_type, headers=headers, body=bodys)
        assert_list = cases.get('assert_list')
        out_params = cases.get('out_params')
        Executor().replace_single_interface_params(request.data)
        if out_params is not None:
            data['extract'] = Executor().extract_out_params(data, out_params)
        if assert_list:
            actual = JSONPathParser().parse_assert(data, cases.get('assert_list'))
            message = Executor().my_assert(actual, True)
            data['asserts'] = message
        return Response(data)

    def run_case(self, request):
        serializer = RunCaseSeralizer(data=request.data)
        serializer.is_valid(raise_exception=True)
        step_id = request.data.get('case_id')
        env = request.data.get('env')
        suite_id = request.data.get('suite_id')
        if step_id is None or step_id == []:
            return Response({'message': '用例id不能为空', 'success': False})
        cases = parse_case(self.case_step_queryset, self.get_queryset(), step_id)
        Executor().add_cases(cases, env, suite_id)
        # 调用内部接口，将测试报告保存到数据库
        message = unittest_run_case(suite_id)
        mes = Executor().create_report(request, message, suite_id)
        return Response(mes)

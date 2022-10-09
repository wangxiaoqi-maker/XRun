import json
import unittest
from functools import wraps

import ddt
from django.db.models import QuerySet

from Interfaces.models import Interfaces
from TestSuit.models import TestSuit
from gm_api_automation.Utils.loguru_util import logger
from gm_api_automation.core.executor import Executor
from gm_api_automation.core.paramters_parse.jsonpath_parser import JSONPathParser
from gm_api_automation.middleware import ddt_util
from gm_api_automation.middleware.HttpClient import Request


def parse_case(query_set: QuerySet, case_id: list):
    """
    运行测试用例
    """
    cases = query_set.filter(id__in=case_id, is_delete=False)
    return cases


# 编写获取测试类中变量的装饰器
def get_test_data(func):
    @wraps(func)
    def wrapper(self, case_data):
        self.case_data = case_data
        return func(self, case_data)

    return wrapper


class ParametrizedTestCase(unittest.TestCase):
    """ TestCase classes that want to be parametrized should
        inherit from this class.
    """

    def __init__(self, methodname='runtest', query_set=None, case_id=None):
        super(ParametrizedTestCase, self).__init__(methodname)
        self.query_set = query_set
        self.case_id = case_id

    @staticmethod
    def parametrize(testcase_klass, query_set=None, case_id=None):
        """ Create a suite containing all tests taken from the given
            subclass, passing them the parameter 'param'.
        """
        testloader = unittest.TestLoader()
        testnames = testloader.getTestCaseNames(testcase_klass)
        suite = unittest.TestSuite()
        for name in testnames:
            suite.addTest(testcase_klass(name, query_set=query_set, case_id=case_id))
        return suite


class ExecutorTest(unittest.TestCase):
    pass


def url_handle(new_url: str, env_url: str):
    """
    根据环境变量替换url
    """
    if new_url.startswith('http') or new_url.startswith('https'):
        return new_url
    else:
        return env_url + new_url


def add_cases(cases, envs, suite_id):
    for i in cases:
        def test(self, case=i, env=envs):
            logger.info(f'正在执行用例：{case.name}')
            executor = Executor()
            case = executor.replace_params(case)
            url = case.url
            url_handle(url, env)
            method = case.request_method
            bodys = case.body
            headers = case.request_headers
            body_type = case.body_type
            data = Request(url, body=bodys).request(method=method, body_type=body_type, headers=headers, body=bodys)
            Interfaces.objects.filter(id=case.id).update(response=data.get("response"))
            # 提取参数
            extract = executor.extract_out_params(data, case)
            assert_list = case.assert_list
            params_list = executor.replace_params(case)
            result = []
            if assert_list:
                actual = JSONPathParser().parse_assert(data, params_list.assert_list)
                message = executor.my_assert(actual, True)
                # message字典中的status为false时，用例执行失败，并且将message字典中的msg信息返回
                try:
                    self.assertEqual(message['status'], True)
                    # 更新用例执行结果为成功
                    Interfaces.objects.filter(id=case.id).update(status="成功")
                    status = {"id": case.id, "status": "成功"}
                    result.append(status)
                    TestSuit.objects.filter(id=suite_id).update(status=str(result))
                except AssertionError as e:
                    # 更新用例执行结果为失败
                    status = {"id": case.id, "status": "失败"}
                    result.append(status)
                    Interfaces.objects.filter(id=case.id).update(status="失败")
                    TestSuit.objects.filter(id=suite_id).update(status=str(result))
                    raise AssertionError(message['msg'])
            else:
                # 更新用例执行结果为成功
                Interfaces.objects.filter(id=case.id).update(status="成功")
                status = {"id": case.id, "status": "成功"}
                result.append(status)
                TestSuit.objects.filter(id=suite_id).update(status=str(result))

        setattr(ExecutorTest, f'test_{i}', test)

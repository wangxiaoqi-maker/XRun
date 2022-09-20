import os
import time
import unittest

import ddt
from XTestRunner import HTMLTestRunner
from django.db.models import QuerySet

from gm_api_automation.core import run_case
from gm_api_automation.core.executor import Executor
from gm_api_automation.core.paramters_parse.jsonpath_parser import JSONPathParser
from gm_api_automation.core.run_case import ParametrizedTestCase, parse_case,ExecutorTest
from gm_api_automation.middleware.HttpClient import Request
from gm_api_automation.middleware import ddt_util


def unittest_run_case():
    """
    使用unittest执行测试用例
    """
    suite = unittest.TestSuite()
    suite.addTest(ExecutorTest('test'))
    # 当前时间
    now = time.strftime("%Y%m%d%H%M%S")
    file_name = str(now) + 'report.html'
    print(file_name)
    basedir = os.path.dirname(os.path.dirname((os.path.abspath(__file__))))
    report_dir = os.path.join(basedir, "report")
    report_name = os.path.join(report_dir, file_name)
    # 通过open()方法以二进制写模式('wb')打开当前目录下的report.html，如果没有，则自动创建
    fp = open(report_name, 'wb')
    runner = HTMLTestRunner(
        stream=fp,  # 指定测试报告文件
        title='接口自动化测试报告',  # 定义测试报告的标题
        description='接口自动化测试报告详细信息',  # 定义测试报告的副标题
        verbosity=2,
        language='zh-CN',
    )
    # 执行测试套件
    runner.run(suite)
    fp.close()
    return report_name




import json
import os
import time
import unittest

from XTestRunner import HTMLTestRunner
from django.http import HttpRequest
from Reports.views import ReportsView
from TestSuit.models import TestSuit
from gm_api_automation.core import run_case, executor


def unittest_run_case(suite_id):
    """
    使用unittest执行测试用例
    """
    start_time = time.time()
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromModule(executor))
    # 当前时间
    now = time.strftime("%Y%m%d%H%M%S")
    file_name = str(now) + 'report.html'
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
    result = runner.run(suite)
    fp.close()
    end_time = time.time()
    # 获取报告源码
    with open(report_name, 'rb') as f:
        report_source = f.readlines()
    suite_data = TestSuit.objects.filter(id=suite_id).first()
    # 用例运行时间保留俩位小数
    run_time = round(end_time - start_time, 2)
    TestSuit.objects.filter(id=suite_id).update(run_duration=run_time)
    status = suite_data.status
    if status:
        status = eval(status)
    message = {"result": result, "report_name": file_name, "report_source": report_source, "status": status}
    return message

import json
import os
import time
import unittest

from XTestRunner import HTMLTestRunner

from TestSuit.models import TestSuit
from gm_api_automation.core import run_case


def unittest_run_case(suite_id):
    """
    使用unittest执行测试用例
    """
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromModule(run_case))
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
    # 获取报告源码
    with open(report_name, 'rb') as f:
        report_source = f.readlines()
        # 将读取到的字符串源码去掉隐号
        report_source = [i.decode('utf-8').replace('"', '').replace("\n", "").replace(",", "") for i in report_source]
    TestSuit.objects.filter(id=suite_id).update(report_source_code=report_source, success_count=result.success_count,
                                                failure_count=result.failure_count, error_count=result.error_count,
                                                skip_count=result.skip_count)
    suite_data = TestSuit.objects.filter(id=suite_id).first()
    status = suite_data.status
    if status:
        status = eval(status)
    message = {"success_count": suite_data.success_count, "failure_count": suite_data.failure_count,
               "error_count": suite_data.error_count, "skip_count": suite_data.skip_count,
               "total_count": suite_data.total_count, "status": status,
               "update_time": suite_data.updated_time, "name": suite_data.name, "id": suite_data.id,
               "update_user": suite_data.update_user, "report_source_code": suite_data.report_source_code,
               }
    return message

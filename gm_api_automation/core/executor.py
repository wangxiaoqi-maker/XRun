import asyncio
import json
import re
import time
import unittest
from collections import defaultdict
from datetime import datetime
from typing import List, Any
from requests import request as requests_request

import jsonpath
from django.db.models import QuerySet

from Interfaces.models import Interfaces
from TestSuit.models import TestSuit
from gm_api_automation.Utils.case_log import CaseLog
from gm_api_automation.Utils.loguru_util import logger
from gm_api_automation.core.paramters_parse.jsonpath_parser import JSONPathParser
from gm_api_automation.middleware.HttpClient import Request


class ExecutorTest(unittest.TestCase):
    pass


class Data(object):
    pass


class Executor(object):
    el_exp = r"\$\{(.+?)\}"
    pattern = re.compile(el_exp)

    def __init__(self, log: CaseLog = None):
        if log is None:
            self._logger = CaseLog()
            self._main = True
        else:
            self._logger = log
            self._main = False

    @property
    def logger(self):
        return self._logger

    def append(self, content, end=False):
        if end:
            self.logger.append(content, end)
        else:
            self.logger.append(content, end)

    def my_assert(self, asserts: List, json_format: bool) -> [str, bool]:
        """
        断言验证
        """
        result = dict()
        ok = True
        if len(asserts) == 0:
            self.append("断言列表为空，用例执行完成", True)
            return json.dumps(result, ensure_ascii=False), ok  # 未设置断言, 用例结束
        for index, item in enumerate(asserts):  # 遍历断言
            try:
                # 解析预期/实际结果
                expected = item.get('expected')  # 循环拿出预期结果
                self.append("预期结果: {}".format(expected))
                # 判断请求返回是否是json格式，如果不是则不进行loads操作
                actually = item.get('actually')  # 循环拿出实际结果
                self.append("实际结果: {}".format(actually))
                self.append("断言类型: {}".format(item.get('assert_type')))
                status, err = self.ops(item.get('assert_type'), expected, actually)  # 判断预期结果和实际结果
                assert_name = item.get('assert_name')
                if assert_name is None:
                    assert_name = f"断言{index + 1}"
                result[assert_name] = {"status": status, "msg": err}  # 将断言结果存入result字典中
                self.append("断言结果: {}".format(result))
                result[assert_name]["logs"] = self.logger.join()
            except Exception as e:
                if ok is True:
                    ok = False
                result = {"status": False, "msg": f"断言取值失败, 请检查断言语句: {e}"}  # 将断言结果存入result字典中
                self.append(f"断言取值失败, 请检查断言语句: {e}")
        self.append("断言执行完成", True)
        return result  # 返回断言结果

    def ops(self, assert_type: str, exp, act) -> (bool, str):
        """
        通过断言类型进行校验
        """
        if assert_type == "equal":
            if exp == act:
                return True, f"预期结果: {exp} 等于 实际结果: {act}【✔】"
            return False, f"预期结果: {exp} 不等于 实际结果: {act}【❌】"
        if assert_type == "not_equal":
            if exp != act:
                return True, f"预期结果: {exp} 不等于 实际结果: {act}【✔】"
            return False, f"预期结果: {exp} 等于 实际结果: {act}【❌】"
        if assert_type == "in":
            if exp in act:
                return True, f"预期结果: {exp} 包含于 实际结果: {act}【✔】"
            return False, f"预期结果: {exp} 不包含于 实际结果: {act}【❌】"
        if assert_type == "not_in":
            if exp not in act:
                return True, f"预期结果: {exp} 不包含于 实际结果: {act}【✔】"
            return False, f"预期结果: {exp} 包含于 实际结果: {act}【❌】"
        if assert_type == "int_equal":
            try:
                if eval(f"{exp} == {act}"):
                    return True, f"预期结果: {exp} 等于 实际结果: {act}【✔】"
                return False, f"预期结果: {exp} 不等于 实际结果: {act}【❌】"
            except Exception as e:
                return False, f"断言语句错误: {e}"
        if assert_type == "int_not_equal":
            try:
                if eval(f"{exp} != {act}"):
                    return True, f"预期结果: {exp} 不等于 实际结果: {act}【✔】"
                return False, f"预期结果: {exp} 等于 实际结果: {act}【❌】"
            except Exception as e:
                return False, f"断言语句错误: {e}"
        if assert_type == "int_greater_than":
            try:
                if eval(f"{exp} > {act}"):
                    return True, f"预期结果: {exp} 大于 实际结果: {act}【✔】"
                return False, f"预期结果: {exp} 不大于 实际结果: {act}【❌】"
            except Exception as e:
                return False, f"断言语句错误: {e}"
        if assert_type == "int_greater_than_or_equal":
            try:
                if eval(f"{exp} >= {act}"):
                    return True, f"预期结果: {exp} 大于等于 实际结果: {act}【✔】"
                return False, f"预期结果: {exp} 不大于等于 实际结果: {act}【❌】"
            except Exception as e:
                return False, f"断言语句错误: {e}"
        if assert_type == "int_less_than":
            try:
                if eval(f"{exp} < {act}"):
                    return True, f"预期结果: {exp} 小于 实际结果: {act}【✔】"
                return False, f"预期结果: {exp} 不小于 实际结果: {act}【❌】"
            except Exception as e:
                return False, f"断言语句错误: {e}"
        if assert_type == "int_less_than_or_equal":
            try:
                if eval(f"{exp} <= {act}"):
                    return True, f"预期结果: {exp} 小于等于 实际结果: {act}【✔】"
                return False, f"预期结果: {exp} 不小于等于 实际结果: {act}【❌】"
            except Exception as e:
                return False, f"断言语句错误: {e}"
        if assert_type == "length_eq":
            if exp == len(act):
                return True, f"预期数量: {exp} 等于 实际数量: {len(act)}【✔】"
            return False, f"预期数量: {exp} 不等于 实际数量: {len(act)}【❌】"
        if assert_type == "length_gt":
            if exp > len(act):
                return True, f"预期数量: {exp} 大于 实际数量: {len(act)}【✔】"
            return False, f"预期数量: {exp} 不大于 实际数量: {len(act)}【❌】"
        if assert_type == "length_ge":
            if exp >= len(act):
                return True, f"预期数量: {exp} 大于等于 实际数量: {len(act)}【✔】"
            return False, f"预期数量: {exp} 小于 实际数量: {len(act)}【❌】"
        if assert_type == "length_le":
            if exp <= len(act):
                return True, f"预期数量: {exp} 小于等于 实际数量: {len(act)}【✔】"
            return False, f"预期数量: {exp} 大于 实际数量: {len(act)}【❌】"
        if assert_type == "length_lt":
            if exp < len(act):
                return True, f"预期数量: {exp} 小于 实际数量: {len(act)}【✔】"
            return False, f"预期数量: {exp} 不小于 实际数量: {len(act)}【❌】"
        if assert_type == "text_in":
            if isinstance(act, str):
                # 如果b是string，则不转换
                if exp in act:
                    return True, f"预期结果: {exp} 文本包含于 实际结果: {act}【✔】"
                return False, f"预期结果: {exp} 文本不包含于 实际结果: {act}【❌】"
            temp = json.dumps(act, ensure_ascii=False)
            if exp in temp:
                return True, f"预期结果: {exp} 文本包含于 实际结果: {act}【✔】"
            return False, f"预期结果: {exp} 文本不包含于 实际结果: {act}【❌】"
        if assert_type == "text_not_in":
            if isinstance(act, str):
                if exp in act:
                    return True, f"预期结果: {exp} 文本包含于 实际结果: {act}【❌】"
                return False, f"预期结果: {exp} 文本不包含于 实际结果: {act}【✔】"
            temp = json.dumps(act, ensure_ascii=False)
            if exp in temp:
                return True, f"预期结果: {exp} 文本包含于 实际结果: {act}【❌】"
            return False, f"预期结果: {exp} 文本不包含于 实际结果: {act}【✔】"
        return False, "不支持的断言方式💔"

    @staticmethod
    def translate(data):
        """
        反序列化为Python对象
        """
        return json.loads(data)

    def extract_out_params(self, data: dict, out_params):
        """
        将传入的out_params列表循环拿出，并通过jsonpath提取response中的参数，并更新out_params列表
        """
        out_params_list = []
        if out_params:
            out_params = self.translate(out_params)
            for param in out_params:
                if param.get('extract_obj') == 'response_json':
                    try:
                        value = JSONPathParser().parse(data, param.get('extract_exp'))
                        logger.info(
                            "出参类型为response_json，提取成功，提取表达式为：{}，提取结果为：{}".format(param.get('extract_exp'), value))
                        self.append(f"出参类型为response_json，提取成功，提取表达式为：{param.get('extract_exp')}，提取结果为：{value}")
                        out_params_list.append({param.get('param_name'): value})
                        setattr(Data, param.get('param_name'), value)
                    except Exception as e:
                        logger.info(f"提取参数失败: {e}")
                        self.append(f"提取参数失败: {e}")
                elif param.get('extract_obj') == 'response_text':
                    try:
                        value = str(data)
                        logger.info(
                            "出参类型为response_text，提取成功，提取表达式为：{}，提取结果为：{}".format(param.get('extract_exp'), value))
                        self.append(f"出参类型为response_text，提取成功，提取表达式为：{param.get('extract_exp')}，提取结果为：{value}")
                        out_params_list.append({param.get('param_name'): value})
                        setattr(Data, param.get('param_name'), value)
                    except Exception as e:
                        logger.info(f"提取参数失败: {e}")
                        self.append(f"提取参数失败: {e}")
                elif param.get('extract_obj') == 'response_headers':
                    try:
                        value = JSONPathParser().header_parse(data, param.get('extract_exp'))
                        logger.info(
                            "出参类型为response_headers，提取成功，提取表达式为：{}，提取结果为：{}".format(param.get('extract_exp'), value))
                        self.append(f"出参类型为response_headers，提取成功，提取表达式为：{param.get('extract_exp')}，提取结果为：{value}")
                        out_params_list.append({param.get('param_name'): value})
                        setattr(Data, param.get('param_name'), value)
                    except Exception as e:
                        logger.info(f"提取参数失败: {e}")
                        self.append(f"提取参数失败: {e}")
                else:
                    logger.info(f"不支持的提取对象: {param.get('extract_obj')}")
                    self.append(f"不支持的提取对象: {param.get('extract_obj')}", True)
            self.append('所有出参提取完成', True)
            return out_params_list
        return None

    def replace_params(self, cases):
        """
        找出用例中需要替换的变量名 ${}包含的变量,并替换为对应的值
        """
        # 遍历querySet对象中的所有数据
        fileds = cases.__dict__
        for k, v in fileds.items():
            var = self.get_el_expression(v)
            if var:
                # 如果变量在Data类中存在，则替换，否则不替换
                if hasattr(Data, var[0]):
                    logger.info(f"匹配到需要替换的变量: {var[0]}")
                    self.append('匹配到需要替换的变量: {}'.format(var[0]))
                    value = getattr(Data, var[0])
                    value = v.replace("${{mark}}".replace("{mark}", var[0]), str(value))
                    logger.info(f"变量替换成功，替换后的值为: {value}")
                    self.append('变量替换成功，替换后的值为: {}'.format(value))
                    setattr(cases, k, value)
                    return cases
        return cases

    @staticmethod
    def url_handle(new_url: str, env_url: str):
        """
        根据环境变量替换url
        """
        if new_url.startswith('http') or new_url.startswith('https'):
            return new_url
        else:
            return env_url + new_url

    def add_cases(self, cases, envs, suite_id, case_id):
        result = []
        # 获取测试类中存储的所有用例名称
        test_list = [test for test in ExecutorTest.__dict__ if 'test' in test]
        for test_case in test_list:
            # 删除测试类中的用例
            delattr(ExecutorTest, test_case)
        for i in cases:

            def test(selfs, case=i, env=envs):
                self.append('开始执行用例: {}'.format(case.name))
                logger.info(f'正在执行用例：{case.name}')
                case = self.replace_params(case)
                url = case.url
                url = self.url_handle(url, env)
                method = case.request_method
                bodys = case.body
                headers = case.request_headers
                body_type = case.body_type
                data = Request(url, body=bodys).request(method=method, body_type=body_type, headers=headers, body=bodys)
                Interfaces.objects.filter(id=case.id).update(response=data.get("response"))
                self.append(f"http请求过程\n\nRequest Method: {method}\n\n"
                            f"Request Headers:\n{headers}\n\nUrl: {url}"
                            f"\n\nBody:\n{bodys}\n\nResponse:\n{data.get('response', '未获取到返回值')}")
                # 提取参数
                out_params = case.out_params
                extract = self.extract_out_params(data, out_params)
                assert_list = case.assert_list
                params_list = self.replace_params(case)
                if assert_list:
                    actual = JSONPathParser().parse_assert(data, params_list.assert_list)
                    message = self.my_assert(actual, True)
                    # message字典中的status为false时，用例执行失败，并且将message字典中的msg信息返回
                    for mes in message:
                        if message[mes].get('status'):
                            self.append(f"断言成功，断言结果为：{message[mes].get('msg')}")
                            logger.info(f"断言成功，断言结果为：{message[mes].get('msg')}")
                            Interfaces.objects.filter(id=case.id).update(status="成功")
                            status = {"id": case.id, "status": "成功", "message": message}
                            result.append(status)
                        else:
                            self.append(f"断言失败，断言结果为：{message[mes].get('msg')}", True)
                            logger.info(f"断言失败，断言结果为：{message[mes].get('msg')}")
                            Interfaces.objects.filter(id=case.id).update(status="失败")
                            status = {"id": case.id, "status": "失败", "message": message}
                            result.append(status)
                            self.append('用例执行完成: {}'.format(case.name), True)
                            Interfaces.objects.filter(id=case.id).update(desc=self.logger.join())
                            self.logger.log.clear()
                            TestSuit.objects.filter(id=suite_id).update(status=str(result), state="已完成",
                                                                        updated_time=time.strftime("%Y-%m-%d %H:%M:%S",
                                                                                                   time.localtime()))
                            raise AssertionError(message)
                else:
                    # 更新用例执行结果为成功
                    Interfaces.objects.filter(id=case.id).update(status="成功")
                    status = {"id": case.id, "status": "成功"}
                    result.append(status)
                self.append('用例执行完成: {}'.format(case.name), True)
                self.logger.log.clear()
                TestSuit.objects.filter(id=suite_id).update(status=str(result), state="已完成",
                                                            updated_time=time.strftime("%Y-%m-%d %H:%M:%S",
                                                                                       time.localtime()))

            setattr(ExecutorTest, f'test_{i}', test)

    def get_case_execute_log(self):
        return self.logger.join()

    @staticmethod
    def get_el_expression(string: str):
        """获取字符串中的el表达式
        """
        if string is None or not isinstance(string, str):
            return []
        return re.findall(Executor.pattern, string)

    @staticmethod
    def create_report(request, message, suite_id):
        """生成测试报告
        """
        now_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
        suite_data = TestSuit.objects.filter(id=suite_id).first()
        result = message.get('result')
        report_name = message.get('report_name')
        # 获取当前用户token，并添加到requests请求头中
        token = request.META.get('HTTP_AUTHORIZATION')
        body = {
            "name": f"{suite_data.name}_{now_time}",
            "testsuit": suite_id,
            "success_count": result.success_count,
            "failure_count": result.failure_count,
            "error_count": result.error_count,
            "skipped_count": result.skip_count,
            "total_count": result.success_count + result.failure_count + result.error_count + result.skip_count,
            "status": suite_data.status,
            "report_name": report_name,
            "project": suite_data.project_id,
        }
        # 获取当前的ip和端口
        ip = request.META.get('HTTP_HOST')
        requests_request('POST', 'http://' + ip + '/CreateReport', json=body,
                         headers={'Authorization': token})  # noqa
        body["status"] = eval(suite_data.status)
        return body

    def parse_list_and_replacre(self, cases: list = None, data: dict =None):
        """
        解析用例中的列表和替换用例中的参数
        cases为空时，解析data中的字典并替换
        """
        if cases:
            for case in cases:
                for k, v in case.items():
                    var = self.get_el_expression(v)
                    if var:
                        # 如果变量在Data类中存在，则替换，否则不替换
                        if hasattr(Data, var[0]):
                            logger.info(f"匹配到需要替换的变量: {var[0]}")
                            self.append('匹配到需要替换的变量: {}'.format(var[0]))
                            value = getattr(Data, var[0])
                            case[k] = v.replace(f'${{{var[0]}}}', value)
                            logger.info(f"变量替换成功，替换后的值为: {value}")
                            self.append('变量替换成功，替换后的值为: {}'.format(value))
                        else:
                            logger.info(f"匹配到需要替换的变量: {var[0]}，但是变量不存在")
                            self.append('匹配到需要替换的变量: {}，但是变量不存在'.format(var[0]))
            return cases
        else:
            for k, v in data.items():
                var = self.get_el_expression(v)
                if var:
                    # 如果变量在Data类中存在，则替换，否则不替换
                    if hasattr(Data, var[0]):
                        logger.info(f"匹配到需要替换的变量: {var[0]}")
                        self.append('匹配到需要替换的变量: {}'.format(var[0]))
                        value = getattr(Data, var[0])
                        data[k] = v.replace(f'${{{var[0]}}}', value)
                        logger.info(f"变量替换成功，替换后的值为: {value}")
                        self.append('变量替换成功，替换后的值为: {}'.format(value))
                    else:
                        logger.info(f"匹配到需要替换的变量: {var[0]}，但是变量不存在")
                        self.append('匹配到需要替换的变量: {}，但是变量不存在'.format(var[0]))
            return data

    def replace_single_interface_params(self, cases):
        """
        用例结构为：{'request_method': 'POST', 'url': 'https://gmjk-hcm-test.nhf.cn/wjj-longhua-project/organization/getOrganizationPageList', 'request_headers': '[{"name":"Authorization","value":"${token}","_type":"String","required":true,"restrict":"","desc":""}]', 'out_params': '[{"param_name":"","extract_obj":"response_json","extract_exp":""}]', 'assert_list': '[{"expected":"","assert_obj":"response_text","assert_type":"in","actually":""}]', 'body_type': 'json', 'body': '{"pageNo":2,"pageSize":10}'}
        遍历用例中的数据，将用例中带有${}中的变量 并替换
        """
        request_headers = self.translate(cases.get('request_headers'))
        out_params = self.translate(cases.get('out_params'))
        assert_list = self.translate(cases.get('assert_list'))
        body = self.translate(cases.get('body'))
        cases['request_headers'] = json.dumps(self.parse_list_and_replacre(request_headers))
        cases['out_params'] = json.dumps(self.parse_list_and_replacre(out_params))
        cases['assert_list'] = json.dumps(self.parse_list_and_replacre(assert_list))
        cases['body'] = json.dumps(self.parse_list_and_replacre(data=body))
        return cases


if __name__ == '__main__':
    exp = 1.05
    act = "1.05"
    s = eval(f"{exp} == {act}")
    print(s)

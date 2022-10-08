import asyncio
import json
import re
import time
import unittest
from collections import defaultdict
from datetime import datetime
from typing import List, Any

import jsonpath
from django.db.models import QuerySet

from Interfaces.models import Interfaces
from gm_api_automation.Utils.loguru_util import logger
from gm_api_automation.core.paramters_parse.jsonpath_parser import JSONPathParser
from gm_api_automation.middleware.HttpClient import Request


class Data(object):
    pass


class Executor(object):
    el_exp = r"\$\{(.+?)\}"
    pattern = re.compile(el_exp)

    def my_assert(self, asserts: List, json_format: bool) -> [str, bool]:
        """
        断言验证
        """
        result = dict()
        ok = True
        if len(asserts) == 0:
            return json.dumps(result, ensure_ascii=False), ok  # 未设置断言, 用例结束
        for item in asserts:  # 遍历断言
            try:
                # 解析预期/实际结果
                expected = item.get('expected')  # 循环拿出预期结果
                # 判断请求返回是否是json格式，如果不是则不进行loads操作
                actually = item.get('actually')  # 循环拿出实际结果
                status, err = self.ops(item.get('assert_type'), expected, actually)  # 判断预期结果和实际结果
                result = {"status": status, "msg": err}  # 将断言结果存入result字典中
            except Exception as e:
                if ok is True:
                    ok = False
                result = {"status": False, "msg": f"断言取值失败, 请检查断言语句: {e}"}  # 将断言结果存入result字典中
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

    def extract_out_params(self, data: dict, cases):
        """
        将传入的out_params列表循环拿出，并通过jsonpath提取response中的参数，并更新out_params列表
        """
        out_params = cases.out_params
        if out_params:
            out_params = self.translate(out_params)
            for param in out_params:
                if param.get('extract_obj') == 'response_json':
                    try:
                        value = JSONPathParser().parse(data, param.get('extract_exp'))
                        logger.info("出参类型为response_json，提取成功，提取表达式为：{}，提取结果为：{}".format(param.get('extract_exp'), value))
                        setattr(Data, param.get('param_name'), value)
                    except Exception as e:
                        logger.info(f"提取参数失败: {e}")
                elif param.get('extract_obj') == 'response_text':
                    try:
                        value = str(data)
                        logger.info("出参类型为response_text，提取成功，提取表达式为：{}，提取结果为：{}".format(param.get('extract_exp'), value))
                        setattr(Data, param.get('param_name'), value)
                    except Exception as e:
                        logger.info(f"提取参数失败: {e}")
                elif param.get('extract_obj') == 'response_headers':
                    try:
                        value = JSONPathParser().header_parse(data, param.get('extract_exp'))
                        logger.info("出参类型为response_headers，提取成功，提取表达式为：{}，提取结果为：{}".format(param.get('extract_exp'), value))
                        setattr(Data, param.get('param_name'), value)
                    except Exception as e:
                        logger.info(f"提取参数失败: {e}")
                else:
                    logger.info(f"不支持的提取对象: {param.get('extract_obj')}")
                return out_params
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
                    value = getattr(Data, var[0])
                    value = v.replace("${{mark}}".replace("{mark}", var[0]), value)
                    logger.info(f"变量替换成功，替换后的值为: {value}")
                    setattr(cases, k, value)
                    return cases
        return cases

    def run(self, cases: list):
        """
        运行测试用例
        """
        for case in cases:
            url = case.url
            method = case.request_method
            bodys = case.body
            headers = case.request_headers
            body_type = case.body_type
            data = Request(url, body=bodys).request(method=method, body_type=body_type, headers=headers, body=bodys)
            Executor().extract_out_params(data, cases)
            params_list = Executor().replace_params(cases)
            actual = JSONPathParser().parse_assert(data, params_list.assert_list)
            message = Executor().my_assert(actual, True)
            return message

    @staticmethod
    def get_el_expression(string: str):
        """获取字符串中的el表达式
        """
        if string is None or not isinstance(string, str):
            return []
        return re.findall(Executor.pattern, string)


if __name__ == '__main__':
    exp = 1.05
    act = "1.05"
    s = eval(f"{exp} == {act}")
    print(s)

import asyncio
import json
import re
import time
from collections import defaultdict
from datetime import datetime
from typing import List, Any


class Executor(object):
    el_exp = r"\$\{(.+?)\}"
    pattern = re.compile(el_exp)
    # 需要替换全局变量的字段
    fields = ['body', 'url', 'request_headers']

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
                status, err = self.ops(item.get('assert_type'), expected, actually)  # 判断预期结果和实际结果是否相等
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
        if assert_type == "contain":
            if act in exp:
                return True, f"预期结果: {exp} 包含 实际结果: {act}【✔】"
            return False, f"预期结果: {exp} 不包含 实际结果: {act}【❌】"
        if assert_type == "not_contain":
            if act not in exp:
                return True, f"预期结果: {exp} 不包含 实际结果: {act}【✔】"
            return False, f"预期结果: {exp} 包含 实际结果: {act}【❌】"
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

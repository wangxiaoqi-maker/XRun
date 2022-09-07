"""
jsonpath parser
"""
import json
from functools import lru_cache
from typing import Any, List

import jsonpath


class CaseParametersException(Exception):
    pass


class JSONPathParser(object):

    def parse(self, source: dict, expression: str = "") -> Any:
        """
        :param source: response
        :param expression: jsonpath
        :return: jsonpath result
        使用jsonpath解析json响应数据，默认返回第一个匹配结果
        """
        source = source.get("response")
        if not source or not expression:
            raise CaseParametersException(f"解析参数失败，响应信息或表达式为空")
        try:
            # data = self.get_object(source)
            results = jsonpath.jsonpath(source, expression)
            if results is False:
                if not source and expression == "$..*":
                    # 说明想要全匹配并且没数据，直接返回data
                    return json.dumps(source, ensure_ascii=False)
                raise CaseParametersException("Jsonpath匹配失败，请检查您的响应或Jsonpath.")
            return results[0]
        except CaseParametersException as e:
            raise e
        except Exception as err:
            raise CaseParametersException(f"解析json数据错误，请检查jsonpath或json: {err}")

    @staticmethod
    def get_object(json_str):
        """
        :param json_str: json string
        :return: json object
        """
        return json.loads(json_str)

    @staticmethod
    def get_dumps(data):
        """
        :param data: json object
        :return: json string
        """
        return json.dumps(data, ensure_ascii=False)

    def parse_assert(self, source: dict, asserts: List):
        """
        :param source: response
        :param asserts: assert list
        :return: assert result
        解析断言表达式
        """
        try:
            asserts = self.get_object(asserts)
        except Exception as e:
            raise CaseParametersException(f"解析断言失败: {e}")
        for ase in asserts:
            if ase.get('assert_obj') == 'response_json':
                ase['actually'] = self.parse(source, ase['actually'])
            elif ase.get('assert_obj') == 'response_text':
                ase['actually'] = self.get_dumps(source.get('response'))
            elif ase.get('assert_obj') == 'response_headers':
                ase['actually'] = self.header_parse(source, ase['actually'])
            elif ase.get('assert_obj') == 'response_cookies':
                ase['actually'] = self.cookie_parse(source, ase['actually'])
            elif ase.get('assert_obj') == 'response_code':
                ase['actually'] = source.get('status_code')
            elif ase.get('assert_obj') == 'request_time':
                ase['actually'] = self.request_time_parse(source)
            else:
                raise CaseParametersException(f"不支持的断言格式: {ase.get('assert_obj')}")
        return asserts

    @staticmethod
    def header_parse(source: dict, key: str = "") -> Any:
        """
        :param source: response
        :param key: response header key
        :return: response header value
        使用key值获取response header value
        """
        source = source.get("response_headers")
        if not source or not key:
            raise CaseParametersException(f"解析参数失败，响应信息或表达式为空")
        try:
            return source.get(key)
        except CaseParametersException as e:
            raise e
        except Exception as err:
            raise CaseParametersException(f"请求头断言获取失败: {err}")

    @staticmethod
    def cookie_parse(source, param):
        """
        :param source: response
        :param param: cookie key
        :return: cookie value
        使用key值获取response cookie value
        """
        source = source.get('cookies')
        if not source or not param:
            raise CaseParametersException(f"解析参数失败，响应信息或表达式为空")
        try:
            return source.get(param)
        except CaseParametersException as e:
            raise e
        except Exception as err:
            raise CaseParametersException(f"cookie断言获取失败: {err}")

    @staticmethod
    def request_time_parse(source):
        """
        :param source: response
        :return: request time
        获取请求时间
        """
        source = source.get('cost')
        if not source:
            raise CaseParametersException(f"解析参数失败，响应信息或表达式为空")
        try:
            if 'ms' in source:
                return source.replace('ms', '')
        except CaseParametersException as e:
            raise e
        except Exception as err:
            raise CaseParametersException(f"请求时间断言获取失败: {err}")


if __name__ == '__main__':
    sources = """{
            "code": 0,
            "data": {
                "id": 1,
                "name": "test",
                "age": 18},
            "msg": "success"
        }"""
    expressions = "$.data.name"
    print(JSONPathParser().parse(sources, expressions))

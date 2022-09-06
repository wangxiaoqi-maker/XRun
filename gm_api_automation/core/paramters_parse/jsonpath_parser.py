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
        return json.loads(json_str)

    def parse_assert(self, source: dict, asserts: List):
        for ase in asserts:
            if ase.get('assert_obj') == 'response_json':
                ase['actually'] = self.parse(source, ase['actually'])
        return asserts


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

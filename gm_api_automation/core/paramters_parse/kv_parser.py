import json
from typing import Any

import jsonpath

from gm_api_automation.core.paramters_parse.jsonpath_parser import CaseParametersException
from gm_api_automation.core.paramters_parse.parser import Parser


class HeaderParser(Parser):

    @staticmethod
    def get_source(data: dict):
        return json.loads(data.get("response_headers"))

    @classmethod
    def parse(cls, source: dict, expression: str = "", idx: str = None) -> Any:
        if not source or not expression:
            raise CaseParametersException(f"parse out parameters failed, source or expression is empty")
        try:
            source = cls.get_source(source)
            results = jsonpath.jsonpath(source, expression)
            if results is False:
                if not source and expression == "$..*":
                    # 说明想要全匹配并且没数据，直接返回data
                    return source
                raise CaseParametersException("jsonpath match failed, please check your response or jsonpath.")
            return Parser.parse_result(results, idx)
        except CaseParametersException as e:
            raise e
        except Exception as err:
            raise CaseParametersException(f"parse json data error, please check jsonpath or json: {err}")


class CookieParser(HeaderParser):
    @staticmethod
    def get_source(data: dict):
        return json.loads(data.get("cookies"))

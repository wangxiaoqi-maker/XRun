import json

from gm_api_automation.core.paramters_parse.parser import Parser


class StatusCodeParser(Parser):
    @staticmethod
    def parse(source: dict, expression: str = "", idx: str = None) -> str:
        return json.dumps(source.get("status_code"))

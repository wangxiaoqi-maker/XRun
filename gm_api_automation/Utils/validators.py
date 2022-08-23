from rest_framework import serializers

from Configs.models import Config
from Interfaces.models import Interfaces
from Projects.models import Projects


class ManualValidateIsExist:
    def __init__(self, kw):
        self.kw = kw

    def __call__(self, value):
        if self.kw == "project":
            if not Projects.objects.filter(id=value).exists():
                raise serializers.ValidationError("项目id不存在")
        elif self.kw == "interface":
            if not Interfaces.objects.filter(id=value).exists():
                raise serializers.ValidationError("接口id不存在")
        elif self.kw == "config":
            if not Config.objects.filter(id=value).exists():
                raise serializers.ValidationError("环境配置id不存在")

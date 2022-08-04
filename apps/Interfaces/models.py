from django.db import models

# Create your models here.
from TestCasesDiretorys.models import TestcaseDirectory
from gm_api_automation.Utils.base_model import BaseModels


class Interfaces(BaseModels):
    name = models.CharField(max_length=20, verbose_name='接口名称', help_text='接口名称', unique=True)
    projects = models.ForeignKey('Projects.Projects', on_delete=models.CASCADE, verbose_name='项目表外键',
                                   help_text='项目表外键', related_name='interfaces', db_constraint=False)
    request_type = models.CharField(max_length=10, verbose_name='请求类型', help_text='请求类型', default='https')
    url = models.CharField(max_length=100, verbose_name='请求url', help_text='请求url', unique=True)
    request_method = models.CharField(max_length=10, verbose_name='请求方式', help_text='请求方式', unique=True)
    request_headers = models.TextField(verbose_name='请求headers', help_text='请求headers', null=True, blank=True,
                                       default='')
    body = models.TextField(verbose_name='请求body', help_text='请求body', null=True, blank=True, default='')
    body_type = models.CharField(max_length=10, verbose_name='请求body类型', help_text='请求body类型', unique=True)
    directory = models.ForeignKey('TestCasesDiretorys.TestcaseDirectory', on_delete=models.CASCADE,
                                  verbose_name='目录表外键', db_constraint=False)
    expected_result = models.TextField(verbose_name='预期结果', help_text='预期结果', null=True, blank=True, default='')
    actual_result = models.TextField(verbose_name='实际结果', help_text='实际结果', null=True, blank=True, default='')
    status = models.CharField(max_length=10, verbose_name='测试结果', help_text='测试结果')
    priority = models.IntegerField(verbose_name='优先级', help_text='优先级')
    case_type = models.CharField(max_length=10, verbose_name='用例类型', help_text='用例类型')
    developer = models.CharField(max_length=10, verbose_name='开发人员', help_text='开发人员')
    tag = models.CharField(max_length=10, verbose_name='标签', help_text='标签')

    class Meta:
        db_table = 'gm_interfaces'
        verbose_name = '接口表'
        verbose_name_plural = '接口表'
        ordering = ['id']

    def __str__(self):
        return f'Interface({self.name})'

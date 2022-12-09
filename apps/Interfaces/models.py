from django.db import models

# Create your models here.
from TestCasesDiretorys.models import TestcaseDirectory
from gm_api_automation.Utils.base_model import BaseModels


class Interfaces(BaseModels):
    host = models.CharField(max_length=100, verbose_name='接口地址', help_text='接口地址', null=True, blank=True, default='')
    name = models.CharField(max_length=50, verbose_name='接口名称', help_text='接口名称')
    request_type = models.CharField(max_length=10, verbose_name='请求类型', help_text='请求类型', default='https')
    url = models.CharField(max_length=100, verbose_name='请求url', help_text='请求url')
    request_method = models.CharField(max_length=10, verbose_name='请求方式', help_text='请求方式', default='POST')
    request_headers = models.TextField(verbose_name='请求headers', help_text='请求headers', null=True, blank=True,
                                       default='')
    body = models.TextField(verbose_name='请求body', help_text='请求body', null=True, blank=True, default='')
    body_type = models.CharField(max_length=10, verbose_name='请求body类型', help_text='请求body类型', default='json')
    directory = models.ForeignKey('TestCasesDiretorys.TestcaseDirectory', on_delete=models.CASCADE,
                                  verbose_name='目录表外键', db_constraint=False, related_name='interfaces')
    # 断言列表
    assert_list = models.TextField(verbose_name='断言列表', help_text='断言列表', null=True, blank=True, default='')
    out_params = models.TextField(verbose_name='出参列表', help_text='出参列表', null=True, blank=True, default='')
    status = models.CharField(max_length=10, verbose_name='测试结果', help_text='测试结果')
    priority = models.CharField(verbose_name='优先级', help_text='优先级', null=True, blank=True, default='', max_length=10)
    case_type = models.CharField(max_length=10, verbose_name='用例类型', help_text='用例类型', null=True, blank=True,
                                 default='')
    response = models.TextField(verbose_name='响应结果', help_text='响应结果', null=True, blank=True, default='')
    project = models.ForeignKey('Projects.Projects', on_delete=models.CASCADE, verbose_name='项目表外键',
                                db_constraint=False, related_name='interfaces')
    developer = models.CharField(max_length=10, verbose_name='开发人员', help_text='开发人员', null=True, blank=True,
                                 default='')
    state = models.CharField(max_length=10, verbose_name='状态', help_text='状态', null=True, blank=True, default='')
    tag = models.CharField(max_length=10, verbose_name='标签', help_text='标签', null=True, blank=True, default='')
    desc = models.TextField(verbose_name='接口描述信息', help_text='接口描述信息', null=True, blank=True, default='')

    class Meta:
        db_table = 'gm_interfaces'
        verbose_name = '接口表'
        verbose_name_plural = '接口表'
        ordering = ['id']

    def __str__(self):
        return f'{self.id}_{self.name}'

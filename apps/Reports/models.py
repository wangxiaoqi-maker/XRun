from django.db import models

# Create your models here.
from gm_api_automation.Utils.base_model import BaseModels


class Reports(BaseModels):
    name = models.CharField(max_length=50, verbose_name='报告名称', help_text='报告名称')
    success_count = models.CharField(verbose_name='成功用例数', max_length=50, help_text='成功用例数', null=True, blank=True)
    failure_count = models.CharField(verbose_name='失败用例数', max_length=50, help_text='失败用例数', null=True, blank=True)
    error_count = models.CharField(verbose_name='错误用例数', max_length=50, help_text='错误用例数', null=True, blank=True)
    skip_count = models.CharField(verbose_name='跳过用例数', max_length=50, help_text='跳过用例数', null=True, blank=True)
    total_count = models.CharField(verbose_name='总用例数', max_length=50, help_text='总用例数', null=True, blank=True)
    report_name = models.TextField(verbose_name='报告名', max_length=1000, null=True, blank=True, help_text='报告名')
    status = models.TextField(verbose_name='状态', null=True, blank=True, help_text='状态')
    project = models.ForeignKey('Projects.Projects', on_delete=models.CASCADE, verbose_name='项目id', null=True,
                                blank=True, help_text='项目id')
    testsuit = models.ForeignKey('TestSuit.TestSuit', on_delete=models.CASCADE, verbose_name='测试套件id', null=True,
                                 blank=True, help_text='测试套件id')
    state = models.CharField(verbose_name='状态', max_length=50, help_text='状态', null=True, blank=True)

    class Meta:
        db_table = 'gm_reports'
        verbose_name = '报告'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

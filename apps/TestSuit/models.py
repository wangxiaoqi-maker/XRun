from django.db import models

# Create your models here.
from gm_api_automation.Utils.base_model import BaseModels


class TestSuit(BaseModels):
    """
    测试套件
    """
    name = models.CharField(verbose_name='套件名称', max_length=200, unique=False, help_text='套件名称')
    project = models.ForeignKey('Projects.Projects', on_delete=models.CASCADE, related_name='testsuit_project',
                                help_text='所属项目', db_constraint=False)
    cron = models.CharField(verbose_name='定时任务', max_length=100, null=True, blank=True, help_text='定时任务')
    priority = models.CharField(verbose_name='优先级', max_length=50, help_text='优先级', default='P0', null=True, blank=True)
    case_list = models.ManyToManyField('Interfaces.Interfaces', related_name='testsuit_interfaces', help_text='用例列表',
                                       db_constraint=False)
    status = models.CharField(verbose_name='执行结果', max_length=500, help_text='执行结果', null=True, blank=True)
    success_count = models.CharField(verbose_name='成功用例数', max_length=50, help_text='成功用例数', null=True, blank=True)
    failure_count = models.CharField(verbose_name='失败用例数', max_length=50, help_text='失败用例数', null=True, blank=True)
    error_count = models.CharField(verbose_name='错误用例数', max_length=50, help_text='错误用例数', null=True, blank=True)
    skip_count = models.CharField(verbose_name='跳过用例数', max_length=50, help_text='跳过用例数', null=True, blank=True)
    total_count = models.CharField(verbose_name='总用例数', max_length=50, help_text='总用例数', null=True, blank=True)
    report_name = models.TextField(verbose_name='报告名', max_length=1000, null=True, blank=True, help_text='报告名')
    state = models.CharField(verbose_name='状态', max_length=50, help_text='状态',
                             default='未完成', blank=True, null=True)  # 默认值是当该字段为空时才会有默认值，如果该字段为空字符串或null，那么默认值就不会生效
    desc = models.TextField(verbose_name='简要描述', help_text='简要描述', blank=True, null=True, default='')

    class Meta:
        db_table = 'gm_testsuits'
        verbose_name = '测试套件'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.name


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
    # case_list = models.ManyToManyField('Interfaces.Interfaces', related_name='testsuit_interfaces', help_text='用例列表',
    #                                    db_constraint=False)
    status = models.TextField(verbose_name='执行结果', null=True, blank=True, help_text='执行结果')
    state = models.CharField(verbose_name='状态', max_length=50, help_text='状态',
                             default='未完成', blank=True, null=True)  # 默认值是当该字段为空时才会有默认值，如果该字段为空字符串或null，那么默认值就不会生效
    run_duration = models.CharField(verbose_name='运行时长', max_length=50, help_text='运行时长', null=True, blank=True)
    desc = models.TextField(verbose_name='简要描述', help_text='简要描述', blank=True, null=True, default='')

    class Meta:
        db_table = 'gm_testsuits'
        verbose_name = '测试套件'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.name


class TestCaseStep(BaseModels):
    """
    测试用例步骤表
    """
    testsuit = models.ForeignKey('TestSuit', on_delete=models.CASCADE, related_name='testsuit_step', help_text='所属套件',
                                 db_constraint=False)
    interface = models.ForeignKey('Interfaces.Interfaces', on_delete=models.CASCADE, related_name='interface_step',
                                  help_text='所属接口', db_constraint=False)
    execution_order = models.CharField(verbose_name='执行顺序', max_length=20, help_text='执行顺序', null=True, blank=True)
    status = models.TextField(verbose_name='执行结果', null=True, blank=True, help_text='执行结果')
    desc = models.TextField(verbose_name='简要描述', help_text='简要描述', blank=True, null=True, default='')

    class Meta:
        db_table = 'gm_testcase_step'
        verbose_name = '测试用例步骤'
        verbose_name_plural = verbose_name
        ordering = ['id']

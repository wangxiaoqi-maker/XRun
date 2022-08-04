from django.db import models

# Create your models here.
from gm_api_automation.Utils.base_model import BaseModels


class TestcaseDirectory(BaseModels):
    name = models.CharField(max_length=50, verbose_name='目录名称', help_text='目录名称')
    projects = models.ForeignKey('Projects.Projects', on_delete=models.CASCADE, verbose_name='项目表外键',
                                 db_constraint=False, related_name='testcase_directory', help_text='项目表外键')
    # 要创建一个递归关系——一个与自己有多对一关系的对象——使用models.ForeignKey('self', on_delete=models.CASCADE)。
    parent = models.ForeignKey('self', on_delete=models.CASCADE, verbose_name='父目录',
                               help_text='父目录', null=True, blank=True, db_constraint=False,
                               related_name='parent_directory')
    desc = models.TextField(verbose_name='目录描述信息', help_text='目录描述信息', null=True, blank=True, default='')

    class Meta:
        # db_table指定创建的数据表名称
        db_table = 'gm_testcases_directory'
        # 为当前数据表设置中文描述信息
        verbose_name = '用例目录表'
        verbose_name_plural = '用例目录表'
        ordering = ['id']

    def __str__(self):
        return f"TestcaseDirectory({self.name})"

from django.db import models

# Create your models here.
from gm_api_automation.Utils.base_model import BaseModels


class Projects(BaseModels):
    name = models.CharField(max_length=50, verbose_name='项目名称', help_text='项目名称', unique=True)  # unique=True 唯一约束
    base_url = models.CharField(max_length=50, verbose_name='项目基础url', help_text='项目基础url', null=True, blank=True)
    owner = models.CharField(max_length=50, verbose_name='项目负责人', help_text='项目负责人')
    app = models.CharField(max_length=50, verbose_name='项目所属应用', help_text='项目所属应用')
    type = models.CharField(max_length=50, verbose_name='项目类型', help_text='项目类型')
    desc = models.TextField(verbose_name='项目描述信息', help_text='项目描述信息', null=True, blank=True, default='')

    class Meta:
        # db_table指定创建的数据表名称
        db_table = 'gm_projects'
        # 为当前数据表设置中文描述信息
        verbose_name = '项目表'
        verbose_name_plural = '项目表'
        ordering = ['id']

    def __str__(self):
        return f"Projects({self.name})"

    def delete(self, using=None, keep_parents=False):
        self.is_delete = True
        self.save()

from django.db import models

# Create your models here.
from gm_api_automation.Utils.base_model import BaseModels


class Config(BaseModels):
    name = models.CharField(max_length=20, verbose_name='配置名称', help_text='配置名称')
    base_url = models.CharField(max_length=100, verbose_name='公共url', help_text='公共url')
    desc = models.TextField(verbose_name='配置描述信息', help_text='配置描述信息', null=True, blank=True, default='')

    class Meta:
        db_table = 'gm_config'
        verbose_name = '配置表'
        verbose_name_plural = '配置表'
        ordering = ['id']

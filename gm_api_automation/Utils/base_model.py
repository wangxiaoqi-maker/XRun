from django.db import models


class BaseModels(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='主键id', help_text='主键id')
    created_time = models.DateTimeField(verbose_name='创建时间', help_text='创建时间', auto_now_add=True)
    updated_time = models.DateTimeField(verbose_name='更新时间', help_text='更新时间', auto_now=True)
    create_user = models.CharField(max_length=50, verbose_name='创建人', help_text='创建人')
    update_user = models.CharField(max_length=50, verbose_name='更新人', help_text='更新人')
    deleted_time = models.DateTimeField(verbose_name='删除时间', help_text='删除时间', null=True, blank=True)
    version = models.IntegerField(verbose_name='版本号', help_text='版本号', default="1.0.1", unique=True)
    is_delete = models.BooleanField(verbose_name='是否删除', help_text='是否删除', default=False)

    class Meta:
        abstract = True  # 抽象模型类

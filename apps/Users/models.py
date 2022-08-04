from django.db import models


# Create your models here.

# class Users(models.Model):
#     id = models.AutoField(primary_key=True)
#     user_name = models.CharField(max_length=50, verbose_name='用户名称', help_text='用户名称', unique=True)
#     password = models.CharField(max_length=50, verbose_name='用户密码', help_text='用户密码', unique=True)
#     email = models.CharField(max_length=50, verbose_name='用户邮箱', help_text='用户邮箱')
#     phone = models.CharField(max_length=50, verbose_name='用户手机号', help_text='用户手机号')
#     role = models.ForeignKey('ProjectRoles.Roles', on_delete=models.CASCADE, verbose_name='角色表外键', help_text='角色表外键',
#                              db_constraint=False)
#     created_time = models.DateTimeField(verbose_name='创建时间', help_text='创建时间', auto_now_add=True)
#     updated_time = models.DateTimeField(verbose_name='更新时间', help_text='更新时间', auto_now=True)
#     updated_user = models.CharField(max_length=50, verbose_name='更新人', help_text='更新人')
#     last_login_time = models.DateTimeField(verbose_name='最后登录时间', help_text='最后登录时间', null=True, blank=True)
#     delete_time = models.DateTimeField(verbose_name='删除时间', help_text='删除时间', null=True, blank=True)
#
#     class Meta:
#         # db_table指定创建的数据表名称
#         db_table = 'gm_users'
#         # 为当前数据表设置中文描述信息
#         verbose_name = '用户表'
#         verbose_name_plural = '用户表'
#         ordering = ['id']
#
#     def __str__(self):
#         return f"Projects({self.user_name})"

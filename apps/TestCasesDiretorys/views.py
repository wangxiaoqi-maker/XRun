import datetime

from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, mixins, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from TestCasesDiretorys.models import TestcaseDirectory
from TestCasesDiretorys.serializers import TestCaseDirectorySerializer


class TestCasesDirectorysView(ModelViewSet):
    queryset = TestcaseDirectory.objects.all()
    serializer_class = TestCaseDirectorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['=name', '=projects', '=id']
    ordering_fields = ['id', 'name', 'projects']

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return response

    def get_queryset(self):
        """
        过滤已删除的项目
        :return:
        """
        if self.request.user.is_superuser:
            return self.queryset.filter(is_delete=False)
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        关联父目录
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        # 判断当parent_directory字段为空时，不用对序列化器进行校验
        super().create(request, *args, **kwargs)
        return Response({'code': 00, 'msg': '目录创建成功', 'success': True})

    def update(self, request, *args, **kwargs):
        """
        更新目录
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        super().update(request, *args, **kwargs)
        return Response({'code': 00, 'msg': '目录更新成功', 'success': True})

    def destroy(self, request, *args, **kwargs):
        # 将物理删除改成逻辑删除
        instance = self.get_object()
        instance.is_delete = True
        instance.deleted_time = datetime.datetime.now()
        instance.update_user = self.request.user.username
        instance.save()
        return Response({'code': 00, 'msg': '目录删除成功', 'success': True})

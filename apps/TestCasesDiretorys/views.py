import datetime

from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, mixins, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from Projects.models import Projects
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
        # 判断项目是否存在
        if request.data.get('projects') is None:
            return Response({'message': '项目id不能为空', 'success': False})
        project = Projects.objects.filter(id=request.data.get('projects')).first()
        if not project:
            return Response({'message': '项目不存在', 'success': False})
        super().create(request, *args, **kwargs)
        return Response({'message': '目录创建成功', 'success': True})

    def update(self, request, *args, **kwargs):
        """
        使用body传参的方式更新测试用例目录，不使用pk值
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if request.data.get('id') is None:
            return Response({'message': '目录id不能为空', 'success': False})
        instance = self.get_queryset().filter(id=request.data.get('id')).first()
        if not instance:
            return Response({'message': '目录不存在', 'success': False})
        # 校验父目录是否存在
        if request.data.get('parent') is not None:
            parent = TestcaseDirectory.objects.filter(id=request.data.get('parent')).first()
            if not parent:
                return Response({'message': '父目录不存在', 'success': False})

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        # 返回更新后的目录信息
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        # 将物理删除改成逻辑删除
        instance = self.get_object()
        instance.is_delete = True
        instance.deleted_time = datetime.datetime.now()
        instance.update_user = self.request.user.username
        instance.save()
        return Response({'message': '目录删除成功', 'success': True})

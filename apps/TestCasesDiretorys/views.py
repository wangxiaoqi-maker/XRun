import datetime

from django.db import IntegrityError
from django.shortcuts import render

# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from Interfaces.models import Interfaces
from Projects.models import Projects
from TestCasesDiretorys.models import TestcaseDirectory
from TestCasesDiretorys.serializers import TestCaseDirectorySerializer
from gm_api_automation.Utils.page_number_pagination import PageNumberPagination


class TestCasesDirectorysView(ModelViewSet):
    queryset = TestcaseDirectory.objects.all()
    serializer_class = TestCaseDirectorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'id', 'projects']
    ordering_fields = ['id', 'name', 'owner']

    def list(self, request, *args, **kwargs):
        # 查询项目下的所有目录
        if request.query_params.get('projects') is not None:
            project = Projects.objects.filter(id=request.query_params.get('projects')).first()
            if not project:
                return Response({'message': '项目不存在', 'success': False})
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
        try:
            super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response({'message': '目录名称重复', 'success': False})
        return Response({'message': '目录创建成功', 'success': True})

    def update(self, request, *args, **kwargs):
        """
        使用body传参的方式更新测试用例目录，不使用pk值
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if request.data.get('id') is None or request.data.get('id') == '':
            return Response({'message': '目录id不能为空', 'success': False})
        instance = self.get_queryset().filter(id=request.data.get('id')).first()
        if not instance:
            return Response({'message': '目录不存在', 'success': False})
        # 校验父目录是否存在
        parent_id = request.data.get('parent')
        if parent_id is not None and parent_id != "":
            parent = TestcaseDirectory.objects.filter(parent_id=request.data.get('parent')).first()
            if not parent:
                return Response({'message': '父目录不存在', 'success': False})
        try:
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
        except IntegrityError:
            return Response({'message': '目录名称重复', 'success': False})
        # 返回更新后的目录信息
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        # 将物理删除改成逻辑删除,使用body传参的方式更新测试用例目录，不使用pk值
        if request.data.get('id') is None and request.data.get('id') == '':
            return Response({'message': '目录id不能为空', 'success': False})
        instance = self.get_queryset().filter(id=request.data.get('id')).first()
        if not instance:
            return Response({'message': '目录不存在', 'success': False})
        self.perform_destroy(instance)
        return Response({'message': '目录删除成功', 'success': True})

    def perform_destroy(self, instance):
        instance.is_delete = True
        instance.deleted_time = datetime.datetime.now()
        instance.update_user = self.request.user.username
        instance.save()
        Interfaces.objects.filter(directory=instance.id).update(is_delete=True, deleted_time=datetime.datetime.now(),
                                                                update_user=self.request.user.username)

    def retrieve(self, request, *args, **kwargs):
        """
        查询单个目录下的接口信息，使用body传参的方式，不使用pk值
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if request.query_params.get('id') is None and request.query_params.get('id') == "":
            return Response({'message': '目录id不能为空', 'success': False})
        instance = self.get_queryset().filter(id=request.query_params.get('id')).first()
        if not instance:
            return Response({'message': '目录不存在', 'success': False})
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

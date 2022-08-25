from datetime import datetime

from django.db import IntegrityError
from django.db.models import Model
from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, mixins, filters, generics
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, ListAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from Interfaces.models import Interfaces
from Projects import serializers
from Projects.models import Projects
from Projects.serializers import ProjectSerializers
from TestCasesDiretorys.models import TestcaseDirectory
from gm_api_automation.Utils.custom_json_response import JsonResponse
from gm_api_automation.Utils.page_number_pagination import PageNumberPagination

from gm_api_automation.Utils.public_response_information import StatusCodeEnum


# 创建项目的视图
class CreateProjectView(CreateAPIView):
    queryset = Projects.objects.all()
    serializer_class = ProjectSerializers
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # 校验当该项目被逻辑删除时，创建项目不需要校验唯一性
        try:
            super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response({'message': '项目已存在', 'success': False})
        return Response({'message': StatusCodeEnum.Project_Create_Success.message,
                         'success': StatusCodeEnum.Project_Create_Success.is_success})


class GetProjectView(ListAPIView):
    queryset = Projects.objects.all()
    serializer_class = ProjectSerializers
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'owner', 'id']
    ordering_fields = ['id', 'name', 'owner']

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


class UpdateProjectView(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Projects.objects.all()
    serializer_class = ProjectSerializers
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        """
        使用body传参的方式更新项目信息，不使用pk
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if request.data.get('id') is None or request.data.get('id') == "":
            return Response({'message': '项目id不能为空', 'success': False})
        instance = self.get_queryset().filter(id=request.data.get('id'), is_delete=False).first()
        if not instance:
            return Response({'message': '项目不存在', 'success': False})
        try:
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
        except IntegrityError:
            return Response({'message': '项目已存在', 'success': False})
        # 返回更新后的项目信息
        return Response(serializer.data)


class DeleteProjectView(mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = Projects.objects.all()
    serializer_class = ProjectSerializers
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        """
        使用body传参的方式删除数据，不使用pk值
        """
        if request.data.get('id') is None and request.data.get('id') == "":
            return Response({'message': '项目id不能为空', 'success': False})
        instance = self.get_queryset().filter(id=request.data.get('id'), is_delete=False).first()
        if not instance:
            return Response({'message': '项目不存在', 'success': False})
        self.perform_destroy(instance)
        return Response({'message': StatusCodeEnum.Project_Delete_Success.message,
                         'success': StatusCodeEnum.Project_Delete_Success.is_success})

    def perform_destroy(self, instance):
        """
        将物理删除改为逻辑删除,
        """
        instance.is_delete = True
        instance.deleted_time = datetime.now()
        instance.update_user = self.request.user.username
        instance.save()
        # 逻辑删除该项目下的所有目录
        TestcaseDirectory.objects.filter(projects_id=instance.id).update(is_delete=True, deleted_time=datetime.now(),
                                                                         update_user=self.request.user.username)
        # 通过项目id查询所有的目录，将目录下的接口删除
        directories = TestcaseDirectory.objects.filter(projects_id=instance.id)
        for directory in directories:
            Interfaces.objects.filter(directory_id=directory.id).update(is_delete=True, deleted_time=datetime.now(),
                                                                        update_user=self.request.user.username)


class GetProjectDetailView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Projects.objects.all()
    serializer_class = ProjectSerializers
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        """
        通过param传参方式获取项目的详情
        """
        if request.query_params.get('id') is None and request.query_params.get('id') == "":
            return Response({'message': '项目id不能为空', 'success': False})
        instance = self.get_queryset().filter(id=request.query_params.get('id'), is_delete=False).first()
        if not instance:
            return Response({'message': '项目不存在', 'success': False})
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        """
        过滤已删除的项目
        :return:
        """
        if self.request.user.is_superuser:
            return self.queryset.filter(is_delete=False)
        return self.queryset.filter(owner=self.request.user)

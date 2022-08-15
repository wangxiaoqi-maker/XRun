from datetime import datetime

from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, mixins, filters, generics
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, ListAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from Projects import serializers
from Projects.models import Projects
from Projects.serializers import ProjectSerializers
from TestCasesDiretorys.models import TestcaseDirectory
from gm_api_automation.Utils.custom_json_response import JsonResponse
from gm_api_automation.Utils.page_number_pagination import PageNumberPagination


# 创建项目的视图
class CreateProjectView(CreateAPIView):
    queryset = Projects.objects.all()
    serializer_class = ProjectSerializers
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response({'message': '项目创建成功', 'success': True})


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
        if request.data.get('id') is None:
            return Response({'message': '项目id不能为空', 'success': False})
        instance = self.get_queryset().filter(id=request.data.get('id')).first()
        if not instance:
            return Response({'message': '项目不存在', 'success': False})
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'message': '项目更新成功', 'success': True})


class DeleteProjectView(mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = Projects.objects.all()
    serializer_class = ProjectSerializers
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({'message': '项目删除成功', 'success': True})

    def perform_destroy(self, instance):
        """
        将物理删除改为逻辑删除
        """
        instance.deleted_time = datetime.now()
        instance.update_user = self.request.user.username
        instance.save()
        super().perform_destroy(instance)
        # 逻辑删除该项目下的所有目录
        TestcaseDirectory.objects.filter(projects_id=instance.id).update(is_delete=True, deleted_time=datetime.now(),
                                                                         update_user=self.request.user.username)


class GetProjectDetailView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Projects.objects.all()
    serializer_class = ProjectSerializers
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        # 判断当获取的项目是否存在
        instance = self.get_queryset().filter(id=kwargs.get('pk')).first()
        if not instance:
            return Response({'message': '项目不存在', 'success': False})
        response = super().retrieve(request, *args, **kwargs)
        return response

    def get_queryset(self):
        """
        过滤已删除的项目
        :return:
        """
        if self.request.user.is_superuser:
            return self.queryset.filter(is_delete=False)
        return self.queryset.filter(owner=self.request.user)

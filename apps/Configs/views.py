from datetime import datetime

from django.db import IntegrityError
from django.shortcuts import render


# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from Configs.models import Config
from Configs.serializers import ConfigSerializer
from gm_api_automation.Utils.page_number_pagination import PageNumberPagination


class ConfigsView(ModelViewSet):
    queryset = Config.objects.all()
    serializer_class = ConfigSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'id']

    def list(self, request, *args, **kwargs):
        # 查询所有的配置信息
        response = super().list(request, *args, **kwargs)
        return response

    def get_queryset(self):
        """
        过滤已删除的配置信息
        :return:
        """
        if self.request.user.is_superuser:
            return self.queryset.filter(is_delete=False)
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        创建配置信息
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        super().create(request, *args, **kwargs)
        return Response({'message': '配置创建成功', 'success': True})

    def update(self, request, *args, **kwargs):
        """
        使用body传参的方式更新数据，不使用pk值
        """
        if request.data.get('id') is None or request.data.get('id') == '':
            return Response({'message': '配置信息id不能为空', 'success': False})
        instance = self.filter_queryset(self.get_queryset()).filter(id=request.data.get("id")).first()
        if not instance:
            return Response({'message': '配置信息不存在', 'success': False})
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        删除配置信息
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if request.data.get('id') is None and request.data.get('id') == '':
            return Response({'message': '配置信息id不能为空', 'success': False})
        instance = self.filter_queryset(self.get_queryset()).filter(id=request.data.get("id")).first()
        if not instance:
            return Response({'message': '配置信息不存在', 'success': False})
        self.perform_destroy(instance)
        return Response({'message': '配置信息删除成功', 'success': True})

    def perform_destroy(self, instance):
        """
        物理删除改为逻辑删除
        """
        instance.is_delete = True
        instance.deleted_time = datetime.now()
        instance.update_user = self.request.user.username
        instance.save()

    def retrieve(self, request, *args, **kwargs):
        """
        通过param传参的方式查询配置信息
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if request.query_params.get('id') is None and request.query_params.get('id') == '':
            return Response({'message': '配置信息id不能为空', 'success': False})
        instance = self.filter_queryset(self.get_queryset()).filter(id=request.query_params.get("id")).first()
        if not instance:
            return Response({'message': '配置信息不存在', 'success': False})
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

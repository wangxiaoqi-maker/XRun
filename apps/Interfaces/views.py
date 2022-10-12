from datetime import datetime

from django.db import IntegrityError
from django.shortcuts import render

# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from Interfaces.models import Interfaces
from Interfaces.serializers import InterfaceSeralizers
from Projects.models import Projects
from gm_api_automation.Utils.page_number_pagination import PageNumberPagination


class InterfacesView(ModelViewSet):
    queryset = Interfaces.objects.all()
    serializer_class = InterfaceSeralizers
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'id', 'directory_id']

    def list(self, request, *args, **kwargs):
        # 查询所有的接口信息，也可通过查询参数进行过滤
        response = super().list(request, *args, **kwargs)
        return response

    def get_queryset(self):
        """
        过滤已删除的接口
        :return:
        """
        if self.request.user.is_superuser:
            return self.queryset.filter(is_delete=False)
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        创建接口
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        super().create(request, *args, **kwargs)
        return Response({'message': '接口创建成功', 'success': True})

    def update(self, request, *args, **kwargs):
        """
        使用body传参的方式更新数据，不使用pk值
        """
        if request.data.get('id') is None or request.data.get('id') == '':
            return Response({'message': '接口id不能为空', 'success': False})
        instance = self.filter_queryset(self.get_queryset()).filter(id=request.data.get("id")).first()
        if not instance:
            return Response({'message': '接口不存在', 'success': False})
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'message': '接口更新成功', 'success': True})

    def destroy(self, request, *args, **kwargs):
        """
        删除接口
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if request.data.get('id') is None and request.data.get('id') == '':
            return Response({'message': '接口id不能为空', 'success': False})
        instance = self.filter_queryset(self.get_queryset()).filter(id=request.data.get("id")).first()
        if not instance:
            return Response({'message': '接口不存在', 'success': False})
        self.perform_destroy(instance)
        return Response({'message': '接口删除成功', 'success': True})

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
        通过param传参的方式查询接口信息
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if request.query_params.get('id') is None and request.query_params.get('id') == '':
            return Response({'message': '接口id不能为空', 'success': False})
        instance = self.filter_queryset(self.get_queryset()).filter(id=request.query_params.get("id")).first()
        if not instance:
            return Response({'message': '接口不存在', 'success': False})
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def interface_total(self, request, *args, **kwargs):
        """
        统计接口的日增、往期、总数
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        total = self.queryset.filter(is_delete=False).count()
        before_today_total = self.queryset.filter(is_delete=False, created_time__lt=datetime.now().date()).count()
        today = datetime.now().date()
        today_total = self.queryset.filter(created_time__contains=today, is_delete=False).count()
        return Response({'total': total, 'previous': before_today_total, 'today_total': today_total, 'success': True})

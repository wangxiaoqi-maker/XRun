import datetime

from django.shortcuts import render

# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from Reports.models import Reports
from Reports.serializers import ReportSerializer
from gm_api_automation.Utils.page_number_pagination import PageNumberPagination


class ReportsView(ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    queryset = Reports.objects.all()
    serializer_class = ReportSerializer
    filterset_fields = ('name', 'created_time', 'state', 'updated_time', "project", 'id')

    def list(self, request, *args, **kwargs):
        # 通过时间筛选报告列表
        if request.query_params.get('start_time') and request.query_params.get('end_time'):
            start_time = request.query_params.get('start_time')
            end_time = request.query_params.get('end_time')
            queryset = self.filter_queryset(self.get_queryset()).filter(
                created_time__gte=start_time, created_time__lte=end_time)
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        """
        过滤已删除的测试套件
        :return:
        """
        if self.request.user.is_superuser:
            return self.queryset.filter(is_delete=False)
        return self.queryset.filter(user=self.request.user, is_delete=False)

    def create(self, request, *args, **kwargs):
        """
        创建报告
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        super().create(request, *args, **kwargs)
        return Response({'message': '测试报告创建成功', 'success': True})

    def update(self, request, *args, **kwargs):
        """
        使用body传参的方式更新数据，不使用pk值
        """
        if request.data.get('id') is None or request.data.get('id') == '':
            return Response({'message': '报告id不能为空', 'success': False})
        instance = self.filter_queryset(self.get_queryset()).filter(id=request.data.get("id")).first()
        if not instance:
            return Response({'message': '测试报告不存在', 'success': False})
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        删除测试套件
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        instance = self.filter_queryset(self.get_queryset()).filter(id=request.data.get('id'), is_delete=False).first()
        if not instance:
            return Response({'message': '测试报告不存在', 'success': False})
        instance.is_delete = True
        instance.deleted_time = datetime.datetime.now()
        instance.update_user = request.user.username
        instance.save()
        return Response({'message': '测试报告删除成功', 'success': True})

    def retrieve(self, request, *args, **kwargs):
        """
        获取报告详情
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        instance = self.filter_queryset(self.get_queryset()).filter(id=request.GET.get('id')).first()
        if not instance:
            return Response({'message': '测试报告不存在', 'success': False})
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

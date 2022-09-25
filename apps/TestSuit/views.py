from django.shortcuts import render


# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from TestSuit.models import TestSuit
from TestSuit.serializers import TestSuitSerializer
from gm_api_automation.Utils.page_number_pagination import PageNumberPagination


class TestSuitView(ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    queryset = TestSuit.objects.all()
    serializer_class = TestSuitSerializer
    filterset_fields = ('name', 'project', 'priority', 'env', 'state')

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return response

    def get_queryset(self):
        """
        过滤已删除的测试套件
        :return:
        """
        if self.request.user.is_superuser:
            return self.queryset.filter(is_delete=False)
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        创建测试套件
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        super().create(request, *args, **kwargs)
        return Response({'message': '测试套件创建成功', 'success': True})

    def update(self, request, *args, **kwargs):
        """
        使用body传参的方式更新数据，不使用pk值
        """
        if request.data.get('id') is None or request.data.get('id') == '':
            return Response({'message': '测试套件id不能为空', 'success': False})
        instance = self.filter_queryset(self.get_queryset()).filter(id=request.data.get("id")).first()
        if not instance:
            return Response({'message': '测试套件不存在', 'success': False})
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
        instance = self.filter_queryset(self.get_queryset()).filter(id=kwargs.get("pk")).first()
        if not instance:
            return Response({'message': '测试套件不存在', 'success': False})
        instance.is_delete = True
        instance.save()
        return Response({'message': '测试套件删除成功', 'success': True})

    def names(self, request, *args, **kwargs):
        """
        返回所有测试套件名称
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        返回测试套件（单个）详情数据
        """
        instance = self.filter_queryset(self.get_queryset()).filter(id=request.GET.get('id')).first()
        if not instance:
            return Response({'message': '测试套件不存在', 'success': False})
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

import datetime

from django.db.models import Count, Q, Sum
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

    def get_weekly_test_case_result_trend(self, request, *args, **kwargs):
        """
        获取某项目最近一周每天的测试套件运行结果，按照日期分组
        """
        project_id = request.query_params.get('project_id')
        # 获取最近一周的日期
        today = datetime.datetime.now().date()
        week_ago = today - datetime.timedelta(days=7)
        # 获取最近一周每天的测试套件运行结果
        case_weekly_result = self.queryset.filter(is_delete=False, project=project_id,
                                                  created_time__range=(week_ago, today)).values(
            'created_time__date').annotate(pass_count=Sum('success_count'), fail_count=Sum('failure_count'),
                                           error_count=Sum('error_count'), skip_count=Sum('skip_count')).order_by(
            "created_time__date")
        # 某个日期没有测试套件运行结果时，返回0
        date_list = []
        for i in range(7):
            date_list.append((today - datetime.timedelta(days=i + 1)).strftime('%Y-%m-%d'))
        case_weekly_result_dict = {}
        for item in case_weekly_result:
            case_weekly_result_dict[item['created_time__date'].strftime('%Y-%m-%d')] = {
                'pass_count': item['pass_count'],
                'fail_count': item['fail_count'],
                'error_count': item['error_count'],
                'skip_count': item['skip_count']}
        for date in date_list:
            if date not in case_weekly_result_dict.keys():
                case_weekly_result_dict[date] = {'pass_count': 0, 'fail_count': 0, 'error_count': 0, 'skip_count': 0}
        return Response({
            'success': True,
            'result': case_weekly_result_dict
        })

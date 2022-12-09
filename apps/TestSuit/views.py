from datetime import datetime, timedelta

from django.db.models import Count
from django.shortcuts import render

# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from Interfaces.models import Interfaces
from TestSuit.models import TestSuit, TestCaseStep
from TestSuit.serializers import TestSuitSerializer, TestCaseStepSerializer
from gm_api_automation.Utils.page_number_pagination import PageNumberPagination


class TestSuitView(ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    queryset = TestSuit.objects.all()
    serializer_class = TestSuitSerializer
    filterset_fields = ('id', 'name', 'project', 'priority', 'state', 'updated_time')

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return response

    def get_queryset(self):
        """
        过滤已删除的测试套件
        :return:
        """
        # start_time = self.request.query_params.get('start_time')
        # end_time = self.request.query_params.get('end_time')
        # if start_time and end_time:
        #     return self.queryset.filter(is_delete=False, updated_time__range=(start_time, end_time))
        # return self.queryset.filter(is_delete=False)
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
        instance = self.filter_queryset(self.get_queryset()).filter(id=request.data.get('id'), is_delete=False).first()
        if not instance:
            return Response({'message': '测试套件不存在', 'success': False})
        instance.is_delete = True
        instance.deleted_time = datetime.now()
        instance.save()
        return Response({'message': '测试套件删除成功', 'success': True})

    def reports(self, request, *args, **kwargs):
        """
        返回所有测试套件名称
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        response = super().list(request, *args, **kwargs)
        return response

    def retrieve(self, request, *args, **kwargs):
        """
        返回测试套件（单个）详情数据
        """
        instance = self.filter_queryset(self.get_queryset()).filter(id=request.GET.get('id')).first()
        if not instance:
            return Response({'message': '测试套件不存在', 'success': False})
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_case_total(self, request, *args, **kwargs):
        """
        获取所有套件的总数，并按照项目分组
        """
        project_id = request.query_params.get('project_id')
        total = self.queryset.filter(is_delete=False, project=project_id).count()
        before_today_total = self.queryset.filter(is_delete=False, project=project_id,
                                                  created_time__lt=datetime.now().date()).count()
        today = datetime.now().date()
        today_total = self.queryset.filter(created_time__contains=today, project=project_id, is_delete=False).count()
        return Response({'total': total, 'previous': before_today_total, 'today_total': today_total, 'success': True})

    def get_case_run_time(self, request, *args, **kwargs):
        """
        获取某项目所有套件的运行时间，按照<1min, 1-5min, 5-10min, 10-30min, 30-60min, >60min分组
        """
        project_id = request.query_params.get('project_id')
        # 小于1分钟总数
        less_than_one_min = self.queryset.filter(is_delete=False, project=project_id, run_duration__lt=60).count()
        # 1-5分钟总数
        one_to_five_min = self.queryset.filter(is_delete=False, project=project_id, run_duration__gte=60,
                                               run_duration__lt=300).count()
        # 5-10分钟总数
        five_to_ten_min = self.queryset.filter(is_delete=False, project=project_id, run_duration__gte=300,
                                               run_duration__lt=600).count()
        # 大于10分钟总数
        more_than_ten_min = self.queryset.filter(is_delete=False, project=project_id, run_duration__gte=600).count()
        return Response({'less_than_one_min': less_than_one_min, 'one_to_five_min': one_to_five_min,
                         'five_to_ten_min': five_to_ten_min, 'more_than_ten_min': more_than_ten_min,
                         'success': True})

    def get_weekly_new_api_and_case_trend(self, request, *args, **kwargs):
        """
        获取某项目最近一周每天新增的接口和套件总数，按照日期分组
        """
        project_id = request.query_params.get('project_id')
        # 获取最近一周的日期
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        # 获取最近一周每天新增的接口总数
        api_weekly_new = Interfaces.objects.filter(is_delete=False, project=project_id,
                                                   created_time__range=(week_ago, today)).values(
            'created_time').annotate(
            count=Count('id'))
        # 获取最近一周每天新增的套件总数
        case_weekly_new = self.queryset.filter(is_delete=False, project=project_id,
                                               created_time__range=(week_ago, today)).values('created_time').annotate(
            count=Count('id'))
        # 某个日期没有新增接口或套件时，返回0
        date_list = []
        for i in range(7):
            date_list.append((today - timedelta(days=i+1)).strftime('%Y-%m-%d'))
        api_weekly_new_dict = {}
        for item in api_weekly_new:
            api_weekly_new_dict[item['created_time'].strftime('%Y-%m-%d')] = item['count']
        # 如果api_weekly_new_dict的key不在date_list中，说明当天没有新增接口，赋值为0，按照字典格式降序排列
        for date in date_list:
            if date not in api_weekly_new_dict:
                api_weekly_new_dict[date] = 0
        api_weekly_new_dicts = dict(sorted(api_weekly_new_dict.items(), key=lambda x: x[0], reverse=True))

        case_weekly_new_dict = {}
        for item in case_weekly_new:
            case_weekly_new_dict[item['created_time'].strftime('%Y-%m-%d')] = item['count']
        # 如果case_weekly_new_dict的key不在date_list中，说明当天没有新增套件，赋值为0，按照字典格式降序排列
        for date in date_list:
            if date not in case_weekly_new_dict:
                case_weekly_new_dict[date] = 0
        case_weekly_new_dicts = dict(sorted(case_weekly_new_dict.items(), key=lambda x: x[0], reverse=True))
        return Response(
            {'api_weekly_new': api_weekly_new_dicts, 'case_weekly_new': case_weekly_new_dicts, 'success': True})


class TestCaseStepView(ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    queryset = TestCaseStep.objects.all()
    serializer_class = TestCaseStepSerializer
    filterset_fields = ('id', 'testsuit', 'interface')

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
        return self.queryset.filter(user=self.request.user, is_delete=False)

    def create(self, request, *args, **kwargs):
        """
        创建测试套件
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        super().create(request, *args, **kwargs)
        return Response({'message': '添加步骤成功', 'success': True})

    def update(self, request, *args, **kwargs):
        """
        使用body传参的方式更新数据，不使用pk值
        """
        if request.data.get('id') is None or request.data.get('id') == '':
            return Response({'message': '测试步骤id不能为空', 'success': False})
        instance = self.filter_queryset(self.get_queryset()).filter(id=request.data.get("id")).first()
        if not instance:
            return Response({'message': '测试步骤不存在', 'success': False})
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
            return Response({'message': '测试步骤不存在', 'success': False})
        instance.is_delete = True
        instance.deleted_time = datetime.now()
        instance.save()
        return Response({'message': '测试步骤删除成功', 'success': True})

from django.urls import path, include
from rest_framework import routers

from Reports import views

urlpatterns = [
    path('CreateReport', views.ReportsView.as_view({'post': 'create'})),
    path('UpdateReport', views.ReportsView.as_view({'post': 'update'})),
    path('DelReport', views.ReportsView.as_view({'post': 'destroy'})),
    path('GetReportList', views.ReportsView.as_view({'get': 'list'})),
    path('GetReportDetail', views.ReportsView.as_view({'get': 'retrieve'})),
    path('getWeeklyTestCaseResultTrend', views.ReportsView.as_view({'get': 'get_weekly_test_case_result_trend'})),
]

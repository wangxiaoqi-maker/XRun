from django.urls import path, include
from rest_framework import routers

from TestSuit import views

urlpatterns = [
    path('createrTestSuits', views.TestSuitView.as_view({'post': 'create'})),
    path('getTestSuits', views.TestSuitView.as_view({'get': 'list'})),
    path('getTestSuitsDetail', views.TestSuitView.as_view({'get': 'retrieve'})),
    path('updateTestSuits', views.TestSuitView.as_view({'post': 'update'})),
    path('delTestSuits', views.TestSuitView.as_view({'post': 'destroy'})),
    path('getReports', views.TestSuitView.as_view({'get': 'reports'})),
    path('getCaseTotal', views.TestSuitView.as_view({'get': 'get_case_total'})),
    path('createrTestCaseStep', views.TestCaseStepView.as_view({'post': 'create'})),
    path('getTestCaseStep', views.TestCaseStepView.as_view({'get': 'list'})),
    path('getTestCaseStepDetail', views.TestCaseStepView.as_view({'get': 'retrieve'})),
    path('updateTestCaseStep', views.TestCaseStepView.as_view({'post': 'update'})),
    path('delTestCaseStep', views.TestCaseStepView.as_view({'post': 'destroy'})),
]

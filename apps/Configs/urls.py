from django.urls import path, include
from rest_framework import routers

from Configs import views

urlpatterns = [
    path('createrCofigs', views.ConfigsView.as_view({'post': 'create'})),
    path('getConfigs', views.ConfigsView.as_view({'get': 'list'})),
    path('getConfigsDetail', views.ConfigsView.as_view({'get': 'retrieve'})),
    path('updateConfigs', views.ConfigsView.as_view({'post': 'update'})),
    path('delConfigs', views.ConfigsView.as_view({'post': 'destroy'})),

]

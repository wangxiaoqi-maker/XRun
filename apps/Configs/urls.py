from django.urls import path, include
from rest_framework import routers

from Configs import views

urlpatterns = [
    path('createrHosts', views.ConfigsView.as_view({'post': 'create'})),
    path('getHosts', views.ConfigsView.as_view({'get': 'list'})),
    path('getHostsDetail', views.ConfigsView.as_view({'get': 'retrieve'})),
    path('updateHosts', views.ConfigsView.as_view({'post': 'update'})),
    path('delHosts', views.ConfigsView.as_view({'post': 'destroy'})),

]

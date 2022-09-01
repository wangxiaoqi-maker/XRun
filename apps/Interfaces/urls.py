from django.urls import path, include
from rest_framework import routers

from Interfaces import views

urlpatterns = [
    path('createrApi', views.InterfacesView.as_view({'post': 'create'})),
    path('getApi', views.InterfacesView.as_view({'get': 'list'})),
    path('getApiDetail', views.InterfacesView.as_view({'get': 'retrieve'})),
    path('updateApi', views.InterfacesView.as_view({'post': 'update'})),
    path('delApi', views.InterfacesView.as_view({'post': 'destroy'})),

]

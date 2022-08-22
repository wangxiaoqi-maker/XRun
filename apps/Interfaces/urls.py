from django.urls import path, include
from rest_framework import routers

from Interfaces import views

# router = routers.SimpleRouter()
# router.register('', views.CreateProjectView)
urlpatterns = [
    path('createrInterfaces', views.InterfacesView.as_view({'post': 'create'})),
    path('getInterfaces', views.InterfacesView.as_view({'get': 'list'})),
    path('getInterfacesDetail', views.InterfacesView.as_view({'get': 'retrieve'})),
    path('updateInterfaces', views.InterfacesView.as_view({'post': 'update'})),
    path('delInterfaces', views.InterfacesView.as_view({'post': 'destroy'})),

]

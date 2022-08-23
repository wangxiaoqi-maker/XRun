from django.urls import path, include
from rest_framework import routers

from Projects import views

urlpatterns = [
    path('createrProject', views.CreateProjectView.as_view()),
    path('getProject', views.GetProjectView.as_view()),
    path('updateProject', views.UpdateProjectView.as_view({"post": "update"})),
    path('delProject', views.DeleteProjectView.as_view({"post": "destroy"})),
    path('getProjectDetail', views.GetProjectDetailView.as_view({'get': 'retrieve'})),
]

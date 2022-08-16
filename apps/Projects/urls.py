from django.urls import path, include
from rest_framework import routers

from Projects import views

# router = routers.SimpleRouter()
# router.register('', views.CreateProjectView)
urlpatterns = [
    path('createrProject', views.CreateProjectView.as_view()),
    path('getProject', views.GetProjectView.as_view()),
    path('updateProject', views.UpdateProjectView.as_view({"post": "update"})),
    path('delProject', views.DeleteProjectView.as_view({"post": "destroy"})),
    path('getProjectDetail/<int:pk>', views.GetProjectDetailView.as_view({'get': 'retrieve'})),
]

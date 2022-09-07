from django.urls import path, include

from Executed import views

urlpatterns = [
    path('runHttpRequest', views.SendHttpRequestView.as_view({'post': 'run_http_request'})),
    path('runCase', views.SendHttpRequestView.as_view({'post': 'run_case'})),
]

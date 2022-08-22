from django.urls import path, include

from TestCasesDiretorys import views

urlpatterns = [
    path('createrCaseDirectory', views.TestCasesDirectorysView.as_view({'post': 'create'})),
    path('getCaseDirectory', views.TestCasesDirectorysView.as_view({'get': 'list'})),
    path('updateCaseDirectory', views.TestCasesDirectorysView.as_view({'post': 'update'})),
    path('delCaseDirectory', views.TestCasesDirectorysView.as_view({'post': 'destroy'})),
    path('getCaseDirectoryDetail', views.TestCasesDirectorysView.as_view({'get': 'retrieve'}))
]

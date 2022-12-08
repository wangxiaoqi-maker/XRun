"""gm_api_automation URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path

from rest_framework.documentation import include_docs_urls
from rest_framework_jwt.views import obtain_jwt_token

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from Users.views import RegisterView

schema_view = get_schema_view(
    openapi.Info(
        title="API接口文档平台",  # 必传
        default_version='v1',  # 必传
        description="接口文档",
        terms_of_service="127.0.0.1",
        contact=openapi.Contact(email="17621525387@139.com"),
        license=openapi.License(name="License"),
    ),
    public=True,
)

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('user/login', obtain_jwt_token),
    path('register', RegisterView.as_view({'post': 'create'})),
    path('', include('Projects.urls')),
    path('', include('TestCasesDiretorys.urls')),
    path('', include('Interfaces.urls')),
    path('', include('Configs.urls')),
    path('', include('Executed.urls')),
    path('', include('TestSuit.urls')),
    path('', include('Reports.urls')),
    path('docs', include_docs_urls(title='测试平台接口文档', description='国民接口文档')),  # 配置coreapi接口文档
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    # 配置swagger json、yaml接口文档
    path('swagger', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),  # 配置swagger ui接口文档
    path('redoc', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),  # 配置redoc接口文档
    path('admin', admin.site.urls),
]

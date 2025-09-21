"""
URL configuration for example_project - Django PostgreSQL Anonymizer Demo
"""

from django.contrib import admin
from django.urls import include, path

from sample_app.masking_demo_views import test_user_data
from sample_app.views import index

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sample/", include("sample_app.urls")),
    path("test-masking/", test_user_data, name="test-masking"),
    path("", index, name="home"),
]

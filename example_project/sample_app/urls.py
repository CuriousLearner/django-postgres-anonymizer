"""
URL configuration for sample_app
"""

from django.shortcuts import redirect
from django.urls import path

from . import anonymization_views, views

app_name = "sample_app"


def redirect_to_home(request):
    """Redirect /sample/ to / to avoid duplicate pages"""
    return redirect("/", permanent=True)


urlpatterns = [
    path("", redirect_to_home, name="index"),
    path("customers/", views.customer_list, name="customer_list"),
    path("customers/<int:pk>/", views.customer_detail, name="customer_detail"),
    path("orders/", views.order_list, name="order_list"),
    path("demo-data/", views.create_demo_data, name="create_demo_data"),
    path("anonymization-demo/", views.anonymization_demo, name="anonymization_demo"),
    # Enhanced anonymization demos
    path("context-manager-demo/", anonymization_views.context_manager_demo, name="context_manager_demo"),
    path("function-validator-demo/", anonymization_views.function_validator_demo, name="function_validator_demo"),
    path("masking-comparison/", anonymization_views.masking_comparison_view, name="masking_comparison"),
    path("anonymized-customers/", anonymization_views.AnonymizedCustomerView.as_view(), name="anonymized_customers"),
    # API endpoints
    path("api/decorated-users/", anonymization_views.decorated_user_list, name="decorated_user_list"),
    path("api/role-required/", anonymization_views.role_required_view, name="role_required_view"),
    path("api/apply-rule/", anonymization_views.apply_masking_rule_ajax, name="apply_masking_rule_ajax"),
    path("api/status/", anonymization_views.anonymization_status_api, name="anonymization_status_api"),
]

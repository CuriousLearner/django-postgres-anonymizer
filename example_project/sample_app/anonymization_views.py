"""
Enhanced views demonstrating django-postgres-anonymizer features
"""

import logging
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from django_postgres_anon.context_managers import anonymized_data, database_role
from django_postgres_anon.decorators import AnonymizedDataMixin, database_role_required, use_anonymized_data
from django_postgres_anon.models import MaskingPreset, MaskingRule
from django_postgres_anon.utils import suggest_anonymization_functions, validate_function_syntax

from .models import Customer

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def context_manager_demo(request: HttpRequest) -> HttpResponse:
    """Demonstrate context manager usage for anonymized data access"""

    context = {
        "normal_data": [],
        "anonymized_data": [],
        "role_switched_data": [],
        "demo_title": "Context Manager Demonstrations",
    }

    try:
        # Normal data access - explicitly use default role to bypass middleware
        with database_role("sanyamkhurana"):  # Use default role to get unmasked data
            normal_users = list(User.objects.values("username", "email", "first_name", "last_name")[:5])
            context["normal_data"] = normal_users

        # Using anonymized_data context manager
        try:
            with anonymized_data():
                anonymized_users = list(User.objects.values("username", "email", "first_name", "last_name")[:5])
                context["anonymized_data"] = anonymized_users
        except Exception as e:
            logger.warning(f"Anonymized data context manager failed: {e}")
            context["anonymized_data"] = [{"error": f"Context manager failed: {e}"}]

        # Using database_role context manager
        try:
            with database_role("masked_reader"):
                role_users = list(User.objects.values("username", "email", "first_name", "last_name")[:5])
                context["role_switched_data"] = role_users
        except Exception as e:
            logger.warning(f"Database role context manager failed: {e}")
            context["role_switched_data"] = [{"error": f"Role switch failed: {e}"}]

    except Exception as e:
        logger.error(f"Context manager demo error: {e}")
        messages.error(request, f"Demo error: {e}")

    return render(request, "sample_app/context_manager_demo.html", context)


@use_anonymized_data
def decorated_user_list(request: HttpRequest) -> JsonResponse:
    """View using the @use_anonymized_data decorator"""
    try:
        users = User.objects.values("username", "email", "first_name", "last_name")[:10]
        return JsonResponse(
            {"message": "Data accessed with @use_anonymized_data decorator", "users": list(users), "anonymized": True}
        )
    except Exception as e:
        logger.error(f"Decorated user list error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@database_role_required("masked_reader")
def role_required_view(request: HttpRequest) -> JsonResponse:
    """View using the @database_role_required decorator"""
    try:
        customers = Customer.objects.select_related("user").values(
            "user__username", "user__email", "phone", "ssn", "annual_income"
        )[:5]

        return JsonResponse(
            {
                "message": "Data accessed with @database_role_required decorator",
                "customers": list(customers),
                "required_role": "masked_reader",
            }
        )
    except Exception as e:
        logger.error(f"Role required view error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@method_decorator(login_required, name="dispatch")
class AnonymizedCustomerView(AnonymizedDataMixin, TemplateView):
    """Class-based view using AnonymizedDataMixin to show only anonymized data"""

    template_name = "sample_app/anonymized_customer_view.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        try:
            # Data will be automatically anonymized due to the mixin
            customers = Customer.objects.select_related("user").all()[:10]

            context.update(
                {
                    "customers": customers,
                    "mixin_used": "AnonymizedDataMixin",
                    "total_customers": customers.count() if hasattr(customers, "count") else len(customers),
                }
            )
        except Exception as e:
            logger.error(f"AnonymizedCustomerView error: {e}")
            context["error"] = str(e)

        return context


@login_required
@require_http_methods(["GET", "POST"])
def function_validator_demo(request: HttpRequest) -> HttpResponse:
    """Demonstrate function validation and suggestion features"""

    context = {
        "validation_results": [],
        "suggestions": [],
        "demo_functions": [
            "anon.fake_email()",
            "anon.fake_first_name()",
            "anon.hash({col})",
            'anon.partial({col}, 2, "***", 2)',
            "invalid_function()",
            "anon.unknown_function()",
        ],
    }

    if request.method == "POST":
        function_to_test = request.POST.get("function_expr", "")

        if function_to_test:
            try:
                # Validate the function
                is_valid = validate_function_syntax(function_to_test)
                context["validation_results"].append(
                    {
                        "function": function_to_test,
                        "is_valid": is_valid,
                        "message": "Valid function" if is_valid else "Invalid function syntax",
                    }
                )
            except Exception as e:
                context["validation_results"].append(
                    {"function": function_to_test, "is_valid": False, "message": f"Validation error: {e}"}
                )

        # Get suggestions for a column type
        column_type = request.POST.get("column_type", "email")
        try:
            suggestions = suggest_anonymization_functions(column_type)
            context["suggestions"] = [
                {"function": func, "description": f"Suggested for {column_type} columns"} for func in suggestions
            ]
        except Exception as e:
            logger.error(f"Function suggestion error: {e}")
            context["suggestion_error"] = str(e)

    # Test all demo functions
    for func in context["demo_functions"]:
        try:
            is_valid = validate_function_syntax(func)
            context["validation_results"].append(
                {"function": func, "is_valid": is_valid, "message": "Valid" if is_valid else "Invalid"}
            )
        except Exception as e:
            context["validation_results"].append({"function": func, "is_valid": False, "message": f"Error: {e}"})

    return render(request, "sample_app/function_validator_demo.html", context)


@login_required
def masking_comparison_view(request: HttpRequest) -> HttpResponse:
    """Compare data before and after masking rules are applied"""

    context = {"comparison_data": [], "active_rules": []}

    try:
        # Get active masking rules (before switching to masked role)
        active_rules = MaskingRule.objects.filter(enabled=True)
        context["active_rules"] = active_rules

        # Get sample data for comparison (before switching to masked role)
        sample_customers = Customer.objects.select_related("user")[:3]

        for customer in sample_customers:
            # Normal access
            normal_data = {
                "username": customer.user.username,
                "email": customer.user.email,
                "first_name": customer.user.first_name,
                "last_name": customer.user.last_name,
                "phone": customer.phone,
                "ssn": customer.ssn,
                "annual_income": customer.annual_income,
            }

            # Try to get anonymized version
            try:
                with anonymized_data():
                    # Fetch the same customer with anonymized data
                    anon_customer = Customer.objects.select_related("user").get(pk=customer.pk)
                    anonymized_data_dict = {
                        "username": anon_customer.user.username,
                        "email": anon_customer.user.email,
                        "first_name": anon_customer.user.first_name,
                        "last_name": anon_customer.user.last_name,
                        "phone": anon_customer.phone,
                        "ssn": anon_customer.ssn,
                        "annual_income": anon_customer.annual_income,
                    }
            except Exception as e:
                logger.warning(f"Could not fetch anonymized data: {e}")
                anonymized_data_dict = {"error": f"Anonymization failed: {e}"}

            context["comparison_data"].append(
                {"customer_id": customer.pk, "normal": normal_data, "anonymized": anonymized_data_dict}
            )

    except Exception as e:
        logger.error(f"Masking comparison error: {e}")
        messages.error(request, f"Comparison demo error: {e}")

    return render(request, "sample_app/masking_comparison.html", context)


@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(["POST"])
def apply_masking_rule_ajax(request: HttpRequest) -> JsonResponse:
    """Apply a masking rule via AJAX"""

    rule_id = request.POST.get("rule_id")

    if not rule_id:
        return JsonResponse({"success": False, "error": "Rule ID required"})

    try:
        rule = MaskingRule.objects.get(pk=rule_id)

        # This is a demo - in real implementation, you'd apply the rule to the database
        # For now, we'll just mark it as applied
        rule.mark_applied()

        return JsonResponse(
            {
                "success": True,
                "message": f"Rule applied: {rule}",
                "rule": {
                    "id": rule.pk,
                    "table": rule.table_name,
                    "column": rule.column_name,
                    "function": rule.function_expr,
                    "applied_at": rule.applied_at.isoformat() if rule.applied_at else None,
                },
            }
        )

    except MaskingRule.DoesNotExist:
        return JsonResponse({"success": False, "error": "Rule not found"})
    except Exception as e:
        logger.error(f"Apply masking rule error: {e}")
        return JsonResponse({"success": False, "error": str(e)})


@login_required
def anonymization_status_api(request: HttpRequest) -> JsonResponse:
    """API endpoint for anonymization status"""

    try:
        total_rules = MaskingRule.objects.count()
        enabled_rules = MaskingRule.objects.filter(enabled=True).count()
        applied_rules = MaskingRule.objects.filter(applied_at__isnull=False).count()
        active_presets = MaskingPreset.objects.filter(is_active=True).count()

        # Get sample of recent rules
        recent_rules = MaskingRule.objects.order_by("-created_at")[:5].values(
            "id", "table_name", "column_name", "function_expr", "enabled", "applied_at"
        )

        return JsonResponse(
            {
                "status": "success",
                "statistics": {
                    "total_rules": total_rules,
                    "enabled_rules": enabled_rules,
                    "applied_rules": applied_rules,
                    "active_presets": active_presets,
                    "coverage_percentage": round((applied_rules / total_rules * 100) if total_rules > 0 else 0, 1),
                },
                "recent_rules": list(recent_rules),
            }
        )

    except Exception as e:
        logger.error(f"Anonymization status API error: {e}")
        return JsonResponse({"status": "error", "error": str(e)}, status=500)

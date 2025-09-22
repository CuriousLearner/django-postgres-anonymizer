"""
Sample views demonstrating django-postgres-anonymizer usage
"""

import logging
import random
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from django_postgres_anon.models import MaskingPreset, MaskingRule
from django_postgres_anon.utils import get_table_columns

from .models import Customer, Order, Payment, SupportTicket, UserActivity

logger = logging.getLogger(__name__)


def index(request: HttpRequest) -> HttpResponse:
    """Sample app home page"""
    context = {
        "customer_count": Customer.objects.count(),
        "order_count": Order.objects.count(),
        "payment_count": Payment.objects.count(),
        "ticket_count": SupportTicket.objects.count(),
        "activity_count": UserActivity.objects.count(),
        "masking_rules_count": MaskingRule.objects.count(),
        "active_presets_count": MaskingPreset.objects.filter(is_active=True).count(),
    }
    return render(request, "sample_app/index.html", context)


def customer_list(request: HttpRequest) -> HttpResponse:
    """List customers with pagination"""
    customers = Customer.objects.select_related("user").all()
    paginator = Paginator(customers, 10)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "sample_app/customer_list.html", {"page_obj": page_obj})


def customer_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Customer detail view"""
    customer = get_object_or_404(Customer, pk=pk)
    orders = customer.order_set.all()[:5]  # Recent orders
    tickets = customer.supportticket_set.filter(status__in=["open", "in_progress"])[:5]

    context = {
        "customer": customer,
        "orders": orders,
        "tickets": tickets,
    }
    return render(request, "sample_app/customer_detail.html", context)


def order_list(request: HttpRequest) -> HttpResponse:
    """List orders with pagination"""
    orders = Order.objects.select_related("customer__user").all()
    paginator = Paginator(orders, 20)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "sample_app/order_list.html", {"page_obj": page_obj})


@user_passes_test(lambda u: u.is_superuser)
def create_demo_data(request: HttpRequest) -> HttpResponse:
    """Create sample data for demonstration purposes"""
    if request.method == "POST":
        try:
            logger.info("Starting demo data creation")
            created_count = 0

            with transaction.atomic():
                # Check if demo data already exists
                if User.objects.filter(username__startswith="demo_user_").exists():
                    messages.warning(request, "Demo data already exists. Skipping creation.")
                    return render(request, "sample_app/create_demo_data.html")

                # Create demo users and customers with obviously fake names
                # This makes anonymization effects clearly visible
                for i in range(10):
                    user = User.objects.create_user(
                        username=f"demo_user_{i}",
                        email=f"demo_user_{i}@example.com",
                        first_name=f"Demo{i}",
                        last_name=f"User{i}",
                    )

                    customer = Customer.objects.create(
                        user=user,
                        phone=f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                        date_of_birth=datetime.now().date() - timedelta(days=random.randint(18 * 365, 65 * 365)),
                        ssn=f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}",
                        address=f"{random.randint(100, 9999)} Demo Street",
                        city=random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                        state=random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                        zip_code=f"{random.randint(10000, 99999)}",
                        annual_income=random.randint(30000, 150000),
                        credit_score=random.randint(300, 850),
                    )
                    created_count += 1

                    # Create orders for each customer
                    for j in range(random.randint(1, 5)):
                        order = Order.objects.create(
                            customer=customer,
                            order_number=f"ORD-{random.randint(100000, 999999)}",
                            total_amount=random.randint(20, 500),
                            status=random.choice(["pending", "processing", "shipped", "delivered"]),
                            shipping_address=customer.address,
                            shipping_city=customer.city,
                            shipping_state=customer.state,
                            shipping_zip=customer.zip_code,
                            notes=f"Demo order {j + 1} for customer {i + 1}",
                        )

                        # Create payment for order
                        Payment.objects.create(
                            order=order,
                            amount=order.total_amount,
                            payment_method=random.choice(["credit_card", "debit_card", "paypal"]),
                            card_last_four=f"{random.randint(1000, 9999)}",
                            card_brand=random.choice(["Visa", "MasterCard", "American Express"]),
                            transaction_id=f"TXN-{random.randint(1000000, 9999999)}",
                            billing_address=customer.address,
                            billing_city=customer.city,
                            billing_state=customer.state,
                            billing_zip=customer.zip_code,
                            processed_at=timezone.now(),
                        )

                    # Create support ticket
                    if random.random() < 0.3:  # 30% chance
                        SupportTicket.objects.create(
                            customer=customer,
                            ticket_number=f"TICK-{random.randint(10000, 99999)}",
                            subject=random.choice(
                                ["Order delivery issue", "Payment problem", "Account access issue", "Product question"]
                            ),
                            description=f"Demo support issue for customer {i + 1}",
                            priority=random.choice(["low", "medium", "high"]),
                            status=random.choice(["open", "in_progress", "resolved"]),
                        )

                    # Create user activity
                    for k in range(random.randint(5, 15)):
                        UserActivity.objects.create(
                            user=user,
                            activity_type=random.choice(["login", "logout", "page_view", "purchase", "search"]),
                            description=f"Demo activity {k + 1}",
                            ip_address=f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
                            user_agent="Demo User Agent String",
                            session_id=f"session_{random.randint(100000, 999999)}",
                            country=random.choice(["US", "CA", "GB", "DE"]),
                            city=random.choice(["New York", "Toronto", "London", "Berlin"]),
                        )

            logger.info(f"Successfully created {created_count} demo customers")
            messages.success(
                request,
                f"Demo data created successfully! Created {created_count} customers with orders, payments, and activities.",
            )

        except Exception as e:
            logger.error(f"Error creating demo data: {e}", exc_info=True)
            messages.error(request, f"Error creating demo data: {e!s}")
            # Re-raise in development for debugging
            if hasattr(request, "user") and request.user.is_superuser:
                raise

    return render(request, "sample_app/create_demo_data.html")


@login_required
def anonymization_demo(request: HttpRequest) -> HttpResponse:
    """Demonstrate anonymization features"""

    # Get current masking rules
    masking_rules = MaskingRule.objects.all()
    presets = MaskingPreset.objects.all()

    # Get sample data to show before/after anonymization
    customers = Customer.objects.select_related("user")[:5]
    orders = Order.objects.select_related("customer__user")[:5]

    # Get table schema information
    schema_info = {}
    try:
        schema_info["sample_app_customer"] = get_table_columns("sample_app_customer")
        schema_info["auth_user"] = get_table_columns("auth_user")
    except Exception as e:
        messages.warning(request, f"Could not retrieve schema info: {e!s}")

    context = {
        "masking_rules": masking_rules,
        "presets": presets,
        "customers": customers,
        "orders": orders,
        "schema_info": schema_info,
    }

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_sample_rules":
            try:
                # Create sample masking rules for demo
                rules_created = []

                # User email anonymization
                rule, created = MaskingRule.objects.get_or_create(
                    table_name="auth_user",
                    column_name="email",
                    defaults={"function_expr": "anon.fake_email()", "notes": "Anonymize user email addresses"},
                )
                if created:
                    rules_created.append(str(rule))

                # Customer SSN anonymization
                rule, created = MaskingRule.objects.get_or_create(
                    table_name="sample_app_customer",
                    column_name="ssn",
                    defaults={
                        "function_expr": "anon.fake_ssn()",
                        "notes": "Anonymize customer SSN",
                        "depends_on_unique": True,
                    },
                )
                if created:
                    rules_created.append(str(rule))

                # Customer phone anonymization
                rule, created = MaskingRule.objects.get_or_create(
                    table_name="sample_app_customer",
                    column_name="phone",
                    defaults={"function_expr": "anon.fake_phone()", "notes": "Anonymize customer phone numbers"},
                )
                if created:
                    rules_created.append(str(rule))

                # Order notes anonymization
                rule, created = MaskingRule.objects.get_or_create(
                    table_name="sample_app_order",
                    column_name="notes",
                    defaults={"function_expr": "anon.lorem_ipsum()", "notes": "Replace order notes with lorem ipsum"},
                )
                if created:
                    rules_created.append(str(rule))

                if rules_created:
                    messages.success(request, f"Created {len(rules_created)} sample masking rules")
                else:
                    messages.info(request, "Sample masking rules already exist")

            except Exception as e:
                messages.error(request, f"Error creating sample rules: {e!s}")

        elif action == "load_preset":
            preset_name = request.POST.get("preset_name")
            if preset_name:
                try:
                    from django_postgres_anon import get_preset_path

                    preset_path = get_preset_path(preset_name)
                    preset, rules_created = MaskingPreset.load_from_yaml(preset_path, f"{preset_name}_demo")
                    messages.success(request, f'Loaded preset "{preset_name}" with {rules_created} rules')
                except Exception as e:
                    messages.error(request, f"Error loading preset: {e!s}")

    return render(request, "sample_app/anonymization_demo.html", context)

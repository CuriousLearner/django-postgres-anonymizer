"""
Admin configuration for sample app models
"""

from django.contrib import admin

from .models import Customer, Order, Payment, SupportTicket, UserActivity


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["user", "phone", "city", "state", "created_at"]
    list_filter = ["state", "created_at"]
    search_fields = ["user__email", "user__first_name", "user__last_name", "phone"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("User Information", {"fields": ("user",)}),
        ("Personal Information", {"fields": ("phone", "date_of_birth", "ssn")}),
        ("Address", {"fields": ("address", "city", "state", "zip_code")}),
        ("Financial Information", {"fields": ("annual_income", "credit_score"), "classes": ("collapse",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "customer", "total_amount", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["order_number", "customer__user__email"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Order Information", {"fields": ("customer", "order_number", "total_amount", "status")}),
        ("Shipping Information", {"fields": ("shipping_address", "shipping_city", "shipping_state", "shipping_zip")}),
        ("Notes", {"fields": ("notes", "internal_notes"), "classes": ("collapse",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["transaction_id", "order", "amount", "payment_method", "processed_at"]
    list_filter = ["payment_method", "card_brand", "processed_at"]
    search_fields = ["transaction_id", "order__order_number"]
    readonly_fields = ["created_at"]

    fieldsets = (
        ("Payment Information", {"fields": ("order", "amount", "payment_method", "processed_at")}),
        ("Card Information", {"fields": ("card_last_four", "card_brand", "transaction_id")}),
        ("Billing Address", {"fields": ("billing_address", "billing_city", "billing_state", "billing_zip")}),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ["ticket_number", "customer", "subject", "priority", "status", "assigned_to", "created_at"]
    list_filter = ["priority", "status", "created_at", "assigned_to"]
    search_fields = ["ticket_number", "subject", "customer__user__email"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Ticket Information", {"fields": ("customer", "ticket_number", "subject", "description")}),
        ("Management", {"fields": ("priority", "status", "assigned_to")}),
        ("Responses", {"fields": ("staff_response", "internal_notes"), "classes": ("collapse",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at", "resolved_at"), "classes": ("collapse",)}),
    )


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ["user", "activity_type", "ip_address", "country", "city", "timestamp"]
    list_filter = ["activity_type", "country", "timestamp"]
    search_fields = ["user__username", "activity_type", "description", "ip_address"]
    readonly_fields = ["timestamp"]

    fieldsets = (
        ("Activity Information", {"fields": ("user", "activity_type", "description")}),
        ("Technical Details", {"fields": ("ip_address", "user_agent", "session_id")}),
        ("Location", {"fields": ("country", "city"), "classes": ("collapse",)}),
        ("Timestamp", {"fields": ("timestamp",), "classes": ("collapse",)}),
    )

    def has_add_permission(self, request):
        """Disable adding activities through admin (they should be created programmatically)"""
        return False

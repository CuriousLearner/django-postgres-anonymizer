"""
Sample models demonstrating data that would benefit from anonymization
"""

from django.contrib.auth.models import User
from django.db import models


class Customer(models.Model):
    """Sample customer model with PII data"""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    ssn = models.CharField(max_length=11, unique=True, help_text="XXX-XX-XXXX format")
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=10)

    # Financial information
    annual_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    credit_score = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.email})"


class Order(models.Model):
    """Sample order model"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=20, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Shipping information (contains PII)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=2)
    shipping_zip = models.CharField(max_length=10)

    # Notes might contain sensitive information
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True, help_text="Internal staff notes")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.order_number} - {self.customer}"


class Payment(models.Model):
    """Sample payment model with financial data"""

    PAYMENT_METHODS = [
        ("credit_card", "Credit Card"),
        ("debit_card", "Debit Card"),
        ("paypal", "PayPal"),
        ("bank_transfer", "Bank Transfer"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)

    # Sensitive payment information
    card_last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)
    transaction_id = models.CharField(max_length=100, unique=True)

    # Billing address (more PII)
    billing_address = models.TextField()
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField(max_length=2)
    billing_zip = models.CharField(max_length=10)

    processed_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-processed_at"]

    def __str__(self):
        return f"Payment ${self.amount} for {self.order.order_number}"


class SupportTicket(models.Model):
    """Sample support ticket model"""

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    ticket_number = models.CharField(max_length=20, unique=True)
    subject = models.CharField(max_length=200)
    description = models.TextField(help_text="May contain sensitive customer information")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")

    # Staff responses might contain internal information
    staff_response = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True, help_text="Internal staff notes")

    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tickets"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ticket {self.ticket_number} - {self.subject}"


class UserActivity(models.Model):
    """Sample user activity log - contains behavioral data"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50)
    description = models.TextField()

    # Potentially sensitive tracking data
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    session_id = models.CharField(max_length=40)

    # Location data
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=100, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} at {self.timestamp}"

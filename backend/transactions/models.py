from django.db import models
from django.contrib.auth.models import User
from banking.models import Bank, EmailPattern

# Create your models here.

class Category(models.Model):
    """Transaction categories that users can assign"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Multi-tenant
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#3B82F6', help_text="Hex color code")
    icon = models.CharField(max_length=50, blank=True, help_text="Icon identifier")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        unique_together = ['user', 'name']  # User can't have duplicate category names


class Transaction(models.Model):
    """Processed transactions extracted from bank emails"""
    TRANSACTION_TYPE_CHOICES = [
        ('purchase', 'Purchase'),
        ('transfer', 'Transfer'), 
        ('atm', 'ATM'),
        ('payment', 'Payment'),
        ('deposit', 'Deposit')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Multi-tenant
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)
    
    # Core transaction data
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    transaction_date = models.DateTimeField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    
    # Extracted metadata
    merchant = models.CharField(max_length=255, blank=True, help_text="Merchant or recipient name")
    location = models.CharField(max_length=255, blank=True, help_text="Transaction location")
    reference = models.CharField(max_length=100, blank=True, help_text="Reference or confirmation number")
    
    # Processing metadata
    confidence_score = models.FloatField(help_text="AI confidence score for extraction accuracy")
    email_pattern_used = models.ForeignKey(EmailPattern, on_delete=models.SET_NULL, null=True, blank=True)
    raw_email_body = models.TextField(help_text="Original email content for debugging")
    
    # User categorization
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - ${self.amount} ({self.user.username})"

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-transaction_date']


class EmailQueue(models.Model):
    """Queue system for processing bank emails with Celery"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)
    
    # Email data
    gmail_message_id = models.CharField(max_length=255, unique=True)
    sender = models.CharField(max_length=255)
    subject = models.TextField()
    body = models.TextField()
    received_at = models.DateTimeField()
    
    # Queue status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Processing metadata
    worker_id = models.CharField(max_length=100, blank=True, help_text="Celery worker ID")
    attempts = models.IntegerField(default=0, help_text="Number of processing attempts")
    error_message = models.TextField(blank=True, help_text="Last error message if failed")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Email from {self.sender} - {self.status}"

    class Meta:
        verbose_name = "Email Queue"
        verbose_name_plural = "Email Queue"
        ordering = ['-created_at']

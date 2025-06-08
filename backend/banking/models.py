from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Bank(models.Model):
    """Bank configuration per user (multi-tenant)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Multi-tenant: each user has their banks
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=2)  # ISO country code
    domains = models.JSONField(default=list, help_text="Bank domains like ['bac.cr', 'baccr.com']")
    sender_emails = models.JSONField(default=list, help_text="Bank sender emails like ['alerts@bac.cr']")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    class Meta:
        verbose_name = "Bank"
        verbose_name_plural = "Banks"
        unique_together = ['user', 'name']  # User can't have duplicate bank names


class EmailPattern(models.Model):
    """AI-generated regex patterns for extracting transaction data from bank emails"""
    TRANSACTION_TYPE_CHOICES = [
        ('purchase', 'Purchase'),
        ('transfer', 'Transfer'),
        ('atm', 'ATM'),
        ('payment', 'Payment'),
        ('deposit', 'Deposit'),
    ]
    
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPE_CHOICES)
    
    # Regex patterns (AI generated)
    amount_regex = models.TextField(help_text="Regex pattern to extract transaction amount")
    merchant_regex = models.TextField(blank=True, help_text="Regex pattern to extract merchant/recipient")
    date_regex = models.TextField(help_text="Regex pattern to extract transaction date")
    reference_regex = models.TextField(blank=True, help_text="Regex pattern to extract reference number")
    
    # Pattern metadata
    confidence_threshold = models.FloatField(default=0.7, help_text="Minimum confidence score to use this pattern")
    success_count = models.IntegerField(default=0, help_text="Number of successful extractions")
    failure_count = models.IntegerField(default=0, help_text="Number of failed extractions")
    is_active = models.BooleanField(default=True)
    
    # AI metadata
    generated_by_ai = models.BooleanField(default=True)
    ai_model = models.CharField(max_length=50, default='gpt-4', help_text="AI model used to generate pattern")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bank.name} - {self.get_transaction_type_display()}"

    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0
        return (self.success_count / total) * 100

    class Meta:
        verbose_name = "Email Pattern"
        verbose_name_plural = "Email Patterns"
        unique_together = ['bank', 'transaction_type']  # One pattern per transaction type per bank

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


# =====================================================
# USER FEEDBACK AND REVIEW MODELS (FOR CELERY)
# =====================================================

class TransactionReview(models.Model):
    """Transactions that need user review due to low confidence scores"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved by User'),
        ('corrected', 'Corrected by User'),
        ('rejected', 'Rejected by User'),
    ]
    
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='review')
    
    # Review metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    review_priority = models.IntegerField(default=5, help_text="1=urgent, 10=low priority")
    
    # Original extracted data (before user corrections)
    original_amount = models.DecimalField(max_digits=12, decimal_places=2)
    original_merchant = models.CharField(max_length=255, blank=True)
    original_date = models.DateTimeField()
    original_type = models.CharField(max_length=20)
    
    # User review data
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, help_text="User notes about the correction")
    
    # Auto-generated suggestions for similar transactions
    similar_transactions_count = models.IntegerField(default=0)
    auto_apply_corrections = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review: {self.transaction} - {self.get_status_display()}"

    class Meta:
        verbose_name = "Transaction Review"
        verbose_name_plural = "Transaction Reviews"
        ordering = ['review_priority', '-created_at']


class UserCorrection(models.Model):
    """Log of user corrections to improve template accuracy"""
    CORRECTION_TYPE_CHOICES = [
        ('amount', 'Amount Correction'),
        ('merchant', 'Merchant Correction'),
        ('date', 'Date Correction'),
        ('type', 'Transaction Type Correction'),
        ('category', 'Category Assignment'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='corrections')
    
    # Correction details
    correction_type = models.CharField(max_length=20, choices=CORRECTION_TYPE_CHOICES)
    field_name = models.CharField(max_length=50)
    old_value = models.TextField()
    new_value = models.TextField()
    
    # Template improvement tracking
    template_updated = models.BooleanField(default=False)
    similar_transactions_updated = models.IntegerField(default=0)
    confidence_improvement = models.FloatField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} corrected {self.field_name}: {self.old_value} → {self.new_value}"

    class Meta:
        verbose_name = "User Correction"
        verbose_name_plural = "User Corrections"
        ordering = ['-created_at']


class TemplateImprovement(models.Model):
    """Track template improvements based on user feedback"""
    bank_template = models.ForeignKey('banking.BankTemplate', on_delete=models.CASCADE, related_name='improvements')
    user_correction = models.ForeignKey(UserCorrection, on_delete=models.CASCADE)
    
    # Improvement details
    pattern_field = models.CharField(max_length=50, help_text="Which regex pattern was improved")
    old_pattern = models.TextField()
    new_pattern = models.TextField()
    improvement_reason = models.TextField()
    
    # Performance impact
    accuracy_before = models.FloatField()
    accuracy_after = models.FloatField(null=True, blank=True)
    transactions_reprocessed = models.IntegerField(default=0)
    
    # AI involvement
    ai_assisted = models.BooleanField(default=False)
    ai_confidence = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Template improvement for {self.bank_template} based on {self.user_correction}"

    class Meta:
        verbose_name = "Template Improvement"
        verbose_name_plural = "Template Improvements"
        ordering = ['-created_at']

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


# =====================================================
# EMAIL PROCESSING QUEUE MODELS (FOR CELERY)
# =====================================================

class EmailQueue(models.Model):
    """Queue for emails to be processed by Celery workers"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('needs_review', 'Needs Review'),
        ('user_corrected', 'User Corrected'),
    ]
    
    QUEUE_TYPE_CHOICES = [
        ('bulk', 'Bulk Import'),
        ('incremental', 'Incremental Sync'),
        ('manual', 'Manual Sync'),
        ('retry', 'Retry'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Multi-tenant
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, null=True, blank=True)  # May be unknown initially
    
    # Email data
    gmail_message_id = models.CharField(max_length=255, unique=True)
    sender = models.CharField(max_length=255)
    subject = models.TextField()
    body = models.TextField()
    received_at = models.DateTimeField()
    
    # Queue metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    queue_type = models.CharField(max_length=20, choices=QUEUE_TYPE_CHOICES, default='incremental')
    priority = models.IntegerField(default=5, help_text="1=highest, 10=lowest priority")
    
    # Processing metadata
    worker_id = models.CharField(max_length=100, blank=True)
    attempts = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Email {self.gmail_message_id} - {self.get_status_display()}"

    class Meta:
        verbose_name = "Email Queue"
        verbose_name_plural = "Email Queue"
        ordering = ['priority', '-created_at']
        indexes = [
            models.Index(fields=['status', 'queue_type']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['gmail_message_id']),
        ]


class EmailProcessingLog(models.Model):
    """Log of email processing attempts for debugging and monitoring"""
    email_queue = models.ForeignKey(EmailQueue, on_delete=models.CASCADE, related_name='processing_logs')
    
    # Processing details
    worker_type = models.CharField(max_length=50)  # 'import', 'processing', 'ai_generation', etc.
    worker_id = models.CharField(max_length=100)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    extracted_data = models.JSONField(null=True, blank=True, help_text="Data extracted from email")
    
    # Performance metrics
    processing_time_seconds = models.FloatField(null=True, blank=True)
    api_calls_made = models.IntegerField(default=0)  # For AI cost tracking
    
    def __str__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"{self.worker_type} - {status} - {self.email_queue.gmail_message_id}"

    class Meta:
        verbose_name = "Processing Log"
        verbose_name_plural = "Processing Logs"
        ordering = ['-started_at']


class BankTemplate(models.Model):
    """Enhanced template system for bank email processing"""
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='templates')
    
    # Template metadata
    name = models.CharField(max_length=100, help_text="Human-readable template name")
    version = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    
    # Email identification patterns
    subject_patterns = models.JSONField(default=list, help_text="Regex patterns to match email subjects")
    sender_patterns = models.JSONField(default=list, help_text="Regex patterns to match sender emails")
    body_keywords = models.JSONField(default=list, help_text="Keywords that must be present in email body")
    
    # Extraction patterns (inherited from EmailPattern)
    email_patterns = models.ManyToManyField(EmailPattern, related_name='templates')
    
    # Template performance
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    confidence_threshold = models.FloatField(default=0.8)
    
    # AI metadata
    generated_by_ai = models.BooleanField(default=True)
    ai_prompt_used = models.TextField(blank=True)
    sample_emails_used = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.bank.name} - {self.name} v{self.version}"

    @property
    def success_rate(self):
        """Calculate template success rate"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0
        return (self.success_count / total) * 100

    class Meta:
        verbose_name = "Bank Template"
        verbose_name_plural = "Bank Templates"
        unique_together = ['bank', 'name', 'version']
        ordering = ['-updated_at']

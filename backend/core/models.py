from django.db import models
from django.contrib.auth.models import User

class Integration(models.Model):
    """
    User email integrations (Gmail, Outlook, Yahoo)
    Each user can have multiple email accounts
    """
    PROVIDER_CHOICES = [
        ('gmail', 'Gmail'),
        ('outlook', 'Microsoft Outlook'),
        ('yahoo', 'Yahoo Mail')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    email_address = models.EmailField()
    is_active = models.BooleanField(default=True)
    provider_config = models.JSONField(default=dict, help_text="OAuth tokens and provider-specific config")
    
    # Nuevos campos para gestión de tokens
    oauth_token_expires_at = models.DateTimeField(null=True, blank=True)
    oauth_token_refreshed_at = models.DateTimeField(null=True, blank=True)
    oauth_token_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('expired', 'Expired'), 
            ('revoked', 'Revoked'),
            ('error', 'Error')
        ],
        default='active'
    )
    auto_refresh_enabled = models.BooleanField(default=True)
    last_refresh_attempt = models.DateTimeField(null=True, blank=True)
    refresh_error_count = models.IntegerField(default=0)
    refresh_error_message = models.TextField(blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='integration_updates')
    updated_message = models.TextField(blank=True, help_text="Reason for last update")
    
    def __str__(self):
        return f"{self.email_address} ({self.get_provider_display()}) - {self.user.username}"
    
    class Meta:
        verbose_name = "Integration"
        verbose_name_plural = "Integrations"
        unique_together = ['user', 'provider', 'email_address']
        indexes = [
            models.Index(fields=['oauth_token_status']),
            models.Index(fields=['oauth_token_expires_at']),
            models.Index(fields=['last_refresh_attempt'])
        ]


class EmailImportJob(models.Model):
    """
    Scheduled import jobs per integration
    Workers read this table to know what to execute
    """
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('error', 'Error'),
        ('suspended', 'Suspended')
    ]
    
    integration = models.ForeignKey(Integration, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    
    # Scheduling
    next_run_at = models.DateTimeField(help_text="When this job should run next")
    retry_after = models.DateTimeField(null=True, blank=True, help_text="When to retry after error")
    period = models.IntegerField(default=30, help_text="Import period in minutes")
    window_start_offset = models.IntegerField(default=0, help_text="Window start offset in minutes")
    
    # Execution tracking
    worker_id = models.CharField(max_length=100, blank=True)
    celery_task_id = models.CharField(max_length=255, blank=True)
    attempts = models.IntegerField(default=0)
    message = models.TextField(blank=True, help_text="Status message or error details")
    
    # Results summary
    summary = models.JSONField(default=dict, help_text="Job execution summary: emails_read, emails_created, etc.")
    
    def __str__(self):
        return f"Job {self.id} - {self.integration.email_address} - {self.get_status_display()}"
    
    class Meta:
        verbose_name = "Email Import Job"
        verbose_name_plural = "Email Import Jobs"
        ordering = ['-next_run_at']


class Email(models.Model):
    """
    Raw email storage - ONLY data storage
    No processing logic, no queue management
    """
    integration = models.ForeignKey(Integration, on_delete=models.CASCADE)
    import_job = models.ForeignKey(EmailImportJob, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Provider-specific unique identifier
    provider_message_id = models.CharField(max_length=255, help_text="Provider's unique message ID")
    
    # Email core data
    sender = models.CharField(max_length=255)
    recipient = models.CharField(max_length=255)
    subject = models.TextField()
    body = models.TextField()
    
    # Email metadata
    raw_headers = models.JSONField(default=dict)
    attachment_count = models.IntegerField(default=0)
    
    # Processing tracking
    created_at = models.DateTimeField(auto_now_add=True, help_text="When system created this record")
    processed_at = models.DateTimeField(null=True, blank=True)
    process_by = models.CharField(max_length=255, blank=True, help_text="Template ID used for processing")
    
    def __str__(self):
        return f"Email {self.id} - {self.subject[:50]} - {self.sender}"
    
    class Meta:
        verbose_name = "Email"
        verbose_name_plural = "Emails"
        unique_together = ['integration', 'provider_message_id']
        indexes = [
            models.Index(fields=['integration', 'processed_at']),
            models.Index(fields=['provider_message_id']),
            models.Index(fields=['created_at'])
        ]


class BankSender(models.Model):
    """
    Global bank senders - shared across all users
    Each bank has specific sender emails that are the same for everyone
    """
    # Django automatically adds 'id' as AutoField primary key
    
    # Relación con Bank (del banking app)
    bank = models.ForeignKey('banking.Bank', on_delete=models.CASCADE, related_name='senders')
    
    # Información del sender
    sender_email = models.EmailField(unique=True, help_text="Unique bank sender email")
    sender_name = models.CharField(max_length=255, blank=True, help_text="Display name of the sender")
    sender_domain = models.CharField(max_length=100, help_text="Domain for pattern matching")
    
    # Template para análisis
    email_template = models.ForeignKey('banking.BankTemplate', on_delete=models.SET_NULL, null=True, blank=True, help_text="Template used to process emails from this sender")
    
    # Metadatos globales
    is_verified = models.BooleanField(default=False, help_text="Verified by admin/community")
    confidence_score = models.FloatField(default=0.8, help_text="Global confidence score for this sender")
    total_emails_processed = models.IntegerField(default=0, help_text="Total emails processed across all users")
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_senders')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_senders')
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.sender_email} ({self.bank.name})"
    
    def save(self, *args, **kwargs):
        # Auto-extract domain from email
        if self.sender_email and not self.sender_domain:
            self.sender_domain = self.sender_email.split('@')[1]
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Bank Sender"
        verbose_name_plural = "Bank Senders"
        ordering = ['-total_emails_processed', 'sender_email']
        indexes = [
            models.Index(fields=['sender_email']),
            models.Index(fields=['sender_domain']),
            models.Index(fields=['bank', 'is_verified']),
            models.Index(fields=['total_emails_processed'])
        ]


class UserBankSender(models.Model):
    """
    User's enabled bank senders - N:N relationship
    Users can enable/disable specific bank senders for their processing
    """
    # Django automatically adds 'id' as AutoField primary key
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_bank_senders')
    integration = models.ForeignKey(Integration, on_delete=models.CASCADE, related_name='bank_senders')
    bank_sender = models.ForeignKey(BankSender, on_delete=models.CASCADE, related_name='user_assignments')
    
    # Configuración por usuario
    is_active = models.BooleanField(default=True, help_text="Whether this sender is active for this user")
    custom_confidence = models.FloatField(null=True, blank=True, help_text="User override confidence (overrides global)")
    custom_name = models.CharField(max_length=255, blank=True, help_text="User's custom name for this sender")
    
    # Estadísticas por usuario
    emails_processed = models.IntegerField(default=0, help_text="Emails processed for this user from this sender")
    last_email_at = models.DateTimeField(null=True, blank=True, help_text="Last email received from this sender")
    
    # Metadatos
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, help_text="User notes about this sender")

    def __str__(self):
        return f"{self.user.username} - {self.bank_sender.sender_email} ({'Active' if self.is_active else 'Inactive'})"
    
    @property
    def effective_confidence(self):
        """Get the effective confidence score (custom or global)"""
        return self.custom_confidence if self.custom_confidence is not None else self.bank_sender.confidence_score
    
    @property
    def display_name(self):
        """Get the display name (custom or default)"""
        return self.custom_name if self.custom_name else self.bank_sender.sender_name or self.bank_sender.sender_email

    class Meta:
        verbose_name = "User Bank Sender"
        verbose_name_plural = "User Bank Senders"
        unique_together = ['user', 'integration', 'bank_sender']
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['user', 'integration', 'is_active']),
            models.Index(fields=['bank_sender', 'is_active']),
            models.Index(fields=['last_email_at'])
        ] 
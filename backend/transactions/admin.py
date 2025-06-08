from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg
from .models import Category, Transaction, EmailQueue

# Create your admin configurations here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Category admin configuration"""
    list_display = ['name', 'user', 'color_display', 'icon', 'transaction_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'user__username', 'user__email']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'is_active')
        }),
        ('Visual Settings', {
            'fields': ('color', 'icon')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def color_display(self, obj):
        """Display color as a colored box"""
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.color
        )
    color_display.short_description = 'Color'
    
    def transaction_count(self, obj):
        """Show number of transactions in this category"""
        count = obj.transaction_set.count()
        return f"{count} transactions"
    transaction_count.short_description = 'Usage'
    
    def get_queryset(self, request):
        """Optimize queryset with annotations"""
        return super().get_queryset(request).select_related('user').annotate(
            transaction_count=Count('transaction')
        )

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Transaction admin configuration"""
    list_display = ['description_short', 'user', 'amount', 'transaction_type', 'bank', 'confidence_display', 'transaction_date']
    list_filter = ['transaction_type', 'bank', 'category', 'transaction_date', 'created_at']
    search_fields = ['description', 'merchant', 'reference', 'user__username', 'bank__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('user', 'bank', 'amount', 'transaction_type', 'transaction_date')
        }),
        ('Description & Metadata', {
            'fields': ('description', 'merchant', 'location', 'reference')
        }),
        ('Processing Information', {
            'fields': ('confidence_score', 'email_pattern_used', 'raw_email_body'),
            'classes': ('collapse',)
        }),
        ('Categorization', {
            'fields': ('category',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def description_short(self, obj):
        """Display shortened description"""
        return obj.description[:50] + ('...' if len(obj.description) > 50 else '')
    description_short.short_description = 'Description'
    
    def confidence_display(self, obj):
        """Display confidence score with color coding"""
        score = obj.confidence_score
        if score >= 0.8:
            color = 'green'
        elif score >= 0.6:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, score * 100
        )
    confidence_display.short_description = 'Confidence'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'user', 'bank', 'category', 'email_pattern_used'
        )

@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    """EmailQueue admin configuration"""
    list_display = ['sender', 'user', 'bank', 'status_display', 'attempts', 'received_at', 'processed_at']
    list_filter = ['status', 'bank', 'received_at', 'created_at']
    search_fields = ['sender', 'subject', 'gmail_message_id', 'user__username', 'bank__name']
    readonly_fields = ['created_at', 'gmail_message_id']
    date_hierarchy = 'received_at'
    
    fieldsets = (
        ('Email Information', {
            'fields': ('user', 'bank', 'gmail_message_id', 'sender', 'subject', 'received_at')
        }),
        ('Processing Status', {
            'fields': ('status', 'worker_id', 'attempts', 'processed_at')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Email Content', {
            'fields': ('body',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        """Display status with color coding"""
        status_colors = {
            'pending': 'blue',
            'processing': 'orange',
            'completed': 'green',
            'failed': 'red'
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'bank')
    
    actions = ['retry_failed_emails']
    
    def retry_failed_emails(self, request, queryset):
        """Admin action to retry failed emails"""
        failed_emails = queryset.filter(status='failed')
        updated = failed_emails.update(status='pending', attempts=0, error_message='')
        self.message_user(request, f'{updated} failed emails marked for retry.')
    retry_failed_emails.short_description = 'Retry selected failed emails'

from django.contrib import admin
from .models import Integration, EmailImportJob, Email

@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ('email_address', 'provider', 'user', 'is_active', 'created_at', 'updated_at')
    list_filter = ('provider', 'is_active', 'created_at')
    search_fields = ('email_address', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'provider', 'email_address', 'is_active')
        }),
        ('Configuration', {
            'fields': ('provider_config',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('updated_by', 'updated_message', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        """Automatically set updated_by when saving"""
        if change:  # Only on updates, not creation
            obj.updated_by = request.user 
        super().save_model(request, obj, form, change)


@admin.register(EmailImportJob)
class EmailImportJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'integration_email', 'status', 'next_run_at', 'attempts', 'worker_id')
    list_filter = ('status', 'next_run_at', 'integration__provider')
    search_fields = ('integration__email_address', 'worker_id', 'celery_task_id')
    readonly_fields = ('celery_task_id', 'worker_id', 'attempts')
    
    fieldsets = (
        (None, {
            'fields': ('integration', 'status', 'next_run_at', 'retry_after')
        }),
        ('Configuration', {
            'fields': ('period', 'window_start_offset')
        }),
        ('Execution', {
            'fields': ('worker_id', 'celery_task_id', 'attempts', 'message'),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('summary',),
            'classes': ('collapse',)
        })
    )
    
    def integration_email(self, obj):
        return obj.integration.email_address
    integration_email.short_description = 'Email Address'
    integration_email.admin_order_field = 'integration__email_address'


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ('id', 'integration_email', 'subject_short', 'sender', 'created_at', 'processed_at')
    list_filter = ('integration__provider', 'created_at', 'processed_at')
    search_fields = ('subject', 'sender', 'recipient', 'provider_message_id')
    readonly_fields = ('created_at', 'provider_message_id', 'raw_headers')
    
    fieldsets = (
        (None, {
            'fields': ('integration', 'import_job', 'provider_message_id')
        }),
        ('Email Data', {
            'fields': ('sender', 'recipient', 'subject', 'body')
        }),
        ('Metadata', {
            'fields': ('attachment_count', 'raw_headers'),
            'classes': ('collapse',)
        }),
        ('Processing', {
            'fields': ('created_at', 'processed_at', 'process_by'),
            'classes': ('collapse',)
        })
    )
    
    def integration_email(self, obj):
        return obj.integration.email_address
    integration_email.short_description = 'Integration'
    integration_email.admin_order_field = 'integration__email_address'
    
    def subject_short(self, obj):
        return obj.subject[:60] + '...' if len(obj.subject) > 60 else obj.subject
    subject_short.short_description = 'Subject'
    subject_short.admin_order_field = 'subject' 
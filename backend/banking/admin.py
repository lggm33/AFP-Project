from django.contrib import admin
from django.utils.html import format_html
from .models import Bank, EmailPattern

# Create your admin configurations here.

class EmailPatternInline(admin.TabularInline):
    """Inline EmailPattern in Bank admin"""
    model = EmailPattern
    extra = 0
    fields = ['transaction_type', 'is_active', 'confidence_threshold', 'success_count', 'failure_count']
    readonly_fields = ['success_count', 'failure_count']

@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    """Bank admin configuration"""
    list_display = ['name', 'user', 'country', 'domains_display', 'pattern_count', 'is_active', 'created_at']
    list_filter = ['country', 'is_active', 'created_at']
    search_fields = ['name', 'user__username', 'user__email']
    readonly_fields = ['created_at']
    inlines = [EmailPatternInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'country', 'is_active')
        }),
        ('Email Configuration', {
            'fields': ('domains', 'sender_emails'),
            'description': 'JSON arrays for bank domains and sender emails'
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def domains_display(self, obj):
        """Display domains in a readable format"""
        if obj.domains:
            return ', '.join(obj.domains[:3]) + ('...' if len(obj.domains) > 3 else '')
        return 'None'
    domains_display.short_description = 'Domains'
    
    def pattern_count(self, obj):
        """Show number of email patterns for this bank"""
        count = obj.emailpattern_set.count()
        active_count = obj.emailpattern_set.filter(is_active=True).count()
        return f"{active_count}/{count}"
    pattern_count.short_description = 'Patterns (Active/Total)'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        return super().get_queryset(request).select_related('user').prefetch_related('emailpattern_set')

@admin.register(EmailPattern)
class EmailPatternAdmin(admin.ModelAdmin):
    """EmailPattern admin configuration"""
    list_display = ['bank', 'transaction_type', 'success_rate_display', 'confidence_threshold', 'is_active', 'ai_model']
    list_filter = ['transaction_type', 'is_active', 'generated_by_ai', 'ai_model', 'created_at']
    search_fields = ['bank__name', 'bank__user__username', 'transaction_type']
    readonly_fields = ['created_at', 'updated_at', 'success_rate']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('bank', 'transaction_type', 'is_active')
        }),
        ('Regex Patterns', {
            'fields': ('amount_regex', 'merchant_regex', 'date_regex', 'reference_regex'),
            'description': 'Regular expressions for extracting transaction data'
        }),
        ('Pattern Performance', {
            'fields': ('confidence_threshold', 'success_count', 'failure_count', 'success_rate')
        }),
        ('AI Metadata', {
            'fields': ('generated_by_ai', 'ai_model'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def success_rate_display(self, obj):
        """Display success rate with color coding"""
        rate = obj.success_rate
        if rate >= 80:
            color = 'green'
        elif rate >= 60:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, rate
        )
    success_rate_display.short_description = 'Success Rate'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('bank__user')

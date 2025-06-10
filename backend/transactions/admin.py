from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg
from .models import Category, Transaction, TransactionReview, UserCorrection, TemplateImprovement

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

# =====================================================
# USER FEEDBACK AND REVIEW ADMIN (FOR CELERY)
# =====================================================

@admin.register(TransactionReview)
class TransactionReviewAdmin(admin.ModelAdmin):
    """TransactionReview admin for managing user reviews"""
    list_display = ['transaction', 'status', 'review_priority', 'original_amount', 'similar_transactions_count', 'created_at']
    list_filter = ['status', 'review_priority', 'auto_apply_corrections', 'created_at']
    search_fields = ['transaction__description', 'transaction__user__username', 'review_notes']
    readonly_fields = ['transaction', 'original_amount', 'original_merchant', 'original_date', 'original_type', 'created_at']
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction', 'status', 'review_priority')
        }),
        ('Original Extracted Data', {
            'fields': ('original_amount', 'original_merchant', 'original_date', 'original_type'),
            'classes': ('collapse',)
        }),
        ('Review Process', {
            'fields': ('reviewed_at', 'review_notes')
        }),
        ('Bulk Operations', {
            'fields': ('similar_transactions_count', 'auto_apply_corrections'),
            'description': 'Options for applying corrections to similar transactions'
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_approved', 'priority_high']
    
    def mark_as_approved(self, request, queryset):
        """Admin action to approve selected reviews"""
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} reviews marked as approved.')
    mark_as_approved.short_description = 'Mark selected reviews as approved'
    
    def priority_high(self, request, queryset):
        """Admin action to set high priority"""
        updated = queryset.update(review_priority=1)
        self.message_user(request, f'{updated} reviews set to high priority.')
    priority_high.short_description = 'Set high priority for selected reviews'

@admin.register(UserCorrection)
class UserCorrectionAdmin(admin.ModelAdmin):
    """UserCorrection admin for tracking user improvements"""
    list_display = ['user', 'transaction', 'correction_type', 'field_name', 'template_updated', 'similar_transactions_updated', 'created_at']
    list_filter = ['correction_type', 'template_updated', 'created_at']
    search_fields = ['user__username', 'transaction__description', 'field_name', 'old_value', 'new_value']
    readonly_fields = ['created_at', 'applied_at']
    
    fieldsets = (
        ('Correction Information', {
            'fields': ('user', 'transaction', 'correction_type', 'field_name')
        }),
        ('Value Changes', {
            'fields': ('old_value', 'new_value')
        }),
        ('Template Impact', {
            'fields': ('template_updated', 'similar_transactions_updated', 'confidence_improvement')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'applied_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('user', 'transaction')

@admin.register(TemplateImprovement)
class TemplateImprovementAdmin(admin.ModelAdmin):
    """TemplateImprovement admin for tracking template evolution"""
    list_display = ['bank_template', 'pattern_field', 'accuracy_before', 'accuracy_after', 'transactions_reprocessed', 'ai_assisted', 'created_at']
    list_filter = ['ai_assisted', 'created_at', 'bank_template__bank']
    search_fields = ['bank_template__name', 'pattern_field', 'improvement_reason']
    readonly_fields = ['created_at', 'applied_at']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('bank_template', 'user_correction', 'pattern_field')
        }),
        ('Pattern Changes', {
            'fields': ('old_pattern', 'new_pattern', 'improvement_reason'),
            'classes': ('collapse',)
        }),
        ('Performance Impact', {
            'fields': ('accuracy_before', 'accuracy_after', 'transactions_reprocessed')
        }),
        ('AI Involvement', {
            'fields': ('ai_assisted', 'ai_confidence')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'applied_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('bank_template__bank', 'user_correction__user')

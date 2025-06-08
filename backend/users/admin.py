from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Subscription

# Create your admin configurations here.

class UserProfileInline(admin.StackedInline):
    """Inline UserProfile in User admin"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class UserAdmin(BaseUserAdmin):
    """Extended User admin with UserProfile inline"""
    inlines = (UserProfileInline,)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """UserProfile admin configuration"""
    list_display = ['user', 'timezone', 'currency', 'created_at']
    list_filter = ['timezone', 'currency', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Settings', {
            'fields': ('timezone', 'currency')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Subscription admin configuration"""
    list_display = ['user', 'plan', 'active', 'expires_at', 'created_at']
    list_filter = ['plan', 'active', 'created_at', 'expires_at']
    search_fields = ['user__username', 'user__email', 'stripe_subscription_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User & Plan', {
            'fields': ('user', 'plan', 'active')
        }),
        ('Stripe Integration', {
            'fields': ('stripe_subscription_id',)
        }),
        ('Dates', {
            'fields': ('expires_at', 'created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')

# Re-register User with our custom admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

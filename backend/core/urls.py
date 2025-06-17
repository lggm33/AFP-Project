"""
URL patterns for core app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'integrations', views.IntegrationViewSet, basename='integration')
router.register(r'bank-senders', views.BankSenderViewSet, basename='banksender')
router.register(r'user-bank-senders', views.UserBankSenderViewSet, basename='userbanksender')

urlpatterns = [
    # Health check endpoints
    path('health/', views.health_check, name='health_check'),
    path('health/detailed/', views.detailed_health_check, name='detailed_health_check'),
    path('admin/error-stats/', views.error_stats, name='error_stats'),
    
    # Include router URLs
    path('', include(router.urls)),
    
    # Message management endpoints
    path('integrations/<int:integration_id>/live-messages/', views.get_live_messages, name='get_live_messages'),
    path('integrations/<int:integration_id>/stored-messages/', views.get_stored_messages, name='get_stored_messages'),
    path('integrations/<int:integration_id>/import-messages/', views.import_messages, name='import_messages'),
    
    # Token management endpoints
    path('integrations/<int:integration_id>/refresh-tokens/', views.refresh_provider_tokens, name='refresh_provider_tokens'),
    path('integrations/<int:integration_id>/token-status/', views.get_provider_token_status, name='get_provider_token_status'),
    path('integrations/<int:integration_id>/revoke-tokens/', views.revoke_provider_tokens, name='revoke_provider_tokens'),
] 
"""
URL configuration for afp_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

# Import ViewSets
from users.views import UserViewSet, UserProfileViewSet, SubscriptionViewSet, check_auth_status, oauth_callback_exchange, user_me, debug_oauth_session, oauth_success_redirect, logout_user, refresh_token
from banking.views import BankViewSet, EmailPatternViewSet
from transactions.views import CategoryViewSet, TransactionViewSet, EmailQueueViewSet

# Create API router
router = DefaultRouter()

# Register ViewSets
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', UserProfileViewSet, basename='userprofile')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'banks', BankViewSet, basename='bank')
router.register(r'email-patterns', EmailPatternViewSet, basename='emailpattern')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'email-queue', EmailQueueViewSet, basename='emailqueue')

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # Django Allauth URLs (direct access)
    path('accounts/', include('allauth.urls')),
    
    # Multi-Provider Authentication (django-allauth)
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/auth/social/', include('allauth.socialaccount.urls')),
    
    # Legacy token auth (keeping for backward compatibility)
    path('api/auth/token/', obtain_auth_token, name='api_token_auth'),
    
    # Custom auth check endpoint (works with sessions)
    path('api/auth/check/', check_auth_status, name='check_auth_status'),
    
    # OAuth callback token exchange (Session → JWT)
    path('api/auth/oauth/exchange/', oauth_callback_exchange, name='oauth_callback_exchange'),
    
    # Current user endpoint (JWT protected)
    path('api/users/me/', user_me, name='user_me'),
    
    # Authentication management endpoints
    path('api/auth/logout/', logout_user, name='logout_user'),
    path('api/auth/refresh/', refresh_token, name='refresh_token'),
    
    # Debug OAuth session endpoint
    path('api/debug/oauth/', debug_oauth_session, name='debug_oauth_session'),
    
    # OAuth success redirect (handles LOGIN_REDIRECT_URL)
    path('auth/success/', oauth_success_redirect, name='oauth_success_redirect'),
    
    # API Endpoints
    path('api/', include(router.urls)),
    
    # Django REST Framework browsable API (for development)
    path('api-auth/', include('rest_framework.urls')),
]

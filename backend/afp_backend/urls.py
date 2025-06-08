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
from users.views import UserViewSet, UserProfileViewSet, SubscriptionViewSet
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
    
    # Multi-Provider Authentication (django-allauth)
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/auth/social/', include('allauth.socialaccount.urls')),
    
    # Legacy token auth (keeping for backward compatibility)
    path('api/auth/token/', obtain_auth_token, name='api_token_auth'),
    
    # API Endpoints
    path('api/', include(router.urls)),
    
    # Django REST Framework browsable API (for development)
    path('api-auth/', include('rest_framework.urls')),
]

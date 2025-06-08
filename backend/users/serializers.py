from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Subscription
from dj_rest_auth.registration.serializers import RegisterSerializer

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['user', 'timezone', 'currency', 'created_at']
        read_only_fields = ['created_at']

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating UserProfile"""
    class Meta:
        model = UserProfile
        fields = ['timezone', 'currency']

class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription model"""
    user = UserSerializer(read_only=True)
    plan_display = serializers.CharField(source='get_plan_display', read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'plan', 'plan_display', 'active', 
            'stripe_subscription_id', 'expires_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class UserDetailSerializer(serializers.ModelSerializer):
    """Complete user information with profile and subscription"""
    profile = UserProfileSerializer(source='userprofile', read_only=True)
    subscription = SubscriptionSerializer(source='subscription_set', many=True, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'date_joined', 'profile', 'subscription'
        ]
        read_only_fields = ['id', 'date_joined']

class CustomRegisterSerializer(RegisterSerializer):
    """Custom registration serializer for django-allauth"""
    first_name = serializers.CharField(required=False, max_length=30)
    last_name = serializers.CharField(required=False, max_length=30)
    
    def save(self, request):
        user = super().save(request)
        user.first_name = self.validated_data.get('first_name', '')
        user.last_name = self.validated_data.get('last_name', '')
        user.save()
        
        # Create UserProfile automatically
        UserProfile.objects.get_or_create(user=user)
        
        return user 
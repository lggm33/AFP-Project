from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile, Subscription
from dj_rest_auth.serializers import UserDetailsSerializer as BaseUserDetailsSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer as BaseRegisterSerializer
from dj_rest_auth.serializers import PasswordResetSerializer as BasePasswordResetSerializer
from dj_rest_auth.serializers import PasswordResetConfirmSerializer as BasePasswordResetConfirmSerializer
from dj_rest_auth.serializers import PasswordChangeSerializer as BasePasswordChangeSerializer

User = get_user_model()

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

class UserDetailsSerializer(BaseUserDetailsSerializer):
    class Meta(BaseUserDetailsSerializer.Meta):
        fields = ('id', 'email', 'first_name', 'last_name', 'is_active', 'date_joined')
        read_only_fields = ('email', 'date_joined')

class CustomRegisterSerializer(BaseRegisterSerializer):
    email = serializers.EmailField(required=True)
    password1 = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    def get_cleaned_data(self):
        return {
            'email': self.validated_data.get('email', ''),
            'password1': self.validated_data.get('password1', ''),
            'password2': self.validated_data.get('password2', ''),
        }

    def save(self, request):
        user = super().save(request)
        user.username = user.email  # Usar email como username
        user.save()
        return user

class CustomPasswordResetSerializer(BasePasswordResetSerializer):
    email = serializers.EmailField(required=True)

class CustomPasswordResetConfirmSerializer(BasePasswordResetConfirmSerializer):
    new_password1 = serializers.CharField(write_only=True, required=True)
    new_password2 = serializers.CharField(write_only=True, required=True)

class CustomPasswordChangeSerializer(BasePasswordChangeSerializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password1 = serializers.CharField(write_only=True, required=True)
    new_password2 = serializers.CharField(write_only=True, required=True)

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
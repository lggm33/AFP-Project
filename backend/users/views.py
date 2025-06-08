from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import UserProfile, Subscription
from .serializers import (
    UserSerializer, UserProfileSerializer, UserProfileUpdateSerializer,
    SubscriptionSerializer, UserDetailSerializer
)

# Create your views here.

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for User model - Read only access to user information
    """
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own information"""
        return User.objects.filter(id=self.request.user.id).select_related('userprofile').prefetch_related('subscription_set')
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user information"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Update user profile settings"""
        try:
            profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist
            profile = UserProfile.objects.create(user=request.user)
        
        serializer = UserProfileUpdateSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserProfileSerializer(profile).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserProfile model
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Users can only access their own profile"""
        return UserProfile.objects.filter(user=self.request.user).select_related('user')
    
    def perform_create(self, serializer):
        """Automatically assign current user to profile"""
        serializer.save(user=self.request.user)

class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Subscription model - Read only
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own subscriptions"""
        return Subscription.objects.filter(user=self.request.user).select_related('user')
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current active subscription"""
        subscription = Subscription.objects.filter(
            user=request.user, 
            active=True
        ).first()
        
        if subscription:
            serializer = self.get_serializer(subscription)
            return Response(serializer.data)
        else:
            return Response({
                'plan': 'free',
                'active': True,
                'message': 'No active subscription found, using free plan'
            })

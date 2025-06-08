from django.shortcuts import render, redirect
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from .models import UserProfile, Subscription
from .serializers import (
    UserSerializer, UserProfileSerializer, UserProfileUpdateSerializer,
    SubscriptionSerializer, UserDetailSerializer
)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from rest_framework_simplejwt.tokens import RefreshToken
from django.middleware.csrf import get_token
from django.utils import timezone
from urllib.parse import urlencode
from allauth.socialaccount.models import SocialAccount
import logging

logger = logging.getLogger(__name__)

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

@csrf_exempt
def check_auth_status(request):
    """Simple endpoint to check if user is authenticated via session"""
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
            }
        })
    else:
        return JsonResponse({
            'authenticated': False,
            'user': None
        }, status=401)

@csrf_exempt  
def oauth_callback_exchange(request):
    """
    Secure endpoint to exchange Django session authentication for JWT tokens
    This is called after successful OAuth to get tokens for the frontend
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Not authenticated',
            'message': 'User must be authenticated via session first'
        }, status=401)
    
    try:
        # Generate JWT tokens for the authenticated user
        refresh = RefreshToken.for_user(request.user)
        access_token = refresh.access_token
        
        # Get user data
        user_data = {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        }
        
        # Check if user has social accounts
        social_accounts = []
        for social_account in request.user.socialaccount_set.all():
            social_accounts.append({
                'provider': social_account.provider,
                'uid': social_account.uid,
                'email': social_account.extra_data.get('email'),
            })
        
        response_data = {
            'success': True,
            'user': user_data,
            'social_accounts': social_accounts,
            'tokens': {
                'access': str(access_token),
                'refresh': str(refresh),
            }
        }
        
        # Create response with tokens in cookies (secure) and JSON (for JS access)
        response = JsonResponse(response_data)
        
        # Set secure HTTP-only cookies for tokens
        response.set_cookie(
            'afp_access_token',
            str(access_token),
            max_age=3600,  # 1 hour
            httponly=False,  # Allow JS access for API calls
            secure=False,  # Set to True in production with HTTPS
            samesite='Lax'
        )
        
        response.set_cookie(
            'afp_refresh_token', 
            str(refresh),
            max_age=604800,  # 7 days
            httponly=True,   # More secure for refresh token
            secure=False,    # Set to True in production
            samesite='Lax'
        )
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'error': 'Token generation failed',
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_me(request):
    """Get current user info - used for token verification"""
    return Response({
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
    })

@csrf_exempt
def debug_oauth_session(request):
    """Debug endpoint to check session status during OAuth callback"""
    debug_info = {
        'timestamp': timezone.now().isoformat(),
        'method': request.method,
        'path': request.path,
        'user_authenticated': request.user.is_authenticated,
        'user_id': getattr(request.user, 'id', None),
        'user_email': getattr(request.user, 'email', None),
        'session_key': request.session.session_key,
        'session_data': dict(request.session.items()) if hasattr(request.session, 'items') else {},
        'cookies': dict(request.COOKIES),
        'headers': {
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
            'origin': request.META.get('HTTP_ORIGIN', ''),
        }
    }
    
    # Get social accounts if user is authenticated
    if request.user.is_authenticated:
        social_accounts = []
        for acc in request.user.socialaccount_set.all():
            social_accounts.append({
                'provider': acc.provider,
                'uid': acc.uid,
                'email': acc.extra_data.get('email'),
                'last_login': acc.last_login.isoformat() if acc.last_login else None
            })
        debug_info['social_accounts'] = social_accounts
    
    return JsonResponse(debug_info, json_dumps_params={'indent': 2})

@csrf_exempt
def oauth_success_redirect(request):
    """
    Handle successful OAuth authentication and redirect to frontend with JWT tokens
    This is the target for LOGIN_REDIRECT_URL
    """
    if not request.user.is_authenticated:
        # If user is not authenticated, redirect to frontend login with error
        return redirect('http://localhost:3000/login?error=auth_failed')
    
    try:
        # Generate JWT tokens for the authenticated user
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Get user data
        user_data = {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        }
        
        # Get social accounts
        social_accounts = []
        for social_account in request.user.socialaccount_set.all():
            social_accounts.append({
                'provider': social_account.provider,
                'uid': social_account.uid,
                'email': social_account.extra_data.get('email'),
            })
        
        # Create query parameters with tokens and user data
        params = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_id': user_data['id'],
            'email': user_data['email'],
            'username': user_data['username'],
            'providers': ','.join([acc['provider'] for acc in social_accounts])
        }
        
        # Redirect to frontend with tokens in URL
        redirect_url = f"http://localhost:3000/auth/callback?{urlencode(params)}"
        
        response = redirect(redirect_url)
        
        # Also set cookies as backup
        response.set_cookie(
            'afp_access_token',
            access_token,
            max_age=3600,
            httponly=False,
            secure=False,
            samesite='Lax'
        )
        
        response.set_cookie(
            'afp_refresh_token',
            refresh_token,
            max_age=604800,
            httponly=True,
            secure=False,
            samesite='Lax'
        )
        
        return response
        
    except Exception as e:
        # If token generation fails, redirect with error
        error_params = {'error': 'token_generation_failed', 'message': str(e)}
        redirect_url = f"http://localhost:3000/login?{urlencode(error_params)}"
        return redirect(redirect_url)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """Logout user and blacklist refresh token"""
    try:
        # Get refresh token from request
        refresh_token = request.data.get('refresh_token')
        
        if refresh_token:
            try:
                # Create RefreshToken instance and blacklist it
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info(f"Successfully blacklisted refresh token for user {request.user.username}")
            except Exception as e:
                logger.warning(f"Failed to blacklist refresh token: {str(e)}")
                # Continue with logout even if blacklisting fails
        
        return Response({
            'message': 'Successfully logged out',
            'detail': 'Refresh token has been blacklisted'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in logout: {str(e)}")
        return Response({
            'message': 'Logged out successfully',
            'detail': 'Token blacklisting may have failed but user is logged out'
        }, status=status.HTTP_200_OK)

@api_view(['POST'])
def refresh_token(request):
    """Refresh access token using refresh token"""
    try:
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Validate and refresh the token
            token = RefreshToken(refresh_token)
            
            # Check if token is blacklisted
            if hasattr(token, 'check_blacklist'):
                token.check_blacklist()
            
            # Generate new access token
            new_access_token = str(token.access_token)
            
            # Optionally rotate refresh token
            if hasattr(token, 'set_jti'):
                token.set_jti()
                new_refresh_token = str(token)
            else:
                new_refresh_token = refresh_token
            
            return Response({
                'access_token': new_access_token,
                'refresh_token': new_refresh_token,
                'token_type': 'Bearer'
            }, status=status.HTTP_200_OK)
            
        except Exception as token_error:
            logger.warning(f"Token refresh failed: {str(token_error)}")
            return Response({
                'error': 'Invalid or expired refresh token',
                'detail': str(token_error)
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        logger.error(f"Error in refresh_token: {str(e)}")
        return Response({'error': 'Token refresh failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

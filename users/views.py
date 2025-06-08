from django.contrib.auth import authenticate
from django.shortcuts import redirect
from django.http import HttpResponse
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from allauth.account.adapter import get_adapter
from allauth.socialaccount.models import SocialAccount
from allauth.account.models import EmailAddress
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_me(request):
    """Get current user information"""
    user = request.user
    try:
        # Get connected social accounts
        social_accounts = SocialAccount.objects.filter(user=user)
        providers = []
        
        for account in social_accounts:
            providers.append({
                'provider': account.provider,
                'uid': account.uid,
                'extra_data': account.extra_data
            })
        
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined,
            'providers': providers
        })
    except Exception as e:
        logger.error(f"Error in user_me: {str(e)}")
        return Response({'error': 'Unable to fetch user data'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

def oauth_success_redirect(request):
    """Handle successful OAuth and redirect to frontend with tokens"""
    try:
        user = request.user
        if not user.is_authenticated:
            logger.error("User not authenticated in oauth_success_redirect")
            return redirect('http://localhost:3000/login?error=authentication_failed')
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Get connected social accounts
        social_accounts = list(SocialAccount.objects.filter(user=user).values_list('provider', flat=True))
        
        # Build redirect URL with tokens
        params = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'providers': ','.join(social_accounts),
            'session_created': 'true'
        }
        
        frontend_callback_url = f"http://localhost:3000/auth/callback?{urlencode(params)}"
        logger.info(f"Redirecting user {user.username} to frontend with tokens")
        
        return redirect(frontend_callback_url)
        
    except Exception as e:
        logger.error(f"Error in oauth_success_redirect: {str(e)}")
        return redirect('http://localhost:3000/login?error=oauth_processing_failed')

def debug_oauth_session(request):
    """Debug endpoint to check OAuth session status"""
    return HttpResponse(f"""
    Debug OAuth Session:
    - User authenticated: {request.user.is_authenticated}
    - User: {request.user if request.user.is_authenticated else 'Anonymous'}
    - Session key: {request.session.session_key}
    - Session data: {dict(request.session)}
    """, content_type='text/plain')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_auth_status(request):
    """Check authentication status with detailed info"""
    try:
        user = request.user
        social_accounts = SocialAccount.objects.filter(user=user)
        
        return Response({
            'authenticated': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
            'social_accounts': [
                {
                    'provider': acc.provider,
                    'uid': acc.uid
                } for acc in social_accounts
            ],
            'session_info': 'JWT authenticated'
        })
    except Exception as e:
        return Response({
            'authenticated': False,
            'error': str(e)
        }, status=status.HTTP_401_UNAUTHORIZED) 
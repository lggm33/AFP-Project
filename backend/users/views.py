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
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from .auth_managers import AppAuthManager

logger = logging.getLogger(__name__)

# Crear instancia global del manager
app_auth_manager = AppAuthManager()

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
            # Usar el nuevo manager para revocar
            app_auth_manager.revoke_app_tokens(refresh_token)
            logger.info(f"Successfully blacklisted refresh token for user {request.user.username}")
        
        return Response({
            'detail': 'Refresh token has been blacklisted'
        })
        
    except Exception as e:
        logger.warning(f"Failed to blacklist refresh token: {str(e)}")
        return Response({
            'detail': 'Logout completed but token blacklist failed'
        })

@api_view(['POST'])
def refresh_token(request):
    """Refresh access token using refresh token"""
    try:
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Usar el nuevo manager para refresh
        new_tokens = app_auth_manager.refresh_app_tokens(refresh_token)
        
        if not new_tokens:
            return Response({
                'error': 'Invalid or expired refresh token',
                'message': 'Please login again'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        return Response({
            'access_token': new_tokens['access_token'],
            'refresh_token': new_tokens['refresh_token']
        })
        
    except Exception as e:
        logger.error(f"Error in refresh_token: {str(e)}")
        return Response({
            'error': 'Token refresh failed',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gmail_test_connection(request):
    """Test Gmail API connection for the current user"""
    try:
        from core.gmail_service import GmailService
        
        gmail_service = GmailService(request.user)
        result = gmail_service.test_connection()
        
        if result['success']:
            return Response({
                'success': True,
                'message': 'Gmail connection successful',
                'data': result
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Gmail connection failed',
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Gmail test connection error for user {request.user.username}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Gmail test failed',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gmail_recent_messages(request):
    """Get recent Gmail messages for the current user"""
    try:
        from core.gmail_service import GmailService
        
        # Get query parameters
        max_results = int(request.GET.get('max_results', 20))
        days_back = int(request.GET.get('days_back', 7))
        
        # Validate parameters
        max_results = min(max_results, 100)  # Limit to 100
        days_back = min(days_back, 90)  # Limit to 90 days
        
        gmail_service = GmailService(request.user)
        messages = gmail_service.get_recent_messages(max_results, days_back)
        
        return Response({
            'success': True,
            'count': len(messages),
            'messages': messages,
            'filters': {
                'max_results': max_results,
                'days_back': days_back
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Gmail recent messages error for user {request.user.username}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to get recent messages',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gmail_banking_messages(request):
    """Get potential banking messages from Gmail"""
    try:
        from core.gmail_service import GmailService
        
        # Get query parameters
        max_results = int(request.GET.get('max_results', 50))
        days_back = int(request.GET.get('days_back', 30))
        
        # Validate parameters
        max_results = min(max_results, 200)  # Limit to 200
        days_back = min(days_back, 90)  # Limit to 90 days
        
        gmail_service = GmailService(request.user)
        banking_messages = gmail_service.get_banking_messages(max_results, days_back)
        
        # Add some basic analysis
        analysis = {
            'total_messages': len(banking_messages),
            'date_range': {
                'start': (datetime.now() - timedelta(days=days_back)).isoformat(),
                'end': datetime.now().isoformat()
            },
            'senders': {},
            'keywords_found': set()
        }
        
        # Analyze senders and keywords
        for msg in banking_messages:
            sender = msg.get('sender', 'unknown')
            if sender in analysis['senders']:
                analysis['senders'][sender] += 1
            else:
                analysis['senders'][sender] = 1
        
        # Convert set to list for JSON serialization
        analysis['keywords_found'] = list(analysis['keywords_found'])
        
        return Response({
            'success': True,
            'analysis': analysis,
            'messages': banking_messages,
            'filters': {
                'max_results': max_results,
                'days_back': days_back
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Gmail banking messages error for user {request.user.username}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to get banking messages',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def gmail_process_banking_messages(request):
    """Process banking messages and extract transaction data"""
    try:
        from core.gmail_service import GmailService
        
        # Get parameters
        days_back = int(request.data.get('days_back', 30))
        process_all = request.data.get('process_all', False)
        
        days_back = min(days_back, 90)  # Limit to 90 days
        
        gmail_service = GmailService(request.user)
        banking_messages = gmail_service.get_banking_messages(100, days_back)
        
        # Basic processing results
        processing_results = {
            'total_messages_found': len(banking_messages),
            'processed_messages': 0,
            'potential_transactions': [],
            'errors': []
        }
        
        # Simple transaction detection (placeholder for AI processing)
        for msg in banking_messages:
            try:
                # Look for transaction patterns in the message
                transaction_data = _extract_basic_transaction_data(msg)
                
                if transaction_data:
                    processing_results['potential_transactions'].append({
                        'message_id': msg['id'],
                        'sender': msg['sender'],
                        'subject': msg['subject'],
                        'timestamp': msg['timestamp'].isoformat(),
                        'transaction_data': transaction_data
                    })
                
                processing_results['processed_messages'] += 1
                
            except Exception as e:
                processing_results['errors'].append({
                    'message_id': msg['id'],
                    'error': str(e)
                })
        
        return Response({
            'success': True,
            'message': f'Processed {processing_results["processed_messages"]} banking messages',
            'results': processing_results
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Gmail process banking messages error for user {request.user.username}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to process banking messages',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _extract_basic_transaction_data(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Basic transaction data extraction (placeholder for AI processing)"""
    try:
        text_content = (message.get('subject', '') + ' ' + message.get('body', '')).lower()
        
        # Simple regex patterns for common transaction data
        import re
        
        # Amount patterns (₡, $, colones, dollars)
        amount_patterns = [
            r'₡\s*(\d{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{2})?)',  # Costa Rican colones
            r'\$\s*(\d{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{2})?)',  # US dollars
            r'(\d{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{2})?)\s*colones',  # Colones word
            r'(\d{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{2})?)\s*dólares',  # Dollars word
        ]
        
        # Transaction type patterns
        transaction_types = {
            'purchase': ['compra', 'purchase', 'pago', 'payment'],
            'withdrawal': ['retiro', 'withdrawal', 'cajero', 'atm'],
            'transfer': ['transferencia', 'transfer', 'envío', 'envio'],
            'deposit': ['depósito', 'deposito', 'deposit', 'abono']
        }
        
        extracted_data = {}
        
        # Try to extract amount
        for pattern in amount_patterns:
            match = re.search(pattern, text_content)
            if match:
                extracted_data['amount'] = match.group(1).replace(',', '')
                break
        
        # Try to determine transaction type
        for trans_type, keywords in transaction_types.items():
            for keyword in keywords:
                if keyword in text_content:
                    extracted_data['transaction_type'] = trans_type
                    break
            if 'transaction_type' in extracted_data:
                break
        
        # Extract merchant/location (basic pattern)
        merchant_patterns = [
            r'establecimiento:?\s*([a-zA-Z0-9\s]+)',
            r'comercio:?\s*([a-zA-Z0-9\s]+)',
            r'merchant:?\s*([a-zA-Z0-9\s]+)',
        ]
        
        for pattern in merchant_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                extracted_data['merchant'] = match.group(1).strip()
                break
        
        # Only return if we found meaningful data
        if len(extracted_data) >= 2:  # At least amount and type, or similar
            extracted_data['confidence'] = 'low'  # Mark as basic extraction
            extracted_data['extraction_method'] = 'regex'
            return extracted_data
        
        return None
        
    except Exception as e:
        logger.warning(f"Error extracting transaction data: {str(e)}")
        return None

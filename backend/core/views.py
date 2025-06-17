from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from .models import Integration, EmailImportJob, Email, BankSender, UserBankSender
from .providers.gmail_provider import GmailProvider
from .serializers import (
    IntegrationSerializer, IntegrationCreateSerializer, EmailSerializer, 
    EmailDetailSerializer, EmailImportRequestSerializer, BankSenderSerializer,
    BankSenderCreateSerializer, UserBankSenderSerializer, UserBankSenderCreateSerializer,
    BankSenderSearchSerializer
)
from banking.models import Bank
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from .auth_managers import EmailProviderAuthManager
from django.http import JsonResponse
from django.utils import timezone
from core.exceptions import (
    AFPBaseException, IntegrationNotFoundError, IntegrationInactiveError,
    GmailAPIError, BusinessLogicError, ValidationError, wrap_exception
)
from core.logging.structured_logger import structured_logger, track_error
from core.health.health_checker import get_system_health, is_system_healthy

logger = logging.getLogger(__name__)

# Global provider auth manager
provider_auth_manager = EmailProviderAuthManager()

# Add health check endpoints at the top
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Simple health check endpoint"""
    try:
        if is_system_healthy():
            return JsonResponse({
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'service': 'afp-backend'
            })
        else:
            return JsonResponse({
                'status': 'unhealthy',
                'timestamp': timezone.now().isoformat(),
                'service': 'afp-backend'
            }, status=503)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'timestamp': timezone.now().isoformat(),
            'service': 'afp-backend'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def detailed_health_check(request):
    """Detailed health check with all system components"""
    try:
        health_data = get_system_health()
        
        if health_data['overall_status'] == 'healthy':
            status_code = 200
        elif health_data['overall_status'] == 'degraded':
            status_code = 200  # Still OK but with warnings
        else:
            status_code = 503  # Service unavailable
        
        return JsonResponse(health_data, status=status_code)
        
    except Exception as e:
        structured_logger.error("Health check failed", exception=e)
        return JsonResponse({
            'status': 'error',
            'message': 'Health check system failed',
            'timestamp': timezone.now().isoformat()
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def error_stats(request):
    """Get error statistics (admin only)"""
    try:
        if not request.user.is_staff:
            raise PermissionDeniedError("Only admin users can access error statistics")
        
        from core.logging.structured_logger import error_tracker
        stats = error_tracker.get_error_stats()
        
        return JsonResponse({
            'success': True,
            'data': stats,
            'timestamp': timezone.now().isoformat()
        })
        
    except AFPBaseException as e:
        track_error(e, user=request.user, request_id=getattr(request, 'request_id', None))
        return JsonResponse(e.to_dict(), status=e.http_status)
    except Exception as e:
        afp_exception = categorize_exception(e)
        track_error(afp_exception, user=request.user, request_id=getattr(request, 'request_id', None))
        return JsonResponse(afp_exception.to_dict(), status=afp_exception.http_status)

class IntegrationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Integration model - User email integrations
    """
    serializer_class = IntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own integrations"""
        return Integration.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Use different serializers for create vs list/retrieve"""
        if self.action == 'create':
            return IntegrationCreateSerializer
        return IntegrationSerializer
    
    def perform_create(self, serializer):
        """Automatically assign current user to integration"""
        serializer.save(user=self.request.user, updated_by=self.request.user)
    
    def perform_update(self, serializer):
        """Track who updated the integration"""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test connection for a specific integration"""
        integration = self.get_object()
        try:
            if integration.provider == 'gmail':
                provider = GmailProvider(integration)
                result = provider.test_connection()
                
                if result['success']:
                    return Response({
                        'success': True,
                        'message': f'{integration.provider.title()} connection successful',
                        'data': result
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'message': f'{integration.provider.title()} connection failed',
                        'error': result['error']
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'success': False,
                    'message': f'Provider {integration.provider} not supported yet'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Connection test error for integration {integration.id}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Connection test failed',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    

def get_user_bank_senders(user, integration):
    """Helper function to get user's active bank senders for an integration"""
    active_senders = UserBankSender.objects.filter(
        user=user,
        integration=integration,
        is_active=True
    ).select_related('bank_sender')
    
    return [ubs.bank_sender.sender_email for ubs in active_senders]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_live_messages(request, integration_id):
    """Get messages directly from Gmail API in real-time with robust error handling"""
    request_id = getattr(request, 'request_id', None)
    
    try:
        # Log business event
        structured_logger.log_business_event(
            event='get_live_messages_started',
            entity='integration',
            entity_id=integration_id,
            user=request.user,
            request_id=request_id,
            extra_data={'message_type': request.GET.get('type', 'all')}
        )
        
        # Get and validate integration
        try:
            integration = Integration.objects.get(
                id=integration_id,
                user=request.user,
                provider='gmail',
                is_active=True
            )
        except Integration.DoesNotExist:
            raise IntegrationNotFoundError(
                message=f"Gmail integration {integration_id} not found or inactive",
                context={'integration_id': integration_id, 'user_id': request.user.id, 'provider': 'gmail'}
            )
        
        # Validate parameters
        try:
            message_type = request.GET.get('type', 'all')  # all, banking
            days_back = min(int(request.GET.get('days_back', 30)), 90)
            page = max(int(request.GET.get('page', 1)), 1)
            page_size = min(int(request.GET.get('page_size', 50)), 100)
            sender_filter = request.GET.get('sender_filter')
        except (ValueError, TypeError) as e:
            raise ValidationError(
                message="Invalid request parameters",
                context={
                    'days_back': request.GET.get('days_back'),
                    'page': request.GET.get('page'),
                    'page_size': request.GET.get('page_size')
                },
                original_exception=e
            )
        
        # Initialize Gmail provider
        try:
            provider = GmailProvider(integration)
        except Exception as e:
            raise GmailAPIError(
                message=f"Failed to initialize Gmail provider for integration {integration_id}",
                context={'integration_id': integration_id, 'email_address': integration.email_address},
                original_exception=e
            )
        
        # Handle different message types
        if message_type == 'banking':
            # Get user's active bank senders for filtering
            user_bank_senders = get_user_bank_senders(request.user, integration)
            if not user_bank_senders:
                raise BusinessLogicError(
                    message="No active bank senders configured for this integration",
                    context={'integration_id': integration_id, 'user_id': request.user.id}
                )
            
            try:
                result = provider.get_banking_messages(
                    days_back=days_back,
                    user_bank_senders=user_bank_senders,
                    page=page,
                    page_size=page_size
                )
            except Exception as e:
                raise GmailAPIError(
                    message="Failed to fetch banking messages from Gmail API",
                    context={
                        'integration_id': integration_id,
                        'message_type': 'banking',
                        'user_bank_senders_count': len(user_bank_senders)
                    },
                    original_exception=e
                )
            
            # Check if provider returned an error
            if not result.get('success', True) and 'error' in result:
                raise GmailAPIError(
                    message=f"Gmail API error: {result['error']}",
                    context={'integration_id': integration_id, 'provider_error': result['error']}
                )
            
            # Enrich messages with bank sender details
            try:
                for message in result['messages']:
                    message['integration_email'] = integration.email_address
                    
                    # Find which bank sender this message came from
                    sender_email = message.get('sender', '').lower()
                    active_senders = UserBankSender.objects.filter(
                        user=request.user,
                        integration=integration,
                        is_active=True
                    ).select_related('bank_sender')
                    
                    for ubs in active_senders:
                        if ubs.bank_sender.sender_email.lower() in sender_email:
                            message['bank_sender_details'] = {
                                'id': ubs.bank_sender.id,
                                'bank_name': ubs.bank_sender.bank.name if ubs.bank_sender.bank else 'Unknown',
                                'sender_name': ubs.bank_sender.sender_name,
                                'sender_email': ubs.bank_sender.sender_email,
                                'confidence_score': ubs.effective_confidence
                            }
                            break
                
                # Add bank sender summary
                bank_sender_summary = []
                active_senders = UserBankSender.objects.filter(
                    user=request.user,
                    integration=integration,
                    is_active=True
                ).select_related('bank_sender')
                
                for ubs in active_senders:
                    bank_sender_summary.append({
                        'id': ubs.bank_sender.id,
                        'bank_name': ubs.bank_sender.bank.name if ubs.bank_sender.bank else 'Unknown',
                        'sender_name': ubs.bank_sender.sender_name,
                        'sender_email': ubs.bank_sender.sender_email,
                        'is_active': ubs.is_active,
                        'confidence_score': ubs.effective_confidence
                    })
                
                response_data = {
                    'success': True,
                    'data': result,
                    'integration': {
                        'id': integration.id,
                        'email_address': integration.email_address
                    },
                    'bank_senders': bank_sender_summary
                }
            except Exception as e:
                raise BusinessLogicError(
                    message="Failed to enrich messages with bank sender details",
                    context={'integration_id': integration_id, 'message_count': len(result.get('messages', []))},
                    original_exception=e
                )
            
        else:
            # Handle 'all' and 'recent' message types
            try:
                result = provider.get_all_messages(
                    days_back=days_back,
                    sender_filter=sender_filter,
                    page=page,
                    page_size=page_size
                )
            except Exception as e:
                raise GmailAPIError(
                    message="Failed to fetch messages from Gmail API",
                    context={'integration_id': integration_id, 'message_type': message_type},
                    original_exception=e
                )
            
            # Add integration info to each message
            for message in result['messages']:
                message['integration_email'] = integration.email_address
            
            response_data = {
                'success': True,
                'data': result,
                'integration': {
                    'id': integration.id,
                    'email_address': integration.email_address
                }
            }
        
        # Log successful completion
        structured_logger.log_business_event(
            event='get_live_messages_completed',
            entity='integration',
            entity_id=integration_id,
            user=request.user,
            request_id=request_id,
            extra_data={
                'message_count': len(response_data['data'].get('messages', [])),
                'total_count': response_data['data'].get('total_count', 0),
                'message_type': message_type
            }
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except AFPBaseException as e:
        # Track and log AFP exceptions
        track_error(e, user=request.user, request_id=request_id)
        return Response({
            'success': False,
            'error': e.to_dict()
        }, status=e.http_status)
        
    except Exception as e:
        # Convert and track unknown exceptions
        afp_exception = categorize_exception(e)
        afp_exception.context.update({'integration_id': integration_id, 'endpoint': 'get_live_messages'})
        track_error(afp_exception, user=request.user, request_id=request_id)
        return Response({
            'success': False,
            'error': afp_exception.to_dict()
        }, status=afp_exception.http_status)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stored_messages(request, integration_id):
    """Get messages already saved in database for a specific integration"""
    try:
        # Get and validate integration
        integration = Integration.objects.get(
            id=integration_id,
            user=request.user
        )
        
        # Get base queryset
        emails = Email.objects.filter(
            integration=integration
        ).select_related('integration').order_by('-created_at')
        
        # Apply filters
        message_type = request.GET.get('type', 'all')
        processed_only = request.GET.get('processed_only')
        
        if processed_only == 'true':
            emails = emails.filter(processed_at__isnull=False)
        elif processed_only == 'false':
            emails = emails.filter(processed_at__isnull=True)
        
        # For banking type, filter by bank senders
        if message_type == 'banking':
            user_bank_senders = get_user_bank_senders(request.user, integration)
            if user_bank_senders:
                # Create Q objects for each bank sender email
                from django.db.models import Q
                q_objects = Q()
                for sender_email in user_bank_senders:
                    q_objects |= Q(sender__icontains=sender_email)
                emails = emails.filter(q_objects)
        
        # Pagination
        page = max(int(request.GET.get('page', 1)), 1)
        page_size = min(int(request.GET.get('page_size', 50)), 200)
        offset = (page - 1) * page_size
        
        total_count = emails.count()
        emails_page = emails[offset:offset + page_size]
        
        # Serialize email data
        emails_data = []
        for email in emails_page:
            emails_data.append({
                'id': email.id,
                'integration': {
                    'id': email.integration.id,
                    'email_address': email.integration.email_address,
                    'provider': email.integration.provider
                },
                'provider_message_id': email.provider_message_id,
                'sender': email.sender,
                'recipient': email.recipient,
                'subject': email.subject,
                'body': email.body[:500] + '...' if len(email.body) > 500 else email.body,
                'attachment_count': email.attachment_count,
                'created_at': email.created_at,
                'processed_at': email.processed_at,
                'process_by': email.process_by
            })
        
        return Response({
            'success': True,
            'total_count': total_count,
            'count': len(emails_data),
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'emails': emails_data,
            'integration': {
                'id': integration.id,
                'email_address': integration.email_address,
                'provider': integration.provider
            }
        }, status=status.HTTP_200_OK)
        
    except Integration.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Integration not found or access denied'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting stored messages for integration {integration_id}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to get stored messages',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_messages(request, integration_id):
    """Import messages from Gmail API to database with automatic deduplication"""
    try:
        # Get and validate integration
        integration = Integration.objects.get(
            id=integration_id,
            user=request.user,
            provider='gmail',
            is_active=True
        )
        
        # Parse parameters
        message_type = request.data.get('type', 'banking')  # all, banking, recent
        days_back = min(int(request.data.get('days_back', 30)), 90)
        max_results = min(int(request.data.get('max_results', 100)), 500)
        
        import_results = {
            'integration_id': integration.id,
            'emails_found': 0,
            'emails_imported': 0,
            'emails_skipped': 0,
            'errors': []
        }
        
        try:
            provider = GmailProvider(integration)
            
            # Get messages based on import type
            if message_type == 'banking':
                user_bank_senders = get_user_bank_senders(request.user, integration)
                if not user_bank_senders:
                    return Response({
                        'success': False,
                        'message': 'No active bank senders configured for this integration'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Get messages without pagination for import
                result = provider.get_banking_messages(
                    days_back=days_back,
                    user_bank_senders=user_bank_senders,
                    page=1,
                    page_size=max_results
                )
                messages = result.get('messages', [])
            else:
                # Get all messages
                result = provider.get_all_messages(
                    days_back=days_back,
                    page=1,
                    page_size=max_results
                )
                messages = result.get('messages', [])
            
            import_results['emails_found'] = len(messages)
            
            # Save emails to database with deduplication
            for msg_data in messages:
                try:
                    # Check if email already exists (deduplication)
                    existing_email = Email.objects.filter(
                        integration=integration,
                        provider_message_id=msg_data.get('provider_message_id', msg_data.get('id'))
                    ).first()
                    
                    if existing_email:
                        import_results['emails_skipped'] += 1
                        continue
                    
                    # Create new email record
                    email = Email.objects.create(
                        integration=integration,
                        provider_message_id=msg_data.get('provider_message_id', msg_data.get('id')),
                        sender=msg_data.get('sender', ''),
                        recipient=msg_data.get('recipient', ''),
                        subject=msg_data.get('subject', ''),
                        body=msg_data.get('body', ''),
                        raw_headers=msg_data.get('raw_headers', {}),
                        attachment_count=msg_data.get('attachment_count', 0)
                    )
                    
                    import_results['emails_imported'] += 1
                    
                except Exception as e:
                    import_results['errors'].append({
                        'message_id': msg_data.get('provider_message_id', msg_data.get('id')),
                        'error': str(e)
                    })
            
        except Exception as e:
            import_results['errors'].append({
                'error': f'Provider error: {str(e)}'
            })
        
        return Response({
            'success': True,
            'message': f'Import completed: {import_results["emails_imported"]} emails imported, {import_results["emails_skipped"]} duplicates skipped',
            'results': import_results
        }, status=status.HTTP_200_OK)
        
    except Integration.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Integration not found or access denied'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Import messages error for integration {integration_id}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Email import failed',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BankSenderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for BankSender model - Global bank senders
    """
    serializer_class = BankSenderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """All users can see all bank senders"""
        return BankSender.objects.select_related('bank', 'created_by', 'verified_by')
    
    def get_serializer_class(self):
        """Use different serializers for create vs list/retrieve"""
        if self.action == 'create':
            return BankSenderCreateSerializer
        return BankSenderSerializer
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a bank sender (admin action)"""
        bank_sender = self.get_object()
        bank_sender.is_verified = True
        bank_sender.verified_by = request.user
        bank_sender.verified_at = datetime.now()
        bank_sender.save()
        
        return Response({
            'success': True,
            'message': f'Bank sender {bank_sender.sender_email} verified successfully'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search bank senders by email, domain, or bank name"""
        serializer = BankSenderSearchSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.get_queryset()
        
        # Apply filters
        if serializer.validated_data.get('email'):
            queryset = queryset.filter(sender_email__icontains=serializer.validated_data['email'])
        
        if serializer.validated_data.get('domain'):
            queryset = queryset.filter(sender_domain__icontains=serializer.validated_data['domain'])
        
        if serializer.validated_data.get('bank_name'):
            queryset = queryset.filter(bank__name__icontains=serializer.validated_data['bank_name'])
        
        if serializer.validated_data.get('verified_only'):
            queryset = queryset.filter(is_verified=True)
        
        # Limit results
        queryset = queryset[:20]
        
        serializer = BankSenderSerializer(queryset, many=True)
        return Response({
            'success': True,
            'count': len(serializer.data),
            'results': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular/verified bank senders"""
        from django.db import models
        queryset = self.get_queryset().filter(
            models.Q(is_verified=True) | models.Q(total_emails_processed__gte=50)
        ).order_by('-total_emails_processed', '-is_verified')[:20]
        
        serializer = BankSenderSerializer(queryset, many=True)
        return Response({
            'success': True,
            'count': len(serializer.data),
            'results': serializer.data
        }, status=status.HTTP_200_OK)


class UserBankSenderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserBankSender model - User's bank sender assignments
    """
    serializer_class = UserBankSenderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own bank sender assignments"""
        return UserBankSender.objects.filter(
            user=self.request.user
        ).select_related('bank_sender', 'bank_sender__bank', 'integration')
    
    def get_serializer_class(self):
        """Use different serializers for create vs list/retrieve"""
        if self.action == 'create':
            return UserBankSenderCreateSerializer
        return UserBankSenderSerializer
    
    def perform_create(self, serializer):
        """Set user to current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['patch'])
    def toggle(self, request, pk=None):
        """Toggle active status of user bank sender"""
        user_sender = self.get_object()
        user_sender.is_active = not user_sender.is_active
        user_sender.save()
        
        return Response({
            'success': True,
            'is_active': user_sender.is_active,
            'message': f'Bank sender {"activated" if user_sender.is_active else "deactivated"}'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def add_by_email(self, request):
        """Add a bank sender by email - creates if doesn't exist"""
        sender_email = request.data.get('sender_email')
        sender_name = request.data.get('sender_name', '')
        bank_name = request.data.get('bank_name')
        integration_id = request.data.get('integration_id')
        
        if not all([sender_email, bank_name, integration_id]):
            return Response({
                'success': False,
                'error': 'sender_email, bank_name, and integration_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Verify integration belongs to user
            integration = Integration.objects.get(id=integration_id, user=request.user)
        except Integration.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Integration not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if bank sender already exists
        try:
            bank_sender = BankSender.objects.get(sender_email=sender_email)
            created = False
        except BankSender.DoesNotExist:
            # Create new bank sender
            # First, get or create the bank
            bank, _ = Bank.objects.get_or_create(
                user=request.user,
                name=bank_name,
                defaults={'country': 'CR'}  # Default to Costa Rica
            )
            
            bank_sender = BankSender.objects.create(
                bank=bank,
                sender_email=sender_email,
                sender_name=sender_name or f"{bank_name} Notifications",
                created_by=request.user
            )
            created = True
        
        # Add to user's list (if not already added)
        user_sender, user_created = UserBankSender.objects.get_or_create(
            user=request.user,
            integration=integration,
            bank_sender=bank_sender,
            defaults={'is_active': True}
        )
        
        if not user_created:
            return Response({
                'success': False,
                'error': 'This bank sender is already in your list'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UserBankSenderSerializer(user_sender)
        return Response({
            'success': True,
            'created_sender': created,
            'message': f'Bank sender {"created and " if created else ""}added successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def by_integration(self, request):
        """Get user's bank senders for a specific integration"""
        integration_id = request.query_params.get('integration_id')
        if not integration_id:
            return Response({
                'success': False,
                'error': 'integration_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.get_queryset().filter(integration_id=integration_id)
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'results': serializer.data
        }, status=status.HTTP_200_OK) 


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_provider_tokens(request, integration_id):
    """
    Endpoint para refrescar tokens OAuth de un proveedor
    """
    try:
        success = provider_auth_manager.refresh_provider_tokens(integration_id)
        
        if not success:
            return Response({
                'error': 'Failed to refresh provider tokens',
                'message': 'Please check the integration status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener estado actualizado
        token_status = provider_auth_manager.get_provider_token_status(integration_id)
        
        return Response({
            'success': True,
            'token_status': token_status
        })
        
    except Exception as e:
        logger.error(f"Error refreshing provider tokens: {str(e)}")
        return Response({
            'error': 'Token refresh failed',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_provider_token_status(request, integration_id):
    """
    Endpoint para obtener el estado de los tokens de un proveedor
    """
    try:
        token_status = provider_auth_manager.get_provider_token_status(integration_id)
        
        if token_status['status'] == 'not_found':
            return Response({
                'error': 'Integration not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'token_status': token_status
        })
        
    except Exception as e:
        logger.error(f"Error getting provider token status: {str(e)}")
        return Response({
            'error': 'Failed to get token status',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_provider_tokens(request, integration_id):
    """
    Endpoint para revocar tokens OAuth de un proveedor
    """
    try:
        success = provider_auth_manager.revoke_provider_tokens(integration_id)
        
        if not success:
            return Response({
                'error': 'Failed to revoke provider tokens',
                'message': 'Integration may not exist'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': 'Provider tokens revoked successfully'
        })
        
    except Exception as e:
        logger.error(f"Error revoking provider tokens: {str(e)}")
        return Response({
            'error': 'Token revocation failed',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
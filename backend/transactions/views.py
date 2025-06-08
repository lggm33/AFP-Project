from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Category, Transaction, EmailQueue
from .serializers import (
    CategorySerializer, CategoryCreateSerializer,
    TransactionSerializer, TransactionCreateSerializer, 
    TransactionUpdateSerializer, TransactionListSerializer,
    EmailQueueSerializer, EmailQueueCreateSerializer
)

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category model
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']
    
    def get_queryset(self):
        """Users can only access their own categories"""
        return Category.objects.filter(user=self.request.user).annotate(
            transaction_count=Count('transaction')
        )
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return CategoryCreateSerializer
        return CategorySerializer
    
    def perform_create(self, serializer):
        """Automatically assign current user to category"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def with_transactions(self, request):
        """Get categories that have transactions"""
        queryset = self.get_queryset().filter(transaction_count__gt=0)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Transaction model with advanced filtering and analytics
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['transaction_type', 'bank', 'category']
    
    def get_queryset(self):
        """Users can only access their own transactions"""
        return Transaction.objects.filter(user=self.request.user).select_related(
            'bank', 'category', 'email_pattern_used'
        ).order_by('-transaction_date')
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return TransactionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TransactionUpdateSerializer
        elif self.action == 'list':
            return TransactionListSerializer
        return TransactionSerializer
    
    def perform_create(self, serializer):
        """Automatically assign current user to transaction"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent transactions (last 30 days)"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        queryset = self.get_queryset().filter(transaction_date__gte=thirty_days_ago)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TransactionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TransactionListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get transaction statistics"""
        queryset = self.get_queryset()
        
        # Date range filtering
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(transaction_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(transaction_date__lte=end_date)
        
        # Calculate statistics
        total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0
        total_count = queryset.count()
        
        # Group by transaction type
        by_type = queryset.values('transaction_type').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-total_amount')
        
        # Group by category
        by_category = queryset.filter(category__isnull=False).values(
            'category__name', 'category__color'
        ).annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-total_amount')
        
        return Response({
            'total_amount': total_amount,
            'total_count': total_count,
            'by_type': list(by_type),
            'by_category': list(by_category)
        })
    
    @action(detail=False, methods=['post'])
    def bulk_categorize(self, request):
        """Bulk categorize transactions"""
        transaction_ids = request.data.get('transaction_ids', [])
        category_id = request.data.get('category_id')
        
        if not transaction_ids:
            return Response(
                {'error': 'transaction_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate transactions belong to user
        transactions = self.get_queryset().filter(id__in=transaction_ids)
        
        if category_id:
            try:
                category = Category.objects.get(id=category_id, user=request.user)
                updated = transactions.update(category=category)
            except Category.DoesNotExist:
                return Response(
                    {'error': 'Category not found or access denied'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Remove category
            updated = transactions.update(category=None)
        
        return Response({
            'updated_count': updated,
            'message': f'Updated {updated} transactions'
        })

class EmailQueueViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EmailQueue model
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'bank']
    
    def get_queryset(self):
        """Users can only access their own email queue"""
        return EmailQueue.objects.filter(user=self.request.user).select_related('bank')
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return EmailQueueCreateSerializer
        return EmailQueueSerializer
    
    def perform_create(self, serializer):
        """Automatically assign current user to email queue"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending emails for processing"""
        queryset = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def failed(self, request):
        """Get failed emails"""
        queryset = self.get_queryset().filter(status='failed')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry processing a failed email"""
        email = self.get_object()
        if email.status == 'failed':
            email.status = 'pending'
            email.attempts = 0
            email.error_message = ''
            email.save()
            
            serializer = self.get_serializer(email)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Only failed emails can be retried'},
                status=status.HTTP_400_BAD_REQUEST
            )

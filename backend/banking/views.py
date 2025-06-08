from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Bank, EmailPattern
from .serializers import (
    BankSerializer, BankCreateSerializer, BankListSerializer,
    EmailPatternSerializer, EmailPatternCreateSerializer
)

class BankViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Bank model with multi-tenant support
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['country', 'is_active']
    
    def get_queryset(self):
        """Users can only access their own banks"""
        return Bank.objects.filter(user=self.request.user).prefetch_related('emailpattern_set')
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return BankCreateSerializer
        elif self.action == 'list':
            return BankListSerializer
        return BankSerializer
    
    def perform_create(self, serializer):
        """Automatically assign current user to bank"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def patterns(self, request, pk=None):
        """Get all email patterns for a specific bank"""
        bank = self.get_object()
        patterns = bank.emailpattern_set.all()
        serializer = EmailPatternSerializer(patterns, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def create_pattern(self, request, pk=None):
        """Create a new email pattern for this bank"""
        bank = self.get_object()
        serializer = EmailPatternCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(bank=bank)
            return Response(
                EmailPatternSerializer(serializer.instance).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active banks"""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = BankListSerializer(queryset, many=True)
        return Response(serializer.data)

class EmailPatternViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EmailPattern model with bank filtering
    """
    serializer_class = EmailPatternSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['transaction_type', 'is_active', 'generated_by_ai', 'bank']
    
    def get_queryset(self):
        """Users can only access patterns from their own banks"""
        return EmailPattern.objects.filter(bank__user=self.request.user).select_related('bank')
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return EmailPatternCreateSerializer
        return EmailPatternSerializer
    
    def perform_create(self, serializer):
        """Validate that bank belongs to current user"""
        bank_id = self.request.data.get('bank')
        if bank_id:
            try:
                bank = Bank.objects.get(id=bank_id, user=self.request.user)
                serializer.save(bank=bank)
            except Bank.DoesNotExist:
                return Response(
                    {'error': 'Bank not found or access denied'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'error': 'Bank ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['patch'])
    def update_performance(self, request, pk=None):
        """Update pattern performance metrics"""
        pattern = self.get_object()
        success_increment = request.data.get('success_increment', 0)
        failure_increment = request.data.get('failure_increment', 0)
        
        pattern.success_count += success_increment
        pattern.failure_count += failure_increment
        pattern.save()
        
        serializer = self.get_serializer(pattern)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_bank(self, request):
        """Get patterns grouped by bank"""
        bank_id = request.query_params.get('bank_id')
        if not bank_id:
            return Response(
                {'error': 'bank_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            bank = Bank.objects.get(id=bank_id, user=request.user)
            patterns = self.get_queryset().filter(bank=bank)
            serializer = self.get_serializer(patterns, many=True)
            return Response(serializer.data)
        except Bank.DoesNotExist:
            return Response(
                {'error': 'Bank not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Integration, EmailImportJob, Email, BankSender, UserBankSender

class IntegrationSerializer(serializers.ModelSerializer):
    """Serializer for Integration model"""
    user = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    
    class Meta:
        model = Integration
        fields = [
            'id', 'user', 'provider', 'provider_display', 'email_address', 'is_active',
            'created_at', 'updated_at', 'updated_by', 'updated_message'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_provider_config(self, value):
        """Validate provider configuration"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Provider config must be a valid JSON object")
        return value


class IntegrationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating integrations (excludes sensitive fields)"""
    
    class Meta:
        model = Integration
        fields = ['provider', 'email_address', 'is_active', 'updated_message']
    
    def validate(self, data):
        """Validate integration data"""
        # Check if user already has this integration
        user = self.context['request'].user
        existing = Integration.objects.filter(
            user=user,
            provider=data['provider'],
            email_address=data['email_address']
        ).first()
        
        if existing:
            raise serializers.ValidationError(
                f"Integration for {data['email_address']} ({data['provider']}) already exists"
            )
        
        return data


class EmailImportJobSerializer(serializers.ModelSerializer):
    """Serializer for EmailImportJob model"""
    integration_email = serializers.CharField(source='integration.email_address', read_only=True)
    integration_provider = serializers.CharField(source='integration.provider', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = EmailImportJob
        fields = [
            'id', 'integration', 'integration_email', 'integration_provider',
            'status', 'status_display', 'next_run_at', 'retry_after',
            'period', 'window_start_offset', 'worker_id', 'celery_task_id',
            'attempts', 'message', 'summary'
        ]
        read_only_fields = ['id', 'worker_id', 'celery_task_id', 'attempts']


class EmailSerializer(serializers.ModelSerializer):
    """Serializer for Email model"""
    integration_email = serializers.CharField(source='integration.email_address', read_only=True)
    integration_provider = serializers.CharField(source='integration.provider', read_only=True)
    body_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = Email
        fields = [
            'id', 'integration', 'integration_email', 'integration_provider',
            'import_job', 'provider_message_id', 'sender', 'recipient',
            'subject', 'body_preview', 'attachment_count',
            'created_at', 'processed_at', 'process_by'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_body_preview(self, obj):
        """Return truncated body for list views"""
        if len(obj.body) > 200:
            return obj.body[:200] + '...'
        return obj.body


class EmailDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Email model (includes full body and headers)"""
    integration_email = serializers.CharField(source='integration.email_address', read_only=True)
    integration_provider = serializers.CharField(source='integration.provider', read_only=True)
    
    class Meta:
        model = Email
        fields = [
            'id', 'integration', 'integration_email', 'integration_provider',
            'import_job', 'provider_message_id', 'sender', 'recipient',
            'subject', 'body', 'raw_headers', 'attachment_count',
            'created_at', 'processed_at', 'process_by'
        ]
        read_only_fields = ['id', 'created_at']


class IntegrationStatsSerializer(serializers.Serializer):
    """Serializer for integration statistics"""
    total_integrations = serializers.IntegerField()
    active_integrations = serializers.IntegerField()
    providers = serializers.DictField()
    total_emails = serializers.IntegerField()
    recent_imports = serializers.ListField()


class EmailImportRequestSerializer(serializers.Serializer):
    """Serializer for email import requests"""
    integration_id = serializers.IntegerField(required=False)
    days_back = serializers.IntegerField(default=30, min_value=1, max_value=90)
    max_results = serializers.IntegerField(default=100, min_value=1, max_value=500)
    import_type = serializers.ChoiceField(
        choices=['all', 'banking', 'recent'],
        default='banking'
    )
    
    def validate_integration_id(self, value):
        """Validate that integration belongs to user"""
        if value:
            user = self.context['request'].user
            if not Integration.objects.filter(id=value, user=user).exists():
                raise serializers.ValidationError("Integration not found or doesn't belong to user")
        return value 


class BankSenderSerializer(serializers.ModelSerializer):
    """Serializer for BankSender model"""
    bank_name = serializers.CharField(source='bank.name', read_only=True)
    bank_country = serializers.CharField(source='bank.country', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    verified_by_username = serializers.CharField(source='verified_by.username', read_only=True)
    
    class Meta:
        model = BankSender
        fields = [
            'id', 'bank', 'bank_name', 'bank_country', 'sender_email', 'sender_name', 
            'sender_domain', 'email_template', 'is_verified', 'confidence_score',
            'total_emails_processed', 'created_at', 'updated_at', 'created_by_username',
            'verified_by_username', 'verified_at'
        ]
        read_only_fields = [
            'id', 'sender_domain', 'total_emails_processed', 'created_at', 'updated_at',
            'created_by_username', 'verified_by_username', 'verified_at'
        ]


class BankSenderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating BankSender"""
    
    class Meta:
        model = BankSender
        fields = ['bank', 'sender_email', 'sender_name', 'confidence_score']
        
    def validate_sender_email(self, value):
        """Validate that sender email is not already registered"""
        if BankSender.objects.filter(sender_email=value).exists():
            raise serializers.ValidationError("This sender email is already registered.")
        return value


class UserBankSenderSerializer(serializers.ModelSerializer):
    """Serializer for UserBankSender model"""
    bank_sender_details = BankSenderSerializer(source='bank_sender', read_only=True)
    integration_email = serializers.CharField(source='integration.email_address', read_only=True)
    effective_confidence = serializers.ReadOnlyField()
    display_name = serializers.ReadOnlyField()
    
    class Meta:
        model = UserBankSender
        fields = [
            'id', 'user', 'integration', 'integration_email', 'bank_sender', 
            'bank_sender_details', 'is_active', 'custom_confidence', 'custom_name',
            'emails_processed', 'last_email_at', 'added_at', 'updated_at', 'notes',
            'effective_confidence', 'display_name'
        ]
        read_only_fields = [
            'id', 'user', 'emails_processed', 'last_email_at', 'added_at', 'updated_at'
        ]


class UserBankSenderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating UserBankSender"""
    
    class Meta:
        model = UserBankSender
        fields = ['integration', 'bank_sender', 'is_active', 'custom_confidence', 'custom_name', 'notes']
        
    def validate(self, data):
        """Validate that the combination doesn't already exist"""
        user = self.context['request'].user
        integration = data['integration']
        bank_sender = data['bank_sender']
        
        if UserBankSender.objects.filter(
            user=user, 
            integration=integration, 
            bank_sender=bank_sender
        ).exists():
            raise serializers.ValidationError(
                "This bank sender is already added to your integration."
            )
        return data


class BankSenderSearchSerializer(serializers.Serializer):
    """Serializer for bank sender search requests"""
    email = serializers.EmailField(required=False)
    domain = serializers.CharField(max_length=100, required=False)
    bank_name = serializers.CharField(max_length=100, required=False)
    verified_only = serializers.BooleanField(default=False)
    
    def validate(self, data):
        """At least one search parameter is required"""
        if not any([data.get('email'), data.get('domain'), data.get('bank_name')]):
            raise serializers.ValidationError(
                "At least one search parameter (email, domain, or bank_name) is required."
            )
        return data 
from rest_framework import serializers
from .models import Bank, EmailPattern, EmailQueue, EmailProcessingLog, BankTemplate

class EmailPatternSerializer(serializers.ModelSerializer):
    """Serializer for EmailPattern model"""
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    success_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = EmailPattern
        fields = [
            'id', 'transaction_type', 'transaction_type_display',
            'amount_regex', 'merchant_regex', 'date_regex', 'reference_regex',
            'confidence_threshold', 'success_count', 'failure_count', 'success_rate',
            'is_active', 'generated_by_ai', 'ai_model', 
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'success_count', 'failure_count', 'success_rate',
            'created_at', 'updated_at'
        ]

class EmailPatternCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating EmailPattern"""
    class Meta:
        model = EmailPattern
        fields = [
            'transaction_type', 'amount_regex', 'merchant_regex', 
            'date_regex', 'reference_regex', 'confidence_threshold',
            'is_active', 'generated_by_ai', 'ai_model'
        ]

class BankSerializer(serializers.ModelSerializer):
    """Serializer for Bank model"""
    patterns = EmailPatternSerializer(source='emailpattern_set', many=True, read_only=True)
    pattern_count = serializers.SerializerMethodField()
    active_pattern_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Bank
        fields = [
            'id', 'name', 'country', 'domains', 'sender_emails',
            'is_active', 'created_at', 'patterns', 'pattern_count', 'active_pattern_count'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_pattern_count(self, obj):
        """Get total number of email patterns"""
        return obj.emailpattern_set.count()
    
    def get_active_pattern_count(self, obj):
        """Get number of active email patterns"""
        return obj.emailpattern_set.filter(is_active=True).count()

class BankCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Bank"""
    class Meta:
        model = Bank
        fields = ['name', 'country', 'domains', 'sender_emails', 'is_active']
        
    def validate_domains(self, value):
        """Validate domains field"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Domains must be a list")
        if not value:
            raise serializers.ValidationError("At least one domain is required")
        return value
    
    def validate_sender_emails(self, value):
        """Validate sender_emails field"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Sender emails must be a list")
        if not value:
            raise serializers.ValidationError("At least one sender email is required")
        return value

class BankListSerializer(serializers.ModelSerializer):
    """Simplified serializer for bank listings"""
    pattern_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Bank
        fields = [
            'id', 'name', 'country', 'is_active', 
            'created_at', 'pattern_count'
        ]
    
    def get_pattern_count(self, obj):
        """Get total number of email patterns"""
        return obj.emailpattern_set.filter(is_active=True).count()


# =====================================================
# EMAIL PROCESSING QUEUE SERIALIZERS (FOR CELERY)
# =====================================================

class EmailQueueSerializer(serializers.ModelSerializer):
    """Serializer for EmailQueue model"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    queue_type_display = serializers.CharField(source='get_queue_type_display', read_only=True)
    bank_name = serializers.CharField(source='bank.name', read_only=True)
    
    class Meta:
        model = EmailQueue
        fields = [
            'id', 'gmail_message_id', 'sender', 'subject', 'received_at',
            'status', 'status_display', 'queue_type', 'queue_type_display',
            'priority', 'worker_id', 'attempts', 'error_message', 'confidence_score',
            'bank_name', 'created_at', 'processed_at', 'last_attempt_at'
        ]
        read_only_fields = [
            'id', 'gmail_message_id', 'worker_id', 'attempts', 'confidence_score',
            'created_at', 'processed_at', 'last_attempt_at'
        ]

class EmailQueueCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating EmailQueue entries"""
    class Meta:
        model = EmailQueue
        fields = [
            'gmail_message_id', 'sender', 'subject', 'body', 'received_at',
            'queue_type', 'priority'
        ]

class EmailProcessingLogSerializer(serializers.ModelSerializer):
    """Serializer for EmailProcessingLog model"""
    email_message_id = serializers.CharField(source='email_queue.gmail_message_id', read_only=True)
    
    class Meta:
        model = EmailProcessingLog
        fields = [
            'id', 'email_message_id', 'worker_type', 'worker_id', 
            'started_at', 'completed_at', 'success', 'error_message',
            'extracted_data', 'processing_time_seconds', 'api_calls_made'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at']

class BankTemplateSerializer(serializers.ModelSerializer):
    """Serializer for BankTemplate model"""
    bank_name = serializers.CharField(source='bank.name', read_only=True)
    success_rate = serializers.ReadOnlyField()
    pattern_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BankTemplate
        fields = [
            'id', 'bank_name', 'name', 'version', 'is_active',
            'subject_patterns', 'sender_patterns', 'body_keywords',
            'success_count', 'failure_count', 'success_rate', 'confidence_threshold',
            'generated_by_ai', 'ai_prompt_used', 'sample_emails_used',
            'pattern_count', 'created_at', 'updated_at', 'last_used_at'
        ]
        read_only_fields = [
            'id', 'success_count', 'failure_count', 'success_rate',
            'created_at', 'updated_at', 'last_used_at'
        ]
    
    def get_pattern_count(self, obj):
        """Get number of email patterns associated with this template"""
        return obj.email_patterns.count()

class BankTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating BankTemplate"""
    class Meta:
        model = BankTemplate
        fields = [
            'name', 'version', 'is_active', 'subject_patterns', 
            'sender_patterns', 'body_keywords', 'confidence_threshold',
            'generated_by_ai', 'ai_prompt_used', 'sample_emails_used'
        ] 
from rest_framework import serializers
from .models import Bank, EmailPattern

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
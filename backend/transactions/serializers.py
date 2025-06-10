from rest_framework import serializers
from .models import Category, Transaction
from banking.serializers import BankListSerializer, EmailPatternSerializer

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    transaction_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'color', 'icon', 'is_active', 
            'created_at', 'transaction_count'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_transaction_count(self, obj):
        """Get number of transactions in this category"""
        return obj.transaction_set.count()

class CategoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Category"""
    class Meta:
        model = Category
        fields = ['name', 'color', 'icon', 'is_active']

class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""
    bank = BankListSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    email_pattern_used = EmailPatternSerializer(read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    confidence_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'bank', 'amount', 'description', 'transaction_date',
            'transaction_type', 'transaction_type_display', 'merchant', 'location', 'reference',
            'confidence_score', 'confidence_percentage', 'email_pattern_used',
            'category', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'confidence_score', 'email_pattern_used', 'raw_email_body',
            'created_at', 'updated_at'
        ]
    
    def get_confidence_percentage(self, obj):
        """Convert confidence score to percentage"""
        return round(obj.confidence_score * 100, 1)

class TransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Transaction"""
    class Meta:
        model = Transaction
        fields = [
            'bank', 'amount', 'description', 'transaction_date',
            'transaction_type', 'merchant', 'location', 'reference',
            'confidence_score', 'raw_email_body', 'category'
        ]

class TransactionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Transaction (mainly category)"""
    class Meta:
        model = Transaction
        fields = ['category', 'description', 'merchant', 'location']

class TransactionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for transaction listings"""
    bank_name = serializers.CharField(source='bank.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'amount', 'description', 'transaction_date',
            'transaction_type', 'transaction_type_display', 'merchant',
            'bank_name', 'category_name', 'category_color', 'confidence_score'
        ]

# EmailQueue serializers moved to banking.serializers 
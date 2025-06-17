"""
Abstract base provider for email services
All email providers (Gmail, Outlook, Yahoo) must implement this interface
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from django.contrib.auth.models import User

class BaseEmailProvider(ABC):
    """Abstract base class for email providers"""
    
    def __init__(self, integration):
        """Initialize provider with integration instance"""
        self.integration = integration
        self.user = integration.user
        self.provider_config = integration.provider_config
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to the email provider"""
        pass
    
    @abstractmethod
    def get_all_messages(self, days_back: int = 30, sender_filter: str = None, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Get all messages with pagination"""
        pass
    
    @abstractmethod
    def get_banking_messages(self, days_back: int = 30, user_bank_senders: List[str] = None, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Get banking messages with pagination"""
        pass
    
    @abstractmethod
    def refresh_tokens_if_needed(self) -> bool:
        """Refresh OAuth tokens if needed"""
        pass
    
    def get_oauth_tokens(self) -> Optional[Dict[str, str]]:
        """Get OAuth tokens from integration config"""
        return self.provider_config.get('oauth_tokens')
    
    def save_oauth_tokens(self, tokens: Dict[str, str]) -> None:
        """Save OAuth tokens to integration config"""
        if 'oauth_tokens' not in self.provider_config:
            self.provider_config['oauth_tokens'] = {}
        
        self.provider_config['oauth_tokens'].update(tokens)
        self.integration.save()
    
    def is_configured(self) -> bool:
        """Check if provider is properly configured with tokens"""
        tokens = self.get_oauth_tokens()
        return tokens is not None and 'access_token' in tokens 
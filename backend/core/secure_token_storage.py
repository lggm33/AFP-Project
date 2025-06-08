"""
Secure Token Storage for OAuth tokens
Implements encryption at rest for sensitive OAuth tokens
"""

import os
from cryptography.fernet import Fernet
from django.conf import settings
from allauth.socialaccount.models import SocialToken
import logging

logger = logging.getLogger(__name__)

class SecureTokenManager:
    """Manager for encrypting/decrypting OAuth tokens"""
    
    def __init__(self):
        self.cipher_suite = self._get_cipher_suite()
    
    def _get_cipher_suite(self):
        """Get or generate encryption key"""
        # In production, store this in environment variable or secure key management
        encryption_key = getattr(settings, 'OAUTH_TOKEN_ENCRYPTION_KEY', None)
        
        if not encryption_key:
            # Generate key if not exists (ONLY for development)
            if settings.DEBUG:
                logger.warning("Generating new encryption key for development. DO NOT use in production!")
                encryption_key = Fernet.generate_key().decode()
                # You should save this key securely
                logger.info(f"Generated encryption key: {encryption_key}")
            else:
                raise ValueError("OAUTH_TOKEN_ENCRYPTION_KEY must be set in production")
        
        return Fernet(encryption_key.encode())
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt OAuth token before storing in database"""
        if not token:
            return token
        
        try:
            encrypted_token = self.cipher_suite.encrypt(token.encode())
            return encrypted_token.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt token: {str(e)}")
            raise
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt OAuth token when retrieving from database"""
        if not encrypted_token:
            return encrypted_token
        
        try:
            decrypted_token = self.cipher_suite.decrypt(encrypted_token.encode())
            return decrypted_token.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt token: {str(e)}")
            raise

class EncryptedSocialToken(SocialToken):
    """Extended SocialToken with encryption capabilities"""
    
    class Meta:
        proxy = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token_manager = SecureTokenManager()
    
    def save(self, *args, **kwargs):
        """Override save to encrypt tokens before storing"""
        if self.token:
            self.token = self.token_manager.encrypt_token(self.token)
        if self.token_secret:
            self.token_secret = self.token_manager.encrypt_token(self.token_secret)
        
        super().save(*args, **kwargs)
    
    def get_decrypted_token(self) -> str:
        """Get decrypted access token"""
        return self.token_manager.decrypt_token(self.token)
    
    def get_decrypted_token_secret(self) -> str:
        """Get decrypted refresh token"""
        return self.token_manager.decrypt_token(self.token_secret)

# Security utilities
def rotate_encryption_key():
    """Rotate encryption key (for periodic security maintenance)"""
    # This would require re-encrypting all existing tokens
    # Implementation depends on your security requirements
    pass

def audit_token_access(user, action, token_type):
    """Log token access for security auditing"""
    logger.info(f"Token access: user={user.username}, action={action}, type={token_type}") 
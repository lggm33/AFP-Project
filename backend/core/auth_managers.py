from django.utils import timezone
from django.conf import settings
from typing import Dict, Optional, Any
import logging
from .models import Integration
from .providers.base_provider import BaseEmailProvider
from .providers.gmail_provider import GmailProvider
from datetime import timedelta

logger = logging.getLogger(__name__)

class EmailProviderAuthManager:
    """
    Manager para la autenticación de proveedores de email.
    Maneja tokens OAuth, refresh y validación por proveedor.
    """
    
    # Configuración por proveedor
    PROVIDER_CONFIGS = {
        'gmail': {
            'refresh_buffer': timedelta(minutes=5),  # Refresh 5 min antes de expirar
            'max_refresh_attempts': 3,
            'refresh_cooldown': timedelta(minutes=5)
        },
        'outlook': {
            'refresh_buffer': timedelta(minutes=5),
            'max_refresh_attempts': 3,
            'refresh_cooldown': timedelta(minutes=5)
        },
        'yahoo': {
            'refresh_buffer': timedelta(minutes=5),
            'max_refresh_attempts': 3,
            'refresh_cooldown': timedelta(minutes=5)
        }
    }
    
    def __init__(self):
        self.providers = {
            'gmail': GmailProvider,
            # 'outlook': OutlookProvider,  # Implementar cuando se agregue
            # 'yahoo': YahooProvider,      # Implementar cuando se agregue
        }
    
    def get_provider_instance(self, integration: Integration) -> Optional[BaseEmailProvider]:
        """
        Obtiene una instancia del proveedor para una integración.
        
        Args:
            integration: Modelo Integration
            
        Returns:
            Instancia del proveedor o None si no se encuentra
        """
        provider_class = self.providers.get(integration.provider)
        if not provider_class:
            logger.error(f"Provider {integration.provider} not implemented")
            return None
            
        return provider_class(integration)
    
    def refresh_provider_tokens(self, integration_id: int) -> bool:
        """
        Refresca los tokens OAuth de un proveedor.
        
        Args:
            integration_id: ID de la integración
            
        Returns:
            True si se refrescaron exitosamente
        """
        try:
            integration = Integration.objects.get(id=integration_id)
            provider = self.get_provider_instance(integration)
            
            if not provider:
                return False
            
            # Verificar si podemos intentar refresh
            if not self._can_attempt_refresh(integration):
                return False
            
            # Intentar refresh
            success = provider.refresh_tokens_if_needed()
            
            if success:
                # Actualizar estado de la integración
                integration.oauth_token_refreshed_at = timezone.now()
                integration.refresh_error_count = 0
                integration.refresh_error_message = ''
                integration.oauth_token_status = 'active'
            else:
                # Incrementar contador de errores
                integration.refresh_error_count += 1
                integration.refresh_error_message = 'Failed to refresh tokens'
                if integration.refresh_error_count >= self.PROVIDER_CONFIGS[integration.provider]['max_refresh_attempts']:
                    integration.oauth_token_status = 'error'
            
            integration.last_refresh_attempt = timezone.now()
            integration.save()
            
            return success
            
        except Integration.DoesNotExist:
            logger.error(f"Integration {integration_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error refreshing tokens for integration {integration_id}: {str(e)}")
            return False
    
    def validate_provider_token(self, integration_id: int) -> bool:
        """
        Valida los tokens OAuth de un proveedor.
        
        Args:
            integration_id: ID de la integración
            
        Returns:
            True si los tokens son válidos
        """
        try:
            integration = Integration.objects.get(id=integration_id)
            provider = self.get_provider_instance(integration)
            
            if not provider:
                return False
            
            # Verificar si los tokens están expirados
            if integration.oauth_token_expires_at and integration.oauth_token_expires_at <= timezone.now():
                return False
            
            # Verificar estado actual
            if integration.oauth_token_status != 'active':
                return False
            
            return True
            
        except Integration.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error validating tokens for integration {integration_id}: {str(e)}")
            return False
    
    def revoke_provider_tokens(self, integration_id: int) -> bool:
        """
        Revoca los tokens OAuth de un proveedor.
        
        Args:
            integration_id: ID de la integración
            
        Returns:
            True si se revocaron exitosamente
        """
        try:
            integration = Integration.objects.get(id=integration_id)
            provider = self.get_provider_instance(integration)
            
            if not provider:
                return False
            
            # Marcar como revocados
            integration.oauth_token_status = 'revoked'
            integration.save()
            
            return True
            
        except Integration.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error revoking tokens for integration {integration_id}: {str(e)}")
            return False
    
    def get_provider_token_status(self, integration_id: int) -> Dict[str, Any]:
        """
        Obtiene el estado actual de los tokens de un proveedor.
        
        Args:
            integration_id: ID de la integración
            
        Returns:
            Dict con información del estado
        """
        try:
            integration = Integration.objects.get(id=integration_id)
            
            return {
                'status': integration.oauth_token_status,
                'expires_at': integration.oauth_token_expires_at,
                'last_refresh': integration.oauth_token_refreshed_at,
                'error_count': integration.refresh_error_count,
                'error_message': integration.refresh_error_message,
                'auto_refresh_enabled': integration.auto_refresh_enabled
            }
            
        except Integration.DoesNotExist:
            return {'status': 'not_found'}
        except Exception as e:
            logger.error(f"Error getting token status for integration {integration_id}: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _can_attempt_refresh(self, integration: Integration) -> bool:
        """
        Verifica si se puede intentar un refresh de tokens.
        
        Args:
            integration: Modelo Integration
            
        Returns:
            True si se puede intentar refresh
        """
        # Si está en cooldown, no intentar
        if integration.last_refresh_attempt:
            cooldown = self.PROVIDER_CONFIGS[integration.provider]['refresh_cooldown']
            if timezone.now() - integration.last_refresh_attempt < cooldown:
                return False
        
        # Si excedió intentos máximos, no intentar
        max_attempts = self.PROVIDER_CONFIGS[integration.provider]['max_refresh_attempts']
        if integration.refresh_error_count >= max_attempts:
            return False
        
        return True 
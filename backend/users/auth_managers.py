from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.utils import timezone
from datetime import timedelta
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class AppAuthManager:
    """
    Manager para la autenticación de la aplicación AFP.
    Maneja tokens JWT, refresh y validación.
    """
    
    def __init__(self):
        self.access_token_lifetime = settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', timedelta(minutes=5))
        self.refresh_token_lifetime = settings.SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME', timedelta(days=7))
        self.rotate_refresh_tokens = settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', True)
    
    def create_tokens(self, user) -> Dict[str, str]:
        """
        Crea nuevos tokens JWT para un usuario.
        
        Args:
            user: Usuario de Django
            
        Returns:
            Dict con access_token y refresh_token
        """
        try:
            refresh = RefreshToken.for_user(user)
            return {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh)
            }
        except Exception as e:
            logger.error(f"Error creating tokens for user {user.id}: {str(e)}")
            raise
    
    def refresh_app_tokens(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        Refresca los tokens JWT usando el refresh token.
        
        Args:
            refresh_token: Token de refresh actual
            
        Returns:
            Dict con nuevos tokens o None si falla
        """
        try:
            token = RefreshToken(refresh_token)
            
            # Verificar si el token está expirado
            if token.current_time > token['exp']:
                logger.warning("Refresh token expired")
                return None
            
            # Crear nuevos tokens
            new_tokens = {
                'access_token': str(token.access_token)
            }
            
            # Rotar refresh token si está configurado
            if self.rotate_refresh_tokens:
                new_tokens['refresh_token'] = str(token)
            else:
                new_tokens['refresh_token'] = refresh_token
            
            return new_tokens
            
        except TokenError as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in refresh_app_tokens: {str(e)}")
            return None
    
    def validate_app_token(self, access_token: str) -> bool:
        """
        Valida un access token JWT.
        
        Args:
            access_token: Token a validar
            
        Returns:
            True si el token es válido, False si no
        """
        try:
            token = RefreshToken(access_token)
            return token.current_time <= token['exp']
        except Exception:
            return False
    
    def revoke_app_tokens(self, refresh_token: str) -> bool:
        """
        Revoca un refresh token (blacklist).
        
        Args:
            refresh_token: Token a revocar
            
        Returns:
            True si se revocó exitosamente
        """
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return True
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
            return False
    
    def get_token_expiry(self, access_token: str) -> Optional[timezone.datetime]:
        """
        Obtiene la fecha de expiración de un token.
        
        Args:
            access_token: Token a verificar
            
        Returns:
            Datetime de expiración o None si no se puede obtener
        """
        try:
            token = RefreshToken(access_token)
            return timezone.datetime.fromtimestamp(token['exp'], tz=timezone.utc)
        except Exception:
            return None 
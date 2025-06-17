from django.utils import timezone
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken
from .auth_managers import AppAuthManager
import logging

logger = logging.getLogger(__name__)

class TokenRefreshMiddleware:
    """
    Middleware para manejar el auto-refresh de tokens JWT.
    Verifica si el token está próximo a expirar y lo refresca automáticamente.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.auth_manager = AppAuthManager()
        self.refresh_buffer = getattr(settings, 'JWT_REFRESH_BUFFER', 300)  # 5 minutos por defecto
    
    def __call__(self, request):
        # Solo procesar si hay token en el header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return self.get_response(request)
        
        try:
            # Extraer token
            token = auth_header.split(' ')[1]
            
            # Verificar si está próximo a expirar
            expiry = self.auth_manager.get_token_expiry(token)
            if not expiry:
                return self.get_response(request)
            
            # Si falta menos del buffer para expirar, refrescar
            if (expiry - timezone.now()).total_seconds() < self.refresh_buffer:
                # Intentar refresh
                refresh_token = request.COOKIES.get('afp_refresh_token')
                if refresh_token:
                    new_tokens = self.auth_manager.refresh_app_tokens(refresh_token)
                    if new_tokens:
                        # Agregar nuevos tokens al header
                        request.META['HTTP_AUTHORIZATION'] = f"Bearer {new_tokens['access_token']}"
                        # Agregar flag para que el frontend sepa que debe actualizar
                        request.META['HTTP_X_TOKEN_REFRESHED'] = 'true'
                        logger.info("Token refreshed automatically via middleware")
        
        except Exception as e:
            logger.warning(f"Error in token refresh middleware: {str(e)}")
        
        return self.get_response(request) 
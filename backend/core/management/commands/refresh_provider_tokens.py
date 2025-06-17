from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Integration
from core.auth_managers import EmailProviderAuthManager
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Refresca los tokens de los proveedores de correo que están próximos a expirar'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar el refresh de todos los tokens activos',
        )

    def handle(self, *args, **options):
        provider_manager = EmailProviderAuthManager()
        force_refresh = options['force']
        
        # Obtener todas las integraciones activas
        integrations = Integration.objects.filter(
            is_active=True,
            oauth_token_status='active'
        )
        
        if not force_refresh:
            # Filtrar solo las que están próximas a expirar (menos de 24 horas)
            integrations = integrations.filter(
                oauth_token_expires_at__lte=timezone.now() + timezone.timedelta(hours=24)
            )
        
        total = integrations.count()
        self.stdout.write(f'Encontradas {total} integraciones para refrescar')
        
        success_count = 0
        error_count = 0
        
        for integration in integrations:
            try:
                self.stdout.write(f'Refrescando tokens para {integration.email_address}...')
                result = provider_manager.refresh_provider_tokens(integration.id)
                
                if result and result.get('status') == 'active':
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Tokens refrescados exitosamente para {integration.email_address}')
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'Error al refrescar tokens para {integration.email_address}: {result.get("error_message", "Unknown error")}')
                    )
            except Exception as e:
                error_count += 1
                logger.error(f'Error al refrescar tokens para {integration.email_address}: {str(e)}')
                self.stdout.write(
                    self.style.ERROR(f'Error al refrescar tokens para {integration.email_address}: {str(e)}')
                )
        
        self.stdout.write(self.style.SUCCESS(
            f'Proceso completado. Éxitos: {success_count}, Errores: {error_count}'
        )) 
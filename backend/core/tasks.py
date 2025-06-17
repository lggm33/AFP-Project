from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

@shared_task
def refresh_provider_tokens(force=False):
    """
    Tarea programada para refrescar los tokens de los proveedores de correo.
    Se ejecuta cada 12 horas por defecto.
    """
    try:
        logger.info('Iniciando refresh automático de tokens de proveedores')
        call_command('refresh_provider_tokens', force=force)
        logger.info('Refresh automático de tokens completado')
    except Exception as e:
        logger.error(f'Error en refresh automático de tokens: {str(e)}')
        raise 
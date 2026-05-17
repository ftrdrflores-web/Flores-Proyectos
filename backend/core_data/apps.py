from django.apps import AppConfig

class CoreDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core_data'

    def ready(self):
        """Se ejecuta cuando Django arranca."""
        import sys
        
        # No iniciar scheduler durante migraciones o comandos de gestión
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return
            
        try:
            from core_data.scheduler import start_scheduler
            start_scheduler()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error iniciando scheduler: {e}")
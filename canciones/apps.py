from django.apps import AppConfig


class CancionesConfig(AppConfig): # <--- ¡IMPORTANTE! Debe ser 'CancionesConfig'
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'canciones' # <--- ¡IMPORTANTE! Debe ser 'canciones'

    def ready(self):
        import canciones.signals # <--- ¡IMPORTANTE! Debe ser 'canciones.signals'
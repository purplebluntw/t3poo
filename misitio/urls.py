# misitio/urls.py

from django.contrib import admin
from django.urls import path, include
from canciones import views # Asegúrate de que esta línea exista para importar las vistas de canciones
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.login, name="login"), # La raíz del sitio lleva al login
    path("register/", views.register, name="register"), # URL para la página de registro
    path("logout/", views.logout_view, name="logout"), # Nueva URL para cerrar sesión
    path("canciones/", include("canciones.urls")), # Incluye las URLs de la aplicación 'canciones'
]

# Configuración para servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
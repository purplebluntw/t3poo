# canciones/urls.py
from django.urls import path
from . import views

app_name = 'canciones' # <--- ¡IMPORTANTE! Define el nombre de la aplicación para el namespace

urlpatterns = [
    # Rutas privadas/protegidas (ahora con el prefijo 'u/' para evitar ambigüedades)
    # Ejemplo de URL: /canciones/u/nombre_de_usuario/
    path("u/<str:name>/", views.lista_canciones, name="lista_canciones"),
    # Ejemplo de URL: /canciones/u/nombre_de_usuario/ID_cancion/editar/
    path("u/<str:name>/<int:id>/editar/", views.editar_cancion, name="editar_cancion"),
    # Ejemplo de URL: /canciones/u/nombre_de_usuario/crear/
    path("u/<str:name>/crear/", views.crear_cancion, name="crear_cancion"),
    # Ejemplo de URL: /canciones/u/nombre_de_usuario/borrar/ID_cancion/
    path("u/<str:name>/borrar/<int:id>/", views.borrar_cancion, name="borrar_cancion"),

    # Rutas públicas (estas NO CAMBIAN, ya que no son ambiguas con las de usuario)
    # Ejemplo de URL: /canciones/publica/
    path("publica/", views.vista_publica_canciones, name="vista_publica_canciones"),
    # Ejemplo de URL: /canciones/publica/ID_cancion/
    path("publica/<int:cancion_id>/", views.detalle_cancion_publico, name="detalle_cancion_publico"),
]
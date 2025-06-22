# canciones/views.py

from django.shortcuts import render, redirect, get_object_or_404
import uuid
from datetime import date
from django.http import HttpResponse # No siempre es necesario si usas render o redirect
from django.template import loader # Solo necesario si usas loader.get_template().render()
from django.contrib import messages # Para mostrar mensajes al usuario
from django.urls import reverse # Para generar URLs dinámicamente

# Importa los modelos
from .models import Cancion, Usuario, UsuarioCancion

# --- Vistas de Autenticación (login, register, logout) ---
# Se asume que estas vistas manejan su propia lógica de sesión
# y redirigen a URLs con nombres definidos en misitio/urls.py o canciones/urls.py

def login(request):
    # Si el usuario ya está logueado en la sesión, redirigir directamente a su lista de canciones
    if 'nombre_usuario' in request.session:
        return redirect(reverse('canciones:lista_canciones', kwargs={'name': request.session['nombre_usuario']}))

    if request.method == 'POST':
        name = request.POST['nombre']
        password = request.POST['pass']
        try:
            usuario = Usuario.objects.get(nombre=name, contrasena=password)
            request.session['nombre_usuario'] = usuario.nombre # Establece el nombre de usuario en la sesión
            messages.success(request, f"¡Bienvenido de nuevo, {usuario.nombre}!")
            return redirect(reverse('canciones:lista_canciones', kwargs={'name': usuario.nombre}))
        except Usuario.DoesNotExist:
            messages.error(request, "Usuario o contraseña incorrectos.")
            return render(request, "canciones/trueIndex.html") # Renderiza el formulario de login de nuevo con el error
    return render(request, "canciones/trueIndex.html") # Para peticiones GET o si no es POST válido


def register(request):
    if request.method == 'POST':
        nombre_usuario = request.POST.get('nombre')
        contrasena = request.POST.get('pass')

        if Usuario.objects.filter(nombre=nombre_usuario).exists():
            messages.error(request, "Este usuario ya existe. Por favor, elige otro nombre.")
            return render(request, "canciones/register.html", {'nombre_usuario_previo': nombre_usuario}) # Mantener el nombre si hay error
        
        # Validación de contraseña simple (puedes añadir más)
        if not contrasena or len(contrasena) < 3: # Ejemplo: contraseña mínimo 3 caracteres
            messages.error(request, "La contraseña debe tener al menos 3 caracteres.")
            return render(request, "canciones/register.html", {'nombre_usuario_previo': nombre_usuario})

        usuario = Usuario(
            nombre = nombre_usuario,
            contrasena = contrasena, # En una app real, la contraseña DEBE ser hasheada
            uuid = uuid.uuid4(),
            fecha_registro=date.today()
        )
        usuario.save()
        messages.success(request, "Cuenta registrada exitosamente. Ahora puedes iniciar sesión.")
        return redirect('login') # Redirige a la página de login después de un registro exitoso
    return render(request, "canciones/register.html")


def logout_view(request):
    """
    Cierra la sesión del usuario eliminando el nombre de usuario de la sesión.
    """
    if 'nombre_usuario' in request.session:
        del request.session['nombre_usuario'] # Elimina el nombre de usuario de la sesión
    messages.info(request, "Has cerrado sesión exitosamente.")
    return redirect('login') # Redirige a la página de login


# --- Funciones de CRUD para canciones del usuario (Requiere Autenticación) ---

def lista_canciones(request, name):
    # Verificar si el usuario está logueado por nuestra sesión personalizada
    if 'nombre_usuario' not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder a esta página.")
        return redirect('login') # Redirigir al login si no está logueado

    # Aseguramos que el usuario en la URL sea el mismo que está logueado en la sesión
    if request.session.get('nombre_usuario') != name:
        messages.error(request, "Acceso no autorizado a la lista de otro usuario.")
        return redirect('login')

    usuario = get_object_or_404(Usuario, nombre=name)
    
    # Obtener las canciones a través de la relación ManyToMany inversa
    # Usamos .all() en la relación definida en Usuario: canciones_favoritas = models.ManyToManyField(Cancion, through='UsuarioCancion', related_name='usuarios_favoritos')
    # Y la relación UsuarioCancion tiene un campo 'cancion' que apunta a Cancion.
    # El diccionario canciones tiene la clave de la relación y el objeto Cancion asociado.
    canciones_favoritas = {rel.clave_relacion: rel.cancion for rel in usuario.canciones_favoritas.all()}
    
    # Usamos render en lugar de loader.get_template().render() para mayor simplicidad
    context = {
        "canciones": canciones_favoritas,
        "name": name,
        "is_authenticated": True # Indica si hay un usuario logueado en la sesión
    }
    return render(request, "canciones/listar_canciones.html", context)


def crear_cancion(request, name):
    # Verificar si el usuario está logueado
    if 'nombre_usuario' not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder a esta página.")
        return redirect('login')

    # Asegurar que el usuario en la URL es el dueño de la sesión
    if request.session.get('nombre_usuario') != name:
        messages.error(request, "Acceso no autorizado para crear canciones para otro usuario.")
        return redirect('login')

    user = get_object_or_404(Usuario, nombre=name)

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        if not titulo:
            messages.error(request, "El título de la canción es obligatorio.")
            return render(request, "canciones/crear_cancion.html", {"name": name, "is_authenticated": True})

        # Verificar si el usuario ya tiene una canción con el mismo título
        if UsuarioCancion.objects.filter(usuario=user, cancion__titulo=titulo).exists():
            messages.error(request, f"Ya tienes una canción llamada '{titulo}' en tus favoritos.")
            return render(request, "canciones/crear_cancion.html", {"name": name, "is_authenticated": True})

        artista = request.POST.get('artista')
        album = request.POST.get('album')
        ano_lanzamiento_str = request.POST.get('ano_lanzamiento')

        try:
            # Si el año de lanzamiento está vacío, lo guardamos como None
            ano_lanzamiento = int(ano_lanzamiento_str) if ano_lanzamiento_str else None
        except ValueError:
            messages.error(request, "El año de lanzamiento debe ser un número válido.")
            return render(request, "canciones/crear_cancion.html", {"name": name, "is_authenticated": True})

        # Crear la canción
        cancion = Cancion(
            titulo = titulo,
            artista = artista,
            album = album,
            ano_lanzamiento = ano_lanzamiento,
            es_favorita = 'es_favorita' in request.POST, # Si el checkbox está marcado
            fecha_agregada=date.today()
        )
        cancion.save()

        # Crear la relación entre el usuario y la canción recién creada
        UsuarioCancion.objects.create(usuario=user, cancion=cancion)

        messages.success(request, f"Canción '{cancion.titulo}' agregada a tus favoritos.")
        # Redirigir a la lista de canciones del usuario actual
        return redirect('canciones:lista_canciones', name=name)

    # Si es una petición GET, simplemente renderiza el formulario
    return render(request, "canciones/crear_cancion.html", {"name": name, "is_authenticated": True})


def editar_cancion(request, name, id):
    # Verificar si el usuario está logueado
    if 'nombre_usuario' not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder a esta página.")
        return redirect('login')

    # Asegurar que el usuario en la URL es el dueño de la sesión y de la canción
    if request.session.get('nombre_usuario') != name:
        messages.error(request, "Acceso no autorizado para editar la canción de otro usuario.")
        return redirect('login')

    user = get_object_or_404(Usuario, nombre=name)
    # Obtener la relación específica para asegurar que la canción le pertenece a este usuario
    relacion = get_object_or_404(UsuarioCancion, usuario=user, cancion__id=id)
    cancion = relacion.cancion # Acceder a la instancia de Cancion a través de la relación

    if request.method == 'POST':
        cancion.titulo = request.POST.get('titulo')
        if not cancion.titulo: # Validación de título no vacío
            messages.error(request, "El título de la canción no puede estar vacío.")
            context = {
                "cancion": cancion,
                "name": name,
                "is_authenticated": True
            }
            return render(request, "canciones/editar_cancion.html", context)
            
        cancion.artista = request.POST.get('artista')
        cancion.album = request.POST.get('album')
        try:
            # Convertir a int, si está vacío o no es un número, se asigna None
            cancion.ano_lanzamiento = int(request.POST.get('ano_lanzamiento')) if request.POST.get('ano_lanzamiento') else None
        except (ValueError, TypeError):
            messages.error(request, "El año de lanzamiento debe ser un número válido.")
            # Volver a renderizar el formulario con el mensaje de error y los datos actuales
            context = {
                "cancion": cancion, # Pasa la canción con los datos actuales para rellenar el formulario
                "name": name,
                "is_authenticated": True
            }
            return render(request, "canciones/editar_cancion.html", context)

        cancion.es_favorita = 'es_favorita' in request.POST # True si el checkbox está marcado
        cancion.save()
        messages.success(request, f"Canción '{cancion.titulo}' actualizada exitosamente.")
        # Redirigir a la lista de canciones del usuario
        return redirect('canciones:lista_canciones', name=name)

    # Si es una petición GET, renderiza el formulario con los datos actuales de la canción
    context = {
        "cancion": cancion,
        "name": name,
        "is_authenticated": True
    }
    return render(request, "canciones/editar_cancion.html", context)


def borrar_cancion(request, name, id):
    # Verificar si el usuario está logueado
    if 'nombre_usuario' not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder a esta página.")
        return redirect('login')

    # Asegurar que el usuario en la URL es el dueño de la sesión y de la canción
    if request.session.get('nombre_usuario') != name:
        messages.error(request, "Acceso no autorizado para borrar la canción de otro usuario.")
        return redirect('login')

    user = get_object_or_404(Usuario, nombre=name)
    
    # Obtener la relación específica para asegurar que la canción le pertenece a este usuario
    relacion = get_object_or_404(UsuarioCancion, usuario=user, cancion__id=id)
    cancion_titulo = relacion.cancion.titulo # Guarda el título antes de borrarla

    if request.method == 'POST':
        relacion.delete() # Borra la relación entre el usuario y la canción
        messages.info(request, f"Canción '{cancion_titulo}' eliminada de tus favoritos.")
    
    # Redirigir a la lista de canciones del usuario después de borrar (GET o POST)
    return redirect('canciones:lista_canciones', name=name)


# --- Vistas Públicas ---
def vista_publica_canciones(request):
    """
    Muestra una lista de todas las canciones marcadas como favoritas (es_favorita=True).
    Accesible sin necesidad de autenticación.
    """
    canciones_favoritas_publicas = Cancion.objects.filter(es_favorita=True).distinct().order_by('titulo')

    context = {
        "canciones": canciones_favoritas_publicas,
        "is_authenticated": 'nombre_usuario' in request.session # Para mostrar/ocultar elementos en la plantilla
    }
    return render(request, "canciones/vista_publica_canciones.html", context)

def detalle_cancion_publico(request, cancion_id):
    """
    Muestra los detalles de una canción específica que es favorita.
    Accesible sin autenticación.
    """
    cancion = get_object_or_404(Cancion, id=cancion_id, es_favorita=True)

    context = {
        "cancion": cancion,
        "is_authenticated": 'nombre_usuario' in request.session
    }
    return render(request, "canciones/detalle_cancion_publico.html", context)
from django.shortcuts import render, redirect, get_object_or_404
import uuid
from datetime import date
from django.contrib import messages
from django.urls import reverse

from .models import Cancion, Usuario, UsuarioCancion

# --- Vistas de Autenticación ---

def login(request):
    """
    Maneja el inicio de sesión de usuarios.
    Si el usuario ya está en sesión, redirige a su lista de canciones.
    Procesa el formulario de login (POST) o muestra el formulario (GET).
    """
    # 1. Comprueba si el usuario ya está en sesión. Si sí, redirige a su lista de canciones.
    if 'nombre_usuario' in request.session:
        return redirect(reverse('canciones:lista_canciones', kwargs={'name': request.session['nombre_usuario']}))

    # 2. Si es una petición POST (envío de formulario de login)
    if request.method == 'POST':
        name = request.POST['nombre']
        password = request.POST['pass']
        try:
            # Intenta encontrar el usuario en la BD con el nombre y contraseña proporcionados
            usuario = Usuario.objects.get(nombre=name, contrasena=password)
            request.session['nombre_usuario'] = usuario.nombre # Almacena el nombre de usuario en la sesión
            messages.success(request, f"¡Bienvenido de nuevo, {usuario.nombre}!")
            return redirect(reverse('canciones:lista_canciones', kwargs={'name': usuario.nombre}))
        except Usuario.DoesNotExist:
            # Si no se encuentra una combinación de usuario/contraseña, muestra un error.
            messages.error(request, "Usuario o contraseña incorrectos.")
            # Vuelve a renderizar el formulario de login para que el usuario intente de nuevo
            return render(request, "canciones/trueIndex.html")
    # 3. Si es una petición GET (primera vez que carga la página de login)
    # Simplemente renderiza la plantilla del formulario de login
    return render(request, "canciones/trueIndex.html")


def register(request):
    """
    Maneja el registro de nuevos usuarios.
    Procesa el formulario de registro (POST) o muestra el formulario (GET).
    Incluye validaciones para el nombre de usuario (no vacío, no solo espacios, único) y contraseña.
    """
    # Si es una petición POST (envío de formulario de registro)
    if request.method == 'POST':
        nombre_usuario = request.POST.get('nombre')
        contrasena = request.POST.get('pass')

        # --- VALIDACIONES DE BACKEND PARA REGISTRO ---
        # 1. Valida que el nombre de usuario no esté vacío o solo contenga espacios
        if not nombre_usuario or not nombre_usuario.strip():
            messages.error(request, "El nombre de usuario no puede estar vacío ni contener solo espacios.")
            # Vuelve a renderizar con el nombre de usuario previo para que el usuario no tenga que reescribirlo
            return render(request, "canciones/register.html", {'nombre_usuario_previo': nombre_usuario})
        
        # 2. Valida si el nombre de usuario ya existe en la base de datos
        if Usuario.objects.filter(nombre=nombre_usuario).exists():
            messages.error(request, "Este usuario ya existe. Por favor, elige otro nombre.")
            return render(request, "canciones/register.html", {'nombre_usuario_previo': nombre_usuario})
        
        # 3. Valida la longitud de la contraseña
        if not contrasena or len(contrasena) < 3:
            messages.error(request, "La contraseña debe tener al menos 3 caracteres.")
            return render(request, "canciones/register.html", {'nombre_usuario_previo': nombre_usuario})
        # --- FIN DE VALIDACIONES ---

        # Si todas las validaciones pasan, crea un nuevo usuario
        usuario = Usuario(
            nombre = nombre_usuario,
            contrasena = contrasena,
            uuid = uuid.uuid4(), # Genera un UUID único para el usuario
            fecha_registro=date.today()
        )
        usuario.save() # Guarda el nuevo usuario en la base de datos
        messages.success(request, "Cuenta registrada exitosamente. Ahora puedes iniciar sesión.")
        return redirect('login') # Redirige al usuario a la página de login
    
    # Si es una petición GET, simplemente renderiza el formulario de registro
    return render(request, "canciones/register.html")


def logout_view(request):
    """
    Cierra la sesión del usuario eliminando su nombre de usuario de la sesión.
    Redirige a la página de login.
    """
    if 'nombre_usuario' in request.session:
        del request.session['nombre_usuario'] # Elimina el nombre de usuario de la sesión
    messages.info(request, "Has cerrado sesión exitosamente.")
    return redirect('login')


# --- Vistas de CRUD de Canciones (Área Privada - Requiere Autenticación) ---

def lista_canciones(request, name):
    """
    Muestra la lista de canciones favoritas de un usuario específico.
    Requiere que el usuario esté autenticado y que el nombre en la URL coincida con el usuario logueado.
    """
    # Control de acceso: Verifica si el usuario está logueado
    if 'nombre_usuario' not in request.session:
        messages.error(request, "Debes iniciar sesión para acceder a esta página.")
        return redirect('login')
    
    # Control de acceso: Verifica si el usuario logueado es el dueño de la lista que intenta ver
    if request.session.get('nombre_usuario') != name:
        messages.error(request, "Acceso no autorizado a la lista de otro usuario.")
        return redirect('login')

    # Obtiene el objeto Usuario o devuelve un 404 si no existe
    usuario = get_object_or_404(Usuario, nombre=name)
    
    # Obtiene todas las canciones relacionadas con este usuario a través de UsuarioCancion
    # Se usa un diccionario para pasar la clave_relacion junto con el objeto Cancion a la plantilla
    canciones_favoritas = {rel.clave_relacion: rel.cancion for rel in usuario.canciones_favoritas.all()}
    
    context = {
        "canciones": canciones_favoritas,
        "name": name, # Pasa el nombre del usuario a la plantilla
        "is_authenticated": True # Indica que el usuario está autenticado para la lógica de la plantilla
    }
    return render(request, "canciones/listar_canciones.html", context)


def crear_cancion(request, name):
    """
    Maneja la creación de una nueva canción para el usuario autenticado.
    Procesa el formulario de creación (POST) o muestra el formulario (GET).
    """
    # Control de acceso
    if 'nombre_usuario' not in request.session or request.session.get('nombre_usuario') != name:
        messages.error(request, "Acceso no autorizado.")
        return redirect('login')

    user = get_object_or_404(Usuario, nombre=name)

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        artista = request.POST.get('artista')
        album = request.POST.get('album')
        ano_lanzamiento_str = request.POST.get('ano_lanzamiento')
        # Determina si el checkbox 'es_favorita' fue marcado.
        # Esto se usará para el campo 'es_favorita' de la tabla global 'Cancion'.
        es_favorita_global = 'es_favorita' in request.POST 

        # --- VALIDACIONES PARA LA CREACIÓN DE CANCIONES ---
        if not titulo or not titulo.strip():
            messages.error(request, "El título de la canción es obligatorio y no puede estar vacío.")
            # Se mantienen los datos para rellenar el formulario si hay un error
            context = {
                "name": name,
                "is_authenticated": True,
                "current_year": date.today().year,
                "cancion": { # Datos de la canción que se intentó crear para rellenar el formulario
                    'titulo': titulo,
                    'artista': artista,
                    'album': album,
                    'ano_lanzamiento': ano_lanzamiento_str,
                    'es_favorita': es_favorita_global # Pasa el estado del checkbox
                }
            }
            return render(request, "canciones/crear_cancion.html", context)

        # Verifica si el usuario ya tiene una canción con este título en su lista
        if UsuarioCancion.objects.filter(usuario=user, cancion__titulo=titulo).exists():
            messages.error(request, f"Ya tienes una canción llamada '{titulo}' en tus favoritos.")
            context = { # Se mantienen los datos para rellenar el formulario si hay un error
                "name": name,
                "is_authenticated": True,
                "current_year": date.today().year,
                "cancion": {
                    'titulo': titulo,
                    'artista': artista,
                    'album': album,
                    'ano_lanzamiento': ano_lanzamiento_str,
                    'es_favorita': es_favorita_global
                }
            }
            return render(request, "canciones/crear_cancion.html", context)

        try:
            # Convierte el año a entero; None si está vacío
            ano_lanzamiento = int(ano_lanzamiento_str) if ano_lanzamiento_str else None
            # Valida el rango del año si se proporcionó
            if ano_lanzamiento is not None and (ano_lanzamiento < 1900 or ano_lanzamiento > date.today().year):
                messages.error(request, f"El año de lanzamiento debe estar entre 1900 y {date.today().year}.")
                context = { # Se mantienen los datos para rellenar el formulario si hay un error
                    "name": name,
                    "is_authenticated": True,
                    "current_year": date.today().year,
                    "cancion": {
                        'titulo': titulo,
                        'artista': artista,
                        'album': album,
                        'ano_lanzamiento': ano_lanzamiento_str,
                        'es_favorita': es_favorita_global
                    }
                }
                return render(request, "canciones/crear_cancion.html", context)

        except ValueError:
            messages.error(request, "El año de lanzamiento debe ser un número válido.")
            context = { # Se mantienen los datos para rellenar el formulario si hay un error
                "name": name,
                "is_authenticated": True,
                "current_year": date.today().year,
                "cancion": {
                    'titulo': titulo,
                    'artista': artista,
                    'album': album,
                    'ano_lanzamiento': ano_lanzamiento_str,
                    'es_favorita': es_favorita_global
                }
            }
            return render(request, "canciones/crear_cancion.html", context)
        # --- FIN DE VALIDACIONES ---

        # Si todas las validaciones pasan, crea o actualiza la Cancion en la tabla global
        # Se usa get_or_create para evitar duplicados en la tabla `Cancion` (global)
        cancion, created = Cancion.objects.get_or_create(
            titulo=titulo,
            artista=artista if artista else '', # Usar cadena vacía para get_or_create si es nulo
            album=album if album else '',
            defaults={
                'ano_lanzamiento': ano_lanzamiento,
                'es_favorita': es_favorita_global, # Aquí se asigna el valor del checkbox
                'fecha_agregada': date.today()
            }
        )
        # Si la canción ya existía, actualiza sus campos (incluyendo es_favorita)
        if not created: 
            cancion.ano_lanzamiento = ano_lanzamiento
            cancion.es_favorita = es_favorita_global # Asegura que se actualice si ya existe
            cancion.save()

        # Luego, crea la relación UsuarioCancion si no existe
        try:
            UsuarioCancion.objects.create(usuario=user, cancion=cancion, clave_relacion=uuid.uuid4())
            messages.success(request, f"Canción '{cancion.titulo}' agregada a tus favoritos.")
        except Exception: 
            messages.info(request, f"La canción '{cancion.titulo}' ya estaba en tus favoritos.")

        return redirect('canciones:lista_canciones', name=name)

    # Para peticiones GET, renderiza el formulario vacío
    context = {
        "name": name,
        "is_authenticated": True,
        "current_year": date.today().year # Pasa el año actual para la validación max del input
    }
    return render(request, "canciones/crear_cancion.html", context)


def editar_cancion(request, name, id):
    """
    Maneja la edición de una canción existente para el usuario autenticado.
    Requiere que el usuario esté autenticado y sea el dueño de la canción.
    """
    # Control de acceso
    if 'nombre_usuario' not in request.session or request.session.get('nombre_usuario') != name:
        messages.error(request, "Acceso no autorizado.")
        return redirect('login')

    user = get_object_or_404(Usuario, nombre=name)
    # Obtiene la relación UsuarioCancion para asegurar que la canción pertenece a este usuario
    relacion = get_object_or_404(UsuarioCancion, usuario=user, cancion__id=id)
    cancion = relacion.cancion # Accede al objeto Cancion a través de la relación

    if request.method == 'POST':
        # Actualiza los campos de la canción con los datos del formulario
        nuevo_titulo = request.POST.get('titulo')
        nuevo_artista = request.POST.get('artista')
        nuevo_album = request.POST.get('album')
        nuevo_ano_lanzamiento_str = request.POST.get('ano_lanzamiento')
        nueva_es_favorita_global = 'es_favorita' in request.POST # Obtiene el estado del checkbox

        # --- VALIDACIONES PARA LA EDICIÓN DE CANCIONES ---
        if not nuevo_titulo or not nuevo_titulo.strip():
            messages.error(request, "El título de la canción no puede estar vacío.")
            # Asegúrate de pasar la canción con los datos actuales para rellenar el formulario
            context = {"cancion": cancion, "name": name, "is_authenticated": True, "current_year": date.today().year}
            return render(request, "canciones/editar_cancion.html", context)
        
        # Validar si el nuevo título ya existe en otra canción del MISMO usuario
        # Se excluye la canción que se está editando actualmente (cancion.id)
        if UsuarioCancion.objects.filter(
            usuario=user, 
            cancion__titulo=nuevo_titulo
        ).exclude(cancion=cancion).exists():
            messages.error(request, f"Ya tienes otra canción con el título '{nuevo_titulo}'.")
            context = {"cancion": cancion, "name": name, "is_authenticated": True, "current_year": date.today().year}
            return render(request, "canciones/editar_cancion.html", context)

        try:
            nuevo_ano_lanzamiento = int(nuevo_ano_lanzamiento_str) if nuevo_ano_lanzamiento_str else None
            if nuevo_ano_lanzamiento is not None and (nuevo_ano_lanzamiento < 1900 or nuevo_ano_lanzamiento > date.today().year):
                messages.error(request, f"El año de lanzamiento debe estar entre 1900 y {date.today().year}.")
                context = {"cancion": cancion, "name": name, "is_authenticated": True, "current_year": date.today().year}
                return render(request, "canciones/editar_cancion.html", context)
        except ValueError:
            messages.error(request, "El año de lanzamiento debe ser un número válido.")
            context = {"cancion": cancion, "name": name, "is_authenticated": True, "current_year": date.today().year}
            return render(request, "canciones/editar_cancion.html", context)
        # --- FIN DE VALIDACIONES ---

        # Asigna los nuevos valores y guarda la canción en la tabla global `Cancion`
        cancion.titulo = nuevo_titulo
        cancion.artista = nuevo_artista
        cancion.album = nuevo_album
        cancion.ano_lanzamiento = nuevo_ano_lanzamiento
        cancion.es_favorita = nueva_es_favorita_global # Aquí se asigna el valor del checkbox
        cancion.save()

        messages.success(request, f"Canción '{cancion.titulo}' actualizada exitosamente.")
        return redirect('canciones:lista_canciones', name=name)

    # Para peticiones GET, renderiza el formulario con los datos actuales de la canción
    context = {
        "cancion": cancion, # Pasa el objeto canción para rellenar el formulario
        "name": name,
        "is_authenticated": True,
        "current_year": date.today().year
    }
    return render(request, "canciones/editar_cancion.html", context)


def borrar_cancion(request, name, id):
    """
    Maneja la eliminación de una canción de la lista de favoritos de un usuario.
    Solo elimina la relación UsuarioCancion, no la canción de la tabla global Cancion.
    Requiere que el usuario esté autenticado y sea el dueño de la relación.
    """
    # Control de acceso
    if 'nombre_usuario' not in request.session or request.session.get('nombre_usuario') != name:
        messages.error(request, "Acceso no autorizado.")
        return redirect('login')

    user = get_object_or_404(Usuario, nombre=name)
    # Obtiene la relación UsuarioCancion específica para el usuario y el ID de canción
    relacion = get_object_or_404(UsuarioCancion, usuario=user, cancion__id=id)
    cancion_titulo = relacion.cancion.titulo # Guarda el título antes de borrar la relación

    if request.method == 'POST':
        relacion.delete() # Elimina la relación, no la canción en sí
        messages.info(request, f"Canción '{cancion_titulo}' eliminada de tus favoritos.")
    
    # Redirige siempre a la lista de canciones del usuario
    return redirect('canciones:lista_canciones', name=name)


# --- Vistas Públicas (No Requieren Autenticación) ---

def vista_publica_canciones(request):
    """
    Muestra una lista de todas las canciones marcadas como 'es_favorita=True'.
    Accesible para cualquier persona, esté o no autenticada.
    """
    # Filtra las canciones que están marcadas como favoritas globalmente
    # .distinct() asegura que no haya duplicados si una canción estuviera agregada múltiples veces por diferentes usuarios y marcada como favorita.
    # .order_by('titulo') las ordena alfabéticamente por título.
    canciones_favoritas_publicas = Cancion.objects.filter(es_favorita=True).distinct().order_by('titulo')
    
    context = {
        "canciones": canciones_favoritas_publicas,
        # Pasa el estado de autenticación para que la plantilla pueda ajustar el header (ej. mostrar login/register)
        "is_authenticated": 'nombre_usuario' in request.session 
    }
    return render(request, "canciones/vista_publica_canciones.html", context)


def detalle_cancion_publico(request, cancion_id):
    """
    Muestra los detalles de una canción pública específica.
    Accesible para cualquier persona, siempre y cuando la canción esté marcada como pública.
    """
    # Obtiene la canción por su ID, pero solo si también está marcada como favorita (pública).
    # Esto evita que se puedan ver detalles de canciones privadas de un usuario si se adivina el ID.
    cancion = get_object_or_404(Cancion, id=cancion_id, es_favorita=True)
    
    context = {
        "cancion": cancion,
        "is_authenticated": 'nombre_usuario' in request.session
    }
    return render(request, "canciones/detalle_cancion_publico.html", context)

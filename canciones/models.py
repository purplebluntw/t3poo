from django.db import models
from datetime import date
import uuid as uuid_lib # Importamos uuid con un alias para evitar conflictos con el nombre de campo

class Cancion(models.Model):
    titulo = models.CharField(max_length=200, default="Sin título") # Cambiado de TextField a CharField, y max_length aumentado
    artista = models.CharField(max_length=100, blank=True, null=True) # Nuevo campo: Artista
    album = models.CharField(max_length=100, blank=True, null=True) # Nuevo campo: Álbum
    ano_lanzamiento = models.IntegerField(blank=True, null=True) # Nuevo campo: Año de lanzamiento
    es_favorita = models.BooleanField(default=False) # Cambiado de 'completado' a 'es_favorita'
    fecha_agregada = models.DateField(default=date.today) # Cambiado de 'fecha' a 'fecha_agregada'
    #uuid = models.TextField(max_length=200, default="Sin uuid") # Eliminamos este uuid de la canción, la relación lo manejará

    def __str__(self):
        return f"{self.titulo} por {self.artista if self.artista else 'Artista Desconocido'}"

class Usuario(models.Model):
    nombre = models.CharField(max_length=100, unique=True) # Cambiado a CharField y añadido unique=True para nombres de usuario
    contrasena = models.CharField(max_length=100) # Cambiado a contrasena (sin ñ) y CharField
    uuid = models.UUIDField(default=uuid_lib.uuid4, editable=False, unique=True) # Usamos UUIDField nativo de Django
    fecha_registro = models.DateField(default=date.today) # Cambiado de 'fecha' a 'fecha_registro'

    def __str__(self):
        return self.nombre

class UsuarioCancion(models.Model): # Cambiado de usuarioTarea a UsuarioCancion
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="canciones_favoritas") # Cambiado related_name
    cancion = models.ForeignKey(Cancion, on_delete=models.CASCADE) # Cambiado de tarea a cancion
    clave_relacion = models.CharField(max_length=100, unique=True, default=uuid_lib.uuid4) # Cambiado de 'clave' a 'clave_relacion', y default a uuid. Tambien unique
    # Nota: `clave_relacion` puede ser útil si necesitas una ID única para la relación en sí misma,
    # aunque a menudo no es estrictamente necesario si ya tienes el id de la Cancion y el Usuario.
    # Lo mantenemos por ahora siguiendo la estructura original con 'clave'.

    class Meta:
        unique_together = ('usuario', 'cancion') # Asegura que un usuario no pueda agregar la misma canción dos veces

    def save(self, *args, **kwargs):
        if not self.clave_relacion:
            self.clave_relacion = str(uuid_lib.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.usuario.nombre} - {self.cancion.titulo}"
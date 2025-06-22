from django.contrib import admin

# canciones/admin.py # MODIFICADO
from django.contrib import admin

from .models import Cancion # MODIFICADO

admin.site.register(Cancion) # MODIFICADO
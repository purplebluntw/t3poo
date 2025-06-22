from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import Cancion, Usuario # MODIFICADO
#Aprender bien
@receiver(pre_delete, sender=Usuario)
def borrar_canciones_relacionadas(sender, instance, **kwargs): # MODIFICADO
    canciones = Cancion.objects.filter( # MODIFICADO
        id__in = instance.tiene.values_list('cancion_id', flat=True) # MODIFICADO
    )
    canciones.delete() # MODIFICADO
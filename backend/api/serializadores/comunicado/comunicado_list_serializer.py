from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from api.models import Comunicado


class ComunicadoListSerializer(serializers.ModelSerializer):
    """
    Serializador de salida optimizado para la lectura y presentación de comunicados.

    Actúa como la capa de transformación de los datos extraídos de la base de datos 
    hacia el cliente HTTP (frontend). Su objetivo es garantizar que la información 
    se devuelva en un formato amigable y legible para el usuario final, traduciendo 
    los datos internos y relaciones a representaciones textuales de solo lectura.

    Transformaciones principales aplicadas:
        - Tipos de datos (tipo_display): Resuelve el valor interno del campo de opciones (choices) a su etiqueta legible.
        - Relaciones (areas_interes): Serializa la relación Many-To-Many (M2M) devolviendo un listado de nombres en lugar de IDs.
        - Campos dinámicos (autor_nombre): Construye y formatea el nombre completo del emisor en tiempo de ejecución, con "Secretaría" como valor de respaldo (fallback).
    """
    tipo_display = serializers.CharField(source='get_tipo_comunicacion_display', read_only=True)
    areas_interes = serializers.SerializerMethodField()
    autor_nombre = serializers.SerializerMethodField()


    class Meta:
        model = Comunicado
        fields = [
            'id', 'titulo', 'contenido', 'fecha_emision', 'imagen_portada',
            'tipo_comunicacion', 'tipo_display', 'autor_nombre', 
            'areas_interes'
        ]


    def get_autor_nombre(self, obj):
        """
        Calcula y formatea el nombre visible del autor del comunicado.

        Este método alimenta el campo dinámico `autor_nombre`. Extrae la información 
        del usuario vinculado, priorizando su nombre de pila y primer apellido. 
        En caso de que falten datos, aplica un sistema de respaldo (fallback): 
        usa el nombre de usuario (username) si el nombre real no está disponible, 
        y devuelve una etiqueta institucional si el comunicado carece de autor explícito.

        Args:
            obj (Comunicado): La instancia del modelo `Comunicado` que se está serializando.

        Returns:
            str: El nombre formateado del autor (ej. "Juan Pérez"). Si no hay 
                autor asociado, devuelve la cadena por defecto "Secretaría".
        """
        try:
            autor = obj.autor
            
            if autor:
                nombre_raw = getattr(autor, 'nombre', None) or getattr(autor, 'username', None) or ""
                nombre = str(nombre_raw).strip()
                
                ap1_raw = getattr(autor, 'primer_apellido', '') or ""
                ap1 = str(ap1_raw).strip()

                if not nombre and not ap1:
                    return "Secretaría"

                return f"{nombre} {ap1}".strip()
                
        except Exception: 
            pass
            
        return "Secretaría"


    def get_areas_interes(self, obj):
        """
        Serializa las áreas de interés capturando posibles fallos 
        en la representación de texto (__str__) del modelo.
        """
        nombres_areas = []
        for area in obj.areas_interes.all():
            try:
                nombres_areas.append(str(area))
            except Exception:
                nombres_areas.append(f"Área (ID: {area.id})")
                
        return nombres_areas
from rest_framework import serializers

from api.models import CuerpoPertenencia, PapeletaSitio, Tramo

class FilaTablaInsigniaSerializer(serializers.Serializer):
    dni = serializers.CharField(max_length=9)
    estado = serializers.CharField(max_length=50)
    fecha_solicitud = serializers.DateTimeField(format="%d/%m/%Y %H:%M", allow_null=True)
    acto = serializers.CharField(max_length=100)
    es_solicitud_insignia = serializers.BooleanField()
    preferencia = serializers.CharField(max_length=200)



class HistorialPapeletaSerializer(serializers.ModelSerializer):
    nombre_acto = serializers.CharField(source='acto.nombre', read_only=True)
    fecha_acto = serializers.DateTimeField(source='acto.fecha', read_only=True)

    nombre_puesto = serializers.CharField(source='puesto.nombre', read_only=True, allow_null=True)
    nombre_tramo = serializers.CharField(source='tramo.nombre', read_only=True, allow_null=True)
    numero_tramo = serializers.IntegerField(source='tramo.numero_orden', read_only=True, allow_null=True)

    es_insignia = serializers.BooleanField(source='puesto.tipo_puesto.es_insignia', read_only=True, default=False)
    tipo_acto = serializers.CharField(source='acto.tipo_acto.tipo', read_only=True)

    lugar_citacion = serializers.CharField(source='puesto.lugar_citacion', read_only=True, allow_null=True)
    hora_citacion = serializers.TimeField(source='puesto.hora_citacion', read_only=True, allow_null=True)

    lado_display = serializers.CharField(source='get_lado_display', read_only=True)

    class Meta:
        model = PapeletaSitio
        fields = [
            'id',
            'acto',
            'estado_papeleta', 
            'fecha_solicitud', 
            'fecha_emision', 
            'anio',
            'tipo_acto',
            'nombre_acto',
            'fecha_acto',
            'nombre_puesto',
            'nombre_tramo',
            'numero_tramo',
            'es_insignia',
            'lugar_citacion',
            'hora_citacion',
            'orden_en_tramo',
            'lado',
            'lado_display'
        ]



class PapeletaSitioSerializer(serializers.ModelSerializer):
    """
    Este es un serializer crítico. Aquí validamos la integridad de la solicitud
    antes de que pase a la capa de servicio.
    """
    nombre_hermano = serializers.CharField(source='hermano.nombre', read_only=True)
    apellidos_hermano = serializers.SerializerMethodField()
    nombre_acto = serializers.CharField(source='acto.nombre', read_only=True)
    nombre_puesto = serializers.CharField(source='puesto.nombre', read_only=True)

    tramo_display = serializers.CharField(source='tramo.__str__', read_only=True)
    nombre_vinculado = serializers.SerializerMethodField()

    lado_display = serializers.CharField(source='get_lado_display', read_only=True)
    
    tramo_id = serializers.PrimaryKeyRelatedField(
        queryset=Tramo.objects.all(), 
        source='tramo', 
        write_only=True, 
        required=False,
        allow_null=True
    )

    class Meta:
        model = PapeletaSitio
        fields = [
            'id', 'estado_papeleta', 'es_solicitud_insignia',
            'fecha_solicitud', 'fecha_emision', 'codigo_verificacion', 
            'anio', 'hermano', 'nombre_hermano', 'apellidos_hermano',
            'acto', 'nombre_acto', 
            'puesto', 'nombre_puesto', 'tramo_display', 'tramo_id',
            'vinculado_a', 'nombre_vinculado',
            'orden_en_tramo', 
            'lado', 
            'lado_display'
        ]
        read_only_fields = ['fecha_emision', 'codigo_verificacion', 'anio', 'tramo_display', 'nombre_vinculado', 'orden_en_tramo', 'lado', 'lado_display']

    def get_apellidos_hermano(self, obj):
        return f"{obj.hermano.primer_apellido} {obj.hermano.segundo_apellido}"
    
    def get_nombre_vinculado(self, obj):
        if obj.vinculado_a:
            return f"{obj.vinculado_a.nombre} {obj.vinculado_a.primer_apellido} {obj.vinculado_a.segundo_apellido} (Nº {obj.vinculado_a.numero_registro})"
        return None

    def validate(self, data):
        """
        Validación de integridad de datos (Data Integrity).
        La lógica de negocio compleja (ej. cálculo de antigüedad) va al Service,
        pero la coherencia básica de los datos va aquí.
        """
        puesto = data.get('puesto')
        acto = data.get('acto')
        hermano = data.get('hermano')
        tramo = data.get('tramo')
        
        if puesto and acto:
            if puesto.acto != acto:
                raise serializers.ValidationError({
                    "puesto": "El puesto seleccionado no pertenece al acto indicado."
                })

        if puesto and not puesto.disponible:
            raise serializers.ValidationError({
                "puesto": "El puesto seleccionado no está marcado como disponible."
            })
        
        if puesto and puesto.tipo_puesto.solo_junta_gobierno:
            es_miembro_junta = hermano.pertenencias_cuerpos.filter(
                cuerpo__nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
            ).exists()

            if not es_miembro_junta:
                raise serializers.ValidationError({
                    "puesto": f"El puesto '{puesto.nombre}' ({puesto.tipo_puesto.nombre_tipo}) está reservado exclusivamente para miembros de la Junta de Gobierno."
                })
            
        if tramo and acto:
            if tramo.acto != acto:
                raise serializers.ValidationError({
                    "tramo_id": f"El tramo {tramo} no pertenece al acto {acto.nombre}."
                })

        return data
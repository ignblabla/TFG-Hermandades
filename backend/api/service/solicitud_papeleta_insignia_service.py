import uuid
from django.utils import timezone
from django.core.exceptions import ValidationError
from ..serializers import SolicitudInsigniaSerializer
from ..models import CuerpoPertenencia, PapeletaSitio


class SolicitudPapeletaService:
    def crear_solicitud_insignia(self, user, data):
        """
        Gestiona la lógica completa para crear una solicitud de insignia.
        Recibe: usuario (request.user) y data (request.data).
        Retorna: La instancia de PapeletaSitio creada.
        """
        self._validar_pertenencia_cuerpos(user)
        serializer = SolicitudInsigniaSerializer(data=data, context={'request': {'user': user}})

        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        acto = validated_data['acto']
        preferencias = validated_data['preferencias']

        self._validar_reglas_acto(acto)
        self._validar_solicitud_unica(user, acto)
        self._validar_son_insignias(preferencias)

        datos_extra = {
            'hermano': user,
            'anio': acto.fecha.year,
            'fecha_solicitud': timezone.now(),
            'estado_papeleta': PapeletaSitio.EstadoPapeleta.SOLICITADA,
            'es_solicitud_insignia': True,
            'numero_papeleta': None,
            'codigo_verificacion': uuid.uuid4().hex[:8].upper()
        }

        papeleta = serializer.save(**datos_extra)
        return papeleta



    def _validar_solicitud_unica(self, user, acto):
        existe_solicitud = PapeletaSitio.objects.filter(
            hermano = user,
            acto = acto
        ).exclude(
            estado_papeleta = PapeletaSitio.EstadoPapeleta.ANULADA
        ).exists()

        if existe_solicitud:
            raise ValidationError(f"Ya tiene una solicitud de papeleta activa para el acto '{acto.nombre}'.")


    def _validar_pertenencia_cuerpos(self, user):
        """
        Regla: Solo pueden solicitar usuarios de NAZARENOS, PRIOSTÍA, JUVENTUD, CARIDAD 
        O que NO pertenezcan a ningún cuerpo.
        """
        cuerpos_permitidos = [
            CuerpoPertenencia.NombreCuerpo.NAZARENOS,
            CuerpoPertenencia.NombreCuerpo.CARIDAD_ACCION_SOCIAL,
            CuerpoPertenencia.NombreCuerpo.JUVENTUD,
            CuerpoPertenencia.NombreCuerpo.PRIOSTÍA
        ]

        mis_cuerpos = user.pertenencias_cuerpos.all()

        if not mis_cuerpos.exists():
            return True
        
        tiene_permiso = any(hc.cuerpo.nombre_cuerpo in cuerpos_permitidos for hc in mis_cuerpos)

        if not tiene_permiso:
            raise ValidationError("Su perfil no cumple los requisitos de pertenencia a cuerpos para solicitar insignia.")
        


    def _validar_reglas_acto(self, acto):
        """
        Valida fechas y configuración del Acto.
        """
        if not acto.tipo_acto.requiere_papeleta:
            raise ValidationError(f"El acto '{acto.nombre}' no tiene habilitada la solicitud de papeletas.")
        
        ahora = timezone.now()

        if not acto.inicio_solicitud or not acto.fin_solicitud:
            raise ValidationError("El plazo de solicitud no está configurado para este acto.")
        
        if ahora < acto.inicio_solicitud:
            raise ValidationError(f"El plazo de solicitud aún no ha comenzado. Empieza el {acto.inicio_solicitud}.")
        
        if ahora > acto.fin_solicitud:
            raise ValidationError(f"El plazo de solicitud finalizó el {acto.fin_solicitud}.")
        


    def _validar_son_insignias(self, preferencias):
        """
        Regla: Solo se pueden escoger puestos donde TipoPuesto.es_insignia = True
        """
        for item in preferencias:
            puesto = item['puesto']
            if not getattr(puesto.tipo_puesto, 'es_insignia', False):
                raise ValidationError(f"El puesto '{puesto.nombre}' no está catalogado como Insignia y no puede solicitarse por esta vía.")
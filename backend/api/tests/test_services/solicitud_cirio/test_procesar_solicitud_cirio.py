from datetime import datetime, timedelta, timezone as py_timezone
from enum import Enum
from unittest.mock import PropertyMock, patch, MagicMock
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from api.servicios.solicitud_cirio.solicitud_cirio_service import SolicitudCirioTradicionalService
from api.models import Acto, CuerpoPertenencia, Hermano, PapeletaSitio


class TestSolicitudCirioTradicionalService(TestCase):

    def setUp(self):
        self.service = SolicitudCirioTradicionalService()
        self.ahora = timezone.now()
        self.service._qs_papeletas_activas = MagicMock()

    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.timezone')
    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.Hermano')
    @patch.object(SolicitudCirioTradicionalService, '_validar_configuracion_acto_tradicional')
    @patch.object(SolicitudCirioTradicionalService, '_validar_plazo_vigente')
    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_apto_para_solicitar')
    @patch.object(SolicitudCirioTradicionalService, '_validar_item_puesto_cirio')
    @patch.object(SolicitudCirioTradicionalService, '_gestionar_conflicto_insignia_y_unicidad')
    @patch.object(SolicitudCirioTradicionalService, '_crear_papeleta_base')
    @patch.object(SolicitudCirioTradicionalService, '_procesar_vinculacion')
    def test_flujo_completo_ok(
        self,
        mock_procesar_vinculacion,
        mock_crear_papeleta_base,
        mock_gestionar_conflicto,
        mock_validar_puesto,
        mock_validar_apto,
        mock_validar_plazo,
        mock_validar_acto,
        mock_hermano_model,
        mock_timezone
    ):
        """
        Test: Flujo completo OK

        Given: Todo válido, sin conflicto de insignia, sin vinculación.
        When: Se procesa la solicitud de cirio tradicional.
        Then: Devuelve papeleta con papeleta.puesto asignado.
        """
        mock_ahora = MagicMock()
        mock_timezone.now.return_value = mock_ahora

        mock_hermano = MagicMock(pk=1)

        mock_hermano.cuerpos.values_list.return_value = ['CuerpoNazarenos']

        mock_acto = MagicMock()
        mock_puesto = MagicMock()

        mock_hermano_model.objects.select_for_update.return_value.only.return_value.get.return_value = mock_hermano

        mock_gestionar_conflicto.return_value = None

        mock_papeleta = MagicMock()
        mock_crear_papeleta_base.return_value = mock_papeleta

        resultado = self.service.procesar_solicitud_cirio_tradicional(
            hermano=mock_hermano,
            acto=mock_acto,
            puesto=mock_puesto,
            numero_registro_vinculado=None
        )

        mock_validar_acto.assert_called_once_with(mock_acto)
        mock_validar_plazo.assert_called_once_with(
            mock_ahora, mock_acto.inicio_solicitud_cirios, mock_acto.fin_solicitud_cirios, "cirios"
        )
        mock_validar_apto.assert_called_once_with(mock_hermano, {'CuerpoNazarenos'}, mock_ahora)
        mock_validar_puesto.assert_called_once_with({'CuerpoNazarenos'}, mock_acto, mock_puesto)
        mock_gestionar_conflicto.assert_called_once_with(mock_hermano, mock_acto, mock_puesto)

        mock_crear_papeleta_base.assert_called_once_with(mock_hermano, mock_acto, mock_ahora)
        
        self.assertEqual(mock_papeleta.puesto, mock_puesto)
        mock_papeleta.save.assert_called_once_with(update_fields=['puesto'])

        self.assertEqual(resultado, mock_papeleta)

        mock_procesar_vinculacion.assert_not_called()



    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.timezone')
    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.Hermano')
    @patch.object(SolicitudCirioTradicionalService, '_validar_configuracion_acto_tradicional')
    @patch.object(SolicitudCirioTradicionalService, '_validar_plazo_vigente')
    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_apto_para_solicitar')
    @patch.object(SolicitudCirioTradicionalService, '_validar_item_puesto_cirio')
    @patch.object(SolicitudCirioTradicionalService, '_gestionar_conflicto_insignia_y_unicidad')
    @patch.object(SolicitudCirioTradicionalService, '_crear_papeleta_base')
    @patch.object(SolicitudCirioTradicionalService, '_procesar_vinculacion')
    def test_con_vinculacion_llama_a_procesar_vinculacion(
        self, 
        mock_procesar_vinculacion, 
        mock_crear_base, 
        mock_conflicto, 
        mock_validar_item, 
        mock_validar_apto, 
        mock_validar_plazo, 
        mock_validar_acto, 
        mock_hermano_model, 
        mock_timezone
    ):
        """
        Test: Con vinculación

        Given: Un número de registro vinculado presente en la llamada.
        When: Se procesa la solicitud exitosamente.
        Then: Se debe invocar el método interno _procesar_vinculacion con los datos correctos.
        """
        mock_hermano = MagicMock(pk=1)
        mock_acto = MagicMock()
        mock_puesto = MagicMock()
        mock_papeleta_nueva = MagicMock()
        num_vinculado = 12345

        mock_hermano_model.objects.select_for_update.return_value.only.return_value.get.return_value = mock_hermano
        mock_conflicto.return_value = None
        mock_crear_base.return_value = mock_papeleta_nueva

        self.service.procesar_solicitud_cirio_tradicional(
            hermano=mock_hermano,
            acto=mock_acto,
            puesto=mock_puesto,
            numero_registro_vinculado=num_vinculado
        )

        mock_procesar_vinculacion.assert_called_once_with(
            mock_hermano, mock_acto, mock_papeleta_nueva, mock_puesto, num_vinculado
        )



    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.timezone')
    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.PapeletaSitio')
    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.Hermano')
    @patch.object(SolicitudCirioTradicionalService, '_validar_configuracion_acto_tradicional')
    @patch.object(SolicitudCirioTradicionalService, '_validar_plazo_vigente')
    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_apto_para_solicitar')
    @patch.object(SolicitudCirioTradicionalService, '_validar_item_puesto_cirio')
    @patch.object(SolicitudCirioTradicionalService, '_gestionar_conflicto_insignia_y_unicidad')
    @patch.object(SolicitudCirioTradicionalService, '_crear_papeleta_base')
    def test_conflicto_con_insignia_anulacion_correcta(
        self, 
        mock_crear_base, 
        mock_conflicto, 
        mock_validar_item, 
        mock_validar_apto, 
        mock_validar_plazo, 
        mock_validar_acto, 
        mock_hermano_model, 
        mock_papeleta_model,
        mock_timezone
    ):
        """
        Test: Conflicto con insignia → anulación correcta

        Given: Un hermano que ya tiene una solicitud de insignia en conflicto.
        When: Se procesa la nueva solicitud de cirio.
        Then: La solicitud de insignia previa debe actualizarse a ANULADA y el flujo debe continuar.
        """
        mock_hermano = MagicMock(pk=1)
        mock_acto = MagicMock()
        mock_puesto = MagicMock()

        mock_solicitud_previa = MagicMock(pk=99)
        mock_conflicto.return_value = mock_solicitud_previa

        mock_queryset = mock_papeleta_model.objects.select_for_update.return_value.filter.return_value
        mock_queryset.update.return_value = 1

        mock_hermano_model.objects.select_for_update.return_value.only.return_value.get.return_value = mock_hermano
        mock_crear_base.return_value = MagicMock()

        self.service.procesar_solicitud_cirio_tradicional(mock_hermano, mock_acto, mock_puesto)

        mock_papeleta_model.objects.select_for_update.return_value.filter.assert_called_once_with(
            pk=99,
            estado_papeleta=mock_papeleta_model.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=True,
            hermano=mock_hermano,
            acto=mock_acto,
        )

        mock_queryset.update.assert_called_once_with(
            estado_papeleta=mock_papeleta_model.EstadoPapeleta.ANULADA
        )

        mock_crear_base.assert_called_once()



    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.timezone')
    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.PapeletaSitio')
    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.Hermano')
    @patch.object(SolicitudCirioTradicionalService, '_validar_configuracion_acto_tradicional')
    @patch.object(SolicitudCirioTradicionalService, '_validar_plazo_vigente')
    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_apto_para_solicitar')
    @patch.object(SolicitudCirioTradicionalService, '_validar_item_puesto_cirio')
    @patch.object(SolicitudCirioTradicionalService, '_gestionar_conflicto_insignia_y_unicidad')
    def test_error_en_anulacion_por_concurrencia_lanza_validation_error(
        self, 
        mock_conflicto, 
        mock_validar_item, 
        mock_validar_apto, 
        mock_validar_plazo, 
        mock_validar_acto, 
        mock_hermano_model, 
        mock_papeleta_model,
        mock_timezone
    ):
        """
        Test: Error en anulación por concurrencia

        Given: Una solicitud de insignia detectada como conflicto.
        When: Se intenta actualizar a ANULADA pero el ORM devuelve 0 filas afectadas.
        Then: Se debe lanzar un ValidationError alertando del cambio de estado durante el proceso.
        """
        mock_hermano = MagicMock(pk=1)
        mock_acto = MagicMock()
        mock_puesto = MagicMock()

        mock_solicitud_previa = MagicMock(pk=99)
        mock_conflicto.return_value = mock_solicitud_previa

        mock_queryset = mock_papeleta_model.objects.select_for_update.return_value.filter.return_value
        mock_queryset.update.return_value = 0

        mock_hermano_model.objects.select_for_update.return_value.only.return_value.get.return_value = mock_hermano

        mensaje_esperado = "Tu solicitud de insignia cambió de estado durante el proceso. Vuelve a intentarlo o contacta con secretaría."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service.procesar_solicitud_cirio_tradicional(mock_hermano, mock_acto, mock_puesto)



    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.timezone')
    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.Hermano')
    @patch.object(SolicitudCirioTradicionalService, '_validar_configuracion_acto_tradicional')
    @patch.object(SolicitudCirioTradicionalService, '_validar_plazo_vigente')
    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_apto_para_solicitar')
    @patch.object(SolicitudCirioTradicionalService, '_validar_item_puesto_cirio')
    @patch.object(SolicitudCirioTradicionalService, '_gestionar_conflicto_insignia_y_unicidad')
    @patch.object(SolicitudCirioTradicionalService, '_crear_papeleta_base')
    def test_integrity_error_al_crear_papeleta_lanza_validation_error(
        self, 
        mock_crear_base, 
        mock_conflicto, 
        mock_validar_item, 
        mock_validar_apto, 
        mock_validar_plazo, 
        mock_validar_acto, 
        mock_hermano_model, 
        mock_timezone
    ):
        """
        Test: IntegrityError al crear papeleta

        Given: Un intento de crear la papeleta base en la base de datos.
        When: El ORM lanza un IntegrityError (ej. violación de unicidad por doble petición).
        Then: El error debe capturarse y transformarse en un ValidationError amigable para el usuario.
        """
        mock_hermano = MagicMock(pk=1)
        mock_acto = MagicMock()
        mock_puesto = MagicMock()

        mock_conflicto.return_value = None
        mock_hermano_model.objects.select_for_update.return_value.only.return_value.get.return_value = mock_hermano

        mock_crear_base.side_effect = IntegrityError("UNIQUE constraint failed")

        mensaje_esperado = "Ya existe una papeleta activa para este acto. Si has pulsado dos veces, espera unos segundos y recarga."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service.procesar_solicitud_cirio_tradicional(mock_hermano, mock_acto, mock_puesto)


    # -------------------------------------------------------------------------
    # TEST VALIDAR CONFIGURACIÓN ACTO TRADICIONAL
    # -------------------------------------------------------------------------

    def test_acto_valido_no_lanza_excepcion(self):
        """
        Test: Acto válido → no lanza excepción

        Given: Un acto que no es None, con tipo_acto_id, que requiere papeleta 
            y cuya modalidad es TRADICIONAL.
        When: Se valida la configuración del acto.
        Then: El método termina su ejecución sin lanzar ninguna excepción.
        """
        acto_dummy = MagicMock()
        acto_dummy.tipo_acto_id = 1
        acto_dummy.tipo_acto.requiere_papeleta = True

        acto_dummy.modalidad = "TRADICIONAL" 

        try:
            self.service._validar_configuracion_acto_tradicional(acto_dummy)
        except Exception as e:
            self.fail(f"La validación falló y lanzó una excepción inesperada: {e}")



    def test_acto_es_none_lanza_error_especifico(self):
        """
        Test: Acto es None

        Given: Un valor None en lugar de una instancia de Acto.
        When: Se intenta validar la configuración.
        Then: Lanza ValidationError con el diccionario {"tipo_acto": "..."}.
        """
        acto_nulo = None
        mensaje_esperado = "El tipo de acto es obligatorio."

        with self.assertRaises(ValidationError) as cm:
            self.service._validar_configuracion_acto_tradicional(acto_nulo)

        self.assertEqual(cm.exception.message_dict["tipo_acto"], [mensaje_esperado])



    def test_acto_no_requiere_papeleta_lanza_error(self):
        """
        Test: No requiere papeleta

        Given: Un acto llamado "Convivencia" configurado con requiere_papeleta = False.
        When: Se intenta validar la configuración.
        Then: Lanza ValidationError con el nombre del acto en el mensaje.
        """
        acto_dummy = MagicMock()
        acto_dummy.nombre = "Convivencia"
        acto_dummy.tipo_acto_id = 1
        acto_dummy.tipo_acto.requiere_papeleta = False
        
        mensaje_esperado = "El acto 'Convivencia' no admite solicitudes de papeleta."

        with self.assertRaises(ValidationError) as cm:
            self.service._validar_configuracion_acto_tradicional(acto_dummy)

        self.assertIn(mensaje_esperado, cm.exception.messages)



    def test_modalidad_incorrecta_lanza_error(self):
        """
        Test: Modalidad incorrecta

        Given: Un acto con modalidad distinta a TRADICIONAL (ej. "INSIGNIA").
        When: Se intenta validar la configuración.
        Then: Lanza ValidationError indicando la exclusividad del proceso.
        """
        acto_dummy = MagicMock()
        acto_dummy.tipo_acto_id = 1
        acto_dummy.tipo_acto.requiere_papeleta = True
        acto_dummy.modalidad = "INSIGNIA" 
        
        mensaje_esperado = "Este proceso es exclusivo para actos de modalidad TRADICIONAL."

        with self.assertRaises(ValidationError) as cm:
            self.service._validar_configuracion_acto_tradicional(acto_dummy)
        
        self.assertIn(mensaje_esperado, cm.exception.messages)



    # -------------------------------------------------------------------------
    # TEST VALIDAR PLAZO VIGENTE
    # -------------------------------------------------------------------------

    def test_dentro_del_rango_valido_no_lanza_excepcion(self):
        """
        Test: Dentro del rango válido → no error

        Given: Un momento 'ahora' que está exactamente entre el inicio y el fin.
        When: Se valida el plazo vigente.
        Then: El método termina sin lanzar ninguna excepción.
        """
        inicio = self.ahora - timedelta(days=1)
        fin = self.ahora + timedelta(days=1)
        nombre_plazo = "cirios"

        try:
            self.service._validar_plazo_vigente(self.ahora, inicio, fin, nombre_plazo)
        except ValidationError as e:
            self.fail(f"_validar_plazo_vigente lanzó ValidationError inesperadamente: {e}")



    def test_falta_configuracion_plazo_fin_lanza_error(self):
        """
        Test: Falta fin (Escenario B)

        Given: Un plazo donde el fin es None.
        When: Se intenta validar la vigencia.
        Then: Lanza ValidationError indicando que no está configurado.
        """
        inicio = self.ahora - timedelta(days=1)
        fin = None
        nombre = "papeletas"
        mensaje_esperado = f"El plazo de {nombre} no está configurado en el acto."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_plazo_vigente(self.ahora, inicio, fin, nombre)



    def test_plazo_aun_no_ha_comenzado_lanza_error(self):
        """
        Test: Aún no ha comenzado

        Given: Un momento 'ahora' que es anterior a la fecha de inicio.
        When: Se valida la vigencia del plazo.
        Then: Lanza ValidationError indicando que el plazo no ha empezado.
        """
        inicio = self.ahora + timedelta(days=1)
        fin = self.ahora + timedelta(days=5)
        nombre = "insignias"
        mensaje_esperado = f"El plazo de solicitud de {nombre} aún no ha comenzado."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_plazo_vigente(self.ahora, inicio, fin, nombre)



    def test_plazo_finalizado_lanza_error(self):
        """
        Test: Plazo finalizado

        Given: Un momento 'ahora' que es posterior a la fecha de fin.
        When: Se valida la vigencia del plazo.
        Then: Lanza ValidationError indicando que el plazo ha terminado.
        """
        inicio = self.ahora - timedelta(days=10)
        fin = self.ahora - timedelta(days=1)
        nombre = "cirios"
        mensaje_esperado = f"El plazo de solicitud de {nombre} ha finalizado."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_plazo_vigente(self.ahora, inicio, fin, nombre)



    def test_limite_exacto_inicio_es_valido(self):
        """
        Test: Límite inferior inclusivo
        Si ahora es exactamente igual al inicio, debe permitirlo.
        """
        self.service._validar_plazo_vigente(self.ahora, self.ahora, self.ahora + timedelta(hours=1), "test")



    def test_limite_exacto_fin_es_valido(self):
        """
        Test: Límite superior inclusivo
        Si ahora es exactamente igual al fin, debe permitirlo.
        """
        self.service._validar_plazo_vigente(self.ahora, self.ahora - timedelta(hours=1), self.ahora, "test")



    # -------------------------------------------------------------------------
    # TEST VALIDAR HERMANO APTO PARA SOLICITAR
    # -------------------------------------------------------------------------

    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_en_alta')
    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_al_corriente_hasta_anio_anterior')
    @patch.object(SolicitudCirioTradicionalService, '_validar_pertenencia_cuerpos')
    def test_llama_a_todas_las_validaciones_de_hermano(
        self, mock_pertenencia, mock_corriente, mock_alta
    ):
        """
        Test: Llama a las 3 validaciones correctamente

        Given: Un hermano y un set de cuerpos.
        When: Se ejecuta la validación de aptitud del hermano.
        Then: Se deben invocar los tres métodos internos de validación exactamente una vez.
        """
        mock_hermano = MagicMock()
        mock_cuerpos = {1, 2}
        ahora = timezone.now()

        self.service._validar_hermano_apto_para_solicitar(mock_hermano, mock_cuerpos, ahora)

        mock_alta.assert_called_once_with(mock_hermano)
        mock_corriente.assert_called_once_with(mock_hermano, ahora)
        mock_pertenencia.assert_called_once_with(mock_cuerpos)



    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_en_alta')
    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_al_corriente_hasta_anio_anterior')
    @patch.object(SolicitudCirioTradicionalService, '_validar_pertenencia_cuerpos')
    def test_orden_logico_de_validaciones_hermano(
        self, mock_pertenencia, mock_corriente, mock_alta
    ):
        """
        Test: Verificar orden de ejecución

        Given: Un flujo de validación de hermano.
        When: Se ejecuta la orquestación.
        Then: El orden debe ser estrictamente: alta -> corriente -> pertenencia.
        """
        manager = MagicMock()
        manager.attach_mock(mock_alta, 'alta')
        manager.attach_mock(mock_corriente, 'corriente')
        manager.attach_mock(mock_pertenencia, 'pertenencia')

        self.service._validar_hermano_apto_para_solicitar(MagicMock(), set(), timezone.now())

        nombres_llamadas = [call[0] for call in manager.mock_calls]
        self.assertEqual(nombres_llamadas, ['alta', 'corriente', 'pertenencia'])



    # -------------------------------------------------------------------------
    # TEST VALIDAR HERMANO EN ALTA
    # -------------------------------------------------------------------------

    def test_hermano_en_estado_alta_no_lanza_excepcion(self):
        """
        Test: Hermano en estado ALTA → válido

        Given: Un objeto hermano cuyo estado es estrictamente 'ALTA'.
        When: Se valida si el hermano está en alta.
        Then: El método termina su ejecución sin lanzar ninguna excepción.
        """
        hermano_dummy = MagicMock()

        hermano_dummy.estado_hermano = "ALTA" 

        try:
            self.service._validar_hermano_en_alta(hermano_dummy)
        except ValidationError as e:
            self.fail(f"_validar_hermano_en_alta lanzó ValidationError inesperadamente: {e}")



    def test_hermano_en_estado_no_activo_lanza_error(self):
        """
        Test: Hermano en estado distinto a ALTA (BAJA)

        Given: Un objeto hermano cuyo estado es 'BAJA'.
        When: Se valida si el hermano está en alta.
        Then: Lanza ValidationError con el mensaje de restricción.
        """
        hermano_dummy = MagicMock()
        hermano_dummy.estado_hermano = "BAJA"
        mensaje_esperado = "Solo los hermanos en estado ALTA pueden solicitar papeleta."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_hermano_en_alta(hermano_dummy)



    # -------------------------------------------------------------------------
    # TEST VALIDAR HERMANO AL CORRIENTE DE PAGO HASTA EL AÑO ANTERIOR
    # -------------------------------------------------------------------------

    def test_hermano_al_corriente_con_historial_no_lanza_error(self):
        """
        Test: Hermano al corriente y con historial → OK

        Given: Un hermano que no tiene deudas en años anteriores (deuda=None)
            pero que sí tiene historial de cuotas (exists=True).
        When: Se valida su situación de tesorería.
        Then: El método termina sin lanzar ninguna excepción.
        """
        mock_hermano = MagicMock()
        ahora = MagicMock()
        ahora.date().year = 2026 

        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = None

        mock_hermano.cuotas.filter.return_value.exists.return_value = True

        try:
            self.service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano, ahora)
        except ValidationError as e:
            self.fail(f"Se lanzó ValidationError inesperadamente: {e}")

        llamadas_filter = mock_hermano.cuotas.filter.call_args_list
        self.assertEqual(llamadas_filter[0].kwargs['anio__lte'], 2025)



    def test_deuda_pendiente_anio_anterior_lanza_error_con_anio_especifico(self):
        """
        Test: Tiene deuda pendiente/devuelta

        Given: Un hermano con una cuota en estado PENDIENTE del año 2024.
        When: Se valida la situación de tesorería en el año 2026.
        Then: Lanza ValidationError con el mensaje formateado con el año 2024.
        """
        mock_hermano = MagicMock()
        ahora = MagicMock()
        ahora.date().year = 2026 

        anio_deuda = 2024
        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = {
            'anio': anio_deuda
        }

        mensaje_esperado = (
            f"Consta una cuota pendiente o devuelta del año {anio_deuda}. "
            f"Por favor, contacte con mayordomía para regularizar su situación."
        )

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano, ahora)

        mock_hermano.cuotas.filter.return_value.exists.assert_not_called()



    def test_sin_historial_de_cuotas_lanza_error_con_anio_limite(self):
        """
        Test: No tiene historial de cuotas

        Given: Un hermano que no tiene deudas registradas (deuda=None)
            pero que tampoco tiene ninguna cuota en el sistema (exists=False).
        When: Se valida la situación de tesorería en el año 2026.
        Then: Lanza ValidationError indicando la falta de historial hasta 2025.
        """
        mock_hermano = MagicMock()
        ahora = MagicMock()
        ahora.date().year = 2026 

        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = None

        mock_hermano.cuotas.filter.return_value.exists.return_value = False

        anio_limite_esperado = 2025
        mensaje_esperado = (
            f"No constan cuotas registradas hasta el año {anio_limite_esperado}. "
            "Contacte con secretaría para verificar su ficha."
        )

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano, ahora)

        ultimo_filtro = mock_hermano.cuotas.filter.call_args_list[-1]
        self.assertEqual(ultimo_filtro.kwargs['anio__lte'], anio_limite_esperado)



    # -------------------------------------------------------------------------
    # TEST VALIDAR PERTENENCIA A CUERPOS
    # -------------------------------------------------------------------------

    def test_sin_cuerpos_asignados_es_valido_early_return(self):
        """
        Test: Sin cuerpos → válido (early return)

        Given: Un conjunto de cuerpos vacío (set()).
        When: Se valida la pertenencia de cuerpos.
        Then: El método termina inmediatamente sin lanzar excepciones.
        """
        cuerpos_vacios = set()

        try:
            self.service._validar_pertenencia_cuerpos(cuerpos_vacios)
        except ValidationError as e:
            self.fail(f"_validar_pertenencia_cuerpos lanzó ValidationError inesperadamente: {e}")



    def test_solo_cuerpos_permitidos_no_lanza_excepcion(self):
        """
        Test: Solo cuerpos permitidos

        Given: Un conjunto de cuerpos que están dentro de la lista blanca 
            (ej. NAZARENOS y JUVENTUD).
        When: Se valida la pertenencia.
        Then: El método no lanza ninguna excepción.
        """
        cuerpos_hermano = {"NAZARENOS", "JUVENTUD"}

        try:
            self.service._validar_pertenencia_cuerpos(cuerpos_hermano)
        except ValidationError as e:
            self.fail(f"_validar_pertenencia_cuerpos falló con cuerpos permitidos: {e}")



    def test_multiples_cuerpos_prohibidos_lanza_error_ordenado_alfabeticamente(self):
        """
        Test: Múltiples cuerpos no permitidos

        Given: Un hermano que pertenece a 'PENITENTES' y 'ACÓLITOS' (ambos prohibidos).
        When: Se valida la pertenencia.
        Then: Lanza ValidationError con ambos cuerpos ordenados: 'ACÓLITOS, PENITENTES'.
        """
        cuerpos_hermano = {"PENITENTES", "ACÓLITOS"}
        mensaje_esperado = "Tu pertenencia a los siguientes cuerpos no permite solicitar esta papeleta: ACÓLITOS, PENITENTES"

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_pertenencia_cuerpos(cuerpos_hermano)



    def test_mezcla_permitido_y_no_permitido_solo_reporta_infractor(self):
        """
        Test: Mezcla de permitidos y no permitidos

        Given: Un set con un cuerpo válido (JUVENTUD) y uno no válido (ACÓLITOS).
        When: Se valida la pertenencia a cuerpos.
        Then: Lanza ValidationError que menciona ÚNICAMENTE a ACÓLITOS.

        """
        cuerpos_hermano = {"JUVENTUD", "ACÓLITOS"}

        mensaje_esperado = "Tu pertenencia a los siguientes cuerpos no permite solicitar esta papeleta: ACÓLITOS"

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_pertenencia_cuerpos(cuerpos_hermano)

        try:
            self.service._validar_pertenencia_cuerpos(cuerpos_hermano)
        except ValidationError as e:
            self.assertNotIn("JUVENTUD", str(e))



    # -------------------------------------------------------------------------
    # TEST VALIDAR PUESTO CIRIOS
    # -------------------------------------------------------------------------

    def test_puesto_valido_pasa_todas_las_validaciones(self):
        """
        Test: Puesto válido → no lanza excepción

        Given: Un puesto que:
            - Existe.
            - Pertenece al acto actual.
            - No es una insignia.
            - Está marcado como disponible.
            - No tiene restricciones de Junta de Gobierno.
        When: Se valida el ítem del puesto de cirio.
        Then: No debe lanzar ninguna ValidationError.
        """
        mock_acto = MagicMock()
        mock_acto.id = 1

        mock_puesto = MagicMock()
        mock_puesto.acto_id = 1
        mock_puesto.nombre = "Cirio de Tramo 1"
        mock_puesto.disponible = True

        mock_puesto.tipo_puesto.es_insignia = False
        mock_puesto.tipo_puesto.solo_junta_gobierno = False

        cuerpos_hermano = {"NAZARENOS"}

        try:
            self.service._validar_item_puesto_cirio(
                cuerpos_hermano, mock_acto, mock_puesto
            )
        except ValidationError as e:
            self.fail(f"_validar_item_puesto_cirio lanzó error con datos válidos: {e}")



    def test_puesto_pertenece_a_otro_acto_lanza_error(self):
        """
        Test: Puesto no pertenece al acto

        Given: Un acto con ID 10 y un puesto cuyo acto_id es 99.
        When: Se valida la coherencia entre puesto y acto.
        Then: Lanza ValidationError con el mensaje 'El puesto no pertenece a este acto.'
        """
        mock_acto = MagicMock()
        mock_acto.id = 10
        
        mock_puesto = MagicMock()
        mock_puesto.acto_id = 99
        
        cuerpos_hermano = set()

        with self.assertRaisesMessage(ValidationError, "El puesto no pertenece a este acto."):
            self.service._validar_item_puesto_cirio(
                cuerpos_hermano, mock_acto, mock_puesto
            )



    def test_puesto_tipo_insignia_lanza_error_especifico(self):
        """
        Test: El puesto es una insignia

        Given: Un puesto cuyo tipo_puesto está marcado como insignia.
        When: Se intenta validar para una solicitud de cirio.
        Then: Lanza ValidationError indicando que es una insignia y no puede solicitarse.
        """
        mock_acto = MagicMock(id=1)
        
        mock_puesto = MagicMock()
        mock_puesto.acto_id = 1
        mock_puesto.nombre = "SIMPECADO"
        mock_puesto.tipo_puesto.es_insignia = True
        
        cuerpos_hermano = set()
        
        mensaje_esperado = f"El puesto '{mock_puesto.nombre}' es una Insignia. No puede solicitarse en este formulario."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_item_puesto_cirio(
                cuerpos_hermano, mock_acto, mock_puesto
            )



    def test_puesto_no_disponible_lanza_error(self):
        """
        Test: Puesto no disponible

        Given: Un puesto con el flag 'disponible' en False.
        When: Se intenta validar para la solicitud.
        Then: Lanza ValidationError indicando que no está disponible.
        """
        mock_acto = MagicMock(id=1)
        mock_puesto = MagicMock(acto_id=1, nombre="Cirio Tramo 4", disponible=False)
        mock_puesto.tipo_puesto.es_insignia = False
        
        mensaje_esperado = f"El puesto '{mock_puesto.nombre}' no está marcado como disponible."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_item_puesto_cirio(set(), mock_acto, mock_puesto)



    def test_puesto_exclusivo_junta_sin_pertenencia_lanza_error(self):
        """
        Test: Puesto exclusivo Junta de Gobierno sin permiso

        Given: Un puesto marcado como 'solo_junta_gobierno' y un hermano
            que no pertenece a dicho cuerpo.
        When: Se valida la solicitud.
        Then: Lanza ValidationError con el mensaje de exclusividad.
        """
        mock_acto = MagicMock(id=1)
        mock_puesto = MagicMock(acto_id=1, nombre="Vara de Oficial")
        mock_puesto.disponible = True
        mock_puesto.tipo_puesto.es_insignia = False
        mock_puesto.tipo_puesto.solo_junta_gobierno = True

        cuerpos_hermano = {"NAZARENOS"}
        
        mensaje_esperado = f"El puesto '{mock_puesto.nombre}' es exclusivo para la Junta de Gobierno."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_item_puesto_cirio(cuerpos_hermano, mock_acto, mock_puesto)



    def test_hermano_junta_gobierno_puede_solicitar_puesto_exclusivo(self):
        """
        Test: Junta de Gobierno SÍ puede acceder

        Given: Un puesto marcado como 'solo_junta_gobierno' y un hermano
            que pertenece efectivamente al cuerpo 'JUNTA_GOBIERNO'.
        When: Se valida la solicitud del puesto.
        Then: No debe lanzar ninguna ValidationError.
        """
        mock_acto = MagicMock(id=1)
        mock_puesto = MagicMock(acto_id=1, nombre="Vara de Mayordomo")
        mock_puesto.disponible = True
        mock_puesto.tipo_puesto.es_insignia = False
        mock_puesto.tipo_puesto.solo_junta_gobierno = True

        cuerpos_hermano = {CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO.value}

        try:
            self.service._validar_item_puesto_cirio(
                cuerpos_hermano, mock_acto, mock_puesto
            )
        except ValidationError as e:
            self.fail(f"Se bloqueó a un miembro de la Junta de Gobierno injustamente: {e}")



    def test_puesto_nulo_lanza_error_de_seleccion_obligatoria(self):
        """
        Test para cubrir la línea: if not puesto: raise ValidationError(...)
        
        Given: Un valor nulo (None) en lugar de un objeto Puesto.
        When: Se invoca la validación del ítem del puesto.
        Then: El sistema debe detectar la ausencia del objeto y lanzar una 
            ValidationError con el mensaje "Debe seleccionar un puesto válido."
        """
        mock_acto = MagicMock()
        cuerpos_hermano = set()
        puesto_nulo = None

        with self.assertRaisesMessage(ValidationError, "Debe seleccionar un puesto válido."):
            self.service._validar_item_puesto_cirio(
                cuerpos_hermano, 
                mock_acto, 
                puesto_nulo
            )



    # -------------------------------------------------------------------------
    # TEST GESTIONAR CONFLICTO INSIGNIA Y UNICIDAD
    # -------------------------------------------------------------------------

    def test_sin_papeletas_previas_no_hay_conflicto_y_retorna_none(self):
        """
        Test: No hay conflictos → devuelve None

        Given: Un hermano que no tiene ninguna papeleta activa para el acto.
        When: Se gestionan los conflictos de insignia y unicidad.
        Then: El método retorna None (no hay nada que anular ni razón para bloquear).
        """
        mock_hermano = MagicMock()
        mock_acto = MagicMock()
        mock_puesto_nuevo = MagicMock()

        self.service._qs_papeletas_activas = MagicMock()

        mock_qs = self.service._qs_papeletas_activas.return_value
        mock_qs.select_for_update.return_value.filter.return_value = []

        resultado = self.service._gestionar_conflicto_insignia_y_unicidad(
            mock_hermano, mock_acto, mock_puesto_nuevo
        )

        self.assertIsNone(resultado)

        mock_qs.select_for_update.assert_called_once()



    def test_insignia_solicitada_previa_se_retorna_para_anulacion(self):
        """
        Test: Existe insignia SOLICITADA → se retorna para anular

        Given: Una papeleta activa que es una solicitud de insignia 
            en estado SOLICITADA.
        When: Se gestiona el conflicto con un nuevo puesto de cirio.
        Then: Retorna dicha papeleta para que el service proceda a anularla.
        """
        mock_hermano = MagicMock()
        mock_acto = MagicMock()
        mock_puesto_nuevo = MagicMock()

        self.service._qs_papeletas_activas = MagicMock()

        mock_papeleta_insignia = MagicMock()
        mock_papeleta_insignia.es_solicitud_insignia = True
        mock_papeleta_insignia.estado_papeleta = PapeletaSitio.EstadoPapeleta.SOLICITADA

        mock_qs = self.service._qs_papeletas_activas.return_value
        mock_qs.select_for_update.return_value.filter.return_value = [mock_papeleta_insignia]

        resultado = self.service._gestionar_conflicto_insignia_y_unicidad(
            mock_hermano, mock_acto, mock_puesto_nuevo
        )

        self.assertEqual(resultado, mock_papeleta_insignia)



    def test_insignia_confirmada_previa_bloquea_solicitud_de_cirio(self):
        """
        Test: Insignia YA asignada (bloqueo total)

        Given: Una papeleta previa de insignia en estado EMITIDA.
        When: El hermano intenta solicitar un nuevo cirio para el mismo acto.
        Then: Lanza ValidationError indicando que ya tiene una insignia asignada.
        """
        mock_hermano = MagicMock()
        mock_acto = MagicMock()
        mock_puesto_nuevo = MagicMock()

        p_insignia_confirmada = MagicMock(
            es_solicitud_insignia=True,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.EMITIDA
        )

        mock_qs = self.service._qs_papeletas_activas.return_value
        mock_qs.select_for_update.return_value.filter.return_value = [p_insignia_confirmada]

        mensaje_esperado = "Ya tienes asignada una Insignia para este acto. No puedes solicitar cirio o cruz de penitente."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._gestionar_conflicto_insignia_y_unicidad(
                mock_hermano, mock_acto, mock_puesto_nuevo
            )



    def test_solicitud_duplicada_del_mismo_tipo_de_puesto_lanza_error(self):
        """
        Test: Papeleta activa del mismo tipo de puesto

        Given: El hermano ya tiene una solicitud de 'Cirio de Tramo'.
        When: Intenta pedir otro puesto que también es de tipo 'Cirio de Tramo'.
        Then: Lanza ValidationError mencionando el nombre del tipo de puesto.
        """
        mock_hermano = MagicMock()
        mock_acto = MagicMock()

        tipo_comun = MagicMock(id=50, nombre_tipo="Cirio de Tramo")

        mock_puesto_nuevo = MagicMock()
        mock_puesto_nuevo.tipo_puesto = tipo_comun

        p_existente = MagicMock(es_solicitud_insignia=False)
        p_existente.puesto.tipo_puesto = tipo_comun

        mock_qs = self.service._qs_papeletas_activas.return_value
        mock_qs.select_for_update.return_value.filter.return_value = [p_existente]

        mensaje_esperado = f"Ya tienes una solicitud activa para '{tipo_comun.nombre_tipo}'."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._gestionar_conflicto_insignia_y_unicidad(
                mock_hermano, mock_acto, mock_puesto_nuevo
            )



    def test_solicitud_de_tipo_distinto_bloquea_por_unicidad_de_sitio(self):
        """
        Test: Papeleta activa de tipo diferente (conflicto general)

        Given: El hermano tiene una solicitud de 'Cirio' (tipo_id=1).
        When: Intenta pedir un puesto de 'Cruz de Penitente' (tipo_id=2).
        Then: Lanza ValidationError indicando que solo puede tener una solicitud de sitio.
        """
        mock_hermano = MagicMock()
        mock_acto = MagicMock()

        mock_puesto_nuevo = MagicMock()
        mock_puesto_nuevo.tipo_puesto.id = 2

        p_existente = MagicMock(es_solicitud_insignia=False)
        p_existente.puesto.tipo_puesto.id = 1

        self.service._qs_papeletas_activas = MagicMock()
        mock_qs = self.service._qs_papeletas_activas.return_value
        mock_qs.select_for_update.return_value.filter.return_value = [p_existente]

        mensaje_esperado = "Solo puedes tener una solicitud de sitio (no puedes pedir Cirio y Penitente a la vez)."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._gestionar_conflicto_insignia_y_unicidad(
                mock_hermano, mock_acto, mock_puesto_nuevo
            )



    # -------------------------------------------------------------------------
    # TEST CREAR PAPELETA BASE
    # -------------------------------------------------------------------------

    @patch("api.models.PapeletaSitio.objects.create")
    @patch("uuid.uuid4")
    def test_crear_papeleta_base_con_datos_validos(self, mock_uuid, mock_create):
        """
        Test: Crea papeleta correctamente

        Given: Un hermano, un acto (con fecha en 2026) y una fecha de solicitud.
        When: Se llama a _crear_papeleta_base.
        Then:
            - Se llama a objects.create con los parámetros correctos.
            - El año se extrae correctamente del acto.
            - El código de verificación es un UUID truncado en mayúsculas.
            - Retorna la instancia creada por el ORM.
        """
        mock_hermano = MagicMock()
        mock_acto = MagicMock()
        mock_acto.fecha.year = 2026
        fecha_ahora = timezone.now()

        mock_uuid_obj = MagicMock()
        mock_uuid_obj.hex = "abcdef1234567890"
        mock_uuid.return_value = mock_uuid_obj

        mock_papeleta_esperada = MagicMock(spec=PapeletaSitio)
        mock_create.return_value = mock_papeleta_esperada

        resultado = self.service._crear_papeleta_base(
            mock_hermano, mock_acto, fecha_ahora
        )

        mock_create.assert_called_once_with(
            hermano=mock_hermano,
            acto=mock_acto,
            anio=2026,
            fecha_solicitud=fecha_ahora,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            vinculado_a=None,
            es_solicitud_insignia=False,
            codigo_verificacion="ABCDEF12"
        )

        self.assertEqual(resultado, mock_papeleta_esperada)



    # -------------------------------------------------------------------------
    # TEST PROCESAR VINCULACIÓN
    # -------------------------------------------------------------------------

    @patch("api.models.Hermano.objects.get")
    def test_procesar_vinculacion_correcta_actualiza_y_guarda(self, mock_hermano_get):
        """
        Test: Vinculación correcta (happy path)

        Given: Dos hermanos (el solicitante más antiguo que el objetivo),
            el objetivo tiene 1 papeleta válida del mismo tipo y sección,
            y el solicitante no tiene dependientes.
        When: Se procesa la vinculación.
        Then: La papeleta del solicitante actualiza su campo 'vinculado_a'
            y se guarda correctamente.
        """
        mock_acto = MagicMock()
        mock_acto.modalidad = Acto.ModalidadReparto.TRADICIONAL

        mock_hermano = MagicMock(id=1, numero_registro=100)
        mock_hermano_objetivo = MagicMock(id=2, numero_registro=500)

        mock_hermano_get.return_value = mock_hermano_objetivo

        mock_mi_puesto = MagicMock(tipo_puesto_id=1, cortejo_cristo=True)
        mock_mi_papeleta = MagicMock()

        mock_puesto_objetivo = MagicMock(tipo_puesto_id=1, cortejo_cristo=True)
        mock_papeleta_objetivo = MagicMock(es_solicitud_insignia=False, puesto=mock_puesto_objetivo)
        mock_papeleta_objetivo.puesto.tipo_puesto.es_insignia = False

        self.service._qs_papeletas_activas = MagicMock()
        mock_base_qs = self.service._qs_papeletas_activas.return_value

        qs_objetivo = mock_base_qs.select_for_update.return_value.filter.return_value.order_by.return_value
        qs_objetivo.count.return_value = 1
        qs_objetivo.get.return_value = mock_papeleta_objetivo

        qs_dependientes = mock_base_qs.filter.return_value
        qs_dependientes.exists.return_value = False

        self.service._procesar_vinculacion(
            mock_hermano, mock_acto, mock_mi_papeleta, mock_mi_puesto, 500
        )

        self.assertEqual(mock_mi_papeleta.vinculado_a, mock_hermano_objetivo)

        mock_mi_papeleta.save.assert_called_once_with(update_fields=['vinculado_a'])



    @patch("api.models.Hermano.objects.get")
    def test_vinculacion_falla_si_el_solicitante_es_mas_nuevo_que_el_objetivo(self, mock_hermano_get):
        """
        Test: hermano “más nuevo” intenta vincularse a uno antiguo

        Given: El solicitante es el Nº 5000 (nuevo) y el objetivo es el Nº 100 (antiguo).
        When: Se intenta procesar la vinculación.
        Then: Lanza ValidationError indicando que solo el antiguo puede vincularse al nuevo.
        """
        mock_acto = MagicMock(modalidad=Acto.ModalidadReparto.TRADICIONAL)

        mock_hermano_nuevo = MagicMock(id=1, numero_registro=5000)
        mock_hermano_antiguo = MagicMock(id=2, numero_registro=100)
        
        mock_hermano_get.return_value = mock_hermano_antiguo

        mensaje_esperado = f"Tú (Nº 5000) eres más nuevo que el Nº 100."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._procesar_vinculacion(
                mock_hermano_nuevo, mock_acto, MagicMock(), MagicMock(), 100
            )



    @patch("api.models.Hermano.objects.get")
    def test_vinculacion_falla_si_el_solicitante_ya_tiene_hermanos_vinculados_a_el(self, mock_hermano_get):
        """
        Test: el usuario ya tiene dependientes

        Given: El solicitante (A) ya es el 'objetivo' de otras papeletas existentes.
        When: El solicitante intenta vincularse a un tercero (B).
        Then: Lanza ValidationError impidiendo cadenas de tipo A->B->C.
        """
        mock_acto = MagicMock(modalidad=Acto.ModalidadReparto.TRADICIONAL)
        mock_hermano = MagicMock(id=1, numero_registro=100)
        mock_hermano_get.return_value = MagicMock(id=2, numero_registro=500)

        self.service._qs_papeletas_activas = MagicMock()
        mock_base_qs = self.service._qs_papeletas_activas.return_value

        qs_objetivo = mock_base_qs.select_for_update.return_value.filter.return_value.order_by.return_value
        qs_objetivo.count.return_value = 1
        qs_objetivo.get.return_value = MagicMock(es_solicitud_insignia=False)

        mock_base_qs.filter.return_value.exists.return_value = True

        mensaje_esperado = "ya tienes a otros hermanos vinculados a ti"

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._procesar_vinculacion(
                mock_hermano, mock_acto, MagicMock(), MagicMock(), 500
            )



    @patch("api.models.Hermano.objects.get")
    def test_vinculacion_falla_si_los_tipos_de_puesto_son_distintos(self, mock_hermano_get):
        mock_hermano = MagicMock(id=1, numero_registro=100) 
        mock_hermano_obj = MagicMock(id=2, numero_registro=500)
        mock_hermano_get.return_value = mock_hermano_obj
        
        mock_mi_puesto = MagicMock(tipo_puesto_id=1)
        mock_puesto_obj = MagicMock(tipo_puesto_id=2)
        
        mock_papeleta_obj = MagicMock(es_solicitud_insignia=False, puesto=mock_puesto_obj)
        mock_papeleta_obj.puesto.tipo_puesto.es_insignia = False

        self.service._qs_papeletas_activas = MagicMock()
        mock_qs = self.service._qs_papeletas_activas.return_value
        mock_qs.select_for_update.return_value.filter.return_value.order_by.return_value.count.return_value = 1
        mock_qs.select_for_update.return_value.filter.return_value.order_by.return_value.get.return_value = mock_papeleta_obj
        mock_qs.filter.return_value.exists.return_value = False

        with self.assertRaisesMessage(ValidationError, "Ambos deben solicitar el mismo tipo de puesto"):
            self.service._procesar_vinculacion(
                mock_hermano, 
                MagicMock(modalidad="TRADICIONAL"), 
                MagicMock(), 
                mock_mi_puesto, 
                500
            )



    @patch("api.models.Hermano.objects.get")
    def test_vinculacion_falla_si_pertenecen_a_cortejos_distintos(self, mock_hermano_get):
        """
        Test: cortejo distinto

        Given: El solicitante va en Cristo y el objetivo va en Virgen.
        When: Se intenta procesar la vinculación.
        Then: Lanza ValidationError: "Conflicto de sección: Uno va en Cristo y otro en Virgen."
        """
        mock_acto = MagicMock(modalidad="TRADICIONAL")

        mock_hermano_solicitante = MagicMock(id=1, numero_registro=100)
        mock_hermano_objetivo = MagicMock(id=2, numero_registro=500)
        mock_hermano_get.return_value = mock_hermano_objetivo

        mock_mi_puesto = MagicMock(tipo_puesto_id=1, cortejo_cristo=True)
        mock_puesto_obj = MagicMock(tipo_puesto_id=1, cortejo_cristo=False)
        
        mock_papeleta_obj = MagicMock(es_solicitud_insignia=False, puesto=mock_puesto_obj)
        mock_papeleta_obj.puesto.tipo_puesto.es_insignia = False

        self.service._qs_papeletas_activas = MagicMock()
        mock_qs = self.service._qs_papeletas_activas.return_value

        mock_qs.select_for_update.return_value.filter.return_value.order_by.return_value.count.return_value = 1
        mock_qs.select_for_update.return_value.filter.return_value.order_by.return_value.get.return_value = mock_papeleta_obj

        mock_qs.filter.return_value.exists.return_value = False

        with self.assertRaisesMessage(ValidationError, "Conflicto de sección"):
            self.service._procesar_vinculacion(
                mock_hermano_solicitante,
                mock_acto, 
                MagicMock(), 
                mock_mi_puesto, 
                500
            )



    @patch("api.models.Hermano.objects.get")
    def test_vinculacion_falla_si_el_objetivo_solicita_insignia(self, mock_hermano_get):
        """
        Test: objetivo es insignia

        Given: El hermano objetivo ha solicitado un puesto marcado como insignia.
        When: Se intenta procesar la vinculación.
        Then: Lanza ValidationError indicando que no es posible vincularse a insignias.
        """
        mock_acto = MagicMock(modalidad=Acto.ModalidadReparto.TRADICIONAL)
        mock_hermano_get.return_value = MagicMock(id=2, numero_registro=500)

        mock_papeleta_obj = MagicMock()
        mock_papeleta_obj.es_solicitud_insignia = True

        self.service._qs_papeletas_activas = MagicMock()
        mock_qs = self.service._qs_papeletas_activas.return_value
        mock_qs.select_for_update.return_value.filter.return_value.order_by.return_value.count.return_value = 1
        mock_qs.select_for_update.return_value.filter.return_value.order_by.return_value.get.return_value = mock_papeleta_obj

        mock_qs.filter.return_value.exists.return_value = False

        with self.assertRaisesMessage(ValidationError, "No puedes vincularte a un hermano que solicita Insignia."):
            self.service._procesar_vinculacion(
                MagicMock(numero_registro=100), mock_acto, MagicMock(), MagicMock(), 500
            )



    @patch("api.models.Hermano.objects.get")
    def test_vinculacion_falla_si_hermano_objetivo_no_existe(self, mock_hermano_get):
        """
        Test: hermano objetivo no existe

        Given: Un número de registro que no corresponde a ningún hermano en la BD.
        When: Se intenta procesar la vinculación.
        Then: Lanza ValidationError: "No existe hermano con Nº 999."
        """
        mock_acto = MagicMock()
        mock_acto.modalidad = Acto.ModalidadReparto.TRADICIONAL

        mock_hermano_get.side_effect = Hermano.DoesNotExist
        
        numero_no_existente = 999

        with self.assertRaisesMessage(ValidationError, f"No existe hermano con Nº {numero_no_existente}."):
            self.service._procesar_vinculacion(
                MagicMock(), mock_acto, MagicMock(), MagicMock(), numero_no_existente
            )



    @patch("api.models.Hermano.objects.get")
    def test_vinculacion_falla_por_intento_de_autovinculacion(self, mock_hermano_get):
        """
        Test: intentar vincularse a sí mismo

        Given: El hermano solicitante y el hermano objetivo tienen el mismo ID.
        When: Se intenta procesar la vinculación.
        Then: Lanza ValidationError: "No puedes vincularte contigo mismo."
        """
        mock_acto = MagicMock()
        mock_acto.modalidad = Acto.ModalidadReparto.TRADICIONAL

        mock_hermano = MagicMock(id=55)
        mock_hermano_objetivo = MagicMock(id=55)
        
        mock_hermano_get.return_value = mock_hermano_objetivo

        with self.assertRaisesMessage(ValidationError, "No puedes vincularte contigo mismo."):
            self.service._procesar_vinculacion(
                mock_hermano, mock_acto, MagicMock(), MagicMock(), 123
            )



    @patch("api.models.Hermano.objects.get")
    def test_vinculacion_falla_si_algun_hermano_no_tiene_numero_registro(self, mock_hermano_get):
        """
        Test: sin número de registro en alguno

        Given: Uno de los dos hermanos tiene numero_registro = None.
        When: Se intenta procesar la vinculación.
        Then: Lanza ValidationError: "Ambos hermanos deben tener número de registro..."
        """
        mock_acto = MagicMock(modalidad=Acto.ModalidadReparto.TRADICIONAL)

        mock_hermano_sin_num = MagicMock(id=1, numero_registro=None)
        mock_hermano_objetivo = MagicMock(id=2, numero_registro=500)
        mock_hermano_get.return_value = mock_hermano_objetivo

        with self.assertRaisesMessage(ValidationError, "Ambos hermanos deben tener número de registro"):
            self.service._procesar_vinculacion(
                mock_hermano_sin_num, mock_acto, MagicMock(), MagicMock(), 500
            )



    @patch("api.models.Hermano.objects.get")
    def test_vinculacion_falla_si_objetivo_no_tiene_solicitud_activa(self, mock_hermano_get):
        """
        Test: objetivo sin solicitudes activas

        Given: El hermano objetivo existe pero el conteo de sus papeletas es 0.
        When: Se intenta procesar la vinculación.
        Then: Lanza ValidationError indicando que no tiene solicitud activa.
        """
        mock_acto = MagicMock(modalidad=Acto.ModalidadReparto.TRADICIONAL)
        mock_hermano_obj = MagicMock(id=2, numero_registro=500)
        mock_hermano_get.return_value = mock_hermano_obj

        self.service._qs_papeletas_activas = MagicMock()
        mock_qs = self.service._qs_papeletas_activas.return_value

        mock_qs.select_for_update.return_value.filter.return_value.order_by.return_value.count.return_value = 0

        with self.assertRaisesMessage(ValidationError, "El hermano Nº 500 no tiene solicitud activa."):
            self.service._procesar_vinculacion(
                MagicMock(numero_registro=100), mock_acto, MagicMock(), MagicMock(), 500
            )



    @patch("api.models.Hermano.objects.get")
    def test_vinculacion_falla_si_el_solicitante_ya_tiene_dependientes(self, mock_hermano_get):
        """
        Test: Bloqueo de cadena de vinculación

        Given: Un hermano que ya tiene a otros hermanos vinculados a él.
        When: Intenta vincularse a un tercero.
        Then: Lanza ValidationError impidiendo la cadena A->B->C.
        """
        mock_acto = MagicMock()
        mock_acto.modalidad = Acto.ModalidadReparto.TRADICIONAL
        
        mock_hermano = MagicMock(id=1, numero_registro=100)
        mock_hermano_objetivo = MagicMock(id=2, numero_registro=500)
        mock_hermano_get.return_value = mock_hermano_objetivo

        self.service._qs_papeletas_activas = MagicMock()
        mock_base_qs = self.service._qs_papeletas_activas.return_value

        qs_objetivo = mock_base_qs.select_for_update.return_value.filter.return_value.order_by.return_value
        qs_objetivo.count.return_value = 1
        qs_objetivo.get.return_value = MagicMock()

        qs_dependientes = mock_base_qs.filter.return_value
        qs_dependientes.exists.return_value = True

        mensaje_esperado = "No puedes vincularte a otro hermano porque ya tienes a otros hermanos vinculados a ti."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._procesar_vinculacion(
                mock_hermano, mock_acto, MagicMock(), MagicMock(), 500
            )



    def test_vinculacion_falla_si_la_modalidad_del_acto_no_es_tradicional(self):
        """
        Test: modalidad incorrecta

        Given: Un acto cuya modalidad es PROXIMIDAD (u otra distinta a TRADICIONAL).
        When: Se intenta realizar una vinculación.
        Then: Lanza ValidationError: "La vinculación solo está disponible en modalidad TRADICIONAL."
        """
        mock_acto = MagicMock()
        mock_acto.modalidad = "PROXIMIDAD" 

        with self.assertRaisesMessage(ValidationError, "La vinculación solo está disponible en modalidad TRADICIONAL."):
            self.service._procesar_vinculacion(
                MagicMock(), mock_acto, MagicMock(), MagicMock(), 500
            )



    def test_vinculacion_falla_si_numero_objetivo_esta_vacio(self):
        """
        Test para cubrir la línea: if not numero_objetivo: raise ValidationError(...)
        
        Given: Un intento de vinculación donde el número del hermano objetivo es una cadena vacía.
        When: Se procesa la lógica de vinculación.
        Then: Se debe lanzar una ValidationError con el mensaje exacto: 
            "Debe indicar un número de registro válido para vincularse."
        """
        mock_acto = MagicMock()
        mock_hermano = MagicMock()
        mock_papeleta = MagicMock()
        mock_puesto = MagicMock()

        numero_objetivo_vacio = ""

        with self.assertRaisesMessage(ValidationError, "Debe indicar un número de registro válido para vincularse."):
            self.service._procesar_vinculacion(
                mock_hermano, 
                mock_acto, 
                mock_papeleta, 
                mock_puesto, 
                numero_objetivo_vacio
            )



    @patch("api.models.Hermano.objects.get")
    def test_vinculacion_falla_si_objetivo_tiene_multiples_solicitudes_activas(self, mock_hermano_get):
        """
        Test para cubrir la línea: if count > 1: raise ValidationError(...)
        
        Given: Un hermano objetivo (Nº 500) que, por un error de integridad en la BD, 
            ya tiene 2 papeletas activas para el mismo acto.
        When: El hermano solicitante intenta vincularse a él.
        Then: El sistema debe detectar la ambigüedad (count=2) y lanzar una 
            ValidationError solicitando contacto con secretaría.
        """
        mock_hermano_objetivo = MagicMock(id=2, numero_registro=500)
        mock_hermano_solicitante = MagicMock(id=1, numero_registro=100)
        
        mock_hermano_get.return_value = mock_hermano_objetivo
        
        mock_acto = MagicMock()
        mock_acto.modalidad = Acto.ModalidadReparto.TRADICIONAL

        self.service._qs_papeletas_activas = MagicMock()
        mock_qs_chain = self.service._qs_papeletas_activas.return_value.select_for_update.return_value.filter.return_value.order_by.return_value

        mock_qs_chain.count.return_value = 2

        mensaje_error_esperado = "tiene múltiples solicitudes activas para este acto. Contacte con secretaría."

        with self.assertRaisesMessage(ValidationError, mensaje_error_esperado):
            self.service._procesar_vinculacion(
                mock_hermano_solicitante,
                mock_acto,
                MagicMock(),
                MagicMock(),
                500
            )



    @patch("api.models.Hermano.objects.get")
    def test_vinculacion_falla_si_papeleta_objetivo_no_tiene_puesto_asignado(self, mock_hermano_get):
        """
        Test para cubrir la línea: if not puesto_objetivo: raise ValidationError(...)
        
        Given: Un hermano objetivo (Nº 500) cuya papeleta activa existe pero tiene 
            el campo 'puesto' como None (sin selección).
        When: El hermano solicitante intenta procesar la vinculación.
        Then: Debe lanzar un ValidationError indicando que el hermano objetivo 
            no tiene puesto seleccionado.
        """
        mock_hermano_solicitante = MagicMock(id=1, numero_registro=100)
        mock_hermano_objetivo = MagicMock(id=2, numero_registro=500)
        mock_hermano_get.return_value = mock_hermano_objetivo

        mock_acto = MagicMock(modalidad=Acto.ModalidadReparto.TRADICIONAL)

        mock_papeleta_sin_puesto = MagicMock(es_solicitud_insignia=False, puesto=None)

        self.service._qs_papeletas_activas = MagicMock()
        mock_qs_chain = self.service._qs_papeletas_activas.return_value.select_for_update.return_value.filter.return_value.order_by.return_value
        
        mock_qs_chain.count.return_value = 1
        mock_qs_chain.get.return_value = mock_papeleta_sin_puesto

        self.service._qs_papeletas_activas.return_value.filter.return_value.exists.return_value = False

        mensaje_error_esperado = "El hermano Nº 500 no tiene puesto seleccionado."

        with self.assertRaisesMessage(ValidationError, mensaje_error_esperado):
            self.service._procesar_vinculacion(
                mock_hermano_solicitante,
                mock_acto,
                MagicMock(),
                MagicMock(),
                500
            )



    # -------------------------------------------------------------------------
    # TEST PAPELETAS ACTIVAS
    # -------------------------------------------------------------------------

    @patch("api.models.PapeletaSitio.objects.exclude")
    def test_excluye_estados_no_activos(self, mock_exclude):
        """
        Test: Validar que el QuerySet excluye los estados ANULADA y NO_ASIGNADA.

        Given: La constante ESTADOS_NO_ACTIVOS definida en el servicio.
        When: Se invoca al método interno _qs_papeletas_activas.
        Then: Se debe llamar a PapeletaSitio.objects.exclude con el filtro estado_papeleta__in.
        """
        servicio = SolicitudCirioTradicionalService()

        mock_qs = MagicMock()
        mock_exclude.return_value = mock_qs

        resultado = servicio._qs_papeletas_activas()

        estados_excluidos = servicio.ESTADOS_NO_ACTIVOS
        
        mock_exclude.assert_called_once_with(
            estado_papeleta__in=estados_excluidos
        )

        self.assertEqual(resultado, mock_qs)
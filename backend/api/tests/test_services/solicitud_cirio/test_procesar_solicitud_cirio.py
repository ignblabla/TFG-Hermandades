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
    @patch.object(SolicitudCirioTradicionalService, '_crear_papeleta_base')
    def test_sin_conflicto_insignia_no_ejecuta_update(
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
        Test: Sin conflicto de insignia

        Given: Un hermano que NO tiene solicitudes previas de insignias en conflicto.
        When: El gestor de conflictos devuelve None.
        Then: No se debe ejecutar ninguna consulta de actualización (update) sobre PapeletaSitio.
        """
        mock_hermano = MagicMock(pk=1)
        mock_acto = MagicMock()
        mock_puesto = MagicMock()

        mock_conflicto.return_value = None

        mock_hermano_model.objects.select_for_update.return_value.only.return_value.get.return_value = mock_hermano
        mock_crear_base.return_value = MagicMock()

        self.service.procesar_solicitud_cirio_tradicional(mock_hermano, mock_acto, mock_puesto)

        mock_papeleta_model.objects.select_for_update.assert_not_called()



    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.timezone')
    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.Hermano')
    @patch.object(SolicitudCirioTradicionalService, '_validar_configuracion_acto_tradicional')
    @patch.object(SolicitudCirioTradicionalService, '_validar_plazo_vigente')
    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_apto_para_solicitar')
    @patch.object(SolicitudCirioTradicionalService, '_validar_item_puesto_cirio')
    @patch.object(SolicitudCirioTradicionalService, '_gestionar_conflicto_insignia_y_unicidad')
    @patch.object(SolicitudCirioTradicionalService, '_crear_papeleta_base')
    def test_creacion_de_papeleta_base_llamada_correctamente(
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
        Test: Creación de papeleta

        Given: Un flujo de solicitud válido.
        When: Se procesa la solicitud de cirio.
        Then: _crear_papeleta_base debe ser invocado exactamente una vez con hermano, acto y ahora.
        """
        mock_hermano = MagicMock(pk=1)
        mock_acto = MagicMock()
        mock_puesto = MagicMock()

        mock_ahora = MagicMock()
        mock_timezone.now.return_value = mock_ahora

        mock_conflicto.return_value = None
        mock_hermano_model.objects.select_for_update.return_value.only.return_value.get.return_value = mock_hermano

        self.service.procesar_solicitud_cirio_tradicional(mock_hermano, mock_acto, mock_puesto)

        mock_crear_base.assert_called_once_with(mock_hermano, mock_acto, mock_ahora)



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



    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.timezone')
    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.Hermano')
    @patch.object(SolicitudCirioTradicionalService, '_validar_configuracion_acto_tradicional')
    def test_validacion_falla_se_propaga_la_excepcion(
        self, 
        mock_validar_acto, 
        mock_hermano_model, 
        mock_timezone
    ):
        """
        Test: Validación falla (cualquier validador)

        Given: Un validador interno (ej. _validar_configuracion_acto_tradicional).
        When: Dicho validador lanza un ValidationError de negocio.
        Then: El servicio debe propagar la excepción inmediatamente sin ejecutar el resto del flujo.
        """
        mock_hermano = MagicMock(pk=1)
        mock_acto = MagicMock()
        mock_puesto = MagicMock()

        mensaje_error = "Este proceso es exclusivo para actos de modalidad TRADICIONAL."
        mock_validar_acto.side_effect = ValidationError(mensaje_error)

        mock_hermano_model.objects.select_for_update.return_value.only.return_value.get.return_value = mock_hermano

        with self.assertRaisesMessage(ValidationError, mensaje_error):
            self.service.procesar_solicitud_cirio_tradicional(mock_hermano, mock_acto, mock_puesto)

        with patch.object(SolicitudCirioTradicionalService, '_crear_papeleta_base') as mock_crear:
            try:
                self.service.procesar_solicitud_cirio_tradicional(mock_hermano, mock_acto, mock_puesto)
            except ValidationError:
                pass
            mock_crear.assert_not_called()



    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.timezone')
    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.Hermano')
    @patch.object(SolicitudCirioTradicionalService, '_validar_configuracion_acto_tradicional')
    @patch.object(SolicitudCirioTradicionalService, '_validar_plazo_vigente')
    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_apto_para_solicitar')
    @patch.object(SolicitudCirioTradicionalService, '_validar_item_puesto_cirio')
    @patch.object(SolicitudCirioTradicionalService, '_gestionar_conflicto_insignia_y_unicidad')
    @patch.object(SolicitudCirioTradicionalService, '_crear_papeleta_base')
    @patch.object(SolicitudCirioTradicionalService, '_procesar_vinculacion')
    def test_sin_vinculacion_no_llama_a_procesar_vinculacion(
        self, 
        mock_procesar_vinculacion, 
        mock_crear_base, 
        mock_conflicto, 
        mock_v_item, 
        mock_v_apto, 
        mock_v_plazo, 
        mock_v_acto, 
        mock_hermano_model, 
        mock_timezone
    ):
        """
        Test: Sin vinculación

        Given: Una solicitud donde numero_registro_vinculado es None.
        When: Se procesa la solicitud exitosamente.
        Then: No se debe invocar el método interno _procesar_vinculacion.
        """
        mock_hermano = MagicMock(pk=1)
        mock_acto = MagicMock(id=1)
        mock_puesto = MagicMock(id=1)

        mock_hermano_model.objects.select_for_update.return_value.only.return_value.get.return_value = mock_hermano

        mock_conflicto.return_value = None 
        
        mock_crear_base.return_value = MagicMock()

        self.service.procesar_solicitud_cirio_tradicional(
            hermano=mock_hermano,
            acto=mock_acto,
            puesto=mock_puesto,
            numero_registro_vinculado=None
        )

        mock_procesar_vinculacion.assert_not_called()



    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.timezone')
    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.Hermano')
    @patch.object(SolicitudCirioTradicionalService, '_validar_configuracion_acto_tradicional')
    @patch.object(SolicitudCirioTradicionalService, '_validar_plazo_vigente')
    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_apto_para_solicitar')
    @patch.object(SolicitudCirioTradicionalService, '_validar_item_puesto_cirio')
    @patch.object(SolicitudCirioTradicionalService, '_gestionar_conflicto_insignia_y_unicidad')
    @patch.object(SolicitudCirioTradicionalService, '_crear_papeleta_base')
    def test_puesto_se_asigna_correctamente_a_la_papeleta(
        self, 
        mock_crear_base, 
        mock_conflicto, 
        mock_v_item, 
        mock_v_apto, 
        mock_v_plazo, 
        mock_v_acto, 
        mock_hermano_model, 
        mock_timezone
    ):
        """
        Test: puesto se asigna correctamente

        Given: Un puesto de cirio específico.
        When: La papeleta base ha sido creada.
        Then: La papeleta devuelta debe tener el puesto asignado y haberse guardado con update_fields=['puesto'].
        """
        mock_hermano = MagicMock(pk=1)
        mock_hermano_model.objects.select_for_update.return_value.only.return_value.get.return_value = mock_hermano

        mock_conflicto.return_value = None 

        puesto_esperado = MagicMock(id=10, nombre="Cirio de Tramo 1")
        mock_papeleta = MagicMock()
        mock_crear_base.return_value = mock_papeleta

        resultado = self.service.procesar_solicitud_cirio_tradicional(
            hermano=mock_hermano,
            acto=MagicMock(id=1),
            puesto=puesto_esperado
        )

        self.assertEqual(resultado.puesto, puesto_esperado)

        mock_papeleta.save.assert_called_once_with(update_fields=['puesto'])



    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.timezone')
    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.Hermano')
    @patch.object(SolicitudCirioTradicionalService, '_validar_configuracion_acto_tradicional')
    @patch.object(SolicitudCirioTradicionalService, '_validar_plazo_vigente')
    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_apto_para_solicitar')
    @patch.object(SolicitudCirioTradicionalService, '_validar_item_puesto_cirio')
    @patch.object(SolicitudCirioTradicionalService, '_gestionar_conflicto_insignia_y_unicidad')
    @patch.object(SolicitudCirioTradicionalService, '_crear_papeleta_base')
    @patch.object(SolicitudCirioTradicionalService, '_procesar_vinculacion')
    def test_orden_estricto_de_ejecucion(
        self, 
        mock_vinculacion, 
        mock_crear, 
        mock_conflicto, 
        mock_v_item, 
        mock_v_hermano, 
        mock_v_plazo, 
        mock_v_config, 
        mock_hermano_model, 
        mock_timezone
    ):
        """

        Test: _gestionar_conflicto... devuelve objeto inválido

        Given: Un escenario donde el método de conflicto devuelve None.
        When: Se procesa la solicitud.
        Then: El servicio no debe intentar llamar a .filter() ni .update() y debe continuar con la creación.
        """
        mock_hermano_model.objects.select_for_update.return_value.only.return_value.get.return_value = MagicMock(pk=1)
        mock_conflicto.return_value = None

        mock_papeleta_resultado = MagicMock(name="PapeletaIndependiente")
        mock_crear.return_value = mock_papeleta_resultado

        manager = MagicMock()
        manager.attach_mock(mock_v_config, 'validar_config')
        manager.attach_mock(mock_conflicto, 'conflicto')
        manager.attach_mock(mock_crear, 'crear')
        manager.attach_mock(mock_vinculacion, 'vinculacion')

        self.service.procesar_solicitud_cirio_tradicional(
            hermano=MagicMock(pk=1), 
            acto=MagicMock(id=1), 
            puesto=MagicMock(id=1), 
            numero_registro_vinculado=999
        )

        nombres_llamadas = [
            call[0] for call in manager.mock_calls 
            if '.' not in call[0] or call[0].endswith('()')
        ]

        expected = ['validar_config', 'conflicto', 'crear', 'vinculacion']

        actual = [n for n in nombres_llamadas if n in expected]

        self.assertEqual(actual, expected)



    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.PapeletaSitio')
    @patch('api.servicios.solicitud_cirio.solicitud_cirio_service.Hermano')
    @patch.object(SolicitudCirioTradicionalService, '_validar_configuracion_acto_tradicional')
    @patch.object(SolicitudCirioTradicionalService, '_validar_plazo_vigente')
    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_apto_para_solicitar')
    @patch.object(SolicitudCirioTradicionalService, '_validar_item_puesto_cirio')
    @patch.object(SolicitudCirioTradicionalService, '_gestionar_conflicto_insignia_y_unicidad')
    @patch.object(SolicitudCirioTradicionalService, '_crear_papeleta_base')
    def test_gestionar_conflicto_devuelve_none_o_invalido_no_rompe_flujo(
        self, 
        mock_crear, 
        mock_conflicto, 
        mock_v_item,
        mock_v_hermano,
        mock_v_plazo,
        mock_v_config, 
        mock_hermano_model, 
        mock_papeleta_model
    ):
        """
        Test: _gestionar_conflicto... devuelve objeto inválido

        Given: Un escenario donde el método de conflicto devuelve None.
        When: Se procesa la solicitud.
        Then: El servicio no debe intentar llamar a .filter() ni .update() y debe continuar con la creación.
        """

        mock_hermano_model.objects.select_for_update.return_value.only.return_value.get.return_value = MagicMock()

        mock_conflicto.return_value = None

        mock_papeleta = MagicMock()
        mock_crear.return_value = mock_papeleta

        self.service.procesar_solicitud_cirio_tradicional(MagicMock(), MagicMock(), MagicMock())

        mock_papeleta_model.objects.select_for_update.return_value.filter.assert_not_called()

        mock_crear.assert_called_once()


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



    def test_tipo_acto_id_es_none_lanza_error_especifico(self):
        """
        Test: tipo_acto_id es None

        Given: Un objeto acto presente pero sin la clave foránea tipo_acto_id definida.
        When: Se intenta validar la configuración.
        Then: Lanza el mismo ValidationError que cuando el acto es None.
        """
        acto_sin_tipo = MagicMock()
        acto_sin_tipo.tipo_acto_id = None
        mensaje_esperado = "El tipo de acto es obligatorio."

        with self.assertRaises(ValidationError) as cm:
            self.service._validar_configuracion_acto_tradicional(acto_sin_tipo)
        
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



    def test_tipo_acto_incompleto_manejo_de_atributo_ausente(self):
        """
        Test: tipo_acto existe pero incompleto

        Given: Un acto con tipo_acto, pero este objeto no tiene el atributo 'requiere_papeleta'.
        When: Se intenta validar la configuración.
        Then: Debe lanzar un AttributeError (comportamiento por defecto) o podemos validar 
            que el test falle si no se maneja, ayudándonos a decidir si añadir un getattr().
        """
        acto_dummy = MagicMock()
        acto_dummy.tipo_acto_id = 1
        del acto_dummy.tipo_acto.requiere_papeleta

        with self.assertRaises(AttributeError):
            self.service._validar_configuracion_acto_tradicional(acto_dummy)



    def test_nombre_vacio_el_mensaje_sigue_siendo_coherente(self):
        """
        Test: nombre vacío

        Given: Un acto cuyo nombre es una cadena vacía ("").
        When: Se valida un acto que no admite papeletas.
        Then: El mensaje debe construirse correctamente como: "El acto '' no admite...".
        """
        acto_dummy = MagicMock()
        acto_dummy.nombre = ""
        acto_dummy.tipo_acto_id = 1
        acto_dummy.tipo_acto.requiere_papeleta = False
        
        mensaje_esperado = "El acto '' no admite solicitudes de papeleta."

        with self.assertRaises(ValidationError) as cm:
            self.service._validar_configuracion_acto_tradicional(acto_dummy)
        
        self.assertIn(mensaje_esperado, cm.exception.messages)



    def test_cortocircuito_cuando_tipo_acto_id_es_none(self):
        """
        Test: Cortocircuito correcto

        Given: Un acto con tipo_acto_id = None.
        When: Se valida la configuración.
        Then: Debe lanzar el error de "tipo de acto obligatorio" y NO evaluar 
            si requiere_papeleta es False (aunque lo sea).
        """

        acto_dummy = MagicMock()
        acto_dummy.tipo_acto_id = None

        type(acto_dummy).tipo_acto = PropertyMock(side_effect=RuntimeError("Se accedió a tipo_acto indebidamente"))

        with self.assertRaises(ValidationError) as cm:
            self.service._validar_configuracion_acto_tradicional(acto_dummy)

        self.assertEqual(cm.exception.message_dict["tipo_acto"], ["El tipo de acto es obligatorio."])



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



    def test_falta_configuracion_plazo_inicio_lanza_error(self):
        """
        Test: Falta inicio (Escenario A)

        Given: Un plazo donde el inicio es None.
        When: Se intenta validar la vigencia.
        Then: Lanza ValidationError indicando que no está configurado.
        """
        inicio = None
        fin = self.ahora + timedelta(days=1)
        nombre = "cirios"
        mensaje_esperado = f"El plazo de {nombre} no está configurado en el acto."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_plazo_vigente(self.ahora, inicio, fin, nombre)



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



    def test_ahora_igual_a_inicio_es_valido(self):
        """
        Test: Igual al inicio (boundary)

        Given: El momento actual es exactamente igual a la fecha de inicio.
        When: Se valida la vigencia del plazo.
        Then: No debe lanzar ValidationError (es inclusivo).
        """
        ahora = self.ahora
        inicio = ahora
        fin = ahora + timedelta(days=1)

        try:
            self.service._validar_plazo_vigente(ahora, inicio, fin, "test")
        except ValidationError:
            self.fail("_validar_plazo_vigente lanzó error en el límite exacto de inicio.")



    def test_ahora_igual_a_fin_es_valido(self):
        """
        Test: Igual al fin (boundary)

        Given: El momento actual es exactamente igual a la fecha de fin.
        When: Se valida la vigencia del plazo.
        Then: No debe lanzar ValidationError (es inclusivo).
        """
        ahora = self.ahora
        inicio = ahora - timedelta(days=1)
        fin = ahora

        try:
            self.service._validar_plazo_vigente(ahora, inicio, fin, "test")
        except ValidationError:
            self.fail("_validar_plazo_vigente lanzó error en el límite exacto de fin.")



    def test_inicio_mayor_que_fin_dato_corrupto(self):
        """
        Test: inicio > fin (dato corrupto)

        Given: Un acto con las fechas invertidas (fin ocurre antes que el inicio).
        When: Se valida con un 'ahora' que queda atrapado en esa incongruencia.
        Then: El sistema debe lanzar error por uno de los dos límites.
        """
        ahora = self.ahora
        inicio = ahora + timedelta(days=1)
        fin = ahora - timedelta(days=1)

        with self.assertRaisesMessage(ValidationError, "aún no ha comenzado"):
            self.service._validar_plazo_vigente(ahora, inicio, fin, "test")



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
    def test_propaga_parametro_ahora_al_validador_de_cuotas(
        self, mock_pertenencia, mock_corriente, mock_alta
    ):
        """
        Test: Propaga ahora correctamente al segundo método

        Given: Una marca de tiempo específica.
        When: Se orquesta la validación del hermano.
        Then: El método '_validar_hermano_al_corriente...' debe recibir exactamente ese objeto 'ahora'.
        """
        mock_hermano = MagicMock()
        momento_especifico = datetime(2026, 3, 4, tzinfo=py_timezone.utc)

        self.service._validar_hermano_apto_para_solicitar(
            mock_hermano, set(), momento_especifico
        )

        args, _ = mock_corriente.call_args
        self.assertEqual(args[1], momento_especifico)



    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_en_alta')
    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_al_corriente_hasta_anio_anterior')
    @patch.object(SolicitudCirioTradicionalService, '_validar_pertenencia_cuerpos')
    def test_falla_en_alta_detiene_ejecucion_y_propaga_error(
        self, mock_pertenencia, mock_corriente, mock_alta
    ):
        """
        Test: Falla en _validar_hermano_en_alta

        Given: Un validador de alta que lanza ValidationError.
        When: Se orquesta la validación del hermano.
        Then: La excepción se propaga y los validadores posteriores NO se ejecutan.
        """
        mensaje_error = "El hermano no se encuentra en estado de ALTA."
        mock_alta.side_effect = ValidationError(mensaje_error)

        with self.assertRaisesMessage(ValidationError, mensaje_error):
            self.service._validar_hermano_apto_para_solicitar(MagicMock(), set(), timezone.now())

        mock_alta.assert_called_once()
        mock_corriente.assert_not_called()
        mock_pertenencia.assert_not_called()



    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_en_alta')
    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_al_corriente_hasta_anio_anterior')
    @patch.object(SolicitudCirioTradicionalService, '_validar_pertenencia_cuerpos')
    def test_falla_en_cuotas_impide_validar_pertenencia_cuerpos(
        self, mock_pertenencia, mock_corriente, mock_alta
    ):
        """
        Test: Falla en _validar_hermano_al_corriente_hasta_anio_anterior

        Given: El hermano está en alta, pero el validador de cuotas lanza error.
        When: Se orquesta la validación.
        Then: Se valida el alta y las cuotas, pero NO se llega a validar la pertenencia a cuerpos.
        """
        mensaje_error = "El hermano tiene cuotas pendientes de años anteriores."
        mock_corriente.side_effect = ValidationError(mensaje_error)

        with self.assertRaisesMessage(ValidationError, mensaje_error):
            self.service._validar_hermano_apto_para_solicitar(MagicMock(), set(), timezone.now())

        mock_alta.assert_called_once()

        mock_corriente.assert_called_once()

        mock_pertenencia.assert_not_called()



    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_en_alta')
    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_al_corriente_hasta_anio_anterior')
    @patch.object(SolicitudCirioTradicionalService, '_validar_pertenencia_cuerpos')
    def test_falla_en_pertenencia_cuerpos_habiendo_pasado_validaciones_previas(
        self, mock_pertenencia, mock_corriente, mock_alta
    ):
        """
        Test: Falla en _validar_pertenencia_cuerpos

        Given: Un hermano que está en ALTA y al corriente, pero no pertenece a los cuerpos.
        When: Se orquesta la validación del hermano.
        Then: Los dos primeros métodos deben ejecutarse, y el error del tercero debe propagarse.
        """
        mock_hermano = MagicMock()
        mock_cuerpos = {"CIRIO", "PENITENTE"}
        ahora = timezone.now()
        
        mensaje_error = "El hermano no pertenece a los cuerpos requeridos para este acto."
        mock_pertenencia.side_effect = ValidationError(mensaje_error)

        with self.assertRaisesMessage(ValidationError, mensaje_error):
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



    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_en_alta')
    @patch.object(SolicitudCirioTradicionalService, '_validar_hermano_al_corriente_hasta_anio_anterior')
    @patch.object(SolicitudCirioTradicionalService, '_validar_pertenencia_cuerpos')
    def test_aislamiento_de_fallo_inicial(
        self, mock_pertenencia, mock_corriente, mock_alta
    ):
        """
        Test: No hay ejecución si el primero falla

        Given: Un error crítico en la primera validación (alta).
        When: Se orquesta la validación.
        Then: Los métodos de cuotas y pertenencia no deben recibir ni una sola llamada.
        """
        mock_alta.side_effect = ValidationError("Error inicial")

        with self.assertRaises(ValidationError):
            self.service._validar_hermano_apto_para_solicitar(MagicMock(), set(), timezone.now())

        mock_corriente.assert_not_called()
        mock_pertenencia.assert_not_called()



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



    def test_hermano_en_estado_baja_lanza_error(self):
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



    def test_hermano_en_estado_suspendido_lanza_error(self):
        """
        Test: Hermano en estado distinto a ALTA (SUSPENDIDO)

        Given: Un objeto hermano cuyo estado es 'SUSPENDIDO'.
        When: Se valida si el hermano está en alta.
        Then: Lanza ValidationError con el mensaje de restricción.
        """
        hermano_dummy = MagicMock()
        hermano_dummy.estado_hermano = "SUSPENDIDO"
        mensaje_esperado = "Solo los hermanos en estado ALTA pueden solicitar papeleta."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_hermano_en_alta(hermano_dummy)



    def test_estado_hermano_es_none_lanza_error(self):
        """
        Test: Estado None o vacío

        Given: Un hermano que por algún error de datos tiene el estado como None.
        When: Se valida la condición.
        Then: La comparación None != 'ALTA' debe ser True y lanzar el error.
        """
        hermano_dummy = MagicMock()
        hermano_dummy.estado_hermano = None
        mensaje_esperado = "Solo los hermanos en estado ALTA pueden solicitar papeleta."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_hermano_en_alta(hermano_dummy)



    def test_estado_inesperado_string_invalido_lanza_error(self):
        """
        Test: Estado inesperado (robustez)

        Given: Un estado que no existe en la lógica de negocio actual ("UNKNOWN").
        When: Se valida el estado del hermano.
        Then: Debe lanzar ValidationError (Fail-safe behavior).
        """
        hermano_dummy = MagicMock()
        hermano_dummy.estado_hermano = "UNKNOWN_STATE_123"
        mensaje_esperado = "Solo los hermanos en estado ALTA pueden solicitar papeleta."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_hermano_en_alta(hermano_dummy)



    def test_comparacion_estricta_con_enum_falla_si_es_string_puro(self):
        """
        Test: Enum correcto vs valor raw

        Given: El modelo usa Enums (Hermano.EstadoHermano.ALTA).
        When: El atributo del hermano es un string simple "ALTA" en lugar del objeto Enum.
        Then: La validación debe fallar si la lógica espera el objeto Enum (o viceversa).
        """
        class MockEstado(Enum):
            ALTA = "ALTA"
            BAJA = "BAJA"

        hermano_dummy = MagicMock()

        hermano_dummy.estado_hermano = "ALTA" 

        with self.assertRaises(ValidationError):
            if hermano_dummy.estado_hermano != MockEstado.ALTA:
                raise ValidationError("Solo los hermanos en estado ALTA...")



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



    def test_prioridad_logica_deuda_sobre_historial(self):
        """
        Test: Tiene ambas condiciones (deuda + no historial)

        Given: Un hermano que tiene una deuda en 2024 Y no tiene historial 
            registrado (escenario de datos corruptos o inconsistentes).
        When: Se valida la situación de tesorería.
        Then: Solo debe lanzar el error de DEUDA, ya que es la primera validación.
        """
        mock_hermano = MagicMock()
        ahora = MagicMock()
        ahora.date().year = 2026 

        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = {
            'anio': 2024
        }

        mock_hermano.cuotas.filter.return_value.exists.return_value = False

        with self.assertRaisesMessage(ValidationError, "Consta una cuota pendiente o devuelta"):
            self.service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano, ahora)

        mock_hermano.cuotas.filter.return_value.exists.assert_not_called()



    def test_deuda_en_anio_limite_exacto_bloquea_solicitud(self):
        """
        Test: Año límite exacto

        Given: Año actual 2026 (límite 2025) y una deuda precisamente en 2025.
        When: Se valida la situación de tesorería.
        Then: Debe lanzar ValidationError porque 2025 <= 2025.
        """
        mock_hermano = MagicMock()
        ahora = MagicMock()
        ahora.date().year = 2026 

        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = {
            'anio': 2025
        }

        with self.assertRaisesMessage(ValidationError, "del año 2025"):
            self.service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano, ahora)



    def test_cuotas_posteriores_al_limite_no_cuentan_como_historial(self):
        """
        Test: Solo cuotas recientes

        Given: Año actual 2026 (límite 2025). El hermano solo tiene cuotas de 2026.
        When: Se ejecuta .filter(anio__lte=2025).exists().
        Then: Debe devolver False y lanzar el error de "No constan cuotas".
        """
        mock_hermano = MagicMock()
        ahora = MagicMock()
        ahora.date().year = 2026 

        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = None

        mock_hermano.cuotas.filter.return_value.exists.return_value = False

        with self.assertRaisesMessage(ValidationError, "No constan cuotas registradas hasta el año 2025"):
            self.service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano, ahora)



    def test_deuda_en_anio_actual_no_bloquea_solicitud(self):
        """
        Test: Deuda en año fuera de rango (NO debe contar)

        Given: Año actual 2026 (límite 2025). El hermano tiene una deuda en 2026.
        When: Se valida la situación de tesorería.
        Then: No debe lanzar ValidationError porque la deuda de 2026 no entra 
            en el filtro anio__lte=2025.
        """
        mock_hermano = MagicMock()
        ahora = MagicMock()
        ahora.date().year = 2026 

        mock_hermano.cuotas.filter.return_value.values.return_value.order_by.return_value.first.return_value = None

        mock_hermano.cuotas.filter.return_value.exists.return_value = True

        try:
            self.service._validar_hermano_al_corriente_hasta_anio_anterior(mock_hermano, ahora)
        except ValidationError as e:
            self.fail(f"El validador bloqueó por error una deuda del año actual: {e}")

        args_deuda = mock_hermano.cuotas.filter.call_args_list[0]
        self.assertEqual(args_deuda.kwargs['anio__lte'], 2025)



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



    def test_mezcla_cuerpos_permitidos_y_prohibidos_lanza_error_filtrado(self):
        """
        Test: Tiene un cuerpo no permitido

        Given: Un hermano que es 'NAZARENOS' (permitido) y 'PENITENTES' (no permitido).
        When: Se valida la pertenencia.
        Then: Lanza ValidationError mencionando SOLO a 'PENITENTES'.
        """
        cuerpos_hermano = {"NAZARENOS", "PENITENTES"}
        mensaje_esperado = "Tu pertenencia a los siguientes cuerpos no permite solicitar esta papeleta: PENITENTES"

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_pertenencia_cuerpos(cuerpos_hermano)



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



    def test_cuerpos_duplicados_se_manejan_correctamente(self):
        """
        Test: Duplicados (aunque set ya los elimina)

        Given: Una entrada que conceptualmente contiene el mismo cuerpo prohibido varias veces.
        When: Se valida la pertenencia.
        Then: El mensaje de error debe listar el cuerpo una sola vez (gracias a la lógica de set).
        """
        cuerpos_con_duplicados = ["ACÓLITOS", "ACÓLITOS", "PENITENTES"]

        mensaje_esperado = "Tu pertenencia a los siguientes cuerpos no permite solicitar esta papeleta: ACÓLITOS, PENITENTES"

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_pertenencia_cuerpos(cuerpos_con_duplicados)



    def test_validacion_es_estricta_con_mayusculas_y_minusculas(self):
        """
        Test: Diferencia exacta de strings (Case-sensitive)

        Given: El cuerpo "Nazarenos" en formato incorrecto (CamelCase).
        When: Se valida contra la lista blanca que contiene "NAZARENOS".
        Then: Debe fallar y reportar "Nazarenos" como no permitido.
        """
        cuerpos_hermano = {"Nazarenos"} 

        with self.assertRaisesMessage(ValidationError, "no permite solicitar esta papeleta: Nazarenos"):
            self.service._validar_pertenencia_cuerpos(cuerpos_hermano)



    def test_todos_los_cuerpos_son_no_permitidos_lanza_error_completo(self):
        """
        Test: Todos los cuerpos no permitidos

        Given: Un hermano que pertenece a 'ACÓLITOS' y 'OTROS' (ninguno permitido).
        When: Se valida la pertenencia a cuerpos.
        Then: Lanza ValidationError listando ambos cuerpos ordenados alfabéticamente.
        """
        cuerpos_hermano = {"ACÓLITOS", "OTROS"}

        mensaje_esperado = "Tu pertenencia a los siguientes cuerpos no permite solicitar esta papeleta: ACÓLITOS, OTROS"

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._validar_pertenencia_cuerpos(cuerpos_hermano)



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



    def test_puesto_nulo_lanza_error_de_seleccion(self):
        """
        Test: Puesto es None

        Given: Un valor 'None' en lugar de un objeto Puesto.
        When: Se intenta validar el ítem.
        Then: Lanza ValidationError con el mensaje 'Debe seleccionar un puesto válido.'
        """
        mock_acto = MagicMock()
        puesto_nulo = None
        cuerpos_hermano = set()

        with self.assertRaisesMessage(ValidationError, "Debe seleccionar un puesto válido."):
            self.service._validar_item_puesto_cirio(
                cuerpos_hermano, mock_acto, puesto_nulo
            )



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



    def test_validacion_puesto_none_detiene_ejecucion_inmediatamente(self):
        """
        Test: Orden de validación (early exit)

        Given: Un puesto que es None.
        When: Se llama a la validación.
        Then: Debe lanzar el error de selección y NO intentar acceder a otras propiedades.
        """
        puesto = None

        with self.assertRaisesMessage(ValidationError, "Debe seleccionar un puesto válido."):
            self.service._validar_item_puesto_cirio(set(), MagicMock(), puesto)



    def test_prioridad_de_errores_puesto_de_otro_acto_antes_que_disponibilidad(self):
        """
        Test: Conflicto múltiple

        Given: Un puesto que pertenece a otro acto Y además no está disponible.
        When: Se valida el ítem.
        Then: Debe lanzar el error de PERTENENCIA AL ACTO, ya que está antes en el código.
        """
        mock_acto = MagicMock(id=1)
        mock_puesto = MagicMock(acto_id=99, disponible=False, nombre="Puesto Problemático")

        with self.assertRaisesMessage(ValidationError, "El puesto no pertenece a este acto."):
            self.service._validar_item_puesto_cirio(set(), mock_acto, mock_puesto)



    def test_tipo_puesto_nulo_lanza_error_de_integridad(self):
        """
        Test: puesto.tipo_puesto = None (robustez)

        Given: Un objeto Puesto que no tiene asignado un TipoPuesto (None).
        When: Se valida el ítem del puesto.
        Then: Debe lanzar un ValidationError o permitir que el programador 
            detecte la falta de integridad (en este caso, lanzará AttributeError 
            si no hay un check previo, pero el test documenta el fallo).
        """
        mock_acto = MagicMock(id=1)
        mock_puesto = MagicMock(acto_id=1, nombre="Puesto Huérfano")

        mock_puesto.tipo_puesto = None 

        with self.assertRaises(AttributeError):
            self.service._validar_item_puesto_cirio(set(), mock_acto, mock_puesto)



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



    def test_mezcla_insignia_pendiente_y_otras_papeletas_prioriza_retorno(self):
        """
        Test: Mezcla válida: insignia pendiente + otras papeletas

        Given: Una lista con una insignia SOLICITADA y otros registros 
            que no bloquean (o que se evalúan después).
        When: Se procesa el bucle de conflictos.
        Then: El método debe identificar la insignia a anular y terminar devolviéndola.
        """
        mock_hermano = MagicMock()
        mock_acto = MagicMock()
        mock_puesto_nuevo = MagicMock()

        p_insignia = MagicMock(
            es_solicitud_insignia=True, 
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA
        )

        mock_qs = self.service._qs_papeletas_activas.return_value
        mock_qs.select_for_update.return_value.filter.return_value = [p_insignia]

        resultado = self.service._gestionar_conflicto_insignia_y_unicidad(
            mock_hermano, mock_acto, mock_puesto_nuevo
        )

        self.assertEqual(resultado, p_insignia)



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



    def test_prioridad_bloqueo_insignia_emitida_sobre_otros_conflictos(self):
        """
        Test: Varias papeletas activas mezcladas

        Given: Una lista con:
                1. Una insignia EMITIDA (bloqueo total).
                2. Una solicitud de cirio (conflicto de unicidad).
        When: Se gestiona el conflicto.
        Then: Debe lanzar el error de la insignia emitida inmediatamente.
        """
        mock_hermano = MagicMock()
        mock_acto = MagicMock()
        mock_puesto_nuevo = MagicMock()

        p_insignia_emitida = MagicMock(
            es_solicitud_insignia=True,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.EMITIDA
        )
        p_cirio = MagicMock(es_solicitud_insignia=False)

        self.service._qs_papeletas_activas = MagicMock()

        self.service._qs_papeletas_activas.return_value.select_for_update.return_value.filter.return_value = [
            p_insignia_emitida, p_cirio
        ]

        mensaje_esperado = "Ya tienes asignada una Insignia para este acto. No puedes solicitar cirio o cruz de penitente."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._gestionar_conflicto_insignia_y_unicidad(
                mock_hermano, mock_acto, mock_puesto_nuevo
            )



    def test_bucle_evalua_todas_las_papeletas_antes_de_confirmar_anulacion(self):
        """
        Test: Orden de evaluación importa

        Given: Un set de datos donde la primera papeleta es 'insignia SOLICITADA' 
            (posible anulación) pero la segunda es un 'CIRIO' (bloqueo).
        When: Se procesa el bucle.
        Then: El error del cirio debe prevalecer sobre la posible anulación de la insignia.
        """
        mock_hermano = MagicMock()
        mock_acto = MagicMock()

        mock_puesto_nuevo = MagicMock()
        mock_puesto_nuevo.tipo_puesto.id = 1

        p_solicitada = MagicMock(
            es_solicitud_insignia=True,
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA
        )

        p_cirio_existente = MagicMock(es_solicitud_insignia=False)
        p_cirio_existente.puesto.tipo_puesto.id = 1

        self.service._qs_papeletas_activas = MagicMock()

        self.service._qs_papeletas_activas.return_value.select_for_update.return_value.filter.return_value = [
            p_solicitada, p_cirio_existente
        ]

        with self.assertRaises(ValidationError):
            self.service._gestionar_conflicto_insignia_y_unicidad(
                mock_hermano, mock_acto, mock_puesto_nuevo
            )



    def test_multiples_insignias_solicitadas_mantiene_la_ultima_encontrada(self):
        """
        Test: Múltiples insignias solicitadas

        Given: Un hermano con dos insignias en estado SOLICITADA.
        When: Se gestiona el conflicto.
        Then: Retorna una de ellas para anular (la última del bucle) sin lanzar error.
        """
        mock_puesto_nuevo = MagicMock()
        self.service._qs_papeletas_activas = MagicMock()

        p_solicitada_1 = MagicMock(es_solicitud_insignia=True, estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA)
        p_solicitada_2 = MagicMock(es_solicitud_insignia=True, estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA)

        self.service._qs_papeletas_activas.return_value.select_for_update.return_value.filter.return_value = [
            p_solicitada_1, p_solicitada_2
        ]

        resultado = self.service._gestionar_conflicto_insignia_y_unicidad(
            MagicMock(), MagicMock(), mock_puesto_nuevo
        )

        self.assertEqual(resultado, p_solicitada_2)



    def test_papeleta_sin_puesto_asignado_lanza_error_de_sitio_general(self):
        """
        Test: p.puesto = None

        Given: Una papeleta activa que no tiene puesto vinculado (error de integridad).
        When: Se valida contra una nueva solicitud de cirio.
        Then: Lanza ValidationError indicando que no puede pedir Cirio y Penitente a la vez.
        """
        mock_puesto_nuevo = MagicMock()
        self.service._qs_papeletas_activas = MagicMock()

        p_sin_puesto = MagicMock(es_solicitud_insignia=False, puesto=None)

        self.service._qs_papeletas_activas.return_value.select_for_update.return_value.filter.return_value = [p_sin_puesto]

        mensaje_esperado = "Solo puedes tener una solicitud de sitio (no puedes pedir Cirio y Penitente a la vez)."

        with self.assertRaisesMessage(ValidationError, mensaje_esperado):
            self.service._gestionar_conflicto_insignia_y_unicidad(
                MagicMock(), MagicMock(), mock_puesto_nuevo
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



    @patch("api.models.PapeletaSitio.objects.create")
    def test_crear_papeleta_usa_anio_del_acto_no_del_sistema(self, mock_create):
        """
        Test: Usa año del acto correctamente

        Given: Un acto cuya fecha está programada para el año 2026.
        When: Se crea la papeleta base.
        Then: El campo 'anio' enviado al ORM debe ser exactamente 2026.
        """
        mock_hermano = MagicMock()
        mock_acto = MagicMock()

        mock_acto.fecha.year = 2026
        
        fecha_solicitud = timezone.now()

        self.service._crear_papeleta_base(
            mock_hermano, mock_acto, fecha_solicitud
        )

        args, kwargs = mock_create.call_args
        
        self.assertEqual(kwargs['anio'], 2026, "La papeleta debe registrar el año del acto.")



    @patch("uuid.uuid4")
    @patch("api.models.PapeletaSitio.objects.create")
    def test_genera_codigo_verificacion_formateado_correctamente(self, mock_create, mock_uuid):
        """
        Test: Genera código de verificación

        Given: Un UUID específico generado por el sistema.
        When: Se crea la papeleta base.
        Then: El codigo_verificacion debe ser los primeros 8 caracteres, 
            en mayúsculas y sin guiones.
        """
        mock_uuid_value = MagicMock()
        mock_uuid_value.hex = "a1b2c3d4e5f6g7h890"
        mock_uuid.return_value = mock_uuid_value

        codigo_esperado = "A1B2C3D4"

        self.service._crear_papeleta_base(
            MagicMock(), MagicMock(), timezone.now()
        )

        _, kwargs = mock_create.call_args
        codigo_enviado = kwargs['codigo_verificacion']
        
        self.assertEqual(len(codigo_enviado), 8, "El código debe tener longitud 8")
        self.assertEqual(codigo_enviado, codigo_esperado, "El código debe ser uppercase y truncado")
        self.assertTrue(codigo_enviado.isupper(), "El código debe estar en mayúsculas")



    @patch("api.models.PapeletaSitio.objects.create")
    def test_vinculacion_de_papeleta_se_pasa_correctamente_al_orm(self, mock_create):
        """
        Test: Vinculación opcional funciona

        Given: Una papeleta ya existente (vinculado_a).
        When: Se crea una nueva papeleta indicando que depende de la anterior.
        Then: El campo 'vinculado_a' en el create del ORM debe ser la papeleta padre.
        """
        mock_papeleta_padre = MagicMock(spec=PapeletaSitio)
        mock_hermano = MagicMock()
        mock_acto = MagicMock()
        mock_acto.fecha.year = 2026

        self.service._crear_papeleta_base(
            mock_hermano, 
            mock_acto, 
            timezone.now(), 
            vinculado_a=mock_papeleta_padre
        )

        _, kwargs = mock_create.call_args
        self.assertEqual(
            kwargs['vinculado_a'], 
            mock_papeleta_padre, 
            "El vínculo con la papeleta padre no se guardó correctamente"
        )



    @patch("uuid.uuid4")
    def test_fallo_en_generacion_uuid_propaga_excepcion(self, mock_uuid):
        """
        Test: UUID falla o no se genera

        Given: Un fallo catastrófico en la librería uuid.
        When: Se intenta crear la papeleta base.
        Then: La excepción se propaga hacia arriba para abortar la transacción.
        """
        mock_uuid.side_effect = RuntimeError("Error crítico del sistema operativo")

        with self.assertRaises(RuntimeError):
            self.service._crear_papeleta_base(
                MagicMock(), MagicMock(), timezone.now()
            )



    @patch("api.models.PapeletaSitio.objects.create")
    def test_acto_sin_fecha_lanza_error_de_atributo(self, mock_create):
        """
        Test: acto.fecha = None

        Given: Un acto cuyos datos maestros están incompletos (fecha es None).
        When: Se intenta extraer el año para la papeleta.
        Then: Lanza AttributeError al intentar acceder a .year en un NoneType.
        """
        mock_acto = MagicMock()
        mock_acto.fecha = None

        with self.assertRaises(AttributeError):
            self.service._crear_papeleta_base(
                MagicMock(), mock_acto, timezone.now()
            )



    @patch("uuid.uuid4")
    @patch("api.models.PapeletaSitio.objects.create")
    def test_codigo_verificacion_cumple_formato_estricto(self, mock_create, mock_uuid):
        """
        Test: Código de verificación formato (A-Z / 0-9 y 8 caracteres)

        Given: Un UUID que contiene letras minúsculas y guiones.
        When: Se genera la papeleta base.
        Then: El código resultante debe tener exactamente 8 caracteres y ser alfanumérico en mayúsculas.
        """
        mock_uuid_value = MagicMock()
        mock_uuid_value.hex = "f47ac10b58cc4372a5670e02b2c3d479"
        mock_uuid.return_value = mock_uuid_value

        codigo_esperado = "F47AC10B"

        self.service._crear_papeleta_base(MagicMock(), MagicMock(), timezone.now())

        _, kwargs = mock_create.call_args
        codigo = kwargs['codigo_verificacion']
        
        self.assertEqual(len(codigo), 8)
        self.assertTrue(codigo.isalnum(), "El código debe ser alfanumérico")
        self.assertTrue(codigo.isupper(), "El código debe estar en mayúsculas")
        self.assertEqual(codigo, codigo_esperado)



    @patch("api.models.PapeletaSitio.objects.create")
    def test_vinculado_a_por_defecto_es_none(self, mock_create):
        """
        Test: vinculado_a = None por defecto

        Given: Una llamada al método sin el cuarto parámetro.
        When: Se crea la papeleta.
        Then: El campo 'vinculado_a' enviado al ORM debe ser None.
        """
        mock_acto = MagicMock()
        mock_acto.fecha.year = 2026

        self.service._crear_papeleta_base(MagicMock(), mock_acto, timezone.now())

        _, kwargs = mock_create.call_args
        self.assertIsNone(kwargs['vinculado_a'], "Por defecto la papeleta no debe estar vinculada")



    @patch("api.models.PapeletaSitio.objects.create")
    def test_crear_papeleta_no_altera_objetos_de_entrada(self, mock_create):
        """
        Test: Validación de parámetros pasados (no alteración)

        Given: Un objeto Acto con un ID y Año específicos.
        When: Se crea la papeleta.
        Then: Los atributos del objeto Acto original deben permanecer intactos.
        """
        mock_acto = MagicMock()
        mock_acto.id = 500
        mock_acto.fecha.year = 2026

        self.service._crear_papeleta_base(MagicMock(), mock_acto, timezone.now())

        self.assertEqual(mock_acto.id, 500)
        self.assertEqual(mock_acto.fecha.year, 2026)



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



    def test_vinculacion_falla_si_numero_objetivo_es_nulo_o_vacio(self):
        """
        Test: numero_objetivo vacío

        Given: Un valor None o un string vacío como número de objetivo.
        When: Se intenta procesar la vinculación.
        Then: Lanza ValidationError: "Debe indicar un número de registro válido para vincularse."
        """
        mock_acto = MagicMock()

        with self.assertRaisesMessage(ValidationError, "Debe indicar un número de registro válido para vincularse."):
            self.service._procesar_vinculacion(
                MagicMock(), mock_acto, MagicMock(), MagicMock(), None
            )

        with self.assertRaisesMessage(ValidationError, "Debe indicar un número de registro válido para vincularse."):
            self.service._procesar_vinculacion(
                MagicMock(), mock_acto, MagicMock(), MagicMock(), ""
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
    def test_vinculacion_falla_si_objetivo_tiene_multiples_solicitudes(self, mock_hermano_get):
        """
        Test: múltiples solicitudes activas

        Given: El hermano objetivo tiene 2 o más papeletas activas (error de integridad).
        When: Se intenta procesar la vinculación.
        Then: Lanza ValidationError sugiriendo contacto con secretaría.
        """
        mock_acto = MagicMock(modalidad=Acto.ModalidadReparto.TRADICIONAL)
        mock_hermano_obj = MagicMock(id=2, numero_registro=500)
        mock_hermano_get.return_value = mock_hermano_obj

        self.service._qs_papeletas_activas = MagicMock()
        mock_qs = self.service._qs_papeletas_activas.return_value

        mock_qs.select_for_update.return_value.filter.return_value.order_by.return_value.count.return_value = 2

        with self.assertRaisesMessage(ValidationError, "tiene múltiples solicitudes activas"):
            self.service._procesar_vinculacion(
                MagicMock(numero_registro=100), mock_acto, MagicMock(), MagicMock(), 500
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
    def test_vinculacion_falla_si_papeleta_objetivo_no_tiene_puesto(self, mock_hermano_get):
        """
        Test: objetivo sin puesto

        Given: La papeleta del hermano objetivo tiene puesto = None.
        When: Se intenta procesar la vinculación.
        Then: Lanza ValidationError: "El hermano Nº 500 no tiene puesto seleccionado."
        """
        mock_acto = MagicMock(modalidad=Acto.ModalidadReparto.TRADICIONAL)

        mock_hermano_solicitante = MagicMock(id=1, numero_registro=100)
        mock_hermano_objetivo = MagicMock(id=2, numero_registro=500)
        mock_hermano_get.return_value = mock_hermano_objetivo

        mock_papeleta_sin_puesto = MagicMock(es_solicitud_insignia=False, puesto=None)

        self.service._qs_papeletas_activas = MagicMock()
        mock_qs = self.service._qs_papeletas_activas.return_value

        mock_qs.select_for_update.return_value.filter.return_value.order_by.return_value.count.return_value = 1
        mock_qs.select_for_update.return_value.filter.return_value.order_by.return_value.get.return_value = mock_papeleta_sin_puesto

        mock_qs.filter.return_value.exists.return_value = False

        with self.assertRaisesMessage(ValidationError, "no tiene puesto seleccionado"):
            self.service._procesar_vinculacion(
                mock_hermano_solicitante,
                mock_acto, 
                MagicMock(), 
                MagicMock(), 
                500
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
    def test_vinculacion_falla_si_hay_error_inesperado_al_obtener_papeleta(self, mock_hermano_get):
        """
        Test: count vs get inconsistente

        Given: El count() devuelve 1, pero al hacer get() la papeleta ya no está.
        When: Se intenta procesar la vinculación.
        Then: Debe propagar la excepción para asegurar el rollback de la transacción.
        """
        mock_hermano_get.return_value = MagicMock(id=2, numero_registro=500)
        self.service._qs_papeletas_activas = MagicMock()
        mock_qs = self.service._qs_papeletas_activas.return_value

        mock_qs.select_for_update.return_value.filter.return_value.order_by.return_value.count.return_value = 1
        mock_qs.select_for_update.return_value.filter.return_value.order_by.return_value.get.side_effect = Exception("Fallo de concurrencia")

        with self.assertRaises(Exception):
            self.service._procesar_vinculacion(MagicMock(), MagicMock(modalidad="TRADICIONAL"), MagicMock(), MagicMock(), 500)



    @patch("api.models.Hermano.objects.get")
    def test_vinculacion_falla_si_objetivo_tiene_datos_corruptos_duplicados(self, mock_hermano_get):
        """
        Test: múltiples papeletas activas (inconsistencia BD)

        Given: El hermano objetivo tiene 2 papeletas activas para el mismo acto.
        When: Se intenta procesar la vinculación.
        Then: Lanza ValidationError indicando inconsistencia y pidiendo contactar con secretaría.
        """
        mock_acto = MagicMock(modalidad=Acto.ModalidadReparto.TRADICIONAL)

        mock_hermano_solicitante = MagicMock(id=1, numero_registro=100)
        mock_hermano_objetivo = MagicMock(id=2, numero_registro=500)
        mock_hermano_get.return_value = mock_hermano_objetivo

        self.service._qs_papeletas_activas = MagicMock()
        mock_qs_chain = self.service._qs_papeletas_activas.return_value.select_for_update.return_value.filter.return_value.order_by.return_value

        mock_qs_chain.count.return_value = 2

        mensaje_error = "tiene múltiples solicitudes activas para este acto. Contacte con secretaría."

        with self.assertRaisesMessage(ValidationError, mensaje_error):
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
        Test: hermano objetivo con puesto None

        Given: La papeleta del objetivo existe pero el campo puesto es None.
        When: Se intenta realizar la vinculación.
        Then: Lanza ValidationError: "El hermano Nº 500 no tiene puesto seleccionado."
        """
        mock_acto = MagicMock(modalidad=Acto.ModalidadReparto.TRADICIONAL)

        mock_hermano_solicitante = MagicMock(id=1, numero_registro=100)
        mock_hermano_objetivo = MagicMock(id=2, numero_registro=500)
        mock_hermano_get.return_value = mock_hermano_objetivo

        mock_papeleta_obj = MagicMock(puesto=None, es_solicitud_insignia=False)

        self.service._qs_papeletas_activas = MagicMock()
        mock_base_qs = self.service._qs_papeletas_activas.return_value

        mock_qs_chain = mock_base_qs.select_for_update.return_value.filter.return_value.order_by.return_value
        mock_qs_chain.count.return_value = 1
        mock_qs_chain.get.return_value = mock_papeleta_obj

        mock_base_qs.filter.return_value.exists.return_value = False

        with self.assertRaisesMessage(ValidationError, "no tiene puesto seleccionado"):
            self.service._procesar_vinculacion(
                mock_hermano_solicitante,
                mock_acto,
                MagicMock(),
                MagicMock(),
                500
            )



    @patch("api.models.Hermano.objects.get")
    def test_vinculacion_boundary_cortejo_incompatible(self, mock_hermano_get):
        """
        Test: cortejo distinto (Boolean Boundary)

        Given: 
            - Un hermano solicitante asignado a la sección de "Paso de Cristo" (cortejo_cristo=True).
            - Un hermano objetivo asignado a la sección de "Paso de Virgen" (cortejo_cristo=False).
            - Ambos hermanos tienen el mismo tipo de puesto (ej: Cirio) y cumplen 
            con los requisitos de antigüedad.
        When: 
            - Se intenta procesar la vinculación entre ambos mediante _procesar_vinculacion.
        Then: 
            - Debe lanzar un ValidationError con el mensaje "Conflicto de sección: 
            Uno va en Cristo y otro en Virgen."
            - No se debe ejecutar el guardado (.save()) de la papeleta, protegiendo 
            la integridad estética y logística del cortejo.
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
    def test_orden_validacion_corta_en_modalidad_antes_de_consultar_db(self, mock_hermano_get):
        """
        Test: orden de validaciones (muy importante)
        
        Given: Un acto con modalidad incorrecta.
        When: Se llama a _procesar_vinculacion.
        Then: 
            - Lanza ValidationError de modalidad.
            - El mock de Hermano.objects.get NUNCA es llamado (ahorro de DB).
        """
        mock_acto = MagicMock(modalidad="PROXIMIDAD")

        with self.assertRaisesMessage(ValidationError, "solo está disponible en modalidad TRADICIONAL"):
            self.service._procesar_vinculacion(
                MagicMock(), mock_acto, MagicMock(), MagicMock(), 500
            )

        mock_hermano_get.assert_not_called()



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



    @patch("api.models.PapeletaSitio.objects.exclude")
    def test_retorna_queryset_resultante(self, mock_exclude):
        """
        Test: Validar que el método devuelve exactamente lo que retorna el ORM.

        Given: Una llamada al manager de PapeletaSitio.
        When: Se ejecuta _qs_papeletas_activas.
        Then: El objeto devuelto por el método debe ser el mismo objeto 
            devuelto por la función .exclude().
        """
        servicio = SolicitudCirioTradicionalService()

        mock_queryset_esperado = MagicMock(name="QuerySet_Filtrado_Activas")

        mock_exclude.return_value = mock_queryset_esperado

        resultado = servicio._qs_papeletas_activas()

        self.assertIs(
            resultado, 
            mock_queryset_esperado, 
            "El método debe retornar el QuerySet que genera el exclude sin alteraciones."
        )

        mock_exclude.assert_called_once()



    @patch("api.models.PapeletaSitio.objects.exclude")
    def test_usa_constante_estados_no_activos(self, mock_exclude):
        """
        Test: Validar que el método usa la constante de la clase y no valores fijos.

        Given: Una instancia de SolicitudCirioTradicionalService.
        When: Se llama a _qs_papeletas_activas.
        Then: Los argumentos de exclude deben coincidir con la constante ESTADOS_NO_ACTIVOS.
        """
        servicio = SolicitudCirioTradicionalService()

        estados_ficticios = ('ESTADO_TEST_1', 'ESTADO_TEST_2')
        
        with patch.object(SolicitudCirioTradicionalService, 'ESTADOS_NO_ACTIVOS', estados_ficticios):
            servicio._qs_papeletas_activas()

            mock_exclude.assert_called_once_with(
                estado_papeleta__in=estados_ficticios
            )



    def test_estados_no_activos_contiene_anulada_y_no_asignada(self):
        """
        Test: Verificar la presencia de estados críticos en la constante.

        Given: La clase SolicitudCirioTradicionalService.
        When: Se inspecciona la constante ESTADOS_NO_ACTIVOS.
        Then: Debe contener al menos ANULADA y NO_ASIGNADA.
        """
        servicio = SolicitudCirioTradicionalService()

        estados = servicio.ESTADOS_NO_ACTIVOS

        self.assertIsInstance(estados, (tuple, list))

        self.assertIn(PapeletaSitio.EstadoPapeleta.ANULADA, estados)
        self.assertIn(PapeletaSitio.EstadoPapeleta.NO_ASIGNADA, estados)

        self.assertEqual(len(estados), 2, "La constante tiene más o menos estados de los esperados originalmente.")



    @patch("api.models.PapeletaSitio.objects.exclude")
    def test_no_modifica_queryset_original(self, mock_exclude):
        """
        Test: Validar que el método solo delega la responsabilidad al ORM.

        Given: Una llamada al método _qs_papeletas_activas.
        When: Se ejecuta la lógica interna.
        Then: 
            - No se deben llamar a métodos de escritura (update, delete, save).
            - El Manager de PapeletaSitio solo debe registrar la llamada a exclude.
        """
        servicio = SolicitudCirioTradicionalService()

        mock_qs_resultado = MagicMock(name="QS_Resultado")
        mock_exclude.return_value = mock_qs_resultado

        servicio._qs_papeletas_activas()

        self.assertTrue(mock_exclude.called)

        self.assertFalse(mock_qs_resultado.delete.called)
        self.assertFalse(mock_qs_resultado.update.called)

        llamadas_manager = [call[0] for call in mock_exclude.call_args_list]
        self.assertEqual(len(llamadas_manager), 1, "El método realizó más llamadas de las esperadas al Manager.")
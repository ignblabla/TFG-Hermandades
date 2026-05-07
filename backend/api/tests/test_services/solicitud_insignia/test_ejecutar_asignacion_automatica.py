from datetime import datetime, timedelta, timezone
from unittest import TestCase
from unittest.mock import MagicMock, patch
from django.core.exceptions import ValidationError

from api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service import RepartoService
from api.models import Acto


class TestRepartoServiceAsignacion(TestCase):

    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.TelegramWebhookService.notificar_papeleta_asignada')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_ejecucion_correcta_asignacion_y_prioridades(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic, mock_telegram
    ):
        """
        Test: Flujo completo con asignación y prioridades

        Given: Un acto válido. Un catálogo con dos puestos disponibles. 
            Dos solicitudes: la primera consigue su preferencia 1, la segunda no 
            tiene stock en su preferencia 1 y consigue la preferencia 2.
        When: Se ejecuta la asignación automática.
        Then: 
            - Se asignan los puestos correctamente respetando las prioridades.
            - Se emiten las papeletas con numeración secuencial.
            - Se envía la notificación por Telegram a quienes tienen chat_id.
            - Se actualiza la fecha de ejecución del reparto en el acto.
        """
        acto_id = 1
        now_val = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
        mock_now.return_value = now_val

        mock_acto_filter.return_value.exists.return_value = True
        mock_acto = MagicMock(nombre="Procesión Test", fecha_ejecucion_reparto=None)
        mock_acto.fin_solicitud = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
        mock_acto_sfu.return_value.get.return_value = mock_acto

        puesto_a = MagicMock(id=10, nombre="Cruz de Guía", numero_maximo_asignaciones=1, total_ocupadas=0)
        puesto_b = MagicMock(id=20, nombre="Senatus", numero_maximo_asignaciones=1, total_ocupadas=0)
        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = [puesto_a, puesto_b]

        s1 = MagicMock()
        s1.hermano.nombre = "Juan"
        s1.hermano.telegram_chat_id = "123456"
        s1.preferencias.all.return_value.order_by.return_value = [MagicMock(puesto_solicitado_id=10)]

        s2 = MagicMock()
        s2.hermano.nombre = "María"
        s2.hermano.telegram_chat_id = None
        s2.preferencias.all.return_value.order_by.return_value = [
            MagicMock(puesto_solicitado_id=10),
            MagicMock(puesto_solicitado_id=20)
        ]

        mock_papeleta_filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = [s1, s2]
        mock_papeleta_filter.return_value.aggregate.return_value = {'max_val': 500}

        resultado = RepartoService.ejecutar_asignacion_automatica(acto_id)

        self.assertEqual(resultado["asignaciones"], 2)
        self.assertEqual(resultado["sin_asignar_count"], 0)
        self.assertEqual(mock_acto.fecha_ejecucion_reparto, now_val)

        self.assertEqual(s1.puesto, puesto_a)
        self.assertEqual(s1.estado_papeleta, "EMITIDA")
        self.assertEqual(s1.numero_papeleta, 501)

        self.assertEqual(s2.puesto, puesto_b)
        self.assertEqual(s2.estado_papeleta, "EMITIDA")
        self.assertEqual(s2.numero_papeleta, 502)

        mock_telegram.assert_called_once_with(
            chat_id="123456",
            nombre_hermano="Juan",
            nombre_acto="Procesión Test",
            estado="ASIGNADA",
            nombre_puesto="Cruz de Guía"
        )

    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.TelegramWebhookService.notificar_papeleta_asignada')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_ejecucion_competencia_y_fallo_asignacion(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic, mock_telegram
    ):
        """
        Test: Competencia por puesto y fallo de asignación por falta de stock

        Given: Un puesto con 1 sola vacante. Dos solicitudes compiten por él.
        When: Se ejecuta el algoritmo de asignación.
        Then: 
            - El primer hermano obtiene el puesto.
            - El segundo hermano queda sin asignar (NO_ASIGNADA).
            - El sistema agrupa a los no asignados en el reporte final y notifica.
        """
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)
        mock_acto_filter.return_value.exists.return_value = True
        mock_acto = MagicMock(nombre="Acto Competencia", fecha_ejecucion_reparto=None, fin_solicitud=None)
        mock_acto_sfu.return_value.get.return_value = mock_acto

        puesto_disputado = MagicMock(id=55, nombre="Vara Única", numero_maximo_asignaciones=1, total_ocupadas=0)
        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = [puesto_disputado]

        s1 = MagicMock(puesto=None)
        s1.hermano.telegram_chat_id = None
        s1.preferencias.all.return_value.order_by.return_value = [MagicMock(puesto_solicitado_id=55)]

        s2 = MagicMock(puesto=None)
        s2.hermano.id = 88
        s2.hermano.nombre = "Luis"
        s2.hermano.primer_apellido = "García"
        s2.hermano.numero_registro = 500
        s2.hermano.telegram_chat_id = "TEL_88"
        s2.preferencias.all.return_value.order_by.return_value = [MagicMock(puesto_solicitado_id=55)]

        mock_papeleta_filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = [s1, s2]
        mock_papeleta_filter.return_value.aggregate.return_value = {'max_val': 0}

        resultado = RepartoService.ejecutar_asignacion_automatica(1)

        self.assertEqual(s1.estado_papeleta, "EMITIDA")
        self.assertEqual(s1.puesto, puesto_disputado)

        self.assertEqual(s2.estado_papeleta, "NO_ASIGNADA")
        self.assertIsNone(s2.puesto)

        self.assertEqual(resultado["asignaciones"], 1)
        self.assertEqual(resultado["sin_asignar_count"], 1)
        self.assertEqual(resultado["sin_asignar_lista"][0]["id"], 88)
        self.assertEqual(resultado["sin_asignar_lista"][0]["nombre"], "Luis García")

        mock_telegram.assert_called_once_with(
            chat_id="TEL_88",
            nombre_hermano="Luis",
            nombre_acto="Acto Competencia",
            estado="NO_ASIGNADA"
        )



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_ejecucion_falla_por_reglas_del_acto(self, mock_acto_filter, mock_acto_sfu, mock_now, mock_atomic):
        """
        Test: Validaciones de negocio y estado del acto

        Given: Diferentes escenarios inválidos para el acto.
        When: Se intenta ejecutar la asignación automática.
        Then: Se lanza ValidationError con el mensaje adecuado interrumpiendo el proceso.
        """
        ahora = datetime(2026, 4, 10, 10, 0, tzinfo=timezone.utc)
        mock_now.return_value = ahora

        mock_acto_filter.return_value.exists.return_value = False
        with self.assertRaises(ValidationError) as cm1:
            RepartoService.ejecutar_asignacion_automatica(99)
        self.assertEqual(cm1.exception.message, "El acto especificado no existe.")

        mock_acto_filter.return_value.exists.return_value = True

        mock_acto_sfu.return_value.get.side_effect = Acto.DoesNotExist
        with self.assertRaises(ValidationError) as cm2:
            RepartoService.ejecutar_asignacion_automatica(1)
        self.assertEqual(cm2.exception.message, "El acto no existe.")

        mock_acto_sfu.return_value.get.side_effect = None

        mock_acto_sfu.return_value.get.return_value = MagicMock(fecha_ejecucion_reparto=ahora)
        with self.assertRaises(ValidationError) as cm3:
            RepartoService.ejecutar_asignacion_automatica(1)
        self.assertIn("El reparto para este acto ya se ejecutó", str(cm3.exception))

        mock_acto_sfu.return_value.get.return_value = MagicMock(
            fecha_ejecucion_reparto=None, 
            fin_solicitud=ahora + timedelta(days=1)
        )
        with self.assertRaises(ValidationError) as cm4:
            RepartoService.ejecutar_asignacion_automatica(1)
        self.assertIn("El plazo de solicitud no ha finalizado aún", str(cm4.exception))



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_ejecucion_sin_solicitudes(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic
    ):
        """
        Test: Cero solicitudes

        Given: Un acto válido pero sin solicitudes de hermanos.
        When: Se procesa el reparto automático.
        Then: El algoritmo no falla, procesa 0 asignaciones.
        """
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)
        mock_acto_filter.return_value.exists.return_value = True
        
        mock_acto = MagicMock(fecha_ejecucion_reparto=None, fin_solicitud=None)
        mock_acto_sfu.return_value.get.return_value = mock_acto
        
        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = []
        mock_papeleta_query = mock_papeleta_filter.return_value

        mock_papeleta_query.select_related.return_value.prefetch_related.return_value.order_by.return_value = []
        mock_papeleta_query.aggregate.return_value = {'max_val': 0}

        resultado_vacio = RepartoService.ejecutar_asignacion_automatica(1)
        self.assertEqual(resultado_vacio["asignaciones"], 0)
        self.assertEqual(resultado_vacio["sin_asignar_count"], 0)



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_ejecucion_solicitud_sin_preferencias(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic
    ):
        """
        Test: Solicitud sin preferencias

        Given: Un acto válido y una solicitud de un hermano pero sin preferencias elegidas.
        When: Se procesa el reparto automático.
        Then: El algoritmo no falla, procesa 0 asignaciones y marca como NO_ASIGNADA 
            la solicitud sin preferencias.
        """
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)
        mock_acto_filter.return_value.exists.return_value = True
        
        mock_acto = MagicMock(fecha_ejecucion_reparto=None, fin_solicitud=None)
        mock_acto_sfu.return_value.get.return_value = mock_acto
        
        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = []
        mock_papeleta_query = mock_papeleta_filter.return_value

        solicitud_sin_prefs = MagicMock()
        solicitud_sin_prefs.hermano.telegram_chat_id = None
        solicitud_sin_prefs.preferencias.all.return_value.order_by.return_value = []
        
        mock_papeleta_query.select_related.return_value.prefetch_related.return_value.order_by.return_value = [solicitud_sin_prefs]
        mock_papeleta_query.aggregate.return_value = {'max_val': 0}

        resultado_sin_prefs = RepartoService.ejecutar_asignacion_automatica(1)
        self.assertEqual(solicitud_sin_prefs.estado_papeleta, "NO_ASIGNADA")
        self.assertEqual(resultado_sin_prefs["asignaciones"], 0)
        self.assertEqual(resultado_sin_prefs["sin_asignar_count"], 1)
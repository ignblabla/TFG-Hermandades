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
    def test_ejecucion_correcta_con_asignaciones(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic, mock_telegram
    ):
        """
        Test: Ejecución correcta con asignaciones

        Given: Un acto válido cuyo plazo ha finalizado, con stock disponible en puestos e insignias solicitadas.
        When: Se ejecuta la asignación automática.
        Then: Se realizan asignaciones, las papeletas cambian a EMITIDA, se asigna número correlativo y se marca el acto como ejecutado.
        """
        acto_id = 1
        now_val = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
        mock_now.return_value = now_val

        mock_acto_filter.return_value.exists.return_value = True
        mock_acto = MagicMock()
        mock_acto.id = acto_id
        mock_acto.nombre = "Procesión Test"
        mock_acto.fecha_ejecucion_reparto = None
        mock_acto.fin_solicitud = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
        mock_acto_sfu.return_value.get.return_value = mock_acto

        mock_puesto = MagicMock()
        mock_puesto.id = 100
        mock_puesto.nombre = "Cruz de Guía"
        mock_puesto.numero_maximo_asignaciones = 2
        mock_puesto.total_ocupadas = 0

        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = [mock_puesto]

        mock_hermano = MagicMock()
        mock_hermano.id = 50
        mock_hermano.nombre = "Juan"
        mock_hermano.primer_apellido = "Pérez"
        mock_hermano.numero_registro = 10
        mock_hermano.telegram_chat_id = "123456"

        mock_solicitud = MagicMock()
        mock_solicitud.hermano = mock_hermano

        mock_pref = MagicMock()
        mock_pref.puesto_solicitado_id = 100
        mock_solicitud.preferencias.all.return_value.order_by.return_value = [mock_pref]

        mock_papeleta_filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = [mock_solicitud]

        mock_papeleta_filter.return_value.aggregate.return_value = {'max_val': 500}

        resultado = RepartoService.ejecutar_asignacion_automatica(acto_id)

        self.assertEqual(resultado["asignaciones"], 1)
        self.assertEqual(resultado["sin_asignar_count"], 0)

        self.assertEqual(mock_solicitud.estado_papeleta, "EMITIDA")
        self.assertEqual(mock_solicitud.numero_papeleta, 501)
        mock_solicitud.save.assert_called()

        self.assertEqual(mock_acto.fecha_ejecucion_reparto, now_val)
        mock_acto.save.assert_called()

        mock_telegram.assert_called_with(
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
    def test_asignacion_respeta_prioridades(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic, mock_telegram
    ):
        """
        Test: Asignación respeta prioridades

        Given: Una solicitud con dos preferencias (Puesto A y Puesto B), donde el Puesto A no tiene stock y el B sí.
        When: Se ejecuta el algoritmo de asignación.
        Then: El sistema debe saltar la primera preferencia y asignar la segunda disponible (Puesto B).
        """
        acto_id = 1
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)

        mock_acto_filter.return_value.exists.return_value = True
        mock_acto = MagicMock(nombre="Viernes Santo")
        mock_acto.fecha_ejecucion_reparto = None
        mock_acto.fin_solicitud = datetime(2026, 3, 1, tzinfo=timezone.utc)
        mock_acto_sfu.return_value.get.return_value = mock_acto

        puesto_a = MagicMock(id=10, nombre="Puesto A", numero_maximo_asignaciones=1, total_ocupadas=1)
        puesto_b = MagicMock(id=20, nombre="Puesto B", numero_maximo_asignaciones=1, total_ocupadas=0)
        
        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = [puesto_a, puesto_b]

        mock_solicitud = MagicMock()
        mock_solicitud.hermano.telegram_chat_id = None
        
        pref_1 = MagicMock(puesto_solicitado_id=10)
        pref_2 = MagicMock(puesto_solicitado_id=20)

        mock_solicitud.preferencias.all.return_value.order_by.return_value = [pref_1, pref_2]

        mock_papeleta_filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = [mock_solicitud]
        mock_papeleta_filter.return_value.aggregate.return_value = {'max_val': 0}

        service = RepartoService()
        service.ejecutar_asignacion_automatica(acto_id)

        self.assertEqual(mock_solicitud.puesto, puesto_b)
        self.assertEqual(mock_solicitud.estado_papeleta, "EMITIDA")

        self.assertNotEqual(mock_solicitud.puesto, puesto_a)
        
        mock_solicitud.save.assert_called()



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.TelegramWebhookService.notificar_papeleta_asignada')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_decremento_de_stock_correcto(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic, mock_telegram
    ):
        """
        Test: Decremento de stock correcto

        Given: Un puesto con 2 unidades de stock disponibles y una solicitud que lo pide.
        When: Se realiza la asignación.
        Then: El atributo _stock_temp del puesto debe disminuir a 1 tras la asignación.
        """
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)
        mock_acto_filter.return_value.exists.return_value = True
        mock_acto_sfu.return_value.get.return_value = MagicMock(fin_solicitud=None, fecha_ejecucion_reparto=None)

        puesto_mock = MagicMock(id=1, numero_maximo_asignaciones=2, total_ocupadas=0)
        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = [puesto_mock]

        mock_solicitud = MagicMock()
        mock_solicitud.hermano.telegram_chat_id = None
        pref = MagicMock(puesto_solicitado_id=1)
        mock_solicitud.preferencias.all.return_value.order_by.return_value = [pref]

        mock_papeleta_filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = [mock_solicitud]
        mock_papeleta_filter.return_value.aggregate.return_value = {'max_val': 0}

        RepartoService.ejecutar_asignacion_automatica(1)

        self.assertEqual(puesto_mock._stock_temp, 1)



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.TelegramWebhookService.notificar_papeleta_asignada')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_eliminacion_puesto_sin_stock(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic, mock_telegram
    ):
        """
        Test: Eliminación de puesto sin stock

        Given: Un puesto con solo 1 unidad de stock y dos hermanos que lo solicitan.
        When: Se procesa la primera solicitud.
        Then: El puesto debe desaparecer del mapa_puestos interno y no estar disponible para la segunda solicitud.
        """
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)
        mock_acto_filter.return_value.exists.return_value = True
        
        mock_acto = MagicMock(fin_solicitud=None, fecha_ejecucion_reparto=None)
        mock_acto.nombre = "Acto Test"
        mock_acto_sfu.return_value.get.return_value = mock_acto

        puesto_mock = MagicMock(id=99, nombre="Insignia Única", numero_maximo_asignaciones=1, total_ocupadas=0)
        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = [puesto_mock]

        solicitud_1 = MagicMock()
        solicitud_1.hermano.telegram_chat_id = None
        solicitud_1.puesto = None

        solicitud_2 = MagicMock()
        solicitud_2.hermano.telegram_chat_id = None
        solicitud_2.puesto = None
        
        for s in [solicitud_1, solicitud_2]:
            pref = MagicMock(puesto_solicitado_id=99)
            s.preferencias.all.return_value.order_by.return_value = [pref]

        mock_papeleta_filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = [solicitud_1, solicitud_2]
        mock_papeleta_filter.return_value.aggregate.return_value = {'max_val': 0}

        RepartoService.ejecutar_asignacion_automatica(1)

        self.assertEqual(solicitud_1.estado_papeleta, "EMITIDA")
        self.assertEqual(solicitud_1.puesto, puesto_mock)

        self.assertEqual(solicitud_2.estado_papeleta, "NO_ASIGNADA")
        self.assertIsNone(solicitud_2.puesto)



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.TelegramWebhookService.notificar_papeleta_asignada')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_numeracion_de_papeletas_correcta(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic, mock_telegram
    ):
        """
        Test: Numeración de papeletas correcta

        Given: El número máximo de papeleta actual en el acto es 500 y hay dos solicitudes por procesar.
        When: Se ejecuta el reparto automático.
        Then: La primera papeleta debe tener el número 501 y la segunda el 502 (incremento secuencial).
        """
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)
        mock_acto_filter.return_value.exists.return_value = True
        mock_acto_sfu.return_value.get.return_value = MagicMock(fin_solicitud=None, fecha_ejecucion_reparto=None)

        puesto_mock = MagicMock(id=1, numero_maximo_asignaciones=10, total_ocupadas=0)
        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = [puesto_mock]

        s1, s2 = MagicMock(), MagicMock()
        for s in [s1, s2]:
            s.hermano.telegram_chat_id = None
            s.preferencias.all.return_value.order_by.return_value = [MagicMock(puesto_solicitado_id=1)]

        mock_papeleta_filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = [s1, s2]

        mock_papeleta_filter.return_value.aggregate.return_value = {'max_val': 500}

        RepartoService.ejecutar_asignacion_automatica(1)

        self.assertEqual(s1.numero_papeleta, 501)
        self.assertEqual(s2.numero_papeleta, 502)



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.TelegramWebhookService.notificar_papeleta_asignada')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_notificacion_telegram_en_asignacion(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic, mock_telegram
    ):
        """
        Test: Notificación Telegram en asignación

        Given: Un hermano con telegram_chat_id configurado que recibe una insignia.
        When: Se completa la asignación de su puesto.
        Then: Se debe invocar al servicio de Telegram con el estado "ASIGNADA" y el nombre del puesto.
        """
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)
        mock_acto_filter.return_value.exists.return_value = True

        mock_acto = MagicMock(nombre="Acto Notificación", fecha_ejecucion_reparto=None, fin_solicitud=None)
        mock_acto_sfu.return_value.get.return_value = mock_acto

        puesto_mock = MagicMock(id=1, nombre="Vara Maestro", numero_maximo_asignaciones=1, total_ocupadas=0)
        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = [puesto_mock]

        solicitud = MagicMock()
        solicitud.hermano.nombre = "Pepe"
        solicitud.hermano.telegram_chat_id = "CHAT_ID_123"
        solicitud.preferencias.all.return_value.order_by.return_value = [MagicMock(puesto_solicitado_id=1)]

        mock_papeleta_filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = [solicitud]
        mock_papeleta_filter.return_value.aggregate.return_value = {'max_val': 0}

        RepartoService.ejecutar_asignacion_automatica(1)

        mock_telegram.assert_called_once_with(
            chat_id="CHAT_ID_123",
            nombre_hermano="Pepe",
            nombre_acto="Acto Notificación",
            estado="ASIGNADA",
            nombre_puesto="Vara Maestro"
        )



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.TelegramWebhookService.notificar_papeleta_asignada')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_caso_sin_asignacion(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic, mock_telegram
    ):
        """
        Test: Caso sin asignación

        Given: Una solicitud para un puesto que ya no tiene stock disponible.
        When: Se ejecuta el reparto automático.
        Then: El estado de la papeleta debe ser NO_ASIGNADA y el hermano debe aparecer en la lista de resultados de sin_asignar_lista.
        """
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)
        mock_acto_filter.return_value.exists.return_value = True
        mock_acto = MagicMock(nombre="Acto Sin Stock", fecha_ejecucion_reparto=None, fin_solicitud=None)
        mock_acto_sfu.return_value.get.return_value = mock_acto

        puesto_agotado = MagicMock(id=5, numero_maximo_asignaciones=1, total_ocupadas=1)
        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = [puesto_agotado]

        mock_hermano = MagicMock(id=88, numero_registro=500, telegram_chat_id=None)
        mock_hermano.nombre = "Luis"
        mock_hermano.primer_apellido = "García"
        
        solicitud = MagicMock()
        solicitud.hermano = mock_hermano
        solicitud.puesto = None 
        solicitud.preferencias.all.return_value.order_by.return_value = [MagicMock(puesto_solicitado_id=5)]

        mock_papeleta_filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = [solicitud]
        mock_papeleta_filter.return_value.aggregate.return_value = {'max_val': 0}

        resultado = RepartoService.ejecutar_asignacion_automatica(1)

        self.assertEqual(solicitud.estado_papeleta, "NO_ASIGNADA")
        solicitud.save.assert_called()

        self.assertEqual(resultado["sin_asignar_count"], 1)
        self.assertEqual(resultado["sin_asignar_lista"][0]["id"], 88)
        self.assertEqual(resultado["sin_asignar_lista"][0]["nombre"], "Luis García")



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.TelegramWebhookService.notificar_papeleta_asignada')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_notificacion_telegram_sin_asignacion(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic, mock_telegram
    ):
        """
        Test: Notificación Telegram sin asignación

        Given: Un hermano con Telegram activo cuya solicitud no puede ser atendida por falta de stock.
        When: El algoritmo finaliza el intento de asignación para dicho hermano.
        Then: Se debe enviar una notificación de Telegram con el estado "NO_ASIGNADA".
        """
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)
        mock_acto_filter.return_value.exists.return_value = True
        mock_acto = MagicMock(nombre="Acto Notif Negativa", fecha_ejecucion_reparto=None, fin_solicitud=None)
        mock_acto_sfu.return_value.get.return_value = mock_acto

        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = []

        solicitud = MagicMock()
        solicitud.hermano.nombre = "Carlos"
        solicitud.hermano.telegram_chat_id = "TELEGRAM_ID_999"
        solicitud.preferencias.all.return_value.order_by.return_value = [MagicMock(puesto_solicitado_id=1)]

        mock_papeleta_filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = [solicitud]
        mock_papeleta_filter.return_value.aggregate.return_value = {'max_val': 0}

        RepartoService.ejecutar_asignacion_automatica(1)

        mock_telegram.assert_called_once_with(
            chat_id="TELEGRAM_ID_999",
            nombre_hermano="Carlos",
            nombre_acto="Acto Notif Negativa",
            estado="NO_ASIGNADA"
        )



    @patch('api.models.Acto.objects.filter')
    def test_acto_no_existe_exists_false(self, mock_acto_filter):
        """
        Test: Acto no existe (exists=False)

        Given: Un acto_id que no se encuentra en la base de datos al realizar la comprobación inicial.
        When: Se intenta ejecutar la asignación automática.
        Then: El sistema debe lanzar una ValidationError con el mensaje "El acto especificado no existe.".
        """
        mock_acto_filter.return_value.exists.return_value = False

        with self.assertRaises(ValidationError) as context:
            RepartoService.ejecutar_asignacion_automatica(acto_id=999)
        
        self.assertEqual(context.exception.message, "El acto especificado no existe.")



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_acto_no_encontrado_en_select_for_update(self, mock_acto_filter, mock_acto_sfu, mock_atomic):
        """
        Test: Acto no encontrado en select_for_update

        Given: Un acto que existe inicialmente, pero que al intentar bloquearlo con select_for_update lanza Acto.DoesNotExist.
        When: El algoritmo intenta obtener el bloqueo pesimista del acto.
        Then: El sistema debe capturar el DoesNotExist y lanzar una ValidationError con el mensaje "El acto no existe.".
        """
        mock_acto_filter.return_value.exists.return_value = True

        mock_acto_sfu.return_value.get.side_effect = Acto.DoesNotExist

        with self.assertRaises(ValidationError) as context:
            RepartoService.ejecutar_asignacion_automatica(acto_id=1)
        
        self.assertEqual(context.exception.message, "El acto no existe.")



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_reparto_ya_ejecutado_idempotencia(self, mock_acto_filter, mock_acto_sfu, mock_atomic):
        """
        Test: Reparto ya ejecutado (idempotencia)

        Given: Un acto que ya tiene una fecha_ejecucion_reparto asignada.
        When: Se intenta ejecutar el algoritmo de asignación nuevamente.
        Then: Se debe lanzar una ValidationError indicando que el reparto ya se ejecutó.
        """
        mock_acto_filter.return_value.exists.return_value = True
        
        fecha_previa = datetime(2026, 3, 15, tzinfo=timezone.utc)
        mock_acto = MagicMock(fecha_ejecucion_reparto=fecha_previa)
        mock_acto_sfu.return_value.get.return_value = mock_acto

        with self.assertRaises(ValidationError) as context:
            RepartoService.ejecutar_asignacion_automatica(acto_id=1)
        
        self.assertIn("El reparto para este acto ya se ejecutó", str(context.exception))



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_plazo_no_finalizado(self, mock_acto_filter, mock_acto_sfu, mock_now, mock_atomic):
        """
        Test: Plazo no finalizado

        Given: Un acto donde la fecha actual (now) es anterior o igual a la fecha fin_solicitud.
        When: Se intenta ejecutar el reparto automático.
        Then: El sistema debe lanzar una ValidationError informando que el plazo no ha finalizado.
        """
        ahora = datetime(2026, 4, 10, 10, 0, tzinfo=timezone.utc)
        fin_plazo = ahora + timedelta(hours=2)
        
        mock_now.return_value = ahora
        mock_acto_filter.return_value.exists.return_value = True
        
        mock_acto = MagicMock(fecha_ejecucion_reparto=None, fin_solicitud=fin_plazo)
        mock_acto_sfu.return_value.get.return_value = mock_acto

        with self.assertRaises(ValidationError) as context:
            RepartoService.ejecutar_asignacion_automatica(acto_id=1)
        
        self.assertIn("El plazo de solicitud no ha finalizado aún", str(context.exception))



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_sin_solicitudes(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic
    ):
        """
        Test: Sin solicitudes

        Given: Un acto válido con puestos disponibles, pero donde ningún hermano ha realizado solicitudes.
        When: Se ejecuta el reparto automático.
        Then: El sistema no debe dar error y debe devolver un resultado con 0 asignaciones y 0 hermanos sin puesto.
        """
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)
        mock_acto_filter.return_value.exists.return_value = True

        mock_acto = MagicMock(fecha_ejecucion_reparto=None, fin_solicitud=None)
        mock_acto.nombre = "Acto Vacío"
        mock_acto_sfu.return_value.get.return_value = mock_acto

        puesto_con_stock = MagicMock(id=1)
        puesto_con_stock.numero_maximo_asignaciones = 5
        puesto_con_stock.total_ocupadas = 0
        
        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = [puesto_con_stock]

        mock_papeleta_query = mock_papeleta_filter.return_value
        mock_papeleta_query.select_related.return_value.prefetch_related.return_value.order_by.return_value = []

        mock_papeleta_query.aggregate.return_value = {'max_val': 0}

        resultado = RepartoService.ejecutar_asignacion_automatica(1)

        self.assertEqual(resultado["asignaciones"], 0)
        self.assertEqual(resultado["sin_asignar_count"], 0)
        mock_acto.save.assert_called_once()



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.TelegramWebhookService.notificar_papeleta_asignada')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_sin_puestos_disponibles(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic, mock_telegram
    ):
        """
        Test: Sin puestos disponibles

        Given: Un acto con solicitudes activas, pero donde ningún puesto cumple la condición de tener stock real > 0.
        When: Se ejecuta el reparto automático.
        Then: Todas las solicitudes deben ser marcadas como NO_ASIGNADA.
        """
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)
        mock_acto_filter.return_value.exists.return_value = True
        mock_acto_sfu.return_value.get.return_value = MagicMock(fecha_ejecucion_reparto=None, fin_solicitud=None)

        puesto_sin_stock = MagicMock(id=1, numero_maximo_asignaciones=5, total_ocupadas=5)
        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = [puesto_sin_stock]

        solicitud = MagicMock()
        solicitud.hermano.telegram_chat_id = None
        solicitud.preferencias.all.return_value.order_by.return_value = [MagicMock(puesto_solicitado_id=1)]

        mock_papeleta_filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = [solicitud]
        mock_papeleta_filter.return_value.aggregate.return_value = {'max_val': 0}

        resultado = RepartoService.ejecutar_asignacion_automatica(1)

        self.assertEqual(solicitud.estado_papeleta, "NO_ASIGNADA")
        self.assertEqual(resultado["asignaciones"], 0)
        self.assertEqual(resultado["sin_asignar_count"], 1)



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_solicitud_sin_preferencias(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic
    ):
        """
        Test: Solicitud sin preferencias

        Given: Una solicitud de insignia que no tiene ninguna preferencia asociada.
        When: Se procesa el reparto automático.
        Then: La solicitud debe marcarse como NO_ASIGNADA y el proceso debe continuar sin errores.
        """
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)
        mock_acto_filter.return_value.exists.return_value = True
        mock_acto_sfu.return_value.get.return_value = MagicMock(fecha_ejecucion_reparto=None, fin_solicitud=None)

        solicitud = MagicMock()
        solicitud.hermano.telegram_chat_id = None

        solicitud.preferencias.all.return_value.order_by.return_value = []

        mock_papeleta_filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = [solicitud]
        mock_papeleta_filter.return_value.aggregate.return_value = {'max_val': 0}

        RepartoService.ejecutar_asignacion_automatica(1)

        self.assertEqual(solicitud.estado_papeleta, "NO_ASIGNADA")
        solicitud.save.assert_called_once()



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.TelegramWebhookService.notificar_papeleta_asignada')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_hermano_sin_telegram_no_notifica(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic, mock_telegram
    ):
        """
        Test: Hermano sin telegram

        Given: Una asignación exitosa para un hermano que no tiene telegram_chat_id (es None).
        When: Se completa la asignación.
        Then: No se debe realizar ninguna llamada al servicio de notificaciones de Telegram.
        """
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)
        mock_acto_filter.return_value.exists.return_value = True
        mock_acto_sfu.return_value.get.return_value = MagicMock(fecha_ejecucion_reparto=None, fin_solicitud=None)

        puesto = MagicMock(id=1, numero_maximo_asignaciones=1, total_ocupadas=0)
        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = [puesto]

        solicitud = MagicMock()
        solicitud.hermano.telegram_chat_id = None
        solicitud.preferencias.all.return_value.order_by.return_value = [MagicMock(puesto_solicitado_id=1)]

        mock_papeleta_filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = [solicitud]
        mock_papeleta_filter.return_value.aggregate.return_value = {'max_val': 0}

        RepartoService.ejecutar_asignacion_automatica(1)

        self.assertEqual(solicitud.estado_papeleta, "EMITIDA")
        mock_telegram.assert_not_called()



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_numero_registro_null_respeta_orden(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic
    ):
        """
        Test: número_registro NULL

        Given: Una consulta de solicitudes ordenadas por el número de registro del hermano.
        When: Se obtienen las solicitudes de la base de datos.
        Then: El sistema debe aplicar un orden ascendente que coloque los valores nulos al final (nulls_last=True).
        """
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)
        mock_acto_filter.return_value.exists.return_value = True
        mock_acto_sfu.return_value.get.return_value = MagicMock(fecha_ejecucion_reparto=None, fin_solicitud=None)

        mock_order_by = mock_papeleta_filter.return_value.select_related.return_value.prefetch_related.return_value.order_by
        mock_order_by.return_value = []

        RepartoService.ejecutar_asignacion_automatica(1)

        args, kwargs = mock_order_by.call_args

        order_expression = args[0]

        self.assertTrue(order_expression.descending is False)
        self.assertTrue(order_expression.nulls_last)



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_aggregate_devuelve_none(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic
    ):
        """
        Test: aggregate devuelve None

        Given: Un acto nuevo donde aún no se han emitido papeletas (Max('numero_papeleta') es None).
        When: Se inicia el proceso de asignación.
        Then: El contador de la primera papeleta asignada debe empezar en 1.
        """
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)
        mock_acto_filter.return_value.exists.return_value = True
        mock_acto_sfu.return_value.get.return_value = MagicMock(fecha_ejecucion_reparto=None, fin_solicitud=None)

        puesto = MagicMock(id=1, numero_maximo_asignaciones=1, total_ocupadas=0)
        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = [puesto]

        solicitud = MagicMock()
        solicitud.hermano.telegram_chat_id = None
        solicitud.preferencias.all.return_value.order_by.return_value = [MagicMock(puesto_solicitado_id=1)]
        
        mock_papeleta_query = mock_papeleta_filter.return_value
        mock_papeleta_query.select_related.return_value.prefetch_related.return_value.order_by.return_value = [solicitud]

        mock_papeleta_query.aggregate.return_value = {'max_val': None}

        RepartoService.ejecutar_asignacion_automatica(1)

        self.assertEqual(solicitud.numero_papeleta, 1)



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_multiples_solicitudes_compitiendo_por_mismo_puesto(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic
    ):
        """
        Test: múltiples solicitudes compitiendo por mismo puesto

        Given: Un puesto con stock real de 1 y dos solicitudes diferentes que lo tienen como única preferencia.
        When: Se ejecuta el reparto automático.
        Then: Solo la primera solicitud (según orden de registro) debe obtener el puesto, mientras que la segunda debe quedar como NO_ASIGNADA.
        """
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)
        mock_acto_filter.return_value.exists.return_value = True
        mock_acto_sfu.return_value.get.return_value = MagicMock(fecha_ejecucion_reparto=None, fin_solicitud=None)

        puesto_disputado = MagicMock(id=55)
        puesto_disputado.numero_maximo_asignaciones = 1
        puesto_disputado.total_ocupadas = 0
        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = [puesto_disputado]

        s1 = MagicMock(puesto=None)
        s2 = MagicMock(puesto=None)
        for s in [s1, s2]:
            s.hermano.telegram_chat_id = None
            pref = MagicMock(puesto_solicitado_id=55)
            s.preferencias.all.return_value.order_by.return_value = [pref]

        mock_papeleta_query = mock_papeleta_filter.return_value
        mock_papeleta_query.select_related.return_value.prefetch_related.return_value.order_by.return_value = [s1, s2]
        mock_papeleta_query.aggregate.return_value = {'max_val': 0}

        RepartoService.ejecutar_asignacion_automatica(1)

        self.assertEqual(s1.estado_papeleta, "EMITIDA")
        self.assertEqual(s1.puesto, puesto_disputado)

        self.assertEqual(s2.estado_papeleta, "NO_ASIGNADA")
        self.assertIsNone(s2.puesto)



    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.transaction.atomic')
    @patch('api.servicios.solicitud_insignia.ejecucion_automatica_insignia_service.timezone.now')
    @patch('api.models.PapeletaSitio.objects.filter')
    @patch('api.models.Puesto.objects.filter')
    @patch('api.models.Acto.objects.select_for_update')
    @patch('api.models.Acto.objects.filter')
    def test_stock_inicial_cero_excluye_puesto_del_mapa(
        self, mock_acto_filter, mock_acto_sfu, mock_puesto_filter, 
        mock_papeleta_filter, mock_now, mock_atomic
    ):
        """
        Test: stock inicial = 0

        Given: Un puesto cuyas asignaciones máximas son iguales a su ocupación real actual (stock 0).
        When: Se genera el mapa de puestos candidatos.
        Then: Dicho puesto no debe ser incluido en el mapa_puestos y ninguna solicitud debe poder asignárselo.
        """
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=timezone.utc)
        mock_acto_filter.return_value.exists.return_value = True
        mock_acto_sfu.return_value.get.return_value = MagicMock(fecha_ejecucion_reparto=None, fin_solicitud=None)

        puesto_agotado = MagicMock(id=77)
        puesto_agotado.numero_maximo_asignaciones = 3
        puesto_agotado.total_ocupadas = 3
        mock_puesto_filter.return_value.select_for_update.return_value.annotate.return_value = [puesto_agotado]

        solicitud = MagicMock(puesto=None)
        solicitud.hermano.telegram_chat_id = None
        pref = MagicMock(puesto_solicitado_id=77)
        solicitud.preferencias.all.return_value.order_by.return_value = [pref]

        mock_papeleta_query = mock_papeleta_filter.return_value
        mock_papeleta_query.select_related.return_value.prefetch_related.return_value.order_by.return_value = [solicitud]
        mock_papeleta_query.aggregate.return_value = {'max_val': 0}

        RepartoService.ejecutar_asignacion_automatica(1)

        self.assertEqual(solicitud.estado_papeleta, "NO_ASIGNADA")
        self.assertIsNone(solicitud.puesto)
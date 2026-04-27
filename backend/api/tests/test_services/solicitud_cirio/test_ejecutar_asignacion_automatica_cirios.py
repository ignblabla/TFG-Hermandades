from unittest import TestCase
import unittest
from unittest.mock import patch, MagicMock
import uuid
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime

from api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service import ReportesCiriosService
from api.models import Acto


class TestReportesCiriosService(TestCase):

    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.TelegramWebhookService.notificar_papeleta_asignada")
    def test_flujo_exitoso_basico_asigna_candidatos_y_actualiza_acto(
        self, mock_telegram, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Flujo exitoso básico (hay candidatos y se asignan)

        Given: 
            - Un Acto válido en modalidad TRADICIONAL con fechas configuradas.
            - Una papeleta candidata para el cortejo de CRISTO.
            - Un tramo de CRISTO con aforo suficiente.
        When: 
            - Se ejecuta la asignación automática de cirios.
        Then: 
            - Se resetean los estados previos.
            - Se asigna el candidato al tramo (tramo, numero, lado, etc.).
            - Se llama a bulk_update para guardar los cambios en lote.
            - Se envía la notificación por Telegram.
            - Se actualiza la fecha de ejecución del acto y retorna 1.
        """
        mock_atomic.return_value.__enter__.return_value = None

        mock_acto = MagicMock()
        mock_acto.fecha_ejecucion_cirios = None
        mock_acto.modalidad = "TRADICIONAL"
        mock_acto.fecha_ejecucion_reparto = timezone.now()
        mock_acto.inicio_solicitud_cirios = timezone.now()
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        mock_papeleta = MagicMock(id=1, vinculado_a_id=None)
        mock_papeleta.hermano.id = 1
        mock_papeleta.hermano.fecha_ingreso_corporacion = datetime.date(2010, 1, 1)
        mock_papeleta.hermano.numero_registro = 150
        mock_papeleta.hermano.telegram_chat_id = "123456789"
        mock_papeleta.puesto.nombre = "Cirio Cristo"

        base_qs_mock = mock_papeleta_mgr.filter.return_value

        base_qs_mock.aggregate.return_value = {'numero_papeleta__max': 100}

        base_qs_mock.select_related.side_effect = [
            [mock_papeleta],
            []
        ]

        mock_tramo = MagicMock()
        mock_tramo.numero_maximo_cirios = 50

        mock_tramo_mgr.filter.return_value.order_by.side_effect = [
            [mock_tramo],
            []
        ]

        papeletas_actualizadas = ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        self.assertEqual(papeletas_actualizadas, 1)

        self.assertEqual(mock_papeleta.estado_papeleta, "EMITIDA")
        self.assertEqual(mock_papeleta.numero_papeleta, 101)
        self.assertEqual(mock_papeleta.tramo, mock_tramo)
        self.assertIsNotNone(mock_papeleta.codigo_verificacion)

        mock_papeleta_mgr.bulk_update.assert_called_once()
        args, kwargs = mock_papeleta_mgr.bulk_update.call_args
        self.assertIn(mock_papeleta, args[0])
        self.assertIn('tramo', kwargs['fields'])

        mock_telegram.assert_called_once_with(
            chat_id="123456789",
            nombre_hermano=mock_papeleta.hermano.nombre,
            nombre_acto=mock_acto.nombre,
            estado="ASIGNADA",
            nombre_puesto="Cirio Cristo"
        )

        self.assertIsNotNone(mock_acto.fecha_ejecucion_cirios)
        mock_acto.save.assert_called_once_with(update_fields=['fecha_ejecucion_cirios'])



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.TelegramWebhookService.notificar_papeleta_asignada")
    def test_no_envia_telegram_si_hermano_no_tiene_chat_id(
        self, mock_telegram, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: No hay telegram_chat_id -> no envía notificaciones
        
        Given: Un hermano asignado correctamente pero con telegram_chat_id = None.
        When: Se ejecuta la asignación.
        Then: La notificación de Telegram no debe ser llamada.
        """
        mock_atomic.return_value.__enter__.return_value = None

        mock_acto = MagicMock(modalidad="TRADICIONAL", fecha_ejecucion_cirios=None)
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        mock_papeleta = MagicMock()
        mock_papeleta.hermano.telegram_chat_id = None
        mock_papeleta.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1)

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 1}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [[mock_papeleta], []]
        
        mock_tramo = MagicMock(numero_maximo_cirios=10)
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[mock_tramo], []]

        ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        mock_telegram.assert_not_called()



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.TelegramWebhookService.notificar_papeleta_asignada")
    def test_envia_notificaciones_multiples_si_hay_chat_id(
        self, mock_telegram, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Hay telegram_chat_id -> envía notificaciones (N veces)
        
        Given: Dos papeletas de hermanos con telegram_chat_id válido.
        When: Se ejecuta la asignación.
        Then: El servicio de Telegram debe llamarse exactamente 2 veces.
        """
        mock_atomic.return_value.__enter__.return_value = None
        
        mock_acto = MagicMock(modalidad="TRADICIONAL", fecha_ejecucion_cirios=None)
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        mock_p1 = MagicMock(id=1, vinculado_a_id=None)
        mock_p1.hermano.telegram_chat_id = "CHAT_1"
        mock_p1.hermano.fecha_ingreso_corporacion = datetime.date(2010, 1, 1)
        
        mock_p2 = MagicMock(id=2, vinculado_a_id=None)
        mock_p2.hermano.telegram_chat_id = "CHAT_2"
        mock_p2.hermano.fecha_ingreso_corporacion = datetime.date(2015, 1, 1)

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 10}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [[mock_p1, mock_p2], []]
        
        mock_tramo = MagicMock(numero_maximo_cirios=100)
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[mock_tramo], []]

        ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        self.assertEqual(mock_telegram.call_count, 2)

        calls = [unittest.mock.call(
            chat_id="CHAT_1", 
            nombre_hermano=mock_p1.hermano.nombre,
            nombre_acto=mock_acto.nombre,
            estado="ASIGNADA",
            nombre_puesto=unittest.mock.ANY
        ), unittest.mock.call(
            chat_id="CHAT_2",
            nombre_hermano=mock_p2.hermano.nombre,
            nombre_acto=mock_acto.nombre,
            estado="ASIGNADA",
            nombre_puesto=unittest.mock.ANY
        )]
        mock_telegram.assert_has_calls(calls, any_order=True)



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.TelegramWebhookService.notificar_papeleta_asignada")
    def test_contador_empieza_en_uno_si_no_hay_papeletas_previas(
        self, mock_telegram, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Maneja correctamente max_papeleta_existente None

        Given: El aggregate de Max('numero_papeleta') devuelve None (primer reparto).
        When: Se ejecuta la asignación.
        Then: La primera papeleta asignada debe tener el numero_papeleta = 1.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="TRADICIONAL", fecha_ejecucion_cirios=None)
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        mock_papeleta = MagicMock(id=1, vinculado_a_id=None)
        mock_papeleta.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1)

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': None}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [[mock_papeleta], []]

        mock_tramo = MagicMock(numero_maximo_cirios=10)
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[mock_tramo], []]

        ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        self.assertEqual(mock_papeleta.numero_papeleta, 1)



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_bulk_update_se_ejecuta_si_hay_papeletas_para_actualizar(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Bulk update se ejecuta cuando hay asignaciones

        Given: Existe al menos una papeleta que ha sido procesada con éxito.
        When: Termina el algoritmo de reparto.
        Then: Se debe llamar exactamente una vez a PapeletaSitio.objects.bulk_update.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="TRADICIONAL", fecha_ejecucion_cirios=None)
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        mock_papeleta = MagicMock(id=1, vinculado_a_id=None)
        mock_papeleta.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1)

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 10}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [[mock_papeleta], []]

        mock_tramo = MagicMock(numero_maximo_cirios=10)
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[mock_tramo], []]

        ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        mock_papeleta_mgr.bulk_update.assert_called_once()

        args, kwargs = mock_papeleta_mgr.bulk_update.call_args
        self.assertEqual(len(args[0]), 1)
        self.assertIn('orden_en_tramo', kwargs['fields'])
        self.assertIn('lado', kwargs['fields'])



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.TelegramWebhookService.notificar_papeleta_asignada")
    def test_no_lanza_excepcion_si_falla_notificacion_telegram(
        self, mock_telegram, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: No rompe si falla Telegram (try/except interno)

        Given: El servicio de Telegram lanza una excepción genérica.
        When: Se ejecuta la asignación.
        Then: 
            - El método NO debe propagar la excepción (no explota).
            - El proceso de guardado y sellado del acto continúa normalmente.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="TRADICIONAL", fecha_ejecucion_cirios=None)
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        mock_papeleta = MagicMock()
        mock_papeleta.hermano.telegram_chat_id = "123"
        mock_papeleta.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1)

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 1}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [[mock_papeleta], []]
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[MagicMock(numero_maximo_cirios=10)], []]

        mock_telegram.side_effect = Exception("Telegram API Down")

        try:
            papeletas_actualizadas = ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)
        except Exception as e:
            self.fail(f"El servicio lanzó una excepción cuando debería haberla capturado: {e}")

        self.assertEqual(papeletas_actualizadas, 1)
        mock_papeleta_mgr.bulk_update.assert_called_once()
        self.assertIsNotNone(mock_acto.fecha_ejecucion_cirios)



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_procesa_correctamente_ambos_pasos_cristo_y_virgen(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Procesa múltiples flujos (CRISTO y VIRGEN)

        Given: Hay 1 candidato para Cristo y 1 para Virgen.
        When: Se ejecuta la asignación.
        Then: 
            - Se realizan 2 búsquedas de candidatos y 2 de tramos.
            - Ambas papeletas terminan EMITIDAS.
            - El contador global de papeleta es consecutivo (ej: 101 y 102).
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="TRADICIONAL", fecha_ejecucion_cirios=None)
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        p_cristo = MagicMock(id=1, vinculado_a_id=None)
        p_cristo.hermano.fecha_ingreso_corporacion = datetime.date(2010, 1, 1)

        p_virgen = MagicMock(id=2, vinculado_a_id=None)
        p_virgen.hermano.fecha_ingreso_corporacion = datetime.date(2010, 1, 1)

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 100}

        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [
            [p_cristo],
            [p_virgen]
        ]

        tramo_c = MagicMock(nombre="Tramo 1 Cristo", numero_maximo_cirios=10)
        tramo_v = MagicMock(nombre="Tramo 1 Virgen", numero_maximo_cirios=10)
        
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [
            [tramo_c],
            [tramo_v]
        ]

        total = ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        self.assertEqual(total, 2)

        self.assertEqual(p_cristo.numero_papeleta, 101)
        self.assertEqual(p_virgen.numero_papeleta, 102)

        self.assertEqual(p_cristo.tramo, tramo_c)
        self.assertEqual(p_virgen.tramo, tramo_v)



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    def test_falla_si_el_acto_especificado_no_existe(self, mock_acto_mgr, mock_atomic):
        """
        Test: Acto no existe

        Given: Un ID de acto que no se encuentra en la base de datos.
        When: Se intenta ejecutar la asignación automática.
        Then: Lanza ValidationError con el mensaje "El acto especificado no existe."
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto_mgr.select_for_update.return_value.get.side_effect = Acto.DoesNotExist

        with self.assertRaises(ValidationError) as cm:
            ReportesCiriosService.ejecutar_asignacion_automatica_cirios(999)
        
        self.assertEqual(str(cm.exception.message), "El acto especificado no existe.")



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    def test_falla_si_el_reparto_de_cirios_ya_fue_ejecutado_previamente(self, mock_acto_mgr, mock_atomic):
        """
        Test: Reparto ya ejecutado

        Given: Un acto que ya tiene una fecha grabada en 'fecha_ejecucion_cirios'.
        When: Se intenta ejecutar la asignación de nuevo.
        Then: Lanza ValidationError indicando la fecha y hora de la ejecución previa.
        """
        mock_atomic.return_value.__enter__.return_value = None
        
        fecha_previa = timezone.now() - datetime.timedelta(days=1)
        mock_acto = MagicMock()
        mock_acto.fecha_ejecucion_cirios = fecha_previa
        
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        mensaje_esperado = f"El reparto de cirios ya se ejecutó el {fecha_previa.strftime('%d/%m/%Y %H:%M')}"

        with self.assertRaises(ValidationError) as cm:
            ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        self.assertIn(mensaje_esperado, str(cm.exception))



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    def test_falla_si_es_modalidad_tradicional_y_no_hay_reparto_de_insignias_previo(self, mock_acto_mgr, mock_atomic):
        """
        Test: Modalidad tradicional sin reparto previo

        Given: Un acto con modalidad TRADICIONAL pero sin fecha de ejecución de insignias.
        When: Se intenta ejecutar el algoritmo de cirios.
        Then: Lanza ValidationError exigiendo el reparto previo de insignias.
        """
        mock_atomic.return_value.__enter__.return_value = None
        
        mock_acto = MagicMock()
        mock_acto.modalidad = "TRADICIONAL"
        mock_acto.fecha_ejecucion_reparto = None
        mock_acto.fecha_ejecucion_cirios = None
        
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        with self.assertRaises(ValidationError) as cm:
            ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)
            
        self.assertIn("sin haber ejecutado previamente el de insignias", str(cm.exception))



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    def test_falla_si_el_acto_no_tiene_configurada_fecha_de_inicio_de_solicitud(self, mock_acto_mgr, mock_atomic):
        """
        Test: Acto sin fechas de solicitud de cirios

        Given: Un acto donde inicio_solicitud_cirios es None.
        When: Se intenta ejecutar el algoritmo.
        Then: Lanza ValidationError sobre la configuración de fechas.
        """
        mock_atomic.return_value.__enter__.return_value = None
        
        mock_acto = MagicMock()
        mock_acto.modalidad = "LIBRE"
        mock_acto.inicio_solicitud_cirios = None
        mock_acto.fecha_ejecucion_cirios = None
        
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        with self.assertRaises(ValidationError) as cm:
            ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)
            
        self.assertIn("no tiene configuradas las fechas de solicitud", str(cm.exception))



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_falla_si_hay_candidatos_pero_no_existen_tramos_configurados(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: No hay tramos pero sí candidatos

        Given: Hay 1 hermano solicitando sitio pero el filtro de Tramos devuelve una lista vacía.
        When: Se ejecuta la asignación.
        Then: Lanza ValidationError indicando que no existen tramos para ese paso.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        mock_papeleta = MagicMock(id=1, vinculado_a_id=None)
        mock_papeleta.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1)
        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [[mock_papeleta], []]

        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[], []]

        with self.assertRaises(ValidationError) as cm:
            ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)
            
        self.assertIn("no existen tramos configurados para ese paso", str(cm.exception))



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_falla_si_un_grupo_vinculado_excede_la_capacidad_maxima_de_un_tramo(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Grupo mayor que capacidad de tramo

        Given:
            - Un grupo de 2 hermanos vinculados entre sí.
            - Un tramo configurado con capacidad máxima de 1 persona.
        When:
            - Se intenta asignar el grupo al tramo.
        Then:
            - Lanza ValidationError indicando que el grupo supera la capacidad del tramo.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        fecha_base = datetime.date(2020, 1, 1)

        p1 = MagicMock(id=10, vinculado_a_id=2)
        p1.hermano.id = 20
        p1.hermano.fecha_ingreso_corporacion = fecha_base
        p1.hermano.numero_registro = 100

        p2 = MagicMock(id=11, vinculado_a_id=None)
        p2.hermano.id = 2
        p2.hermano.fecha_ingreso_corporacion = fecha_base
        p2.hermano.numero_registro = 101

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}

        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [[p1, p2], []]

        mock_tramo = MagicMock(numero_maximo_cirios=1, nombre="Tramo Estrecho")
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[mock_tramo], []]

        with self.assertRaises(ValidationError) as cm:
            ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)
            
        self.assertIn("supera la capacidad total del tramo", str(cm.exception))


    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_falla_si_el_aforo_total_de_los_tramos_es_insuficiente(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: No caben todos los grupos (aforo insuficiente)

        Given: 
            - 3 candidatos solicitando sitio.
            - Solo existe 1 tramo con capacidad para 2 personas.
        When: 
            - Se ejecuta la asignación automática.
        Then: 
            - Lanza ValidationError con el mensaje "ERROR DE AFORO".
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        papeletas = []
        for i in range(3):
            p = MagicMock(id=i, vinculado_a_id=None)
            p.hermano.id = i + 100
            p.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1)
            p.hermano.numero_registro = 1000 + i 
            papeletas.append(p)

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}

        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [papeletas, []]

        mock_tramo = MagicMock(numero_maximo_cirios=2, nombre="Tramo 1")
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[mock_tramo], []]

        with self.assertRaises(ValidationError) as cm:
            ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)
            
        self.assertIn("ERROR DE AFORO EN CRISTO", str(cm.exception))
        self.assertIn("Se han quedado 1 hermanos sin asignar", str(cm.exception))



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_falla_con_detalle_si_no_se_encuentran_candidatos_validos(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: No hay candidatos válidos

        Given: El queryset de candidatos está vacío.
        When: El algoritmo termina el bucle de flujos sin haber asignado nada.
        Then: Lanza ValidationError con el conteo detallado de por qué se ignoraron.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        base_qs = mock_papeleta_mgr.filter.return_value

        base_qs.aggregate.return_value = {'numero_papeleta__max': 0}

        base_qs.select_related.return_value = []

        base_qs.exclude.return_value.count.side_effect = [5, 3, 8]

        mock_tramo_mgr.filter.return_value.order_by.return_value = []

        with self.assertRaises(ValidationError) as cm:
            ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)
            
        error_msg = str(cm.exception)
        self.assertIn("No se ha encontrado ninguna papeleta válida", error_msg)
        self.assertIn("Ignoradas por ser Insignias: 3", error_msg)
        self.assertIn("Ignoradas por NO tener Puesto asignado: 5", error_msg)
        self.assertIn("Total activas: 8", error_msg)



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_no_llama_a_bulk_update_si_no_se_realizaron_asignaciones(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: bulk_update no se ejecuta si no hay asignaciones

        Given: Un acto donde no hay candidatos válidos.
        When: Se ejecuta el proceso.
        Then:
            - Se lanza la ValidationError de diagnóstico.
            - PapeletaSitio.objects.bulk_update NUNCA es llamado.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}
        mock_papeleta_mgr.filter.return_value.select_related.return_value = []

        mock_papeleta_mgr.filter.return_value.exclude.return_value.count.return_value = 0

        with self.assertRaises(ValidationError):
            ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        mock_papeleta_mgr.bulk_update.assert_not_called()



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_error_en_bulk_update_se_propaga_correctamente(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Error en bulk_update se propaga

        Given: Un escenario de asignación exitosa pero donde la base de datos falla al guardar.
        When: Se intenta ejecutar bulk_update.
        Then: La excepción lanzada por el ORM se propaga hacia arriba.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        p = MagicMock(id=1, vinculado_a_id=None)
        p.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1)
        p.hermano.numero_registro = 100
        
        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [[p], []]
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[MagicMock(numero_maximo_cirios=10)], []]

        mock_papeleta_mgr.bulk_update.side_effect = Exception("Database Connection Lost")

        with self.assertRaises(Exception) as cm:
            ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        self.assertEqual(str(cm.exception), "Database Connection Lost")



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    def test_error_inesperado_en_select_for_update_se_propaga(self, mock_acto_mgr, mock_atomic):
        """
        Test: Error en select_for_update get (carrera)

        Given: La base de datos lanza una excepción inesperada (ej: DatabaseError) 
            al intentar bloquear la fila del Acto.
        When: Se inicia el proceso de asignación.
        Then: 
            - La excepción se propaga hacia arriba.
            - No se ejecuta ninguna línea posterior del servicio.
        """

        mock_atomic.return_value.__enter__.return_value = None

        mock_acto_mgr.select_for_update.return_value.get.side_effect = Exception("Lock wait timeout exceeded")

        with self.assertRaises(Exception) as cm:
            ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        self.assertEqual(str(cm.exception), "Lock wait timeout exceeded")



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_generacion_de_grupos_consolida_correctamente_hermanos_vinculados(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Generación de grupos respeta vinculación

        Given: 
            - Hermano A vinculado a Hermano B.
            - Hermano C también vinculado a Hermano B (solicitud inversa).
        When: 
            - Se procesa la asignación.
        Then: 
            - Los tres hermanos deben terminar en el mismo grupo.
            - No debe haber duplicados en el procesamiento (ids_procesados funciona).
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        fecha = datetime.date(2020, 1, 1)

        p_a = MagicMock(id=101, vinculado_a_id=2); p_a.hermano.id = 1
        p_b = MagicMock(id=102, vinculado_a_id=None); p_b.hermano.id = 2
        p_c = MagicMock(id=103, vinculado_a_id=2); p_c.hermano.id = 3

        for p in [p_a, p_b, p_c]:
            p.hermano.fecha_ingreso_corporacion = fecha
            p.hermano.numero_registro = 100 + p.hermano.id

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [[p_a, p_b, p_c], []]

        mock_tramo = MagicMock(numero_maximo_cirios=10, nombre="Tramo 1")
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[mock_tramo], []]

        ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        self.assertEqual(p_a.tramo, mock_tramo)
        self.assertEqual(p_b.tramo, mock_tramo)
        self.assertEqual(p_c.tramo, mock_tramo)

        ordenes = {p_a.orden_en_tramo, p_b.orden_en_tramo, p_c.orden_en_tramo}
        self.assertTrue(all(o in [1, 2] for o in ordenes))



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_ordenacion_de_grupos_respeta_fecha_y_numero_registro(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Ordenación por fecha_ingreso y numero_registro

        Given:
            - Grupo A: Fecha 2010, Registro 50 (El más antiguo).
            - Grupo B: Fecha 2010, Registro 100 (Misma fecha, registro más alto = más moderno).
            - Grupo C: Fecha 2015, Registro 10 (El más moderno por fecha).
        When:
            - Se asignan los tramos ordenando de forma ascendente.
        Then:
            - El orden de asignación es: A (más antiguo), luego B, luego C (más moderno).
            - Los números de papeleta reflejan este orden (1, 2, 3 respectivamente).
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        p_a = MagicMock(id=1, vinculado_a_id=None); p_a.hermano.id = 1
        p_a.hermano.fecha_ingreso_corporacion = datetime.date(2010, 1, 1)
        p_a.hermano.numero_registro = 50

        p_b = MagicMock(id=2, vinculado_a_id=None); p_b.hermano.id = 2
        p_b.hermano.fecha_ingreso_corporacion = datetime.date(2010, 1, 1)
        p_b.hermano.numero_registro = 100

        p_c = MagicMock(id=3, vinculado_a_id=None); p_c.hermano.id = 3
        p_c.hermano.fecha_ingreso_corporacion = datetime.date(2015, 1, 1)
        p_c.hermano.numero_registro = 10

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [[p_a, p_b, p_c], []]

        mock_tramo = MagicMock(numero_maximo_cirios=100)
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[mock_tramo], []]

        ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        self.assertEqual(p_a.numero_papeleta, 1)
        self.assertEqual(p_b.numero_papeleta, 2)
        self.assertEqual(p_c.numero_papeleta, 3)



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_alternancia_de_lado_asigna_izquierda_y_derecha_correctamente(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Alternancia de lado (izquierda/derecha)

        Given: 2 candidatos para un mismo tramo.
        When: Se ejecuta la asignación.
        Then: 
            - El primero (índice 0/par) recibe el lado DERECHA.
            - El segundo (índice 1/impar) recibe el lado IZQUIERDA.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        p1 = MagicMock(id=1, vinculado_a_id=None); p1.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1); p1.hermano.numero_registro = 1
        p2 = MagicMock(id=2, vinculado_a_id=None); p2.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1); p2.hermano.numero_registro = 2

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [[p1, p2], []]

        mock_tramo = MagicMock(numero_maximo_cirios=10)
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[mock_tramo], []]

        ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        self.assertEqual(p1.lado, "DERECHA")
        self.assertEqual(p2.lado, "IZQUIERDA")



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_orden_en_tramo_se_calcula_por_parejas(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Orden en tramo correcto

        Given: 4 candidatos asignados al mismo tramo.
        When: Se procesa la asignación.
        Then: 
            - Los dos primeros deben tener orden_en_tramo = 1.
            - Los dos siguientes deben tener orden_en_tramo = 2.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        papeletas = []
        for i in range(4):
            p = MagicMock()
            p.id = i
            p.vinculado_a_id = None
            p.hermano.id = i + 100
            p.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1)
            p.hermano.numero_registro = i + 1 
            papeletas.append(p)

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [papeletas, []]

        mock_tramo = MagicMock(numero_maximo_cirios=10)
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[mock_tramo], []]

        ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        self.assertEqual(papeletas[0].orden_en_tramo, 1)
        self.assertEqual(papeletas[1].orden_en_tramo, 1)
        self.assertEqual(papeletas[2].orden_en_tramo, 2)
        self.assertEqual(papeletas[3].orden_en_tramo, 2)



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    @patch("uuid.uuid4") # Parcheamos la librería uuid estándar
    def test_asignacion_de_codigo_de_verificacion_con_formato_correcto(
        self, mock_uuid, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Asignación de código de verificación

        Given: Un candidato válido para asignar.
        When: El algoritmo le genera su papeleta.
        Then: 
            - Se llama a uuid.uuid4().
            - Se asigna un string alfanumérico.
            - La longitud es exactamente de 12 caracteres.
            - Todos los caracteres están en mayúsculas.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        p = MagicMock()
        p.id = 1
        p.vinculado_a_id = None
        p.hermano.id = 100
        p.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1)
        p.hermano.numero_registro = 1
        p.codigo_verificacion = None 

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [[p], []]

        mock_tramo = MagicMock(numero_maximo_cirios=10)
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[mock_tramo], []]

        mock_uuid.return_value = uuid.UUID("12345678-abcd-5678-1234-567812345678")

        ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        mock_uuid.assert_called()

        self.assertIsNotNone(p.codigo_verificacion)

        self.assertIsInstance(p.codigo_verificacion, str)

        self.assertEqual(len(p.codigo_verificacion), 12)

        self.assertTrue(p.codigo_verificacion.isupper())



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_agrega_solicitantes_inversos_al_grupo(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Rama mapa_solicitudes_inversas (Test positivo)

        Escenario:
            - A (p1, hermano 1) tiene papeleta normal.
            - B (p2, hermano 2) está vinculado a A (vinculado_a_id = 1).
        
        Given: El mapa de solicitudes inversas debe detectar que B quiere ir con A.
        When: Se ejecuta la asignación.
        Then: 
            - Se agrupan [p1, p2] en la misma iteración.
            - Ambos comparten la misma "fila" (orden_en_tramo = 1).
            - p2.id se añade a ids_procesados internamente (evitando que se procese 2 veces).
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        p1 = MagicMock()
        p1.id = 101
        p1.vinculado_a_id = None
        p1.hermano.id = 1
        p1.hermano.fecha_ingreso_corporacion = datetime.date(2010, 1, 1)
        p1.hermano.numero_registro = 1

        p2 = MagicMock()
        p2.id = 102
        p2.vinculado_a_id = 1
        p2.hermano.id = 2
        p2.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1)
        p2.hermano.numero_registro = 2

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}

        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [[p1, p2], []]

        mock_tramo = MagicMock(numero_maximo_cirios=10)
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[mock_tramo], []]

        ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        self.assertEqual(p1.tramo, mock_tramo)
        self.assertEqual(p2.tramo, mock_tramo)

        
        args, kwargs = mock_papeleta_mgr.bulk_update.call_args
        papeletas_actualizadas = args[0]

        self.assertEqual(len(papeletas_actualizadas), 2)

        ids_actualizados = [p.id for p in papeletas_actualizadas]
        self.assertCountEqual(ids_actualizados, [101, 102])

        self.assertEqual(p1.orden_en_tramo, 1)
        self.assertEqual(p2.orden_en_tramo, 1)



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_no_agrega_solicitantes_inversos_si_no_existe_vinculacion(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Rama mapa_solicitudes_inversas (Test negativo)

        Given:
            - A (p1, hermano 1) tiene papeleta normal.
            - B (p2, hermano 2) tiene papeleta normal, pero NO apunta a A.
        When:
            - Se ejecuta la asignación.
        Then:
            - El grupo de A solo contiene a p1.
            - No se producen agrupaciones accidentales.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        p1 = MagicMock()
        p1.id = 101
        p1.vinculado_a_id = None
        p1.hermano.id = 1
        p1.hermano.fecha_ingreso_corporacion = datetime.date(2010, 1, 1)
        p1.hermano.numero_registro = 1

        p2 = MagicMock()
        p2.id = 102
        p2.vinculado_a_id = None
        p2.hermano.id = 2
        p2.hermano.fecha_ingreso_corporacion = datetime.date(2011, 1, 1)
        p2.hermano.numero_registro = 2

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [[p1, p2], []]

        mock_tramo = MagicMock(numero_maximo_cirios=10)
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[mock_tramo], []]

        ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        self.assertEqual(p1.orden_en_tramo, 1)
        self.assertEqual(p1.lado, "DERECHA")
        
        self.assertEqual(p2.orden_en_tramo, 1)
        self.assertEqual(p2.lado, "IZQUIERDA")

        self.assertEqual(p1.numero_papeleta, 1)
        self.assertEqual(p2.numero_papeleta, 2)



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_no_añade_solicitante_inverso_si_ya_ha_sido_procesado(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Rama mapa_solicitudes_inversas (Edge case: Ya procesado)

        Escenario:
            - p2 (hermano 2) ya fue procesado individualmente (está en ids_procesados).
            - p2 apunta a p1 (hermano 1).
            - Al procesar a p1, el algoritmo ve que p2 le apunta.
        
        Given: p2.id ya existe en el set ids_procesados.
        When: Se procesa p1.
        Then: 
            - El grupo de p1 NO debe incluir a p2.
            - El tamaño del grupo debe ser 1.
            - No se debe duplicar p2 en el bulk_update.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        p2 = MagicMock()
        p2.id = 102
        p2.vinculado_a_id = 1 
        p2.hermano.id = 2
        p2.hermano.fecha_ingreso_corporacion = datetime.date(2000, 1, 1)
        p2.hermano.numero_registro = 1

        p1 = MagicMock()
        p1.id = 101
        p1.vinculado_a_id = None
        p1.hermano.id = 1
        p1.hermano.fecha_ingreso_corporacion = datetime.date(2010, 1, 1)
        p1.hermano.numero_registro = 2

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}

        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [[p2, p1], []]

        mock_tramo = MagicMock(numero_maximo_cirios=10)
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[mock_tramo], []]

        ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        args, _ = mock_papeleta_mgr.bulk_update.call_args
        papeletas_actualizadas = args[0]

        self.assertEqual(len(papeletas_actualizadas), 2)
        
        ids_vistos = [p.id for p in papeletas_actualizadas]
        self.assertEqual(ids_vistos.count(101), 1)
        self.assertEqual(ids_vistos.count(102), 1)

        self.assertEqual(p2.numero_papeleta, 1)
        self.assertEqual(p1.numero_papeleta, 2)



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_rompe_el_bucle_cuando_index_alcanza_total_grupos(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Rama if index_grupo_actual >= total_grupos (Test Positivo)

        Escenario:
            - Solo hay 1 candidato (1 grupo en total).
            - Hay 2 tramos configurados con gran capacidad.
        
        Given: index_grupo_actual alcanza el valor de total_grupos (1) tras el primer paso.
        When: El bucle de Tramos intenta seguir rellenando huecos.
        Then: 
            - El 'break' se activa evitando un IndexError.
            - El proceso termina limpiamente y solo guarda 1 papeleta.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        p1 = MagicMock()
        p1.id = 1
        p1.vinculado_a_id = None
        p1.hermano.id = 100
        p1.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1)
        p1.hermano.numero_registro = 1

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [[p1], []]

        tramo1 = MagicMock(numero_maximo_cirios=10, nombre="Tramo 1")
        tramo2 = MagicMock(numero_maximo_cirios=10, nombre="Tramo 2")

        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[tramo1, tramo2], []]

        try:
            ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)
        except IndexError:
            self.fail("El test falló: El bucle no se rompió y lanzó un IndexError al buscar más grupos.")

        self.assertEqual(p1.tramo, tramo1)

        args, _ = mock_papeleta_mgr.bulk_update.call_args
        papeletas_actualizadas = args[0]
        
        self.assertEqual(len(papeletas_actualizadas), 1)
        self.assertEqual(papeletas_actualizadas[0].id, 1)



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_continua_iterando_tramos_mientras_queden_grupos_pendientes(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Rama if index_grupo_actual >= total_grupos (Test Negativo)

        Escenario:
            - Hay 2 grupos (hermanos individuales).
            - El Tramo 1 solo tiene capacidad para 1 persona.
            - El Tramo 2 tiene capacidad para el resto.
        
        Given: Tras llenar el Tramo 1, index_grupo_actual es 1, y total_grupos es 2.
        When: Se evalúa la condición de rotura.
        Then: 
            - El 'break' NO debe ejecutarse (1 < 2).
            - El algoritmo pasa al Tramo 2 y asigna al segundo hermano.
            - Se guardan un total de 2 papeletas.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        p1 = MagicMock(); p1.id = 101; p1.vinculado_a_id = None
        p1.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1); p1.hermano.numero_registro = 1

        p2 = MagicMock(); p2.id = 102; p2.vinculado_a_id = None
        p2.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1); p2.hermano.numero_registro = 2

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [[p1, p2], []]

        tramo1 = MagicMock(numero_maximo_cirios=1, nombre="Tramo 1")
        tramo2 = MagicMock(numero_maximo_cirios=10, nombre="Tramo 2")
        
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[tramo1, tramo2], []]

        ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        self.assertEqual(p1.tramo, tramo1)

        self.assertEqual(p2.tramo, tramo2)

        args, _ = mock_papeleta_mgr.bulk_update.call_args
        self.assertEqual(len(args[0]), 2)



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_cupo_ideal_asigna_todos_los_restantes_en_el_ultimo_tramo(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Rama else: cupo_ideal = personas_restantes_count

        Escenario:
            - Solo hay 1 tramo configurado (total_tramos = 1).
            - En la primera iteración (i = 0), tramos_restantes (1 - 0 - 1) será 0.
        
        Given: tramos_restantes == 0.
        When: Se calcula el cupo_ideal para el tramo.
        Then: 
            - Se ejecuta el bloque ELSE.
            - cupo_ideal es exactamente igual al número de personas que quedan por procesar.
            - Todos los hermanos son asignados a ese último tramo.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        papeletas = []
        for i in range(3):
            p = MagicMock()
            p.id = i + 100
            p.vinculado_a_id = None
            p.hermano.id = i + 1
            p.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1)
            p.hermano.numero_registro = i + 1
            papeletas.append(p)

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [papeletas, []]

        tramo_unico = MagicMock(numero_maximo_cirios=10, nombre="Último Tramo")
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[tramo_unico], []]

        try:
            ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)
        except ZeroDivisionError:
            self.fail("El test falló: Se intentó dividir por cero en lugar de entrar en el bloque ELSE.")

        self.assertEqual(papeletas[0].tramo, tramo_unico)
        self.assertEqual(papeletas[1].tramo, tramo_unico)
        self.assertEqual(papeletas[2].tramo, tramo_unico)

        args, _ = mock_papeleta_mgr.bulk_update.call_args
        self.assertEqual(len(args[0]), 3)



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_cupo_ideal_calcula_proporcionalmente_si_quedan_tramos(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Rama if tramos_restantes > 0 (Test Negativo del else)

        Escenario:
            - Hay 4 personas restantes por procesar.
            - Hay 2 tramos en total.
            - En la primera iteración (i=0):
                tramos_restantes = 2 - 0 - 1 = 1 (Es > 0).
        
        Given: tramos_restantes > 0.
        When: Se calcula el cupo_ideal.
        Then: 
            - Se usa math.ceil(4 / 1) = 4.
            - IMPORTANTE: Si el algoritmo tiene un aforo menor al cupo ideal, 
            el tramo se llenará hasta su máximo y el resto pasará al siguiente.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        papeletas = []
        for i in range(4):
            p = MagicMock()
            p.id = i + 100
            p.vinculado_a_id = None
            p.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1)
            p.hermano.numero_registro = i + 1
            papeletas.append(p)

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [papeletas, []]

        tramo1 = MagicMock(numero_maximo_cirios=2, nombre="Tramo 1")
        tramo2 = MagicMock(numero_maximo_cirios=10, nombre="Tramo 2")
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[tramo1, tramo2], []]

        ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        self.assertEqual(papeletas[0].tramo, tramo1)
        self.assertEqual(papeletas[1].tramo, tramo1)

        self.assertEqual(papeletas[2].tramo, tramo2)
        self.assertEqual(papeletas[3].tramo, tramo2)

        args, _ = mock_papeleta_mgr.bulk_update.call_args
        self.assertEqual(len(args[0]), 4)



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_corta_asignacion_cuando_se_alcanza_cupo_ideal(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Rama if ocupacion_actual_tramo >= cupo_ideal (Test Positivo)

        Escenario:
            - Tenemos 4 hermanos (4 grupos).
            - Tenemos 2 tramos con mucha capacidad (aforo 10).
            - El algoritmo calcula un cupo_ideal de 2 para el primer tramo.
        
        Given: El Tramo 1 ya tiene 2 personas asignadas (ocupacion == cupo_ideal).
        When: Se evalúa la condición para el tercer hermano.
        Then: 
            - El 'break' del bucle 'while' se activa.
            - El tercer y cuarto hermano NO entran en el Tramo 1.
            - El algoritmo salta al Tramo 2 para continuar.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        papeletas = []
        for i in range(4):
            p = MagicMock()
            p.id = i + 100
            p.vinculado_a_id = None
            p.hermano.id = i + 1
            p.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1)
            p.hermano.numero_registro = i + 1
            papeletas.append(p)

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [papeletas, []]

        t1 = MagicMock(numero_maximo_cirios=10, nombre="Tramo 1")
        t2 = MagicMock(numero_maximo_cirios=10, nombre="Tramo 2")
        t3 = MagicMock(numero_maximo_cirios=10, nombre="Tramo 3")
        
        mock_tramo_mgr.filter.return_value.order_by.return_value = [t1, t2, t3]

        ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        self.assertEqual(papeletas[0].tramo, t1)
        self.assertEqual(papeletas[1].tramo, t1)

        self.assertEqual(papeletas[2].tramo, t2)
        self.assertEqual(papeletas[3].tramo, t2)

        args, _ = mock_papeleta_mgr.bulk_update.call_args
        self.assertEqual(len(args[0]), 4)



    @patch("django.db.transaction.atomic")
    @patch("api.models.Acto.objects")
    @patch("api.models.PapeletaSitio.objects")
    @patch("api.models.Tramo.objects")
    def test_sigue_asignando_al_tramo_mientras_la_ocupacion_sea_menor_al_cupo(
        self, mock_tramo_mgr, mock_papeleta_mgr, mock_acto_mgr, mock_atomic
    ):
        """
        Test: Rama if ocupacion_actual_tramo >= cupo_ideal (Test Negativo)

        Escenario:
            - Tenemos 2 candidatos.
            - El cupo_ideal calculado es 5.
        
        Given: ocupacion_actual_tramo (0, luego 1) es menor que cupo_ideal (5).
        When: Se evalúa la condición de corte.
        Then: 
            - El 'break' NO se ejecuta.
            - Ambos hermanos entran en el mismo tramo.
            - El algoritmo no salta de tramo innecesariamente.
        """
        mock_atomic.return_value.__enter__.return_value = None
        mock_acto = MagicMock(modalidad="LIBRE", fecha_ejecucion_cirios=None, inicio_solicitud_cirios=timezone.now())
        mock_acto_mgr.select_for_update.return_value.get.return_value = mock_acto

        papeletas = []
        for i in range(2):
            p = MagicMock()
            p.id = i + 100
            p.vinculado_a_id = None
            p.hermano.fecha_ingreso_corporacion = datetime.date(2020, 1, 1)
            p.hermano.numero_registro = i + 1
            papeletas.append(p)

        mock_papeleta_mgr.filter.return_value.aggregate.return_value = {'numero_papeleta__max': 0}
        mock_papeleta_mgr.filter.return_value.select_related.side_effect = [papeletas, []]

        tramo1 = MagicMock(numero_maximo_cirios=10, nombre="Tramo 1")
        mock_tramo_mgr.filter.return_value.order_by.side_effect = [[tramo1], []]

        ReportesCiriosService.ejecutar_asignacion_automatica_cirios(1)

        self.assertEqual(papeletas[0].tramo, tramo1)
        self.assertEqual(papeletas[1].tramo, tramo1)
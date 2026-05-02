from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
from rest_framework.response import Response
from unittest.mock import patch

from api.vistas.papeleta_sitio.papeleta_telegram_webhook_view import TelegramWebhookView

class TestTelegramWebhookViewPermisos(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = TelegramWebhookView.as_view()
        self.path = "/api/telegram/webhook/"



    @patch('api.vistas.papeleta_sitio.papeleta_telegram_webhook_view.TelegramWebhookService.procesar_actualizacion')
    def test_acceso_permitido_sin_autenticacion(self, mock_procesar_actualizacion):
        """
        Test: Acceso permitido sin autenticación (AllowAny)
        
        Given: Una petición HTTP POST entrante sin credenciales de usuario ni token de sesión.
        When: La petición intenta acceder al endpoint del webhook.
        Then: La capa de permisos (AllowAny) permite el paso y la vista procesa la petición devolviendo un 200 OK.
        """
        payload = {"update_id": 123456789, "message": {"text": "/start"}}
        request = self.factory.post(self.path, data=payload, format='json')

        
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_procesar_actualizacion.assert_called_once()



    @patch('api.vistas.papeleta_sitio.papeleta_telegram_webhook_view.TelegramWebhookService.procesar_actualizacion')
    def test_llama_correctamente_al_servicio_con_request_data(self, mock_service):
        """
        Test: Llama correctamente al servicio con request.data
        
        Given: Un payload JSON enviado por Telegram.
        When: Se recibe la petición POST.
        Then: Se debe invocar al método 'procesar_actualizacion' del servicio exactamente una vez.
        """
        payload = {"test": "data"}
        request = self.factory.post(self.path, data=payload, format='json')
        
        self.view(request)
        
        mock_service.assert_called_once()



    @patch('api.vistas.papeleta_sitio.papeleta_telegram_webhook_view.TelegramWebhookService.procesar_actualizacion')
    def test_devuelve_respuesta_200_siempre(self, mock_service):
        """
        Test: Devuelve respuesta 200 siempre
        
        Given: Una petición válida que llega al endpoint.
        When: El servicio procesa la actualización (sin importar el resultado interno).
        Then: La vista debe responder con status 200 OK y el cuerpo {"status": "ok"}.
        """
        request = self.factory.post(self.path, data={}, format='json')
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok"})



    @patch('api.vistas.papeleta_sitio.papeleta_telegram_webhook_view.TelegramWebhookService.procesar_actualizacion')
    def test_se_pasa_exactamente_el_payload_del_request_al_servicio(self, mock_service):
        """
        Test: Se pasa exactamente el payload del request al servicio
        
        Given: Un payload complejo con mensajes anidados de Telegram.
        When: Se ejecuta la vista.
        Then: El servicio recibe exactamente el mismo diccionario (request.data) sin modificaciones.
        """
        payload_complejo = {
            "update_id": 999,
            "message": {
                "from": {"id": 123},
                "text": "Hola"
            }
        }
        request = self.factory.post(self.path, data=payload_complejo, format='json')
        
        self.view(request)
        
        mock_service.assert_called_once_with(payload_complejo)



    @patch('api.vistas.papeleta_sitio.papeleta_telegram_webhook_view.TelegramWebhookService.procesar_actualizacion')
    def test_no_transforma_ni_valida_el_payload(self, mock_service):
        """
        Test: No transforma ni valida el payload
        
        Given: Un payload con datos inesperados o tipos diferentes.
        When: La vista los recibe.
        Then: La vista no aplica validaciones de serializador (según diseño) y los entrega al servicio "tal cual".
        """
        payload_sucio = {"dato_random": 12345, "extra": None}
        request = self.factory.post(self.path, data=payload_sucio, format='json')
        
        self.view(request)

        args, _ = mock_service.call_args
        self.assertEqual(args[0], payload_sucio)



    @patch('api.vistas.papeleta_sitio.papeleta_telegram_webhook_view.TelegramWebhookService.procesar_actualizacion')
    def test_error_en_el_servicio_propaga_excepcion(self, mock_service):
        """
        Test: Error en el servicio → propaga excepción
        
        Given: El servicio de Telegram lanza una excepción durante el procesamiento.
        When: La vista invoca al servicio y no tiene un bloque try/except interno.
        Then: La excepción se propaga, lo cual en un entorno Django resultaría en un status 500.
        """
        request = self.factory.post(self.path, data={}, format='json')
        mock_service.side_effect = Exception("Error interno en el servicio de Telegram")
        
        with self.assertRaises(Exception):
            self.view(request)



    def test_request_sin_data_no_falla_en_la_view(self):
        """
        Test: Request sin data
        
        Given: Una petición POST que llega sin cuerpo (body) o con un JSON vacío.
        When: La vista accede a request.data.
        Then: DRF devuelve un diccionario vacío por defecto, se llama al servicio y se retorna 200 OK.
        """
        request = self.factory.post(self.path, data={}, format='json')
        
        with patch('api.vistas.papeleta_sitio.papeleta_telegram_webhook_view.TelegramWebhookService.procesar_actualizacion') as mock_service:
            response = self.view(request)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_service.assert_called_once_with({})



    @patch('api.vistas.papeleta_sitio.papeleta_telegram_webhook_view.TelegramWebhookService.procesar_actualizacion')
    def test_request_con_payload_invalido_se_pasa_al_servicio(self, mock_service):
        """
        Test: Request con payload inválido
        
        Given: Un payload que no sigue el esquema esperado de Telegram (ej: una lista o tipos erróneos).
        When: La vista recibe la petición.
        Then: La vista, al no validar el esquema, delega la responsabilidad al servicio y devuelve 200 OK.
        """
        payload_invalido = ["esto", "no", "es", "un", "diccionario"]
        request = self.factory.post(self.path, data=payload_invalido, format='json')
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_service.assert_called_once_with(payload_invalido)



    @patch('api.vistas.papeleta_sitio.papeleta_telegram_webhook_view.TelegramWebhookService.procesar_actualizacion')
    def test_error_inesperado_en_la_view_detiene_ejecucion(self, mock_service):
        """
        Test: Error inesperado en la view
        
        Given: Un fallo crítico inesperado antes de retornar la respuesta.
        When: Ocurre una excepción.
        Then: No se llega a ejecutar el 'return Response', confirmando que la vista depende de la estabilidad del servicio.
        """
        request = self.factory.post(self.path, data={}, format='json')
        mock_service.side_effect = RuntimeError("Fallo crítico de ejecución")
        
        try:
            self.view(request)
        except RuntimeError:
            pass

        mock_service.assert_called_once()



    @patch('api.vistas.papeleta_sitio.papeleta_telegram_webhook_view.TelegramWebhookService.procesar_actualizacion')
    def test_payload_grande_o_malformado(self, mock_service):
        """
        Test: Payload grande o malformado
        
        Given: Un payload con una estructura inusual o muy pesada.
        When: La vista lo recibe en el request.data.
        Then: La vista lo transfiere íntegramente al servicio sin intentar validarlo o recortarlo.
        """
        payload_extenso = {"key": "value" * 1000, "malformado": [1, 2, 3], "anidado": {"a": 1, "b": None}}
        request = self.factory.post(self.path, data=payload_extenso, format='json')
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_service.assert_called_once_with(payload_extenso)



    @patch('api.vistas.papeleta_sitio.papeleta_telegram_webhook_view.TelegramWebhookService.procesar_actualizacion')
    def test_verificar_que_siempre_devuelve_status_ok(self, mock_service):
        """
        Test: Verificar que siempre devuelve {"status": "ok"}
        
        Given: Una petición procesada por el servicio.
        When: La vista termina su ejecución.
        Then: El cuerpo de la respuesta debe ser exactamente el diccionario {"status": "ok"}.
        """
        request = self.factory.post(self.path, data={}, format='json')
        
        response = self.view(request)
        
        self.assertEqual(response.data, {"status": "ok"})



    @patch('api.vistas.papeleta_sitio.papeleta_telegram_webhook_view.TelegramWebhookService.procesar_actualizacion')
    def test_verificar_que_el_servicio_se_llama_exactamente_una_vez(self, mock_service):
        """
        Test: Verificar que el servicio se llama exactamente una vez
        
        Given: Una petición POST estándar.
        When: Se ejecuta la vista.
        Then: El método procesar_actualizacion se invoca una única vez para evitar duplicidad de mensajes en Telegram.
        """
        request = self.factory.post(self.path, data={}, format='json')
        
        self.view(request)
        
        self.assertEqual(mock_service.call_count, 1)



    @patch('api.vistas.papeleta_sitio.papeleta_telegram_webhook_view.TelegramWebhookService.procesar_actualizacion')
    def test_verificar_que_no_hay_logica_adicional_en_la_view(self, mock_service):
        """
        Test: Verificar que no hay lógica adicional en la view
        
        Given: Una petición al webhook.
        When: Se analiza la ejecución.
        Then: Se confirma que tras la llamada al servicio, la vista solo devuelve la respuesta sin realizar cálculos o transformaciones extra.
        """
        request = self.factory.post(self.path, data={"key": "val"}, format='json')
        
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok"})



    @patch('api.vistas.papeleta_sitio.papeleta_telegram_webhook_view.Response')
    @patch('api.vistas.papeleta_sitio.papeleta_telegram_webhook_view.TelegramWebhookService.procesar_actualizacion')
    def test_verificar_status_200_siempre(self, mock_service, mock_response_class):
        """
        Test: Verificar status 200 siempre
        
        Given: Una ejecución exitosa del flujo.
        When: Se instancia la respuesta.
        Then: El argumento status pasado a la clase Response debe ser 200 OK.
        """
        request = self.factory.post(self.path, data={}, format='json')

        mock_response_class.return_value = Response({"status": "ok"})
        
        self.view(request)

        _, kwargs = mock_response_class.call_args
        self.assertEqual(kwargs.get('status'), status.HTTP_200_OK)
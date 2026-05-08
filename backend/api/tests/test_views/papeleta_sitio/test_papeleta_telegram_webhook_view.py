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
    def test_post_webhook_procesa_actualizacion_correctamente(self, mock_procesar_actualizacion):
        """
        Test: Webhook procesa actualización correctamente
        
        Given: Una petición POST (sin necesidad de autenticación por AllowAny) con el payload de Telegram.
        When: Se recibe la petición en el endpoint público.
        Then: Se permite el acceso, se delega el payload intacto al servicio de Telegram y se retorna 200 OK.
        """
        payload = {"update_id": 123456789, "message": {"text": "/start"}}
        request = self.factory.post(self.path, data=payload, format='json')

        response = self.view(request)

        mock_procesar_actualizacion.assert_called_once_with(payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok"})
import unittest
from unittest.mock import MagicMock, patch
import json

from api.servicios.comunicado.podcast_service import generar_guion_conversacional


class TestGenerarGuionConversacional(unittest.TestCase):

    def setUp(self):
        self.comunicado = MagicMock()
        self.comunicado.titulo = "Título de Prueba"
        self.comunicado.contenido = "Contenido de Prueba"
        self.api_key = "fake_api_key_123"

        self.url_principal = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        self.url_respaldo = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={self.api_key}"



    @patch("api.servicios.comunicado.podcast_service._hacer_peticion_con_reintentos")
    def test_flujo_feliz_modelo_principal_ok(self, mock_peticion):
        """
        Test: Flujo feliz (modelo principal OK)
        
        Given: Un comunicado válido y una API key.
        When: El modelo principal de Gemini responde exitosamente en el primer intento.
        Then: La función debe llamar a la URL principal, procesar la estructura JSON 
            anidada de la respuesta y retornar un diccionario de Python válido.
        """
        mock_response = MagicMock()

        json_gemini_esperado = '{"dialogos": [{"locutor": "Carmen", "texto": "Hola Antonio"}]}'
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": json_gemini_esperado}]
                }
            }]
        }
        mock_peticion.return_value = mock_response

        resultado = generar_guion_conversacional(self.comunicado, self.api_key)

        mock_peticion.assert_called_once()

        args, kwargs = mock_peticion.call_args
        url_llamada = args[0]
        payload_enviado = args[1]
        self.assertEqual(url_llamada, self.url_principal)

        prompt_enviado = payload_enviado["contents"][0]["parts"][0]["text"]
        self.assertIn("Título de Prueba", prompt_enviado)
        self.assertIn("Contenido de Prueba", prompt_enviado)

        self.assertIsInstance(resultado, dict)
        self.assertIn("dialogos", resultado)
        self.assertEqual(resultado["dialogos"][0]["locutor"], "Carmen")



    @patch("api.servicios.comunicado.podcast_service._hacer_peticion_con_reintentos")
    @patch("builtins.print")
    def test_modelo_principal_falla_usa_fallback(self, mock_print, mock_peticion):
        """
        Test: Modelo principal falla → usa fallback
        
        Given: El modelo principal (Flash) falla con una excepción.
        When: Se intenta generar el guion.
        Then: Se debe capturar el error, imprimir el aviso y realizar una segunda 
            petición a la URL del modelo de respaldo (Flash-lite).
        """
        mock_resp_respaldo = MagicMock()
        mock_resp_respaldo.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": '{"dialogos": []}'}]}}]
        }
        mock_peticion.side_effect = [Exception("fail main"), mock_resp_respaldo]

        generar_guion_conversacional(self.comunicado, self.api_key)

        self.assertEqual(mock_peticion.call_count, 2)

        args, kwargs = mock_peticion.call_args
        self.assertEqual(args[0], self.url_respaldo)
        self.assertEqual(kwargs.get("max_reintentos"), 2)

        mock_print.assert_called_with("⚠️ El modelo principal falló (fail main). Activando Plan B con gemini-2.5-flash-lite...")



    @patch("api.servicios.comunicado.podcast_service._hacer_peticion_con_reintentos")
    def test_ambos_modelos_fallan(self, mock_peticion):
        """
        Test: Ambos modelos fallan
        
        Given: Tanto el modelo principal como el de respaldo fallan.
        When: Se agotan todas las vías de petición.
        Then: Lanza una excepción final informando que ambos modelos están caídos.
        """
        mock_peticion.side_effect = [Exception("Error 1"), Exception("Error 2")]

        with self.assertRaisesRegex(Exception, "Ambos modelos de Gemini están caídos. Error final: Error 2"):
            generar_guion_conversacional(self.comunicado, self.api_key)



    @patch("api.servicios.comunicado.podcast_service._hacer_peticion_con_reintentos")
    def test_api_devuelve_none(self, mock_peticion):
        """
        Test: API devuelve None
        
        Given: El wrapper de peticiones no lanza excepción pero devuelve None.
        When: Se evalúa la respuesta.
        Then: Lanza un ValueError indicando que no hubo respuesta.
        """
        mock_peticion.return_value = None

        with self.assertRaisesRegex(ValueError, "La API de Gemini no devolvió ninguna respuesta."):
            generar_guion_conversacional(self.comunicado, self.api_key)
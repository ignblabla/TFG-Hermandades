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



    @patch("api.servicios.comunicado.podcast_service.json.loads")
    @patch("api.servicios.comunicado.podcast_service._hacer_peticion_con_reintentos")
    def test_json_mal_formado_propaga_excepcion(self, mock_peticion, mock_json_loads):
        """
        Test: JSON mal formado
        
        Given: Gemini responde con un texto que no es un JSON válido.
        When: Se intenta parsear el contenido.
        Then: La excepción JSONDecodeError se propaga hacia arriba.
        """
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "no soy un json"}]}}]
        }
        mock_peticion.return_value = mock_resp

        mock_json_loads.side_effect = json.JSONDecodeError("msg", "doc", 0)

        with self.assertRaises(json.JSONDecodeError):
            generar_guion_conversacional(self.comunicado, self.api_key)



    @patch("api.servicios.comunicado.podcast_service.json.loads")
    @patch("api.servicios.comunicado.podcast_service._hacer_peticion_con_reintentos")
    def test_json_correcto_parseado(self, mock_peticion, mock_json_loads):
        """
        Test: JSON correcto parseado
        
        Given: Una respuesta exitosa de la API.
        When: Se recibe el texto plano de Gemini.
        Then: Se debe llamar a json.loads exactamente una vez para convertir el string en diccionario.
        """
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": '{"dialogos": []}'}]}}]
        }
        mock_peticion.return_value = mock_resp
        mock_json_loads.return_value = {"dialogos": []}

        generar_guion_conversacional(self.comunicado, self.api_key)

        mock_json_loads.assert_called_once_with('{"dialogos": []}')



    @patch("api.servicios.comunicado.podcast_service._hacer_peticion_con_reintentos")
    def test_usa_prompt_correctamente(self, mock_peticion):
        """
        Test: Usa prompt correctamente
        
        Given: Un comunicado con título "T" y contenido "C".
        When: Se construye el payload para la API.
        Then: El prompt enviado debe incluir obligatoriamente ambos campos para el contexto de la IA.
        """
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"candidates": [{"content": {"parts": [{"text": "{}"}]}}]}
        mock_peticion.return_value = mock_resp

        generar_guion_conversacional(self.comunicado, self.api_key)

        args, _ = mock_peticion.call_args
        payload = args[1]
        prompt = payload["contents"][0]["parts"][0]["text"]
        
        self.assertIn("Título del comunicado: T", prompt)
        self.assertIn("Contenido original: C", prompt)



    @patch("api.servicios.comunicado.podcast_service._hacer_peticion_con_reintentos")
    @patch("builtins.print")
    def test_retry_lanza_excepcion_va_a_fallback_con_reintentos_especificos(self, mock_print, mock_peticion):
        """
        Test: retry lanza excepción en primera llamada
            fallback también usa max_reintentos=2
        
        Given: El modelo principal falla por un error de red.
        When: Se activa el plan de respaldo.
        Then: La segunda llamada debe realizarse a la URL de respaldo Y 
            especificar explícitamente max_reintentos=2.
        """
        mock_resp_fallback = MagicMock()
        mock_resp_fallback.json.return_value = {"candidates": [{"content": {"parts": [{"text": "{}"}]}}]}

        mock_peticion.side_effect = [Exception("network"), mock_resp_fallback]

        generar_guion_conversacional(self.comunicado, self.api_key)

        args_fallback = mock_peticion.call_args_list[1]
        
        self.assertEqual(args_fallback[1]["max_reintentos"], 2)
        self.assertIn("gemini-2.5-flash-lite", args_fallback[0][0])



    @patch("api.servicios.comunicado.podcast_service._hacer_peticion_con_reintentos")
    def test_respuesta_sin_candidates_lanza_error(self, mock_peticion):
        """
        Test: respuesta sin candidates
        
        Given: Una respuesta de la API de Gemini que viene vacía de candidatos (ej. por bloqueo de seguridad).
        When: Se intenta acceder al primer candidato.
        Then: La función debe lanzar un IndexError o KeyError al intentar navegar por la estructura.
        """
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"candidates": []}
        mock_peticion.return_value = mock_resp

        with self.assertRaises((IndexError, KeyError)):
            generar_guion_conversacional(self.comunicado, self.api_key)



    @patch("api.servicios.comunicado.podcast_service._hacer_peticion_con_reintentos")
    def test_respuesta_sin_parts_lanza_error(self, mock_peticion):
        """
        Test: respuesta sin parts
        
        Given: Una respuesta con candidato pero sin contenido o partes.
        When: Se intenta acceder a candidates[0]["content"]["parts"].
        Then: La función lanza un KeyError indicando que la estructura esperada no está presente.
        """
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"candidates": [{"content": {}}]}
        mock_peticion.return_value = mock_resp

        with self.assertRaises(KeyError):
            generar_guion_conversacional(self.comunicado, self.api_key)



    @patch("api.servicios.comunicado.podcast_service._hacer_peticion_con_reintentos")
    def test_texto_vacio_falla_en_loads(self, mock_peticion):
        """
        Test: texto vacío
        
        Given: Gemini responde con una estructura correcta pero el campo "text" está vacío.
        When: Se pasa el string vacío a json.loads().
        Then: Lanza un JSONDecodeError ya que un string vacío no es un JSON válido.
        """
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": ""}]
                }
            }]
        }
        mock_peticion.return_value = mock_resp

        with self.assertRaises(json.JSONDecodeError):
            generar_guion_conversacional(self.comunicado, self.api_key)
import unittest
from unittest.mock import MagicMock, call, patch

import requests
from requests.exceptions import RequestException

from api.servicios.comunicado.podcast_service import _hacer_peticion_con_reintentos


class TestHacerPeticionConReintentos(unittest.TestCase):

    def setUp(self):
        self.url = "https://api.fake-podcast.com/generate"
        self.payload = {"texto": "Hola mundo"}



    @patch("api.servicios.comunicado.podcast_service.time.sleep")
    @patch("api.servicios.comunicado.podcast_service.requests.post")
    def test_respuesta_200_inmediata(self, mock_post, mock_sleep):
        """
        Test: Respuesta 200 inmediata
        
        Given: Una API que responde exitosamente (status 200) al primer intento.
        When: Se invoca la función _hacer_peticion_con_reintentos.
        Then: La función debe retornar la respuesta de inmediato, sin realizar 
            llamadas adicionales (retry) ni invocar time.sleep.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        resultado = _hacer_peticion_con_reintentos(url=self.url, payload=self.payload)

        self.assertEqual(resultado, mock_response)

        mock_post.assert_called_once_with(self.url, json=self.payload, timeout=30)

        mock_sleep.assert_not_called()



    @patch("api.servicios.comunicado.podcast_service.time.sleep")
    @patch("api.servicios.comunicado.podcast_service.requests.post")
    def test_429_con_exito_en_retry(self, mock_post, mock_sleep):
        """
        Test: 429 con éxito en retry
        
        Given: La API devuelve un 429 al inicio y un 200 en el segundo intento.
        When: Se invoca la función de petición.
        Then: Se realiza un reintento tras un sleep de 15 segundos (15 * (0+1)).
        """
        mock_429 = MagicMock(status_code=429)
        mock_200 = MagicMock(status_code=200)
        mock_post.side_effect = [mock_429, mock_200]

        resultado = _hacer_peticion_con_reintentos(self.url, self.payload)

        self.assertEqual(resultado.status_code, 200)
        self.assertEqual(mock_post.call_count, 2)

        mock_sleep.assert_called_once_with(15)



    @patch("api.servicios.comunicado.podcast_service.time.sleep")
    @patch("api.servicios.comunicado.podcast_service.requests.post")
    def test_429_hasta_agotar_reintentos(self, mock_post, mock_sleep):
        """
        Test: 429 hasta agotar reintentos
        
        Given: Una API que devuelve 429 constantemente.
        When: Se alcanzan los 4 intentos (default).
        Then: Lanza una excepción específica informando que se agotó la cuota.
        """
        mock_response = MagicMock(status_code=429)
        mock_post.return_value = mock_response

        with self.assertRaisesRegex(Exception, "Límite de cuota \(429\) excedido"):
            _hacer_peticion_con_reintentos(self.url, self.payload)

        self.assertEqual(mock_post.call_count, 4)
        self.assertEqual(mock_sleep.call_count, 3)



    @patch("api.servicios.comunicado.podcast_service.time.sleep")
    @patch("api.servicios.comunicado.podcast_service.requests.post")
    def test_500_con_exito_en_retry_backoff_exponencial(self, mock_post, mock_sleep):
        """
        Test: 500 con éxito en retry
        
        Given: La API devuelve dos errores 500 y luego un 200.
        When: Se procesan los reintentos.
        Then: El tiempo de espera sigue un backoff exponencial (2^intento).
        """
        mock_500 = MagicMock(status_code=500)
        mock_200 = MagicMock(status_code=200)
        mock_post.side_effect = [mock_500, mock_500, mock_200]

        _hacer_peticion_con_reintentos(self.url, self.payload)

        self.assertEqual(mock_sleep.call_count, 2)
        from unittest.mock import call
        mock_sleep.assert_has_calls([call(1), call(2)])



    @patch("api.servicios.comunicado.podcast_service.time.sleep")
    @patch("api.servicios.comunicado.podcast_service.requests.post")
    def test_503_con_exito_en_retry(self, mock_post, mock_sleep):
        """
        Test: 503 con éxito en retry
        
        Given: El servidor está temporalmente sobrecargado (503).
        When: El segundo intento devuelve un 200.
        Then: Se aplica el backoff exponencial (2^0 = 1s) y se retorna éxito.
        """
        mock_post.side_effect = [MagicMock(status_code=503), MagicMock(status_code=200)]

        _hacer_peticion_con_reintentos(self.url, self.payload)

        self.assertEqual(mock_post.call_count, 2)
        mock_sleep.assert_called_once_with(1)



    @patch("api.servicios.comunicado.podcast_service.time.sleep")
    @patch("api.servicios.comunicado.podcast_service.requests.post")
    def test_500_sin_exito_final(self, mock_post, mock_sleep):
        """
        Test: 500 sin éxito final
        
        Given: Un servidor que devuelve 500 en todos los intentos.
        When: Se agotan los 4 reintentos.
        Then: Lanza una excepción indicando que el servidor está caído tras reintentar.
        """
        mock_post.return_value = MagicMock(status_code=500)

        with self.assertRaisesRegex(Exception, "Servidor caído \(500\) tras todos los reintentos"):
            _hacer_peticion_con_reintentos(self.url, self.payload)

        self.assertEqual(mock_post.call_count, 4)

        mock_sleep.assert_has_calls([call(1), call(2), call(4)])



    @patch("api.servicios.comunicado.podcast_service.time.sleep")
    @patch("api.servicios.comunicado.podcast_service.requests.post")
    def test_error_de_red_con_recuperacion(self, mock_post, mock_sleep):
        """
        Test: Error de red con recuperación
        
        Given: Una excepción de red (RequestException) en el primer intento.
        When: El segundo intento funciona correctamente.
        Then: La función captura el error de requests y aplica el retry.
        """
        mock_200 = MagicMock(status_code=200)
        mock_post.side_effect = [RequestException("Timeout local"), mock_200]

        resultado = _hacer_peticion_con_reintentos(self.url, self.payload)

        self.assertEqual(resultado.status_code, 200)
        self.assertEqual(mock_post.call_count, 2)
        mock_sleep.assert_called_once_with(1)



    @patch("api.servicios.comunicado.podcast_service.time.sleep")
    @patch("api.servicios.comunicado.podcast_service.requests.post")
    def test_error_de_red_sin_recuperacion(self, mock_post, mock_sleep):
        """
        Test: Error de red sin recuperación
        
        Given: Errores de red persistentes en todos los intentos.
        When: Se llega al límite de reintentos.
        Then: Lanza una excepción de "Fallo de red" que envuelve el error original.
        """
        mock_post.side_effect = RequestException("DNS Failure")

        with self.assertRaisesRegex(Exception, "Fallo de red: DNS Failure"):
            _hacer_peticion_con_reintentos(self.url, self.payload)

        self.assertEqual(mock_post.call_count, 4)



    @patch("api.servicios.comunicado.podcast_service.time.sleep")
    @patch("api.servicios.comunicado.podcast_service.requests.post")
    def test_status_inexistente_lanza_raise_for_status(self, mock_post, mock_sleep):
        """
        # Comentario requerido por [2026-03-04]
        Test: status != 200/429/500/503
        
        Given: La API responde con un 404 (Not Found).
        When: Se procesa la respuesta y se llama a raise_for_status().
        Then: Al heredar HTTPError de RequestException, el bloque except lo captura, 
            realiza los 4 reintentos y lanza la excepción final formateada.
        """
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
        mock_post.return_value = mock_response

        with self.assertRaisesRegex(Exception, "Fallo de red: 404 Client Error"):
            _hacer_peticion_con_reintentos(self.url, self.payload)

        self.assertEqual(mock_post.call_count, 4)

        self.assertEqual(mock_sleep.call_count, 3)



    @patch("api.servicios.comunicado.podcast_service.time.sleep")
    @patch("api.servicios.comunicado.podcast_service.requests.post")
    def test_backoff_exponencial_correcto_500_503(self, mock_post, mock_sleep):
        """
        Test: Backoff exponencial correcto (500/503)
        
        Given: Errores persistentes de servidor.
        When: Se ejecutan los reintentos.
        Then: Los tiempos de espera deben ser 2^0, 2^1, 2^2.
        """
        mock_post.return_value = MagicMock(status_code=500)

        try:
            _hacer_peticion_con_reintentos(self.url, self.payload)
        except:
            pass

        expected_calls = [call(1), call(2), call(4)]
        mock_sleep.assert_has_calls(expected_calls)



    @patch("api.servicios.comunicado.podcast_service.time.sleep")
    @patch("api.servicios.comunicado.podcast_service.requests.post")
    def test_backoff_lineal_para_429(self, mock_post, mock_sleep):
        """
        Test: Backoff lineal para 429
        
        Given: Errores por límite de cuota (429).
        When: Se ejecutan los reintentos.
        Then: El tiempo de espera debe ser 15 * (intento + 1).
        """
        mock_post.return_value = MagicMock(status_code=429)

        try:
            _hacer_peticion_con_reintentos(self.url, self.payload)
        except:
            pass

        expected_calls = [call(15), call(30), call(45)]
        mock_sleep.assert_has_calls(expected_calls)



    @patch("api.servicios.comunicado.podcast_service.time.sleep")
    @patch("api.servicios.comunicado.podcast_service.requests.post")
    def test_excede_todos_los_reintentos_429(self, mock_post, mock_sleep):
        """
        Test: Excede todos los reintentos (429)
        
        Given: El límite de cuota persiste durante los 4 intentos.
        When: Se procesa el último intento.
        Then: Lanza una excepción con el mensaje de "Límite de cuota excedido".
        """
        mock_post.return_value = MagicMock(status_code=429)

        with self.assertRaisesRegex(Exception, "Límite de cuota \(429\) excedido tras todos los reintentos"):
            _hacer_peticion_con_reintentos(self.url, self.payload)

        self.assertEqual(mock_post.call_count, 4)



    @patch("api.servicios.comunicado.podcast_service.time.sleep")
    @patch("api.servicios.comunicado.podcast_service.requests.post")
    def test_forzar_excepcion_final_fuera_del_bucle(self, mock_post, mock_sleep):
        """
        # Comentario requerido por [2026-03-04]
        Test: TEST UNITARIO (forzando la excepción final)
        
        Given: Una respuesta de la API con un status code de éxito distinto a 200 (ej. 202 Accepted).
        When: Se procesan los intentos.
        Then: Como no es 200 no retorna. Como no es error, raise_for_status() no lanza nada. 
            El bucle itera sin pausas (sleeps) hasta agotarse y cae en la excepción final genérica.
        """
        mock_response = MagicMock()
        mock_response.status_code = 202

        mock_response.raise_for_status.return_value = None 
        mock_post.return_value = mock_response

        mensaje_esperado = "No se pudo obtener respuesta de la API tras varios intentos."

        with self.assertRaisesRegex(Exception, mensaje_esperado):
            _hacer_peticion_con_reintentos(self.url, self.payload)

        self.assertEqual(mock_post.call_count, 4)

        mock_sleep.assert_not_called()
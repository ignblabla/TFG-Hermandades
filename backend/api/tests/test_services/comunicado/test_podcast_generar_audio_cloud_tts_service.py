import unittest
from unittest.mock import MagicMock, patch, ANY

from api.servicios.comunicado.podcast_service import generar_audio_cloud_tts


class TestCloudTTSGeneracion(unittest.TestCase):

    @patch("api.servicios.comunicado.podcast_service.texttospeech.TextToSpeechClient")
    def test_flujo_feliz_audio_generado_correctamente(self, mock_tts_client_class):
        """
        Test: Flujo feliz (audio generado correctamente)
        
        Given: Un texto y el nombre de la voz que se desea sintetizar.
        When: Se ejecuta la función generar_audio_cloud_tts.
        Then: La llamada al cliente de la SDK es exitosa y se retornan los bytes del audio.
        """
        mock_client_instance = mock_tts_client_class.return_value

        mock_response = MagicMock()
        mock_response.audio_content = b"audio-bytes"
        mock_client_instance.synthesize_speech.return_value = mock_response

        texto = "Bienvenidos al podcast"
        nombre_voz = "es-ES-Studio-C"

        resultado = generar_audio_cloud_tts(texto, nombre_voz)

        self.assertEqual(resultado, b"audio-bytes")

        mock_client_instance.synthesize_speech.assert_called_once()

        kwargs = mock_client_instance.synthesize_speech.call_args.kwargs
        self.assertIn('input', kwargs)
        self.assertIn('voice', kwargs)
        self.assertIn('audio_config', kwargs)



    @patch("api.servicios.comunicado.podcast_service.texttospeech.VoiceSelectionParams")
    @patch("api.servicios.comunicado.podcast_service.texttospeech.SynthesisInput")
    @patch("api.servicios.comunicado.podcast_service.texttospeech.TextToSpeechClient")
    @patch("builtins.print")
    def test_error_en_api_retorna_none(self, mock_print, mock_client_class, mock_input, mock_voice):
        """
        Test: Error en API → retorna None
        
        Given: Un fallo de conexión o de cuota en el servicio de Google Cloud.
        When: synthesize_speech lanza una excepción.
        Then: La función debe capturar el error, imprimirlo y retornar None de forma segura.
        """
        mock_instance = mock_client_class.return_value
        mock_instance.synthesize_speech.side_effect = Exception("fail tts")

        resultado = generar_audio_cloud_tts("texto", "es-ES-Studio-C")

        self.assertIsNone(resultado)
        mock_print.assert_called_with("Error en Google Cloud TTS: fail tts")



    @patch("api.servicios.comunicado.podcast_service.texttospeech")
    def test_construccion_correcta_de_parametros_tts(self, mock_tts):
        """
        Test: Se crea cliente correctamente
            Se construye SynthesisInput correctamente
            VoiceSelectionParams correcto
        
        Given: Un texto y una voz específica.
        When: Se invoca al servicio.
        Then: Se deben instanciar los objetos de la SDK con los valores exactos 
            de idioma ("es-ES") y contenido.
        """
        mock_client_instance = mock_tts.TextToSpeechClient.return_value
        texto_input = "Hola mundo"
        voz_input = "es-ES-Studio-F"

        generar_audio_cloud_tts(texto_input, voz_input)

        mock_tts.TextToSpeechClient.assert_called_once()

        mock_tts.SynthesisInput.assert_called_once_with(text=texto_input)

        mock_tts.VoiceSelectionParams.assert_called_once_with(
            language_code="es-ES", 
            name=voz_input
        )

        mock_client_instance.synthesize_speech.assert_called_once_with(
            input=mock_tts.SynthesisInput.return_value,
            voice=mock_tts.VoiceSelectionParams.return_value,
            audio_config=mock_tts.AudioConfig.return_value
        )



    @patch("api.servicios.comunicado.podcast_service.texttospeech")
    def test_configuracion_tecnica_y_respeto_de_parametros(self, mock_tts):
        """
        Test: Nombre de voz se respeta
            AudioConfig correcto (MP3)
        
        Given: Un nombre de voz específico y el requerimiento de formato MP3.
        When: Se configura la síntesis.
        Then: La SDK debe recibir exactamente el nombre de voz solicitado y 
            el encoding debe ser obligatoriamente MP3.
        """
        nombre_voz_test = "es-ES-Studio-Z"
        
        generar_audio_cloud_tts("texto", nombre_voz_test)

        mock_tts.VoiceSelectionParams.assert_called_once_with(
            language_code="es-ES", 
            name=nombre_voz_test
        )

        mock_tts.AudioConfig.assert_called_once_with(
            audio_encoding=mock_tts.AudioEncoding.MP3
        )



    @patch("api.servicios.comunicado.podcast_service.texttospeech.TextToSpeechClient")
    def test_texto_vacio_no_rompe_servicio(self, mock_client_class):
        """
        Test: Texto vacío
        
        Given: Un string de texto vacío.
        When: Se llama a la API de Google.
        Then: Aunque la API podría devolver un error, la función debe manejarlo 
            según su bloque try/except y devolver None sin crashear.
        """
        mock_instance = mock_client_class.return_value
        mock_instance.synthesize_speech.side_effect = Exception("400: text is empty")

        resultado = generar_audio_cloud_tts("", "es-ES-Studio-C")

        self.assertIsNone(resultado)



    @patch("api.servicios.comunicado.podcast_service.texttospeech.TextToSpeechClient")
    @patch("builtins.print")
    def test_nombre_voz_invalido_retorna_none(self, mock_print, mock_client_class):
        """
        Test: Nombre de voz inválido
        
        Given: Un nombre de voz que no existe en el catálogo de Google Cloud.
        When: La SDK intenta realizar la petición.
        Then: Se captura la excepción (ej. 404 voice not found) y retorna None.
        """
        mock_instance = mock_client_class.return_value

        mock_instance.synthesize_speech.side_effect = Exception("Voice not supported")

        resultado = generar_audio_cloud_tts("texto", "invalid-voice")

        self.assertIsNone(resultado)
        mock_print.assert_called_with("Error en Google Cloud TTS: Voice not supported")



    @patch("api.servicios.comunicado.podcast_service.texttospeech.TextToSpeechClient")
    def test_respuesta_sin_audio_content_retorna_none(self, mock_client_class):
        """
        Test: API responde sin audio_content
        
        Given: Una respuesta exitosa de la API (status 200) pero con el cuerpo de audio vacío.
        When: Se intenta acceder a response.audio_content.
        Then: La función debe retornar None.
        """
        mock_instance = mock_client_class.return_value

        mock_response = MagicMock()
        mock_response.audio_content = None
        mock_instance.synthesize_speech.return_value = mock_response

        resultado = generar_audio_cloud_tts("texto", "es-ES-Studio-C")

        self.assertIsNone(resultado)



    @patch("api.servicios.comunicado.podcast_service.texttospeech.TextToSpeechClient")
    @patch("builtins.print")
    def test_timeout_o_error_de_red_retorna_none(self, mock_print, mock_client_class):
        """
        Test: Timeout / network error
        
        Given: Un problema de conectividad con los servidores de Google.
        When: synthesize_speech lanza una excepción de timeout.
        Then: Se captura el error y se retorna None para no interrumpir el flujo asíncrono.
        """
        mock_instance = mock_client_class.return_value

        mock_instance.synthesize_speech.side_effect = Exception("timeout")

        resultado = generar_audio_cloud_tts("texto", "es-ES-Studio-C")

        self.assertIsNone(resultado)
        mock_print.assert_called_with("Error en Google Cloud TTS: timeout")



    @patch("api.servicios.comunicado.podcast_service.texttospeech.TextToSpeechClient")
    @patch("builtins.print")
    def test_cliente_no_inicializado_correctamente_retorna_none(self, mock_print, mock_client_class):
        """
        Test: client no inicializado correctamente
        
        Given: Un error al instanciar el cliente (ej. falta de credenciales de Google).
        When: TextToSpeechClient() lanza una excepción.
        Then: El error ocurre dentro del bloque try, por lo que se captura y retorna None.
        """
        mock_client_class.side_effect = Exception("init error")

        resultado = generar_audio_cloud_tts("texto", "es-ES-Studio-C")

        self.assertIsNone(resultado)
        mock_print.assert_called_with("Error en Google Cloud TTS: init error")
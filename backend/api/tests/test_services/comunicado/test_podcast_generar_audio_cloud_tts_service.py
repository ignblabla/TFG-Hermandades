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
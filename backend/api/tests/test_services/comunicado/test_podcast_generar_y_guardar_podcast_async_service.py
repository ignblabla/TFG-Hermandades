import unittest
from unittest.mock import MagicMock, call, patch, ANY
import io

from api.servicios.comunicado.podcast_service import generar_y_guardar_podcast_async
from api.models import Comunicado


class TestPodcastServiceGeneracion(unittest.TestCase):

    def setUp(self):
        self.comunicado_id = 1

    @patch("api.servicios.comunicado.podcast_service.settings")
    @patch("api.servicios.comunicado.podcast_service.ContentFile")
    @patch("api.servicios.comunicado.podcast_service.AudioSegment")
    @patch("api.servicios.comunicado.podcast_service.generar_audio_cloud_tts")
    @patch("api.servicios.comunicado.podcast_service.generar_guion_conversacional")
    @patch("api.servicios.comunicado.podcast_service.Comunicado")
    def test_flujo_feliz_podcast_generado_correctamente(
        self, mock_comunicado, mock_guion, mock_tts, mock_audio, mock_content_file, mock_settings
    ):
        """
        Test: Flujo feliz (podcast generado correctamente)
        
        Given: Un ID de comunicado válido y respuestas exitosas de las APIs (Gemini y TTS).
        When: Se ejecuta la generación asíncrona.
        Then: Se deben generar los audios según el locutor, concatenarse correctamente, 
            y llamar a archivo_podcast.save() para almacenar el MP3 final.
        """
        mock_settings.GEMINI_API_KEY = "test_key"

        mock_comunicado_instancia = MagicMock()
        mock_comunicado_instancia.id = self.comunicado_id
        mock_comunicado.objects.get.return_value = mock_comunicado_instancia

        mock_guion.return_value = {
            "dialogos": [
                {"locutor": "Carmen", "texto": "Hola bienvenidos."},
                {"locutor": "Carlos", "texto": "Gracias Carmen."}
            ]
        }

        mock_tts.return_value = b"fake_audio_bytes"

        mock_audio_final = MagicMock()
        mock_audio_final.__len__.return_value = 100

        mock_audio_final.__iadd__.return_value = mock_audio_final
        
        mock_audio.empty.return_value = mock_audio_final
        mock_audio.from_file.return_value = MagicMock()
        mock_audio.silent.return_value = MagicMock()

        generar_y_guardar_podcast_async(self.comunicado_id)

        mock_guion.assert_called_once_with(mock_comunicado_instancia, "test_key")

        self.assertEqual(mock_tts.call_count, 2)
        from unittest.mock import call
        mock_tts.assert_has_calls([
            call("Hola bienvenidos.", "es-ES-Studio-C"),
            call("Gracias Carmen.", "es-ES-Studio-F")
        ])

        mock_audio_final.export.assert_called_once_with(ANY, format="mp3", bitrate="128k")

        nombre_esperado = f"podcast_comunicado_{self.comunicado_id}.mp3"
        mock_comunicado_instancia.archivo_podcast.save.assert_called_once_with(
            nombre_esperado, mock_content_file.return_value, save=True
        )



    @patch("api.servicios.comunicado.podcast_service.Comunicado")
    @patch("builtins.print")
    def test_comunicado_no_existe_en_podcast(self, mock_print, mock_comunicado):
        """
        Test: Comunicado no existe
        
        Given: Un ID que no existe en la base de datos.
        When: Se intenta generar el podcast.
        Then: Se captura el error DoesNotExist y se imprime el mensaje de error por consola.
        """
        mock_comunicado.DoesNotExist = Comunicado.DoesNotExist
        
        mock_comunicado.objects.get.side_effect = Comunicado.DoesNotExist()

        generar_y_guardar_podcast_async(self.comunicado_id)

        mock_print.assert_called_with(f"Error generando podcast para comunicado {self.comunicado_id}: ")



    @patch("api.servicios.comunicado.podcast_service.settings")
    @patch("api.servicios.comunicado.podcast_service.generar_guion_conversacional")
    @patch("api.servicios.comunicado.podcast_service.Comunicado")
    @patch("builtins.print")
    def test_gemini_devuelve_none_lanza_value_error(self, mock_print, mock_comunicado, mock_guion, mock_settings):
        """
        Test: Gemini devuelve None
        
        Given: Un comunicado válido pero Gemini no logra generar el JSON del guion.
        When: generar_guion_conversacional retorna None.
        Then: Se levanta un ValueError que es capturado por el bloque except general.
        """
        mock_comunicado.objects.get.return_value = MagicMock()

        mock_guion.return_value = None

        generar_y_guardar_podcast_async(self.comunicado_id)

        mock_print.assert_called_with(
            f"Error generando podcast para comunicado {self.comunicado_id}: Gemini no pudo generar el guion conversacional."
        )



    @patch("api.servicios.comunicado.podcast_service.settings")
    @patch("api.servicios.comunicado.podcast_service.generar_guion_conversacional")
    @patch("api.servicios.comunicado.podcast_service.Comunicado")
    @patch("builtins.print")
    def test_gemini_falla_excepcion_es_capturada(self, mock_print, mock_comunicado, mock_guion, mock_settings):
        """
        Test: Gemini falla (exception)
        
        Given: Un fallo de conexión o error interno en la API de Gemini.
        When: generar_guion_conversacional lanza una Exception.
        Then: El error se captura en el bloque catch general de la función.
        """
        mock_comunicado.DoesNotExist = Comunicado.DoesNotExist
        mock_comunicado.objects.get.return_value = MagicMock()

        mock_guion.side_effect = Exception("AI error")

        generar_y_guardar_podcast_async(self.comunicado_id)

        mock_print.assert_called_with(f"Error generando podcast para comunicado {self.comunicado_id}: AI error")



    @patch("api.servicios.comunicado.podcast_service.AudioSegment")
    @patch("api.servicios.comunicado.podcast_service.generar_audio_cloud_tts")
    @patch("api.servicios.comunicado.podcast_service.generar_guion_conversacional")
    @patch("api.servicios.comunicado.podcast_service.Comunicado")
    @patch("api.servicios.comunicado.podcast_service.settings")
    def test_procesa_multiples_dialogos_y_voces(
        self, mock_settings, mock_comunicado, mock_guion, mock_tts, mock_audio
    ):
        """
        Test: Procesa correctamente múltiples diálogos
            Selección de voz correcta (Carmen)
            Selección de voz default
        
        Given: Un guion con dos locutores distintos (Carmen y Juan).
        When: Se itera sobre la lista de diálogos.
        Then: Se debe llamar al TTS con la voz 'Studio-C' para Carmen y 
            'Studio-F' para cualquier otro locutor, acumulando ambos audios.
        """
        mock_comunicado.objects.get.return_value = MagicMock()

        mock_guion.return_value = {
            "dialogos": [
                {"locutor": "Carmen", "texto": "hola"},
                {"locutor": "Juan", "texto": "hola 2"}
            ]
        }

        mock_tts.return_value = b"audio_data"

        mock_segment = MagicMock()
        mock_segment.__len__.return_value = 10
        mock_segment.__iadd__.return_value = mock_segment
        mock_audio.empty.return_value = mock_segment
        mock_audio.from_file.return_value = MagicMock()

        generar_y_guardar_podcast_async(self.comunicado_id)

        self.assertEqual(mock_tts.call_count, 2)

        expected_calls = [
            call("hola", "es-ES-Studio-C"),
            call("hola 2", "es-ES-Studio-F")
        ]
        mock_tts.assert_has_calls(expected_calls)



    @patch("api.servicios.comunicado.podcast_service.AudioSegment")
    @patch("api.servicios.comunicado.podcast_service.generar_audio_cloud_tts")
    @patch("api.servicios.comunicado.podcast_service.generar_guion_conversacional")
    @patch("api.servicios.comunicado.podcast_service.Comunicado")
    def test_seleccion_voz_default_para_locutor_desconocido(
        self, mock_comunicado, mock_guion, mock_tts, mock_audio
    ):
        """
        Test: Selección de voz default
        
        Given: Un locutor que no es "Carmen" (ej. "Narrador").
        When: Se procesa el texto.
        Then: El sistema debe asignar por defecto la voz "es-ES-Studio-F".
        """
        mock_comunicado.objects.get.return_value = MagicMock()
        mock_guion.return_value = {
            "dialogos": [{"locutor": "Narrador", "texto": "Texto de prueba"}]
        }
        mock_tts.return_value = b"audio"

        mock_segment = MagicMock()
        mock_segment.__iadd__.return_value = mock_segment
        mock_audio.empty.return_value = mock_segment

        generar_y_guardar_podcast_async(self.comunicado_id)

        mock_tts.assert_called_with("Texto de prueba", "es-ES-Studio-F")



    @patch("api.servicios.comunicado.podcast_service.AudioSegment")
    @patch("api.servicios.comunicado.podcast_service.generar_audio_cloud_tts")
    @patch("api.servicios.comunicado.podcast_service.generar_guion_conversacional")
    @patch("api.servicios.comunicado.podcast_service.Comunicado")
    def test_tts_devuelve_none_no_anhade_audio(self, mock_comunicado, mock_guion, mock_tts, mock_audio):
        """
        Test: TTS devuelve None
        
        Given: El servicio TTS falla para una línea específica.
        When: generar_audio_cloud_tts retorna None.
        Then: No se intenta procesar el segmento con AudioSegment ni se suma al audio final.
        """
        mock_comunicado.objects.get.return_value = MagicMock()
        mock_guion.return_value = {"dialogos": [{"locutor": "Carmen", "texto": "hola"}]}

        mock_tts.return_value = None

        generar_y_guardar_podcast_async(self.comunicado_id)

        mock_audio.from_file.assert_not_called()



    @patch("api.servicios.comunicado.podcast_service.AudioSegment")
    @patch("api.servicios.comunicado.podcast_service.generar_audio_cloud_tts")
    @patch("api.servicios.comunicado.podcast_service.generar_guion_conversacional")
    @patch("api.servicios.comunicado.podcast_service.Comunicado")
    @patch("builtins.print")
    def test_audio_segment_from_file_falla(self, mock_print, mock_comunicado, mock_guion, mock_tts, mock_audio):
        """
        Test: AudioSegment.from_file falla
        
        Given: El TTS devuelve bytes corruptos o pydub falla al procesarlos.
        When: from_file lanza una excepción.
        Then: La excepción es capturada por el bloque general y se imprime el error.
        """
        mock_comunicado.objects.get.return_value = MagicMock()
        mock_guion.return_value = {"dialogos": [{"locutor": "Carmen", "texto": "hola"}]}
        mock_tts.return_value = b"bytes_corruptos"

        mock_audio.from_file.side_effect = Exception("audio error")

        generar_y_guardar_podcast_async(self.comunicado_id)

        mock_print.assert_called_with(f"Error generando podcast para comunicado {self.comunicado_id}: audio error")



    @patch("api.servicios.comunicado.podcast_service.AudioSegment")
    @patch("api.servicios.comunicado.podcast_service.generar_audio_cloud_tts")
    @patch("api.servicios.comunicado.podcast_service.generar_guion_conversacional")
    @patch("api.servicios.comunicado.podcast_service.Comunicado")
    @patch("builtins.print")
    def test_export_o_save_falla_captura_error(self, mock_print, mock_comunicado, mock_guion, mock_tts, mock_audio):
        """
        Test: export falla / save falla en storage
        
        Given: El proceso de audio fue exitoso pero falla la escritura final en disco/storage.
        When: export o save lanzan una excepción.
        Then: El catch global captura el fallo y evita el crash del servicio.
        """
        instancia = MagicMock()
        mock_comunicado.objects.get.return_value = instancia
        mock_guion.return_value = {"dialogos": [{"locutor": "Carmen", "texto": "hola"}]}
        mock_tts.return_value = b"audio"

        mock_audio_final = MagicMock()
        mock_audio_final.__len__.return_value = 100
        mock_audio_final.__iadd__.return_value = mock_audio_final
        mock_audio.empty.return_value = mock_audio_final

        instancia.archivo_podcast.save.side_effect = Exception("storage error")

        generar_y_guardar_podcast_async(self.comunicado_id)

        mock_print.assert_called_with(f"Error generando podcast para comunicado {self.comunicado_id}: storage error")



    @patch("api.servicios.comunicado.podcast_service.AudioSegment")
    @patch("api.servicios.comunicado.podcast_service.generar_audio_cloud_tts")
    @patch("api.servicios.comunicado.podcast_service.generar_guion_conversacional")
    @patch("api.servicios.comunicado.podcast_service.Comunicado")
    def test_no_guarda_si_audio_vacio(self, mock_comunicado, mock_guion, mock_tts, mock_audio):
        """
        Test: No guarda si audio vacío
        
        Given: Un guion que no generó diálogos o audios fallidos.
        When: El objeto audio_final tiene longitud 0.
        Then: No se intenta exportar ni llamar al método .save() del modelo.
        """
        instancia = MagicMock()
        mock_comunicado.objects.get.return_value = instancia
        mock_guion.return_value = {"dialogos": []}

        mock_audio_final = MagicMock()
        mock_audio_final.__len__.return_value = 0
        mock_audio.empty.return_value = mock_audio_final

        generar_y_guardar_podcast_async(self.comunicado_id)

        mock_audio_final.export.assert_not_called()
        instancia.archivo_podcast.save.assert_not_called()
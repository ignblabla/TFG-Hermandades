import unittest
from unittest.mock import MagicMock, patch

from api.servicios.comunicado.gemini_service import generar_y_guardar_embedding_async
from api.models import Comunicado


class TestGeminiServiceAsync(unittest.TestCase):

    def setUp(self):
        self.comunicado_id = 123
        self.titulo = "Alerta de Clima"
        self.contenido = "Se esperan lluvias intensas."



    @patch("api.servicios.comunicado.gemini_service.threading.Thread")
    @patch("api.servicios.comunicado.gemini_service.genai.Client")
    @patch("api.servicios.comunicado.gemini_service.Comunicado")
    @patch("api.servicios.comunicado.gemini_service.settings")
    def test_se_crea_el_thread_correctamente(self, mock_settings, mock_comunicado, mock_genai, mock_thread):
        """
        Test: Se crea el Thread correctamente
        
        Given: Un ID de comunicado para procesar.
        When: Se invoca la función generar_y_guardar_embedding_async.
        Then: La función debe instanciar un threading.Thread pasándole la función 
            interna _run como target y debe ejecutar el método start().
        """
        comunicado_id = 1

        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        generar_y_guardar_embedding_async(comunicado_id)

        mock_thread.assert_called_once()

        _, kwargs = mock_thread.call_args

        target_function = kwargs.get("target")
        self.assertIsNotNone(target_function, "El argumento target del Thread no debe ser None")
        self.assertTrue(callable(target_function), "El target debe ser una función callable")

        mock_thread_instance.start.assert_called_once()



    @patch("api.servicios.comunicado.gemini_service.threading.Thread")
    def test_se_llama_start_correctamente(self, mock_thread):
        """
        Test: Se llama .start()
        
        Given: El inicio del servicio asíncrono.
        When: Se crea la instancia del hilo.
        Then: Se debe llamar al método .start() para que el hilo comience su ejecución.
        """
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        generar_y_guardar_embedding_async(self.comunicado_id)

        mock_thread_instance.start.assert_called_once()



    @patch("api.servicios.comunicado.gemini_service.genai.Client")
    @patch("api.servicios.comunicado.gemini_service.Comunicado")
    @patch("api.servicios.comunicado.gemini_service.threading.Thread")
    def test_flujo_interno_ejecuta_comunicado_get(self, mock_thread, mock_comunicado, mock_genai):
        """
        Test: Flujo interno ejecuta Comunicado.objects.get
        
        Given: La función _run capturada del mock del hilo.
        When: Ejecutamos manualmente el target del hilo.
        Then: Se debe llamar a Comunicado.objects.get con el ID proporcionado.
        """
        generar_y_guardar_embedding_async(self.comunicado_id)

        target = mock_thread.call_args[1]["target"]
        target()

        mock_comunicado.objects.get.assert_called_once_with(pk=self.comunicado_id)



    @patch("api.servicios.comunicado.gemini_service.Comunicado")
    @patch("api.servicios.comunicado.gemini_service.threading.Thread")
    @patch("api.servicios.comunicado.gemini_service.genai.Client")
    @patch("builtins.print")
    def test_comunicado_no_existe_maneja_excepcion(self, mock_print, mock_genai, mock_thread, mock_comunicado):
        """
        Test: Comunicado no existe
        
        Given: Un ID que no existe en la DB.
        When: Se ejecuta el target del hilo y lanza DoesNotExist.
        Then: El error debe ser capturado internamente y mostrar un warning por consola.
        """
        mock_comunicado.DoesNotExist = Comunicado.DoesNotExist

        mock_comunicado.objects.get.side_effect = Comunicado.DoesNotExist()

        generar_y_guardar_embedding_async(self.comunicado_id)
        target = mock_thread.call_args[1]["target"]

        try:
            target()
        except Exception as e:
            self.fail(f"El target() lanzó una excepción no controlada: {e}")

        mock_print.assert_any_call(f"⚠️ Comunicado {self.comunicado_id} no encontrado para embedding.")
        mock_genai.assert_not_called()



    @patch("api.servicios.comunicado.gemini_service.settings")
    @patch("api.servicios.comunicado.gemini_service.Comunicado")
    @patch("api.servicios.comunicado.gemini_service.genai.Client")
    @patch("api.servicios.comunicado.gemini_service.threading.Thread")
    def test_construccion_texto_y_llamada_genai(self, mock_thread, mock_genai, mock_comunicado, mock_settings):
        """
        Test: Se construye correctamente el texto
            Se llama a Google GenAI client
            Se usa modelo correcto
        
        Given: Un comunicado con título y contenido específicos.
        When: Se ejecuta la lógica interna del hilo (_run).
        Then: Se debe llamar a embed_content con el formato de texto correcto
            y utilizando el modelo 'gemini-embedding-001'.
        """
        mock_settings.GEMINI_API_KEY = "test_key"

        instancia_comunicado = MagicMock()
        instancia_comunicado.titulo = self.titulo
        instancia_comunicado.contenido = self.contenido
        mock_comunicado.objects.get.return_value = instancia_comunicado

        mock_client = MagicMock()
        mock_genai.return_value = mock_client

        mock_client.models.embed_content.return_value = MagicMock()

        generar_y_guardar_embedding_async(self.comunicado_id)
        target = mock_thread.call_args[1]["target"]
        target()

        mock_client.models.embed_content.assert_called_once()

        _, kwargs = mock_client.models.embed_content.call_args

        texto_esperado = f"Título: {self.titulo}\nContenido: {self.contenido}"
        self.assertEqual(kwargs["contents"], texto_esperado)

        self.assertEqual(kwargs["model"], "gemini-embedding-001")



    @patch("api.servicios.comunicado.gemini_service.Comunicado")
    @patch("api.servicios.comunicado.gemini_service.genai.Client")
    @patch("api.servicios.comunicado.gemini_service.threading.Thread")
    def test_task_type_y_actualizacion_db(self, mock_thread, mock_genai, mock_comunicado):
        """
        Test: Se usa task_type correcto
            Se actualiza embedding en DB
        
        Given: Una respuesta exitosa de Gemini con un vector de embedding.
        When: Se ejecuta el proceso interno del hilo.
        Then: La llamada a la API debe incluir el task_type RETRIEVAL_DOCUMENT 
            y la base de datos debe actualizarse con los valores recibidos.
        """
        mock_comunicado.objects.get.return_value = MagicMock(titulo="T", contenido="C")

        mock_client = mock_genai.return_value
        mock_resultado = MagicMock()
        mock_resultado.embeddings = [MagicMock(values=[0.1, 0.2, 0.3])]
        mock_client.models.embed_content.return_value = mock_resultado

        generar_y_guardar_embedding_async(self.comunicado_id)
        target = mock_thread.call_args[1]["target"]
        target()

        _, kwargs = mock_client.models.embed_content.call_args
        self.assertEqual(kwargs["config"].task_type, "RETRIEVAL_DOCUMENT")

        mock_comunicado.objects.filter.assert_called_once_with(pk=self.comunicado_id)
        mock_comunicado.objects.filter.return_value.update.assert_called_once_with(
            embedding=[0.1, 0.2, 0.3]
        )



    @patch("api.servicios.comunicado.gemini_service.settings")
    @patch("api.servicios.comunicado.gemini_service.Comunicado")
    @patch("api.servicios.comunicado.gemini_service.threading.Thread")
    @patch("builtins.print")
    def test_api_key_missing_maneja_excepcion(self, mock_print, mock_thread, mock_comunicado, mock_settings):
        """
        Test: API Key missing
        
        Given: Un entorno donde GEMINI_API_KEY no está definida.
        When: El hilo intenta instanciar el cliente de GenAI.
        Then: Se debe capturar la excepción y mostrar el error por consola sin romper el hilo principal.
        """
        mock_comunicado.DoesNotExist = Comunicado.DoesNotExist

        mock_settings.GEMINI_API_KEY = None
        mock_comunicado.objects.get.return_value = MagicMock()

        with patch("api.servicios.comunicado.gemini_service.genai.Client", side_effect=Exception("API Key missing")):
            generar_y_guardar_embedding_async(self.comunicado_id)
            target = mock_thread.call_args[1]["target"]
            target()

        mock_print.assert_any_call(f"⚠️ Error generando embedding para comunicado {self.comunicado_id}: API Key missing")



    @patch("api.servicios.comunicado.gemini_service.Comunicado")
    @patch("api.servicios.comunicado.gemini_service.genai.Client")
    @patch("api.servicios.comunicado.gemini_service.threading.Thread")
    @patch("builtins.print")
    def test_error_en_gemini_api_capturado(self, mock_print, mock_thread, mock_genai, mock_comunicado):
        """
        Test: error en Gemini API
        
        Given: Un comunicado válido y una configuración correcta.
        When: La API de Gemini falla durante la generación del embedding (ej. timeout o cuota excedida).
        Then: La excepción es capturada dentro del hilo, evitando un crash, y se imprime el error.
        """
        mock_comunicado.DoesNotExist = Comunicado.DoesNotExist

        mock_comunicado.objects.get.return_value = MagicMock()

        mock_client = mock_genai.return_value
        mock_client.models.embed_content.side_effect = Exception("API error")

        generar_y_guardar_embedding_async(self.comunicado_id)
        target = mock_thread.call_args[1]["target"]

        try:
            target()
        except Exception as e:
            self.fail(f"El target() lanzó una excepción hacia afuera: {e}")

        mock_print.assert_any_call(f"⚠️ Error generando embedding para comunicado {self.comunicado_id}: API error")



    @patch("api.servicios.comunicado.gemini_service.Comunicado")
    @patch("api.servicios.comunicado.gemini_service.genai.Client")
    @patch("api.servicios.comunicado.gemini_service.threading.Thread")
    @patch("builtins.print")
    def test_fallo_en_update_db_capturado(self, mock_print, mock_thread, mock_genai, mock_comunicado):
        """
        Test: fallo en update DB
        
        Given: Un embedding generado exitosamente por Gemini.
        When: Se intenta guardar el vector en la base de datos pero ocurre un error (ej. desconexión).
        Then: El error de base de datos es capturado internamente y registrado por consola.
        """
        mock_comunicado.DoesNotExist = Comunicado.DoesNotExist

        mock_comunicado.objects.get.return_value = MagicMock()

        mock_client = mock_genai.return_value
        mock_client.models.embed_content.return_value = MagicMock(
            embeddings=[MagicMock(values=[0.1, 0.2])]
        )

        mock_comunicado.objects.filter.return_value.update.side_effect = Exception("DB error")

        generar_y_guardar_embedding_async(self.comunicado_id)
        target = mock_thread.call_args[1]["target"]

        try:
            target()
        except Exception as e:
            self.fail(f"El target() filtró la excepción de DB: {e}")

        mock_print.assert_any_call(f"⚠️ Error generando embedding para comunicado {self.comunicado_id}: DB error")
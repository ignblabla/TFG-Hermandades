import unittest
from unittest.mock import patch, MagicMock

from api.servicios.comunicado.comunicado_rag_service import ComunicadoRAGService


class TestComunicadoRagServicePreguntar(unittest.TestCase):

    def setUp(self):
        self.servicio = ComunicadoRAGService()
        self.servicio.client = MagicMock()

        self.mock_ai_response = MagicMock()
        self.mock_ai_response.text = "Respuesta generada"
        self.servicio.client.models.generate_content.return_value = self.mock_ai_response



    def test_genera_respuesta_correctamente_con_contexto(self):
        """
        Test: Genera respuesta correctamente con contexto
        
        Given: Una pregunta del usuario y un contexto semántico recuperado exitosamente.
        When: Se llama al método para hacer la pregunta a los comunicados.
        Then: Se verifica que se arma el prompt correctamente, se invoca al modelo de Gemini configurado (gemini-2.5-flash) y se retorna el texto generado.
        """
        pregunta = "¿A qué hora es la procesión?"
        contexto_simulado = "--- COMUNICADO: Horarios (Fecha: 10/04/2026) ---\nLa procesión comienza a las 18:00.\n\n"

        self.servicio._recuperar_contexto_semantico = MagicMock(return_value=contexto_simulado)

        mock_respuesta_gemini = MagicMock()
        mock_respuesta_gemini.text = "Según los comunicados oficiales, la procesión comienza a las 18:00."
        self.servicio.client.models.generate_content.return_value = mock_respuesta_gemini

        resultado = self.servicio.preguntar_a_comunicados(pregunta)

        self.servicio._recuperar_contexto_semantico.assert_called_once_with(pregunta)

        self.servicio.client.models.generate_content.assert_called_once()
        args_llamada = self.servicio.client.models.generate_content.call_args.kwargs

        self.assertEqual(args_llamada['model'], 'gemini-2.5-flash')

        prompt_generado = args_llamada['contents']
        self.assertIn("Eres el asistente virtual oficial de la Hermandad", prompt_generado)
        self.assertIn(contexto_simulado, prompt_generado)
        self.assertIn(pregunta, prompt_generado)

        self.assertEqual(resultado, "Según los comunicados oficiales, la procesión comienza a las 18:00.")



    def test_genera_respuesta_sin_contexto_usa_texto_defecto(self):
        """
        Test: Genera respuesta cuando no hay contexto (usa texto por defecto)
        
        Given: La recuperación semántica no devuelve ningún comunicado (string vacío).
        When: Se llama a preguntar_a_comunicados.
        Then: Se verifica que el prompt enviado a la IA contiene el texto por defecto: "No hay comunicados relevantes para esta consulta."
        """
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value="")

        self.servicio.preguntar_a_comunicados("¿Hay noticias?")

        args = self.servicio.client.models.generate_content.call_args.kwargs
        self.assertIn("No hay comunicados relevantes para esta consulta.", args['contents'])



    def test_error_en_recuperar_contexto_semantico(self):
        """
        Test: Error en _recuperar_contexto_semantico
        
        Given: El método interno de recuperación de contexto falla (ej. error de base de datos).
        When: Se intenta generar una respuesta.
        Then: La excepción se propaga hacia el llamador, ya que este método no tiene un try/except que cubra la llamada inicial.
        """
        self.servicio._recuperar_contexto_semantico = MagicMock(side_effect=Exception("DB Failure"))

        with self.assertRaises(Exception) as context:
            self.servicio.preguntar_a_comunicados("test")
        self.assertIn("DB Failure", str(context.exception))



    def test_error_en_generate_content(self):
        """
        Test: Error en generate_content
        
        Given: El cliente de Gemini lanza una excepción (ej. cuota excedida o error de red).
        When: Se intenta obtener la respuesta de la IA.
        Then: El servicio captura el error, imprime el mensaje exacto y relanza una excepción con un mensaje descriptivo.
        """
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value="Contexto")
        self.servicio.client.models.generate_content.side_effect = Exception("Quota exceeded")

        with self.assertRaises(Exception) as context:
            self.servicio.preguntar_a_comunicados("test")
        
        self.assertIn("Error al generar la respuesta con la IA: Quota exceeded", str(context.exception))



    def test_verificar_excepcion_con_mensaje_controlado(self):
        """
        Test: Verificar que se lanza excepción con mensaje controlado
        
        Given: Un fallo crítico en el modelo de generación.
        When: Se captura la excepción en el bloque try/except.
        Then: La excepción relanzada debe contener el prefijo "Error al generar la respuesta con la IA:" seguido del error original.
        """
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value="Info")
        error_msg = "Model overload"
        self.servicio.client.models.generate_content.side_effect = Exception(error_msg)

        with self.assertRaises(Exception) as context:
            self.servicio.preguntar_a_comunicados("test")
        
        self.assertEqual(str(context.exception), f"Error al generar la respuesta con la IA: {error_msg}")
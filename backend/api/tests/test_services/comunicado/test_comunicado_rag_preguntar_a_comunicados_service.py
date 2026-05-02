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



    def test_construye_correctamente_prompt_con_contexto(self):
        """
        Test: Se construye correctamente el prompt con contexto
        
        Given: Un contexto textual recuperado.
        When: Se prepara la llamada a la IA.
        Then: Se verifica que el bloque "COMUNICADOS OFICIALES" en el prompt contiene exactamente el contexto recuperado.
        """
        contexto = "Info oficial: La casa hermandad estará cerrada."
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value=contexto)

        self.servicio.preguntar_a_comunicados("test")

        args = self.servicio.client.models.generate_content.call_args.kwargs
        prompt_generado = args['contents']

        self.assertIn("COMUNICADOS OFICIALES:", prompt_generado)
        self.assertIn(contexto, prompt_generado)



    def test_incluye_pregunta_usuario_en_prompt(self):
        """
        Test: Se incluye correctamente la pregunta del usuario en el prompt
        
        Given: Una pregunta específica del usuario.
        When: Se genera el prompt estricto.
        Then: El prompt final debe incluir la sección "PREGUNTA DEL HERMANO" con la pregunta original.
        """
        pregunta = "¿Cuándo es el próximo cabildo?"
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value="Contexto")

        self.servicio.preguntar_a_comunicados(pregunta)

        args = self.servicio.client.models.generate_content.call_args.kwargs
        prompt_generado = args['contents']

        self.assertIn("PREGUNTA DEL HERMANO:", prompt_generado)
        self.assertIn(pregunta, prompt_generado)



    def test_devuelve_respuesta_text(self):
        """
        Test: Devuelve respuesta.text
        
        Given: Una respuesta exitosa del objeto de IA con un atributo .text.
        When: Finaliza la ejecución del método.
        Then: El valor retornado debe ser exactamente el contenido de respuesta.text.
        """
        texto_esperado = "Esta es la respuesta de la IA"
        self.mock_ai_response.text = texto_esperado
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value="Contexto")

        resultado = self.servicio.preguntar_a_comunicados("pregunta")

        self.assertEqual(resultado, texto_esperado)



    def test_llama_al_modelo_correcto(self):
        """
        Test: Llama al modelo correcto (gemini-2.5-flash)
        
        Given: Una petición estándar.
        When: Se invoca a generate_content.
        Then: Se verifica que el parámetro 'model' utilizado es estrictamente 'gemini-2.5-flash'.
        """
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value="Contexto")

        self.servicio.preguntar_a_comunicados("test")

        args = self.servicio.client.models.generate_content.call_args.kwargs
        self.assertEqual(args['model'], 'gemini-2.5-flash')



    def test_llama_una_unica_vez_a_generate_content(self):
        """
        Test: Se llama una única vez a generate_content
        
        Given: Un flujo de ejecución normal.
        When: Se procesa la pregunta.
        Then: El cliente de modelos solo debe ser llamado una vez para optimizar tokens y tiempo de respuesta.
        """
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value="Contexto")

        self.servicio.preguntar_a_comunicados("test")

        self.servicio.client.models.generate_content.assert_called_once()



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



    def test_generate_content_devuelve_objeto_sin_text(self):
        """
        Test: generate_content devuelve objeto sin .text
        
        Given: La respuesta del modelo no contiene el atributo 'text' (modelo mal configurado o respuesta inesperada).
        When: Se intenta acceder a respuesta.text.
        Then: Se captura el AttributeError resultante dentro del bloque try/except y se relanza como una excepción de IA.
        """
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value="Contexto")

        self.servicio.client.models.generate_content.return_value = MagicMock(spec=[])

        with self.assertRaises(Exception) as context:
            self.servicio.preguntar_a_comunicados("test")
        self.assertIn("Error al generar la respuesta con la IA", str(context.exception))



    def test_respuesta_text_es_none(self):
        """
        Test: respuesta.text es None
        
        Given: El modelo responde exitosamente pero el contenido del texto es nulo (None).
        When: El servicio intenta retornar el resultado.
        Then: El método retorna None (comportamiento por defecto del lenguaje), permitiendo que el flujo continúe o falle según quien reciba el dato.
        """
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value="Contexto")
        mock_res = MagicMock()
        mock_res.text = None
        self.servicio.client.models.generate_content.return_value = mock_res

        resultado = self.servicio.preguntar_a_comunicados("test")

        self.assertIsNone(resultado)



    def test_contexto_con_solo_espacios_usa_fallback(self):
        """
        Test: Contexto con solo espacios (debe usar fallback)
        
        Given: El método de recuperación devuelve un string que solo contiene espacios en blanco o tabulaciones.
        When: Se evalúa la condición del prompt para el bloque de comunicados.
        Then: Se verifica que se utiliza el texto de fallback: "No hay comunicados relevantes para esta consulta."
        """
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value="   \n   ")

        self.servicio.preguntar_a_comunicados("test")

        args = self.servicio.client.models.generate_content.call_args.kwargs
        self.assertIn("No hay comunicados relevantes para esta consulta.", args['contents'])



    def test_pregunta_vacia(self):
        """
        Test: Pregunta vacía
        
        Given: El usuario envía una cadena vacía como pregunta.
        When: Se genera el prompt.
        Then: El sistema debe procesar la solicitud e incluir el campo de pregunta vacío en el prompt enviado a la IA.
        """
        pregunta_vacia = ""
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value="Contexto")

        self.servicio.preguntar_a_comunicados(pregunta_vacia)

        args = self.servicio.client.models.generate_content.call_args.kwargs
        self.assertIn("PREGUNTA DEL HERMANO:", args['contents'])
        self.servicio.client.models.generate_content.assert_called_once()



    def test_pregunta_muy_larga(self):
        """
        Test: Pregunta muy larga
        
        Given: Una pregunta que contiene miles de caracteres.
        When: Se construye el prompt.
        Then: Se verifica que la pregunta completa se concatena correctamente en el prompt sin truncamientos previos a la llamada de la IA.
        """
        pregunta_extensa = "Pregunta " * 2000
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value="Contexto corto")

        self.servicio.preguntar_a_comunicados(pregunta_extensa)

        args = self.servicio.client.models.generate_content.call_args.kwargs
        self.assertIn(pregunta_extensa, args['contents'])



    def test_contexto_muy_largo(self):
        """
        Test: Contexto muy largo
        
        Given: Un contexto recuperado que excede el tamaño habitual (muchos comunicados o muy extensos).
        When: Se inserta el contexto en el prompt estricto.
        Then: El prompt debe contener la totalidad del contexto proporcionado por el servicio de recuperación semántica.
        """
        contexto_gigante = "COMUNICADO DETALLADO: " * 5000
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value=contexto_gigante)

        self.servicio.preguntar_a_comunicados("¿Resumen?")

        args = self.servicio.client.models.generate_content.call_args.kwargs
        self.assertIn(contexto_gigante, args['contents'])



    def test_caracteres_especiales_en_pregunta_contexto(self):
        """
        Test: Caracteres especiales en pregunta/contexto
        
        Given: Una pregunta y un contexto con emojis, símbolos matemáticos y caracteres Unicode (ñ, á).
        When: Se genera el prompt para la IA.
        Then: El sistema debe manejar los caracteres sin errores de encoding y enviarlos íntegramente en la llamada a generate_content.
        """
        pregunta_especial = "¿Cómo va la procesión? ✝️ ✨"
        contexto_especial = "Contexto: Mañana habrá 25% de descuento en la tienda de la Ñ."
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value=contexto_especial)

        self.servicio.preguntar_a_comunicados(pregunta_especial)

        args = self.servicio.client.models.generate_content.call_args.kwargs
        self.assertIn(pregunta_especial, args['contents'])
        self.assertIn(contexto_especial, args['contents'])



    def test_verificar_bloque_comunicados_oficiales_en_prompt(self):
        """
        Test: Verificar que el prompt incluye el bloque "COMUNICADOS OFICIALES"
        
        Given: Una ejecución estándar del servicio.
        When: Se construye el prompt estricto.
        Then: Se verifica que el delimitador visual "COMUNICADOS OFICIALES:" está presente para guiar correctamente a la IA.
        """
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value="Info")

        self.servicio.preguntar_a_comunicados("test")

        args = self.servicio.client.models.generate_content.call_args.kwargs
        self.assertIn("COMUNICADOS OFICIALES:", args['contents'])



    def test_verificar_instruccion_estricta_en_prompt(self):
        """
        Test: Verificar que el prompt incluye instrucción estricta
        
        Given: El prompt definido en el servicio.
        When: Se envía la información a Gemini.
        Then: Se verifica que se incluye la orden de responder ÚNICAMENTE con la información proporcionada y la frase de fallback exacta.
        """
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value="Info")

        self.servicio.preguntar_a_comunicados("test")

        args = self.servicio.client.models.generate_content.call_args.kwargs
        prompt = args['contents']
        self.assertIn("responde EXACTAMENTE: \"Lo siento, no encuentro información", prompt)
        self.assertIn("ÚNICAMENTE la información proporcionada", prompt)



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



    def test_no_se_modifica_pregunta_original(self):
        """
        Test: Verificar que no se modifica la pregunta original
        
        Given: Un string que representa la pregunta del usuario.
        When: Se ejecuta todo el flujo de preguntar_a_comunicados.
        Then: La variable que contiene la pregunta original debe permanecer intacta después de la ejecución.
        """
        pregunta_original = "¿Cuál es el horario?"
        copia_pregunta = str(pregunta_original)
        self.servicio._recuperar_contexto_semantico = MagicMock(return_value="Contexto")

        self.servicio.preguntar_a_comunicados(pregunta_original)

        self.assertEqual(pregunta_original, copia_pregunta)
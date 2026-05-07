
from datetime import datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch

from api.servicios.comunicado.comunicado_rag_service import ComunicadoRAGService

class TestComunicadoRagService(TestCase):

    def setUp(self):
        self.servicio = ComunicadoRAGService()
        self.servicio.client = MagicMock()

        mock_res = MagicMock()
        mock_res.embeddings = [MagicMock(values=[0.1, 0.2])]
        self.servicio.client.models.embed_content.return_value = mock_res



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_recuperar_contexto_semantico_ordenado_por_similitud(self, mock_comunicado):
        """
        Test: Devuelve contexto con comunicados ordenados por similitud
        
        Given: Una pregunta del usuario, un mock del modelo de embeddings que devuelve un vector, comunicados mockeados en la base de datos y un cálculo de similitud predefinido.
        When: Se ejecuta la recuperación de contexto semántico.
        Then: Se verifica que se obtienen los embeddings, se filtran los comunicados, se calcula su similitud, y se retorna un string formateado con los 3 comunicados más similares en orden descendente.
        """
        servicio = ComunicadoRAGService()
        servicio.client = MagicMock()

        mock_embedding_result = MagicMock()
        mock_embedding_value = MagicMock()
        mock_embedding_value.values = [0.1, 0.2, 0.3]
        mock_embedding_result.embeddings = [mock_embedding_value]
        servicio.client.models.embed_content.return_value = mock_embedding_result

        com1 = MagicMock(titulo="Com 1", contenido="Info 1", fecha_emision=datetime(2026, 5, 1), embedding=[0.1])
        com2 = MagicMock(titulo="Com 2", contenido="Info 2", fecha_emision=datetime(2026, 5, 2), embedding=[0.2])
        com3 = MagicMock(titulo="Com 3", contenido="Info 3", fecha_emision=datetime(2026, 5, 3), embedding=[0.3])
        com4 = MagicMock(titulo="Com 4", contenido="Info 4", fecha_emision=datetime(2026, 5, 4), embedding=[0.4])
        
        mock_queryset = MagicMock()
        mock_comunicado.objects.filter.return_value = mock_queryset
        mock_queryset.only.return_value = [com1, com2, com3, com4]

        servicio._calcular_similitud_coseno = MagicMock(side_effect=[0.7, 0.2, 0.9, 0.5])

        pregunta = "¿Cuáles son los comunicados más recientes?"
        resultado = servicio._recuperar_contexto_semantico(pregunta)

        servicio.client.models.embed_content.assert_called_once()
        args_llamada = servicio.client.models.embed_content.call_args.kwargs
        self.assertEqual(args_llamada['model'], 'gemini-embedding-001')
        self.assertEqual(args_llamada['contents'], pregunta)
        self.assertEqual(args_llamada['config'].task_type, "RETRIEVAL_QUERY")

        mock_comunicado.objects.filter.assert_called_once_with(embedding__isnull=False)
        mock_queryset.only.assert_called_once_with('titulo', 'contenido', 'fecha_emision', 'embedding')

        self.assertEqual(servicio._calcular_similitud_coseno.call_count, 4)

        contexto_esperado = (
            "--- COMUNICADO: Com 3 (Fecha: 03/05/2026) ---\nInfo 3\n\n"
            "--- COMUNICADO: Com 1 (Fecha: 01/05/2026) ---\nInfo 1\n\n"
            "--- COMUNICADO: Com 4 (Fecha: 04/05/2026) ---\nInfo 4\n\n"
        )
        
        self.assertEqual(resultado, contexto_esperado)



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_limita_a_los_tres_mejores_comunicados(self, mock_comunicado):
        """
        Test: Limita a los 3 mejores comunicados
        
        Given: Una lista de 5 comunicados en la base de datos.
        When: Se ejecuta la recuperación de contexto.
        Then: Se verifica que el string resultante solo contiene la información de los 3 comunicados con mayor similitud.
        """
        coms = [MagicMock(titulo=f"C{i}", contenido="...", fecha_emision=datetime.now()) for i in range(5)]
        mock_comunicado.objects.filter.return_value.only.return_value = coms

        self.servicio._calcular_similitud_coseno = MagicMock(side_effect=[0.1, 0.2, 0.3, 0.4, 0.5])

        resultado = self.servicio._recuperar_contexto_semantico("test")

        self.assertIn("C4", resultado)
        self.assertIn("C3", resultado)
        self.assertIn("C2", resultado)
        self.assertNotIn("C1", resultado)
        self.assertNotIn("C0", resultado)



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_ordena_por_similitud_descendente(self, mock_comunicado):
        """
        Test: Ordena correctamente por similitud descendente
        
        Given: Tres comunicados con diferentes grados de similitud calculada.
        When: Se genera el contexto final.
        Then: Se verifica que el comunicado con mayor similitud aparece primero en el string de retorno, independientemente del orden de base de datos.
        """
        mock_embedding_result = MagicMock()
        mock_embedding_result.embeddings = [MagicMock(values=[0.1])]
        self.servicio.client.models.embed_content.return_value = mock_embedding_result
        
        com_baja = MagicMock(titulo="Baja", contenido="...", fecha_emision=datetime.now())
        com_alta = MagicMock(titulo="Alta", contenido="...", fecha_emision=datetime.now())
        mock_comunicado.objects.filter.return_value.only.return_value = [com_baja, com_alta]

        self.servicio._calcular_similitud_coseno = MagicMock(side_effect=[0.1, 0.9])

        resultado = self.servicio._recuperar_contexto_semantico("test")

        pos_alta = resultado.find("Alta")
        pos_baja = resultado.find("Baja")
        self.assertTrue(pos_alta < pos_baja, "El comunicado con mayor similitud debería aparecer primero")



    @patch('api.servicios.comunicado.comunicado_rag_service.types')
    def test_vectoriza_correctamente_pregunta(self, mock_types):
        """
        Test: Se vectoriza correctamente la pregunta
        
        Given: Una cadena de texto con la pregunta del usuario.
        When: Se llama a la función de recuperación de contexto.
        Then: Se verifica que el cliente de modelos realiza la llamada con los parámetros correctos (modelo y tipo de tarea) y extrae el vector resultante.
        """
        pregunta = "¿Qué es la IA?"
        mock_embedding_result = MagicMock()
        mock_embedding_result.embeddings = [MagicMock(values=[0.1, 0.1, 0.1])]
        self.servicio.client.models.embed_content.return_value = mock_embedding_result

        with patch('api.servicios.comunicado.comunicado_rag_service.Comunicado') as mock_comunicado:
            mock_comunicado.objects.filter.return_value.only.return_value = []
            self.servicio._recuperar_contexto_semantico(pregunta)

        self.servicio.client.models.embed_content.assert_called_with(
            model='gemini-embedding-001',
            contents=pregunta,
            config=mock_types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )



    def test_error_al_vectorizar_pregunta(self):
        """
        Test: Error al vectorizar la pregunta
        
        Given: El cliente de modelos lanza una excepción al intentar obtener el embedding.
        When: Se ejecuta la recuperación de contexto.
        Then: Se captura la excepción, se imprime el error y se devuelve un string vacío.
        """
        self.servicio.client.models.embed_content.side_effect = Exception("API Down")

        resultado = self.servicio._recuperar_contexto_semantico("test")

        self.assertEqual(resultado, "")



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_devuelve_string_vacio_si_no_hay_comunicados(self, mock_comunicado):
        """
        Test: Devuelve string vacío si no hay comunicados
        
        Given: Una base de datos que no devuelve comunicados con embedding.
        When: Se solicita el contexto semántico.
        Then: El método debe retornar un string vacío sin errores.
        """
        mock_comunicado.objects.filter.return_value.only.return_value = []

        resultado = self.servicio._recuperar_contexto_semantico("test")

        self.assertEqual(resultado, "")



    def test_resultado_embeddings_vacio(self):
        """
        Test: Resultado de embeddings vacío o mal formado
        
        Given: Una respuesta de la API de embeddings que no contiene elementos en la lista.
        When: Se intenta acceder al primer elemento del resultado.
        Then: El servicio maneja el IndexError (o similar) mediante el bloque try/except y devuelve string vacío.
        """
        mock_res = MagicMock()
        mock_res.embeddings = []
        self.servicio.client.models.embed_content.return_value = mock_res

        resultado = self.servicio._recuperar_contexto_semantico("test")

        self.assertEqual(resultado, "")



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_construye_correctamente_string_contexto(self, mock_comunicado):
        """
        Test: Construye correctamente el string de contexto
        
        Given: Un comunicado con título, contenido y fecha específicos.
        When: Se genera el contexto.
        Then: Se verifica que el string sigue el formato exacto de separadores, saltos de línea y estructura requerida.
        """
        fecha = datetime(2026, 1, 1)
        com = MagicMock(titulo="Alerta", contenido="Cuerpo del mensaje", fecha_emision=fecha)
        mock_comunicado.objects.filter.return_value.only.return_value = [com]
        self.servicio._calcular_similitud_coseno = MagicMock(return_value=0.9)

        resultado = self.servicio._recuperar_contexto_semantico("test")

        esperado = "--- COMUNICADO: Alerta (Fecha: 01/01/2026) ---\nCuerpo del mensaje\n\n"
        self.assertEqual(resultado, esperado)
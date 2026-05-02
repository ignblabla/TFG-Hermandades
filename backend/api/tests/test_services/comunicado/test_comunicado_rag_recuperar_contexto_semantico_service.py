
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



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_obtencion_embeddings_comunicados(self, mock_comunicado):
        """
        Test: Se obtienen embeddings de comunicados correctamente
        
        Given: La base de datos con comunicados.
        When: Se ejecuta la recuperación.
        Then: Se verifica que se filtran solo los comunicados que tienen embedding y se piden solo los campos necesarios.
        """
        mock_embedding_result = MagicMock()
        mock_embedding_result.embeddings = [MagicMock(values=[0.1])]
        self.servicio.client.models.embed_content.return_value = mock_embedding_result
        
        mock_queryset = MagicMock()
        mock_comunicado.objects.filter.return_value = mock_queryset
        mock_queryset.only.return_value = []

        self.servicio._recuperar_contexto_semantico("test")

        mock_comunicado.objects.filter.assert_called_once_with(embedding__isnull=False)
        mock_queryset.only.assert_called_once_with('titulo', 'contenido', 'fecha_emision', 'embedding')



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_calcula_similitud_cada_comunicado(self, mock_comunicado):
        """
        Test: Se calcula similitud para cada comunicado
        
        Given: Una lista de comunicados recuperados de la base de datos.
        When: Se procesan los resultados para el contexto.
        Then: Se verifica que el método de cálculo de similitud se llama exactamente una vez por cada comunicado encontrado.
        """
        mock_embedding_result = MagicMock()
        mock_embedding_result.embeddings = [MagicMock(values=[0.1])]
        self.servicio.client.models.embed_content.return_value = mock_embedding_result
        
        com1 = MagicMock(embedding=[0.1])
        com2 = MagicMock(embedding=[0.2])
        mock_comunicado.objects.filter.return_value.only.return_value = [com1, com2]
        
        self.servicio._calcular_similitud_coseno = MagicMock(return_value=0.5)

        self.servicio._recuperar_contexto_semantico("test")

        self.assertEqual(self.servicio._calcular_similitud_coseno.call_count, 2)



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



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_formatea_correctamente_fecha(self, mock_comunicado):
        """
        Test: Formatea correctamente la fecha
        
        Given: Un comunicado con una fecha de emisión.
        When: Se construye el contexto.
        Then: Se verifica que se llama a strftime con el formato '%d/%m/%Y'.
        """
        com = MagicMock()
        com.fecha_emision = MagicMock(spec=datetime)
        mock_comunicado.objects.filter.return_value.only.return_value = [com]
        self.servicio._calcular_similitud_coseno = MagicMock(return_value=0.8)

        self.servicio._recuperar_contexto_semantico("test")

        com.fecha_emision.strftime.assert_called_once_with('%d/%m/%Y')



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
    def test_error_en_calcular_similitud_coseno(self, mock_comunicado):
        """
        Test: Error en _calcular_similitud_coseno
        
        Given: El método interno de cálculo de similitud falla (ej. por dimensiones incompatibles).
        When: Se itera sobre los comunicados para puntuarlos.
        Then: La ejecución se detiene por la excepción (ya que este punto no tiene un try/except interno en el código proporcionado).
        """
        mock_res = MagicMock()
        mock_res.embeddings = [MagicMock(values=[0.1])]
        self.servicio.client.models.embed_content.return_value = mock_res
        
        mock_com = MagicMock(embedding=[0.1])
        mock_comunicado.objects.filter.return_value.only.return_value = [mock_com]
        
        self.servicio._calcular_similitud_coseno = MagicMock(side_effect=ValueError("Math error"))

        with self.assertRaises(ValueError):
            self.servicio._recuperar_contexto_semantico("test")



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_error_en_queryset_comunicados(self, mock_comunicado):
        """
        Test: Error en queryset de comunicados
        
        Given: Un error de conexión o de sintaxis en la base de datos al ejecutar el filter.
        When: Se intenta recuperar los comunicados.
        Then: La excepción se propaga hacia arriba.
        """
        mock_res = MagicMock()
        mock_res.embeddings = [MagicMock(values=[0.1])]
        self.servicio.client.models.embed_content.return_value = mock_res
        
        mock_comunicado.objects.filter.side_effect = Exception("DB Connection Error")

        with self.assertRaises(Exception):
            self.servicio._recuperar_contexto_semantico("test")



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_error_en_strftime(self, mock_comunicado):
        """
        Test: Error en strftime
        
        Given: Un objeto de fecha mal formado o un error al formatear el string de fecha.
        When: Se construye el string de contexto final.
        Then: El proceso lanza la excepción correspondiente durante la concatenación de strings.
        """
        mock_res = MagicMock()
        mock_res.embeddings = [MagicMock(values=[0.1])]
        self.servicio.client.models.embed_content.return_value = mock_res
        
        com = MagicMock()
        com.fecha_emision.strftime.side_effect = AttributeError("Invalid date format")
        mock_comunicado.objects.filter.return_value.only.return_value = [com]
        self.servicio._calcular_similitud_coseno = MagicMock(return_value=0.9)

        with self.assertRaises(AttributeError):
            self.servicio._recuperar_contexto_semantico("test")



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_comunicados_con_embedding_invalido(self, mock_comunicado):
        """
        Test: Comunicados con embedding vacío o inválido
        
        Given: Comunicados que superan el filtro de base de datos pero tienen un campo embedding None o corrupto.
        When: Se intenta calcular la similitud coseno.
        Then: El sistema lanza una excepción (TypeError o similar) al procesar el valor inválido en el cálculo.
        """
        com_invalid = MagicMock(embedding=None)
        mock_comunicado.objects.filter.return_value.only.return_value = [com_invalid]
        self.servicio._calcular_similitud_coseno = MagicMock(side_effect=TypeError)

        with self.assertRaises(TypeError):
            self.servicio._recuperar_contexto_semantico("test")



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_valores_similitud_iguales_empate(self, mock_comunicado):
        """
        Test: Valores de similitud iguales (empate)
        
        Given: Dos comunicados con exactamente la misma puntuación de similitud.
        When: Se ordena la lista de resultados.
        Then: El sistema mantiene un orden estable (usualmente el orden original de la lista) y devuelve ambos en el contexto.
        """
        com1 = MagicMock(titulo="A", contenido="...", fecha_emision=datetime.now())
        com2 = MagicMock(titulo="B", contenido="...", fecha_emision=datetime.now())
        mock_comunicado.objects.filter.return_value.only.return_value = [com1, com2]

        self.servicio._calcular_similitud_coseno = MagicMock(return_value=0.85)

        resultado = self.servicio._recuperar_contexto_semantico("test")

        self.assertIn("A", resultado)
        self.assertIn("B", resultado)



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_menos_de_tres_comunicados_disponibles(self, mock_comunicado):
        """
        Test: Menos de 3 comunicados disponibles
        
        Given: La base de datos solo contiene 1 comunicado que cumple los filtros.
        When: Se intenta obtener el top 3.
        Then: El sistema no falla por índice fuera de rango y devuelve el contexto solo con el comunicado disponible.
        """
        com_unico = MagicMock(titulo="Único", contenido="Solo hay uno", fecha_emision=datetime.now())
        mock_comunicado.objects.filter.return_value.only.return_value = [com_unico]
        self.servicio._calcular_similitud_coseno = MagicMock(return_value=0.99)

        resultado = self.servicio._recuperar_contexto_semantico("test")

        self.assertIn("Único", resultado)
        self.assertEqual(resultado.count("--- COMUNICADO:"), 1)



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_texto_largo_en_contenido(self, mock_comunicado):
        """
        Test: Texto largo en contenido
        
        Given: Un comunicado con un contenido extremadamente extenso.
        When: Se construye el string de contexto.
        Then: El string se concatena correctamente conteniendo todo el texto sin truncamientos inesperados.
        """
        texto_largo = "Contenido " * 1000 
        com = MagicMock(titulo="Largo", contenido=texto_largo, fecha_emision=datetime.now())
        mock_comunicado.objects.filter.return_value.only.return_value = [com]
        self.servicio._calcular_similitud_coseno = MagicMock(return_value=0.9)

        resultado = self.servicio._recuperar_contexto_semantico("test")

        self.assertIn(texto_largo, resultado)
        self.assertTrue(len(resultado) > len(texto_largo))



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_caracteres_especiales_en_titulo_contenido(self, mock_comunicado):
        """
        Test: Caracteres especiales en título/contenido
        
        Given: Un comunicado con emojis, saltos de línea y caracteres Unicode (tildes, ñ) en el título y contenido.
        When: Se construye el string de contexto.
        Then: El sistema debe procesar y concatenar el texto correctamente sin errores de codificación.
        """
        titulo_esp = "¡Atención! 📢 Comunicado de Mañana"
        contenido_esp = "Línea 1: Contenido con tildes y eñes.\nLínea 2: Símbolos <>&%$."
        com = MagicMock(titulo=titulo_esp, contenido=contenido_esp, fecha_emision=datetime.now())
        mock_comunicado.objects.filter.return_value.only.return_value = [com]
        self.servicio._calcular_similitud_coseno = MagicMock(return_value=0.9)

        resultado = self.servicio._recuperar_contexto_semantico("pregunta")

        self.assertIn(titulo_esp, resultado)
        self.assertIn(contenido_esp, resultado)



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_verificar_llamadas_similitud_coseno(self, mock_comunicado):
        """
        Test: Verificar que _calcular_similitud_coseno se llama una vez por comunicado
        
        Given: Una lista de 3 comunicados devueltos por la base de datos.
        When: Se puntúan los resultados para el ordenamiento.
        Then: El método interno de cálculo de similitud debe invocarse exactamente una vez para cada comunicado.
        """
        coms = [MagicMock(embedding=[i]) for i in range(3)]
        mock_comunicado.objects.filter.return_value.only.return_value = coms
        self.servicio._calcular_similitud_coseno = MagicMock(return_value=0.5)

        self.servicio._recuperar_contexto_semantico("test")

        self.assertEqual(self.servicio._calcular_similitud_coseno.call_count, 3)



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_verificar_llamada_unica_embed_content(self, mock_comunicado):
        """
        Test: Verificar que embed_content se llama una sola vez
        
        Given: Una petición de recuperación de contexto.
        When: Se inicia el proceso de vectorización.
        Then: El cliente de Gemini solo debe ser invocado una vez para vectorizar la pregunta, optimizando el uso de la API.
        """
        mock_comunicado.objects.filter.return_value.only.return_value = []

        self.servicio._recuperar_contexto_semantico("pregunta de prueba")

        self.servicio.client.models.embed_content.assert_called_once()



    @patch('api.servicios.comunicado.comunicado_rag_service.Comunicado')
    def test_verificar_uso_de_only_en_queryset(self, mock_comunicado):
        """
        Test: Verificar que se usa only(...) en queryset
        
        Given: El acceso a la base de datos para recuperar comunicados.
        When: Se ejecuta la consulta.
        Then: Se verifica que se utiliza el método .only() con los campos específicos para asegurar una consulta eficiente y no traer campos innecesarios.
        """
        mock_queryset = MagicMock()
        mock_comunicado.objects.filter.return_value = mock_queryset
        mock_queryset.only.return_value = []

        self.servicio._recuperar_contexto_semantico("test")

        mock_queryset.only.assert_called_once_with('titulo', 'contenido', 'fecha_emision', 'embedding')
from unittest import TestCase
from unittest.mock import MagicMock, patch
from django.db.models import F
from django.db.models.expressions import OrderBy

from api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service import ReportesCiriosService


class TestGenerarPDFCiriosService(TestCase):

    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.Paragraph")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_titulo_default_sin_filtro(
        self, mock_filter, mock_paragraph, mock_doc_template
    ):
        """
        Test: Título por defecto cuando filtro_paso=None

        Given: Un acto válido y filtro_paso=None.
        When: Se llama a la generación del PDF.
        Then: 
            - El título generado es 'Asignación de Tramos y Cirios - {acto.nombre}'.
            - Se llama a doc.build() sin intentar crear un archivo real.
        """
        mock_acto = MagicMock()
        mock_acto.nombre = "Viernes Santo"

        mock_qs = MagicMock()
        mock_qs.filter.return_value.select_related.return_value.order_by.return_value = []
        mock_filter.return_value = mock_qs

        mock_doc_instance = MagicMock()
        mock_doc_template.return_value = mock_doc_instance

        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto, filtro_paso=None)

        self.assertGreaterEqual(len(mock_paragraph.call_args_list), 1)

        primer_texto_generado = mock_paragraph.call_args_list[0][0][0]
        
        titulo_esperado = "Asignación de Tramos y Cirios - Viernes Santo"
        self.assertEqual(primer_texto_generado, titulo_esperado)

        segundo_texto_generado = mock_paragraph.call_args_list[1][0][0]
        self.assertEqual(segundo_texto_generado, "No se han asignado cirios para estos criterios.")

        mock_doc_instance.build.assert_called_once()



    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.Paragraph")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_titulo_cristo(self, mock_filter, mock_paragraph, mock_doc_template):
        """
        Test: Rama if filtro_paso == 'CRISTO'

        Given: Un acto y filtro_paso='CRISTO'.
        When: Se genera el PDF.
        Then: El título debe incluir la mención al paso de Cristo.
        """
        mock_acto = MagicMock()
        mock_acto.nombre = "Madrugá"

        mock_qs = MagicMock()
        mock_qs.filter.return_value.filter.return_value.select_related.return_value.order_by.return_value = []
        mock_filter.return_value = mock_qs

        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto, filtro_paso='CRISTO')

        texto_generado = mock_paragraph.call_args_list[0][0][0]
        titulo_esperado = "Asignación Cirios (Cristo) - Madrugá"
        
        self.assertEqual(texto_generado, titulo_esperado)



    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.Paragraph")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_titulo_virgen(self, mock_filter, mock_paragraph, mock_doc_template):
        """
        Test: Rama elif filtro_paso == 'VIRGEN'

        Given: Un acto y filtro_paso='VIRGEN'.
        When: Se genera el PDF.
        Then: El título debe incluir la mención al paso de Virgen.
        """
        mock_acto = MagicMock()
        mock_acto.nombre = "Madrugá"

        mock_qs = MagicMock()
        mock_qs.filter.return_value.filter.return_value.select_related.return_value.order_by.return_value = []
        mock_filter.return_value = mock_qs

        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto, filtro_paso='VIRGEN')

        texto_generado = mock_paragraph.call_args_list[0][0][0]
        titulo_esperado = "Asignación Cirios (Virgen) - Madrugá"
        
        self.assertEqual(texto_generado, titulo_esperado)



    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_aplica_filtro_paso_en_queryset(self, mock_filter, mock_doc_template):
        """
        Test: Validar que se aplica el filtro tramo__paso si se recibe filtro_paso.

        Given: Un filtro_paso='CRISTO'.
        When: Se genera el PDF.
        Then: Se debe llamar a .filter(tramo__paso='CRISTO') en la cadena del queryset.
        """
        mock_acto = MagicMock()
        mock_acto.nombre = "Test"

        mock_qs_1 = MagicMock(name="QS_1_Filtro_Acto")
        mock_qs_2 = MagicMock(name="QS_2_Filtro_Insignias")
        mock_qs_3 = MagicMock(name="QS_3_Filtro_Paso")

        mock_filter.return_value = mock_qs_1

        mock_qs_1.filter.return_value = mock_qs_2

        mock_qs_2.filter.return_value = mock_qs_3

        mock_qs_3.select_related.return_value.order_by.return_value = []

        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto, filtro_paso='CRISTO')

        mock_qs_2.filter.assert_called_once_with(tramo__paso='CRISTO')



    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.Paragraph")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_sin_asignaciones_muestra_mensaje(self, mock_filter, mock_paragraph, mock_doc_template):
        """
        Test: Validar mensaje de error en el PDF cuando no hay datos.

        Given: Un QuerySet que no devuelve resultados.
        When: Se genera el PDF.
        Then:
            - Se debe añadir un párrafo con el texto 'No se han asignado cirios...'.
            - No se debe intentar crear una Table (opcional, pero recomendado).
        """
        mock_acto = MagicMock()

        mock_qs = MagicMock()
        mock_qs.filter.return_value.select_related.return_value.order_by.return_value = []
        mock_filter.return_value = mock_qs
        
        mock_doc_instance = MagicMock()
        mock_doc_template.return_value = mock_doc_instance

        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto)

        mensajes = [call[0][0] for call in mock_paragraph.call_args_list]
        
        mensaje_esperado = "No se han asignado cirios para estos criterios."
        self.assertIn(mensaje_esperado, mensajes)

        mock_doc_instance.build.assert_called_once()



    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.Table")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.TableStyle")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_con_asignaciones_crea_tabla(self, mock_filter, mock_doc_template, mock_table_style, mock_table):
        """
        Test: Validar que se crea una tabla cuando el QuerySet tiene datos.

        Given: Un QuerySet con una asignación.
        When: Se genera el PDF.
        Then:
            - Se debe instanciar la clase Table con los datos.
            - Se debe llamar a build() del documento.
        """
        mock_acto = MagicMock(nombre="Prueba Tabla")

        mock_asignacion = MagicMock()
        mock_asignacion.hermano.numero_registro = 123
        mock_asignacion.puesto.nombre = "Cirio"
        mock_asignacion.tramo.numero_orden = 1
        mock_asignacion.tramo.get_paso_display.return_value = "CRISTO"
        mock_asignacion.lado = "I"
        mock_asignacion.get_lado_display.return_value = "Izquierda"
        mock_asignacion.orden_en_tramo = 5

        mock_qs = MagicMock()

        mock_filter.return_value.filter.return_value.select_related.return_value.order_by.return_value = [mock_asignacion]

        mock_doc_instance = MagicMock()
        mock_doc_template.return_value = mock_doc_instance

        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto)

        mock_table.assert_called_once()

        args_tabla = mock_table.call_args[0][0]
        self.assertEqual(len(args_tabla), 2)
        self.assertEqual(args_tabla[1][0], "123")

        mock_doc_instance.build.assert_called_once()



    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.Table")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_numero_registro_null_muestra_sin_nr(self, mock_filter, mock_doc_template, mock_table):
        """
        Test: Validar que si el hermano no tiene número de registro, aparece 'Sin N.R.'

        Given: Una asignación donde hermano.numero_registro es None.
        When: Se genera el PDF.
        Then: La fila correspondiente en la tabla debe contener 'Sin N.R.'.
        """
        mock_acto = MagicMock(nombre="Prueba Nulo")

        mock_asignacion = MagicMock()
        mock_asignacion.hermano.numero_registro = None

        mock_asignacion.puesto = None
        mock_asignacion.tramo = None
        mock_asignacion.lado = None
        mock_asignacion.orden_en_tramo = None

        mock_filter.return_value.filter.return_value.select_related.return_value.order_by.return_value = [mock_asignacion]

        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto)

        data_enviada_a_tabla = mock_table.call_args[0][0]

        valor_registro = data_enviada_a_tabla[1][0]
        
        self.assertEqual(valor_registro, "Sin N.R.")



    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.Table")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_puesto_null_muestra_cirio(self, mock_filter, mock_doc_template, mock_table):
        """
        Test: Validar que si el puesto es None, aparece 'Cirio' por defecto.

        Given: Una asignación donde puesto es None.
        When: Se genera el PDF.
        Then: La columna 'Puesto' debe contener el texto 'Cirio'.
        """
        mock_acto = MagicMock(nombre="Prueba Puesto")
        
        mock_asignacion = MagicMock()
        mock_asignacion.hermano.numero_registro = 1
        mock_asignacion.puesto = None

        mock_asignacion.tramo = None
        mock_asignacion.lado = None
        mock_asignacion.orden_en_tramo = None

        mock_filter.return_value.filter.return_value.select_related.return_value.order_by.return_value = [mock_asignacion]

        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto)

        data_enviada = mock_table.call_args[0][0]

        valor_puesto = data_enviada[1][1]
        
        self.assertEqual(valor_puesto, "Cirio")



    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.Table")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_tramo_null_muestra_guion(self, mock_filter, mock_doc_template, mock_table):
        """
        Test: Validar que si el tramo es None, aparece '-' por defecto.

        Given: Una asignación donde tramo es None.
        When: Se genera el PDF.
        Then: La columna 'Tramo' debe contener el texto '-'.
        """
        mock_acto = MagicMock(nombre="Prueba Tramo")
        
        mock_asignacion = MagicMock()
        mock_asignacion.hermano.numero_registro = 1
        mock_asignacion.puesto.nombre = "Insignia"
        mock_asignacion.tramo = None
        
        mock_asignacion.lado = None
        mock_asignacion.orden_en_tramo = None

        mock_filter.return_value.filter.return_value.select_related.return_value.order_by.return_value = [mock_asignacion]

        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto)

        data_enviada = mock_table.call_args[0][0]

        valor_tramo = data_enviada[1][2]
        
        self.assertEqual(valor_tramo, "-")



    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.Table")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_lado_null_muestra_guion(self, mock_filter, mock_doc_template, mock_table):
        """
        Test: Validar que si el lado es None, aparece '-' por defecto.

        Given: Una asignación donde lado es None.
        When: Se genera el PDF.
        Then: La columna 'Lado' debe contener el texto '-'.
        """
        mock_acto = MagicMock(nombre="Prueba Lado")
        
        mock_asignacion = MagicMock()
        mock_asignacion.hermano.numero_registro = 1
        mock_asignacion.puesto.nombre = "Cirio"
        mock_asignacion.tramo.numero_orden = 1
        mock_asignacion.tramo.get_paso_display.return_value = "CRISTO"

        mock_asignacion.lado = None
        mock_asignacion.orden_en_tramo = 10

        mock_filter.return_value.filter.return_value.select_related.return_value.order_by.return_value = [mock_asignacion]

        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto)

        data_enviada = mock_table.call_args[0][0]

        valor_lado = data_enviada[1][3]
        
        self.assertEqual(valor_lado, "-")



    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.Table")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_orden_null_muestra_guion(self, mock_filter, mock_doc_template, mock_table):
        """
        Test: Validar que si orden_en_tramo es None, aparece '-' por defecto.

        Given: Una asignación donde orden_en_tramo es None.
        When: Se genera el PDF.
        Then: La columna 'Orden' debe contener el texto '-'.
        """
        mock_acto = MagicMock(nombre="Prueba Orden")
        
        mock_asignacion = MagicMock()
        mock_asignacion.hermano.numero_registro = 1
        mock_asignacion.puesto.nombre = "Cirio"
        mock_asignacion.tramo.numero_orden = 2
        mock_asignacion.tramo.get_paso_display.return_value = "VIRGEN"
        mock_asignacion.lado = "D"
        mock_asignacion.get_lado_display.return_value = "Derecha"

        mock_asignacion.orden_en_tramo = None

        mock_filter.return_value.filter.return_value.select_related.return_value.order_by.return_value = [mock_asignacion]

        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto)

        data_enviada = mock_table.call_args[0][0]

        valor_orden = data_enviada[1][4]
        
        self.assertEqual(valor_orden, "-")



    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_order_by_es_llamado_correctamente(self, mock_filter, mock_doc_template):
        """
        Test: Validar que se aplica el ordenamiento por número de registro (nulls last).

        Given: Un acto válido.
        When: Se genera el PDF.
        Then: Se debe llamar a .order_by() con la expresión F() configurada correctamente.
        """
        mock_acto = MagicMock(nombre="Test Orden")
        mock_qs_1 = MagicMock(name="QS_Filtro_1")
        mock_qs_2 = MagicMock(name="QS_Filtro_2")
        mock_qs_select = MagicMock(name="QS_Select_Related")
        
        mock_filter.return_value = mock_qs_1
        mock_qs_1.filter.return_value = mock_qs_2
        mock_qs_2.select_related.return_value = mock_qs_select
        mock_qs_select.order_by.return_value = []

        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto)

        args, _ = mock_qs_select.order_by.call_args
        expresion_orden = args[0]

        self.assertIsInstance(expresion_orden, OrderBy)

        self.assertEqual(expresion_orden.expression.name, 'hermano__numero_registro')

        self.assertEqual(expresion_orden.nulls_last, True)

        mock_qs_select.order_by.assert_called_once()



    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_select_related_es_llamado(self, mock_filter, mock_doc_template):
        """
        Test: Validar la optimización de la consulta mediante select_related.

        Given: Un acto válido.
        When: Se genera el PDF.
        Then: Se debe llamar a .select_related() con las relaciones necesarias.
        """
        mock_acto = MagicMock(nombre="Test Optimización")
        
        mock_qs_1 = MagicMock(name="QS_Filtro_1")
        mock_qs_2 = MagicMock(name="QS_Filtro_2")
        
        mock_filter.return_value = mock_qs_1
        mock_qs_1.filter.return_value = mock_qs_2

        mock_qs_select = MagicMock(name="QS_Select_Related")
        mock_qs_2.select_related.return_value = mock_qs_select
        mock_qs_select.order_by.return_value = []

        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto)

        mock_qs_2.select_related.assert_called_once_with('hermano', 'puesto', 'tramo')



    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.BytesIO")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_buffer_se_reposiciona(self, mock_filter, mock_doc_template, mock_bytesio):
        """
        Test: Validar que se llama a buffer.seek(0) antes de retornar.

        Given: El proceso de generación de PDF finaliza.
        When: Se va a retornar el objeto BytesIO.
        Then: Se debe haber vuelto al inicio del stream para permitir su lectura.
        """
        mock_acto = MagicMock(nombre="Test Seek")

        mock_buffer_instance = MagicMock()
        mock_bytesio.return_value = mock_buffer_instance

        mock_filter.return_value.filter.return_value.select_related.return_value.order_by.return_value = []

        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto)

        mock_buffer_instance.seek.assert_called_once_with(0)



    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_doc_build_es_ejecutado(self, mock_filter, mock_doc_template):
        """
        Test: Validar que se llama a doc.build() para finalizar el PDF.

        Given: Un acto válido.
        When: Se genera el PDF.
        Then: El objeto SimpleDocTemplate debe llamar a su método build.
        """
        mock_acto = MagicMock(nombre="Test Build")

        mock_doc_instance = MagicMock()
        mock_doc_template.return_value = mock_doc_instance

        mock_filter.return_value.filter.return_value.select_related.return_value.order_by.return_value = []

        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto)

        mock_doc_instance.build.assert_called_once()

        args, _ = mock_doc_instance.build.call_args
        self.assertIsInstance(args[0], list)
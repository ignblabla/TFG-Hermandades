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
        Then: El título generado es 'Asignación de Tramos y Cirios - {acto.nombre}'.
        """
        mock_acto = MagicMock()
        mock_acto.nombre = "Viernes Santo"

        mock_qs = MagicMock()
        mock_qs.filter.return_value.select_related.return_value.order_by.return_value = []
        mock_filter.return_value = mock_qs

        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto, filtro_paso=None)

        primer_texto_generado = mock_paragraph.call_args_list[0][0][0]
        titulo_esperado = "Asignación de Tramos y Cirios - Viernes Santo"
        
        self.assertEqual(primer_texto_generado, titulo_esperado)

    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.Paragraph")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_aplica_filtro_paso_y_cambia_titulo_segun_paso(self, mock_filter, mock_paragraph, mock_doc_template):
        """
        Test: Aplicación de filtro por paso y cambio de título (Cristo y Virgen)

        Given: Un acto y diferentes valores para filtro_paso ('CRISTO' y 'VIRGEN').
        When: Se genera el PDF para cada paso.
        Then: 
            - Se aplica el filtro al queryset con tramo__paso correspondiente.
            - El título debe incluir la mención específica al paso evaluado.
        """
        mock_acto = MagicMock()
        mock_acto.nombre = "Madrugá"

        casos = [
            ('CRISTO', "Asignación Cirios (Cristo) - Madrugá"),
            ('VIRGEN', "Asignación Cirios (Virgen) - Madrugá")
        ]

        for paso, titulo_esperado in casos:
            with self.subTest(paso=paso):
                # Reseteamos los mocks para cada iteración del subtest
                mock_filter.reset_mock()
                mock_paragraph.reset_mock()

                mock_qs_1 = MagicMock()
                mock_qs_2 = MagicMock()
                mock_qs_3 = MagicMock()

                mock_filter.return_value = mock_qs_1
                mock_qs_1.filter.return_value = mock_qs_2
                mock_qs_2.filter.return_value = mock_qs_3
                mock_qs_3.select_related.return_value.order_by.return_value = []

                ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto, filtro_paso=paso)

                mock_qs_2.filter.assert_called_once_with(tramo__paso=paso)

                texto_generado = mock_paragraph.call_args_list[0][0][0]
                self.assertEqual(texto_generado, titulo_esperado)

    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.Paragraph")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_sin_asignaciones_muestra_mensaje(self, mock_filter, mock_paragraph, mock_doc_template):
        """
        Test: Validar mensaje de error en el PDF cuando no hay datos

        Given: Un QuerySet que no devuelve resultados.
        When: Se genera el PDF.
        Then: Se debe añadir un párrafo con el texto indicando que no hay cirios asignados.
        """
        mock_acto = MagicMock()

        mock_qs = MagicMock()
        mock_qs.filter.return_value.select_related.return_value.order_by.return_value = []
        mock_filter.return_value = mock_qs
        
        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto)

        mensajes = [call[0][0] for call in mock_paragraph.call_args_list]
        mensaje_esperado = "No se han asignado cirios para estos criterios."
        
        self.assertIn(mensaje_esperado, mensajes)

    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.Table")
    @patch("api.servicios.solicitud_cirio.ejecucion_automatica_cirio_service.SimpleDocTemplate")
    @patch("api.models.PapeletaSitio.objects.filter")
    def test_mapeo_de_datos_en_tabla_incluyendo_valores_nulos(self, mock_filter, mock_doc_template, mock_table):
        """
        Test: Validar la generación de filas de la tabla con datos reales y defaults (nulos)

        Given: Un QuerySet que devuelve dos asignaciones (una completa, otra con campos nulos).
        When: Se genera el PDF.
        Then: 
            - Se crea la tabla con los datos correspondientes.
            - Los valores nulos se formatean correctamente a sus defaults ('Sin N.R.', 'Cirio', '-').
        """
        mock_acto = MagicMock(nombre="Prueba Datos")

        asignacion_completa = MagicMock()
        asignacion_completa.hermano.numero_registro = 123
        asignacion_completa.puesto.nombre = "Insignia"
        asignacion_completa.tramo.numero_orden = 1
        asignacion_completa.tramo.get_paso_display.return_value = "CRISTO"
        asignacion_completa.lado = "I"
        asignacion_completa.get_lado_display.return_value = "Izquierda"
        asignacion_completa.orden_en_tramo = 5

        asignacion_vacia = MagicMock()
        asignacion_vacia.hermano.numero_registro = None
        asignacion_vacia.puesto = None
        asignacion_vacia.tramo = None
        asignacion_vacia.lado = None
        asignacion_vacia.orden_en_tramo = None

        mock_filter.return_value.filter.return_value.select_related.return_value.order_by.return_value = [
            asignacion_completa, 
            asignacion_vacia
        ]

        ReportesCiriosService.generar_pdf_cirios_asignados(mock_acto)

        args_tabla = mock_table.call_args[0][0]
        
        fila_completa = args_tabla[1]
        self.assertEqual(fila_completa, ["123", "Insignia", "1º - CRISTO", "Izquierda", "5"])

        fila_vacia = args_tabla[2]
        self.assertEqual(fila_vacia, ["Sin N.R.", "Cirio", "-", "-", "-"])
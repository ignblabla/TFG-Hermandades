from io import BytesIO
from unittest import TestCase
from unittest.mock import MagicMock, patch

from api.models import Acto
from api.servicios.solicitud_insignia.solicitud_insignia_service import SolicitudInsigniaService


class TestGenerarPdfTodasInsignias(TestCase):

    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Paragraph')
    @patch('api.models.Puesto.objects.filter')
    def test_genera_tabla_cuando_hay_puestos(self, mock_filter, mock_paragraph, mock_table, mock_doc):
        """
        Test: Genera tabla cuando hay puestos

        Given: Un acto con al menos un puesto configurado como insignia en el queryset.
        When: Se genera el catálogo de todas las insignias.
        Then: Se debe instanciar el objeto Table y llamar al método build del documento para generar el PDF.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock()
        mock_acto.nombre = "Acto Principal"

        mock_doc_instance = mock_doc.return_value

        puesto_mock = MagicMock(
            nombre="Senatus",
            cortejo_cristo=True,
            numero_maximo_asignaciones=3
        )

        mock_filter.return_value.order_by.return_value = [puesto_mock]

        service.generar_pdf_todas_insignias(mock_acto)

        mock_table.assert_called_once()
        mock_doc_instance.build.assert_called_once()



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Paragraph')
    @patch('api.models.Puesto.objects.filter')
    def test_transformacion_correcta_de_datos(self, mock_filter, mock_paragraph, mock_table, mock_doc):
        """
        Test: Transformación correcta de datos

        Given: Un puesto con nombre "Varal", cortejo de cristo y 5 asignaciones.
        When: Se genera el catálogo de insignias.
        Then: La fila generada en la tabla debe ser ["Varal", "Paso de Cristo", "5"].
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock()

        puesto_mock = MagicMock()
        puesto_mock.nombre = "Varal"
        puesto_mock.cortejo_cristo = True
        puesto_mock.numero_maximo_asignaciones = 5

        mock_filter.return_value.order_by.return_value = [puesto_mock]

        service.generar_pdf_todas_insignias(mock_acto)

        data_enviada = mock_table.call_args[0][0]

        fila_esperada = ["Varal", "Paso de Cristo", "5"]
        self.assertEqual(data_enviada[1], fila_esperada)



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Paragraph')
    @patch('api.models.Puesto.objects.filter')
    def test_conversion_cortejo_virgen_correcta(self, mock_filter, mock_paragraph, mock_table, mock_doc):
        """
        Test: Conversión Virgen

        Given: Un puesto configurado con cortejo_cristo = False.
        When: Se genera el catálogo de insignias.
        Then: El texto del cortejo en la fila correspondiente debe ser "Paso de Virgen".
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock()

        puesto_virgen = MagicMock()
        puesto_virgen.nombre = "Manto"
        puesto_virgen.cortejo_cristo = False
        puesto_virgen.numero_maximo_asignaciones = 1

        mock_filter.return_value.order_by.return_value = [puesto_virgen]

        service.generar_pdf_todas_insignias(mock_acto)

        data_enviada = mock_table.call_args[0][0]

        columna_cortejo = data_enviada[1][1]
        self.assertEqual(columna_cortejo, "Paso de Virgen")



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Paragraph')
    @patch('api.models.Puesto.objects.filter')
    def test_sin_datos_muestra_mensaje_alternativo(self, mock_filter, mock_paragraph, mock_table, mock_doc):
        """
        Test: Sin datos → mensaje alternativo

        Given: Un acto que no tiene puestos configurados como insignia (queryset vacío).
        When: Se genera el catálogo de insignias.
        Then: No se debe crear la tabla y se debe añadir un párrafo con el mensaje "No hay insignias configuradas para este acto.".
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock()

        mock_filter.return_value.order_by.return_value = []

        service.generar_pdf_todas_insignias(mock_acto)

        mock_table.assert_not_called()

        mensajes_enviados = [call.args[0] for call in mock_paragraph.call_args_list]
        self.assertIn("No hay insignias configuradas para este acto.", mensajes_enviados)



    @patch('api.models.Puesto.objects.filter')
    def test_error_en_queryset_se_propaga(self, mock_filter):
        """
        Test: Error en queryset

        Given: Una falla en la base de datos al intentar filtrar los puestos.
        When: Se llama al método de generación de PDF.
        Then: La excepción lanzada por el ORM debe propagarse hacia arriba sin ser capturada silenciosamente.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock()

        mock_filter.side_effect = Exception("Error de conexión a BD")

        with self.assertRaises(Exception) as context:
            service.generar_pdf_todas_insignias(mock_acto)
        
        self.assertEqual(str(context.exception), "Error de conexión a BD")



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Paragraph')
    @patch('api.models.Puesto.objects.filter')
    def test_cupo_cero_se_renderiza_correctamente(self, mock_filter, mock_paragraph, mock_table, mock_doc):
        """
        Test: Cupo = 0

        Given: Un puesto configurado con 0 asignaciones máximas.
        When: Se genera el catálogo de insignias.
        Then: El valor en la columna "Cupo Total" debe ser el string "0" y no omitirse.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock()
        
        puesto_mock = MagicMock(
            nombre="Insignia Vacía", 
            cortejo_cristo=True, 
            numero_maximo_asignaciones=0
        )
        mock_filter.return_value.order_by.return_value = [puesto_mock]

        service.generar_pdf_todas_insignias(mock_acto)

        data_enviada = mock_table.call_args[0][0]

        self.assertEqual(data_enviada[1][2], "0")



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Paragraph')
    @patch('api.models.Puesto.objects.filter')
    def test_orden_aplicado_correctamente(self, mock_filter, mock_paragraph, mock_doc):
        """
        Test: Orden aplicado correctamente

        Given: Una solicitud de generación de PDF.
        When: Se consulta la base de datos para obtener los puestos.
        Then: Se debe llamar a order_by con los criterios '-cortejo_cristo' (Cristo primero) y 'nombre'.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock()

        mock_order_by = mock_filter.return_value.order_by
        mock_order_by.return_value = []

        service.generar_pdf_todas_insignias(mock_acto)

        mock_order_by.assert_called_once_with('-cortejo_cristo', 'nombre')



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Paragraph')
    @patch('api.models.Puesto.objects.filter')
    def test_titulo_correcto(self, mock_filter, mock_paragraph, mock_doc):
        """
        Test: Título correcto

        Given: Un acto con el nombre "Salida Procesional 2026".
        When: Se genera el catálogo de insignias.
        Then: El primer párrafo creado debe contener el texto "Catálogo de Insignias - Salida Procesional 2026".
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock()
        mock_acto.nombre = "Salida Procesional 2026"

        mock_filter.return_value.order_by.return_value = []

        service.generar_pdf_todas_insignias(mock_acto)

        llamada_titulo = mock_paragraph.call_args_list[0]
        texto_titulo = llamada_titulo.args[0]
        
        self.assertEqual(texto_titulo, "Catálogo de Insignias - Salida Procesional 2026")
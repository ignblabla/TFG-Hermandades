from io import BytesIO
from unittest import TestCase
from unittest.mock import MagicMock, patch

from api.models import Acto
from api.servicios.solicitud_insignia.solicitud_insignia_service import SolicitudInsigniaService


class TestGenerarPdfTodasInsignias(TestCase):

    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Paragraph')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_todas_insignias_flujo_completo_con_datos(self, mock_filter, mock_table, mock_paragraph, mock_doc):
        """
        Test: Catálogo generado correctamente con datos

        Given: Un acto válido y puestos de insignias configurados (Cristo y Virgen, incluyendo cupo 0).
        When: Se genera el catálogo de todas las insignias.
        Then: 
            - El título contiene el nombre del acto.
            - Los booleanos de cortejo se traducen correctamente a texto ("Paso de Cristo" / "Paso de Virgen").
            - Los cupos numéricos se convierten a string (incluso el 0).
            - Se genera la tabla estructurada y se construye el documento.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock()
        mock_acto.nombre = "Salida Procesional 2026"

        p_cristo = MagicMock(nombre="Senatus", cortejo_cristo=True, numero_maximo_asignaciones=3)
        p_virgen = MagicMock(nombre="Manto", cortejo_cristo=False, numero_maximo_asignaciones=1)
        p_vacio = MagicMock(nombre="Insignia Vacía", cortejo_cristo=True, numero_maximo_asignaciones=0)

        mock_filter.return_value.order_by.return_value = [p_cristo, p_virgen, p_vacio]

        service.generar_pdf_todas_insignias(mock_acto)

        # Verificación del Título
        args_titulo = mock_paragraph.call_args_list[0][0]
        self.assertEqual(args_titulo[0], "Catálogo de Insignias - Salida Procesional 2026")

        # Verificación de datos de la Tabla
        mock_table.assert_called_once()
        data_enviada = mock_table.call_args[0][0]
        
        self.assertEqual(len(data_enviada), 4)
        self.assertEqual(data_enviada[0], ["Puesto / Insignia", "Cortejo", "Cupo Total"])
        self.assertEqual(data_enviada[1], ["Senatus", "Paso de Cristo", "3"])
        self.assertEqual(data_enviada[2], ["Manto", "Paso de Virgen", "1"])
        self.assertEqual(data_enviada[3], ["Insignia Vacía", "Paso de Cristo", "0"])

        mock_doc.return_value.build.assert_called_once()


    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Paragraph')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_todas_insignias_sin_datos_muestra_mensaje(self, mock_filter, mock_table, mock_paragraph, mock_doc):
        """
        Test: Sin datos → mensaje alternativo

        Given: Un acto que no tiene puestos configurados como insignia (queryset vacío).
        When: Se genera el catálogo de insignias.
        Then: 
            - No se debe instanciar la clase Table.
            - Se debe añadir un párrafo con el mensaje indicando que no hay insignias configuradas.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock()
        mock_acto.nombre = "Acto Vacío"

        mock_filter.return_value.order_by.return_value = []

        service.generar_pdf_todas_insignias(mock_acto)

        mock_table.assert_not_called()

        args_aviso = mock_paragraph.call_args_list[1][0]
        self.assertEqual(args_aviso[0], "No hay insignias configuradas para este acto.")
        
        mock_doc.return_value.build.assert_called_once()


    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_todas_insignias_error_en_queryset_se_propaga(self, mock_filter):
        """
        Test: Error en queryset

        Given: Una falla en la base de datos al intentar filtrar los puestos.
        When: Se llama al método de generación de PDF.
        Then: La excepción lanzada por el ORM debe propagarse hacia arriba sin ser capturada.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock()

        mock_filter.side_effect = Exception("Error de conexión a BD")

        with self.assertRaises(Exception) as context:
            service.generar_pdf_todas_insignias(mock_acto)
        
        self.assertEqual(str(context.exception), "Error de conexión a BD")
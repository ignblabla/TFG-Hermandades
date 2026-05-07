from unittest import TestCase
from unittest.mock import MagicMock, patch

from django.db import DatabaseError

from api.models import Acto
from api.servicios.solicitud_insignia.solicitud_insignia_service import SolicitudInsigniaService


class TestGenerarPDFAsignados(TestCase):

    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Paragraph')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_asignados_construye_tabla_con_datos(self, mock_filter, mock_table, mock_paragraph, mock_doc):
        """
        Test: PDF generado con asignaciones

        Given: Un acto con nombre y dos papeletas asignadas válidas.
        When: Se llama a generar_pdf_asignados.
        Then: 
            - El título del documento contiene el nombre del acto.
            - Se filtran papeletas con es_solicitud_insignia=True y puesto asignado.
            - Se construye una tabla con el encabezado y los datos esperados.
            - Se llama al método build del documento.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)
        mock_acto.nombre = "Salida Procesional 2026"

        mock_papeleta_1 = MagicMock(hermano=MagicMock(numero_registro=50), puesto=MagicMock(nombre="Cruz de Guía"))
        mock_papeleta_2 = MagicMock(hermano=MagicMock(numero_registro=120), puesto=MagicMock(nombre="Senatus"))
        
        mock_query = mock_filter.return_value.select_related.return_value.order_by.return_value
        mock_query.__iter__.return_value = [mock_papeleta_1, mock_papeleta_2]

        service.generar_pdf_asignados(mock_acto)

        args_titulo, _ = mock_paragraph.call_args_list[0]
        self.assertIn("Salida Procesional 2026", args_titulo[0])

        mock_filter.assert_called_once_with(
            acto=mock_acto,
            es_solicitud_insignia=True,
            puesto__isnull=False
        )

        args, _ = mock_table.call_args
        data_enviada = args[0]
        self.assertEqual(len(data_enviada), 3)
        self.assertEqual(data_enviada[0], ["Nº Registro", "Insignia Asignada"])
        self.assertEqual(data_enviada[1], ["50", "Cruz de Guía"])
        self.assertEqual(data_enviada[2], ["120", "Senatus"])

        mock_doc.return_value.build.assert_called_once()


    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_maneja_mezcla_de_registros_validos_y_nulos(self, mock_filter, mock_table):
        """
        Test: Mezcla de datos válidos e inválidos

        Given: Una lista con un hermano con Nº registro (10) y otro sin él (None).
        When: Se genera el PDF.
        Then: La tabla debe contener el string "10" en la primera fila de datos 
            y "Sin N.R." en la segunda fila, demostrando el formato correcto.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        p1 = MagicMock(hermano=MagicMock(numero_registro=10), puesto=MagicMock(nombre="Insignia A"))
        p2 = MagicMock(hermano=MagicMock(numero_registro=None), puesto=MagicMock(nombre="Insignia B"))
        
        mock_query = mock_filter.return_value.select_related.return_value.order_by.return_value
        mock_query.__iter__.return_value = [p1, p2]

        service.generar_pdf_asignados(mock_acto)

        data_enviada = mock_table.call_args[0][0]
        self.assertEqual(data_enviada[1][0], "10")
        self.assertEqual(data_enviada[2][0], "Sin N.R.")


    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Paragraph')
    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_asignados_muestra_mensaje_cuando_no_hay_asignaciones(self, mock_filter, mock_paragraph, mock_doc):
        """
        Test: Rama sin datos → mensaje alternativo

        Given: Un acto sin ninguna insignia asignada en la base de datos.
        When: Se llama a generar_pdf_asignados.
        Then: 
            - Se añade al PDF el párrafo indicando que no hay asignaciones.
            - El documento se construye con este mensaje.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)
        mock_acto.nombre = "Acto Vacío"

        mock_query = mock_filter.return_value.select_related.return_value.order_by.return_value
        mock_query.__iter__.return_value = []

        service.generar_pdf_asignados(mock_acto)

        args_segundo_parrafo = mock_paragraph.call_args_list[1][0]
        texto_error = args_segundo_parrafo[0]

        self.assertEqual(texto_error, "No se han asignado insignias en este reparto.")
        mock_doc.return_value.build.assert_called_once()


    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_asignados_propaga_error_de_base_de_datos(self, mock_filter):
        """
        Test: Error en queryset

        Given: Un error inesperado en la base de datos durante el filtrado.
        When: Se llama a generar_pdf_asignados.
        Then: El servicio debe propagar la excepción original (DatabaseError) 
            sin capturarla ni silenciarla.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        mock_filter.side_effect = DatabaseError("Error de conexión con la BD")

        with self.assertRaises(DatabaseError) as cm:
            service.generar_pdf_asignados(mock_acto)
        
        self.assertEqual(str(cm.exception), "Error de conexión con la BD")
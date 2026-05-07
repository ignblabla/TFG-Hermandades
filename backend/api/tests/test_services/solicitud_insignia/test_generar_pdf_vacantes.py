from unittest import TestCase
from unittest.mock import MagicMock, patch

from django.db import DatabaseError

from api.models import Acto
from api.servicios.solicitud_insignia.solicitud_insignia_service import SolicitudInsigniaService


class TestGenerarPDFVacantes(TestCase):

    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_con_puestos_disponibles(self, mock_filter, mock_table, mock_doc):
        """
        Test: Genera PDF con puestos vacantes

        Given: Un acto con dos puestos (Cristo y Virgen) que tienen plazas disponibles.
        When: Se llama a generar_pdf_vacantes.
        Then: 
            - Se calcula correctamente el número de vacantes (max - ocupacion).
            - Se traduce el booleano 'cortejo_cristo' a "Paso de Cristo" o "Paso de Virgen".
            - Se añaden los datos a la tabla respetando el formato (strings).
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)
        mock_acto.nombre = "Semana Santa 2026"

        p_cristo = MagicMock(nombre="Vara", cortejo_cristo=True, numero_maximo_asignaciones=5, ocupacion_real=2)
        p_virgen = MagicMock(nombre="Bocina", cortejo_cristo=False, numero_maximo_asignaciones=3, ocupacion_real=1)

        mock_query = mock_filter.return_value.annotate.return_value.order_by.return_value
        mock_query.__iter__.return_value = [p_cristo, p_virgen]

        service.generar_pdf_vacantes(mock_acto)

        args, _ = mock_table.call_args
        data_enviada = args[0]
        
        self.assertEqual(len(data_enviada), 3)
        self.assertEqual(data_enviada[0], ["Puesto / Insignia", "Cortejo", "Plazas Vacantes"])
        self.assertEqual(data_enviada[1], ["Vara", "Paso de Cristo", "3"])
        self.assertEqual(data_enviada[2], ["Bocina", "Paso de Virgen", "2"])
        
        mock_doc.return_value.build.assert_called_once()


    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_excluye_puestos_sin_vacantes(self, mock_filter, mock_table):
        """
        Test: Excluye puestos llenos o sobreasignados

        Given: Puestos donde numero_maximo_asignaciones es igual o menor a ocupacion_real 
            (vacantes = 0 y vacantes = -1).
        When: Se genera el PDF.
        Then: Ninguno de estos puestos se añade a la matriz de datos, 
            y al no haber vacantes, no se instancia la tabla.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        puesto_exacto = MagicMock(numero_maximo_asignaciones=2, ocupacion_real=2)
        puesto_sobreasignado = MagicMock(numero_maximo_asignaciones=2, ocupacion_real=3)
        
        mock_query = mock_filter.return_value.annotate.return_value.order_by.return_value
        mock_query.__iter__.return_value = [puesto_exacto, puesto_sobreasignado]

        service.generar_pdf_vacantes(mock_acto)

        mock_table.assert_not_called()


    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Paragraph')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_muestra_mensaje_cuando_todo_esta_asignado(self, mock_filter, mock_paragraph, mock_doc):
        """
        Test: Rama sin vacantes → mensaje alternativo

        Given: Un escenario donde no hay puestos con vacantes > 0.
        When: Se llama a generar_pdf_vacantes.
        Then: 
            - Se añade al PDF el mensaje: "Todas las insignias han sido asignadas. No hay vacantes."
            - El documento se construye con este mensaje.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)
        mock_acto.nombre = "Acto Completo"

        mock_query = mock_filter.return_value.annotate.return_value.order_by.return_value
        mock_query.__iter__.return_value = []

        service.generar_pdf_vacantes(mock_acto)

        args_aviso = mock_paragraph.call_args_list[1][0]
        self.assertEqual(args_aviso[0], "Todas las insignias han sido asignadas. No hay vacantes.")
        
        mock_doc.return_value.build.assert_called_once()


    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_propaga_error_de_base_de_datos(self, mock_filter):
        """
        Test: Queryset falla

        Given: Un fallo de conexión o error en la base de datos durante la consulta o anotación.
        When: Se llama a generar_pdf_vacantes.
        Then: La excepción (DatabaseError) debe propagarse íntegramente hacia arriba.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        mock_filter.side_effect = DatabaseError("Fallo crítico en DB")

        with self.assertRaises(DatabaseError) as cm:
            service.generar_pdf_vacantes(mock_acto)
        
        self.assertEqual(str(cm.exception), "Fallo crítico en DB")
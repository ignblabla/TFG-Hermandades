from unittest import TestCase
from unittest.mock import MagicMock, patch

from django.db import DatabaseError

from api.models import Acto
from api.servicios.solicitud_insignia.solicitud_insignia_service import SolicitudInsigniaService


class TestGenerarPDFAsignados(TestCase):

    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_asignados_construye_tabla_con_datos(self, mock_filter, mock_table, mock_doc):
        """
        Test: PDF generado con asignaciones

        Given: Un acto con dos papeletas asignadas.
        When: Se llama a generar_pdf_asignados.
        Then: 
            - Se filtran papeletas con es_solicitud_insignia=True y puesto asignado.
            - Se construye una tabla con 3 filas (Header + 2 Datos).
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
    def test_generar_pdf_formato_numero_registro_conversion_a_string(self, mock_filter, mock_table):
        """
        Test: Formato correcto de número de registro

        Given: Una asignación donde el hermano tiene el número de registro 123 (int).
        When: Se genera el PDF de asignados.
        Then: El valor enviado a la tabla de ReportLab debe ser el string "123".
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        mock_papeleta = MagicMock()
        mock_papeleta.hermano.numero_registro = 123
        mock_papeleta.puesto.nombre = "Vara de Presidencia"

        mock_query = mock_filter.return_value.select_related.return_value.order_by.return_value
        mock_query.__iter__.return_value = [mock_papeleta]

        service.generar_pdf_asignados(mock_acto)

        args, _ = mock_table.call_args
        data_enviada = args[0]

        num_registro_pdf = data_enviada[1][0]
        
        self.assertEqual(num_registro_pdf, "123")
        self.assertIsInstance(num_registro_pdf, str, "El número de registro debe convertirse a string")



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_formato_numero_registro_cuando_es_nulo(self, mock_filter, mock_table):
        """
        Test: Número de registro vacío

        Given: Una asignación donde el hermano tiene numero_registro = None.
        When: Se genera el PDF de asignados.
        Then: 
            - El servicio debe detectar el valor nulo.
            - La celda en el PDF debe mostrar exactamente el string "Sin N.R.".
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        mock_papeleta = MagicMock()
        mock_papeleta.hermano.numero_registro = None
        mock_papeleta.puesto.nombre = "Libro de Reglas"

        mock_query = mock_filter.return_value.select_related.return_value.order_by.return_value
        mock_query.__iter__.return_value = [mock_papeleta]

        service.generar_pdf_asignados(mock_acto)

        args, _ = mock_table.call_args
        data_enviada = args[0]
        
        num_registro_pdf = data_enviada[1][0]
        self.assertEqual(num_registro_pdf, "Sin N.R.")



    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_asignados_aplica_ordenacion_correcta(self, mock_filter):
        """
        Test: Ordenación por número de registro

        Given: Un acto válido.
        When: Se genera el QuerySet de asignaciones.
        Then: Se debe llamar a order_by con la expresión de ordenación correcta.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        service.generar_pdf_asignados(mock_acto)

        mock_order_by = mock_filter.return_value.select_related.return_value.order_by
        args, kwargs = mock_order_by.call_args

        orden_obj = args[0]

        self.assertEqual(orden_obj.expression.name, 'hermano__numero_registro')

        self.assertFalse(orden_obj.descending)

        self.assertTrue(orden_obj.nulls_last)



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_asignados_instancia_tabla_con_dimensiones_correctas(self, mock_filter, mock_table):
        """
        Test: Rama con datos → crea tabla

        Given: Un QuerySet con al menos una asignación.
        When: El servicio llega a la validación 'if len(data) == 1'.
        Then: 
            - Se debe instanciar la clase Table.
            - El parámetro colWidths debe ser exactamente [150, 350].
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        mock_papeleta = MagicMock()
        mock_query = mock_filter.return_value.select_related.return_value.order_by.return_value
        mock_query.__iter__.return_value = [mock_papeleta]

        service.generar_pdf_asignados(mock_acto)

        mock_table.assert_called_once()
        _, kwargs = mock_table.call_args
        
        self.assertEqual(kwargs.get('colWidths'), [150, 350])



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Paragraph')
    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_asignados_muestra_mensaje_cuando_no_hay_asignaciones(self, mock_filter, mock_paragraph, mock_doc):
        """
        Test: Rama sin datos → mensaje alternativo

        Given: Un acto sin ninguna insignia asignada en la base de datos.
        When: Se llama a generar_pdf_asignados.
        Then: 
            - La lista 'data' solo contiene el encabezado (len == 1).
            - Se añade al PDF el párrafo: "No se han asignado insignias en este reparto."
            - No se debe instanciar la clase Table (opcional, para mayor rigor).
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



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_asignados_llama_a_build_al_finalizar(self, mock_filter, mock_doc):
        """
        Test: PDF se genera correctamente

        Given: Un acto con datos válidos.
        When: Se termina de recolectar todos los elementos (títulos y tablas).
        Then: Se debe invocar el método .build() de la instancia del documento 
            pasándole la lista de elementos.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        service.generar_pdf_asignados(mock_acto)

        instancia_doc = mock_doc.return_value
        instancia_doc.build.assert_called_once()

        args, _ = instancia_doc.build.call_args
        self.assertGreater(len(args[0]), 0, "Se debe llamar a build con elementos.")



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.BytesIO')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_resetea_puntero_del_buffer(self, mock_filter, mock_doc, mock_bytesio):
        """
        Test: Buffer se resetea correctamente

        Given: Un proceso de generación de PDF completo.
        When: El documento se ha construido (build).
        Then: El servicio debe llamar a buffer.seek(0) para permitir que el 
            receptor del PDF pueda leerlo desde el principio.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        instancia_buffer = mock_bytesio.return_value

        service.generar_pdf_asignados(mock_acto)

        instancia_buffer.seek.assert_called_once_with(0)



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



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_asignados_falla_si_reportlab_falla(self, mock_filter, mock_doc):
        """
        Test: Fallo en doc.build()

        Given: Un estado donde ReportLab no puede renderizar el documento.
        When: Se invoca doc.build(elementos).
        Then: Debe lanzarse la excepción correspondiente (ej: Exception genérica o de ReportLab).
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        instancia_doc = mock_doc.return_value
        instancia_doc.build.side_effect = Exception("Error fatal de renderizado en ReportLab")

        with self.assertRaises(Exception) as cm:
            service.generar_pdf_asignados(mock_acto)
        
        self.assertIn("Error fatal de renderizado", str(cm.exception))



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_maneja_mezcla_de_registros_validos_y_nulos(self, mock_filter, mock_table):
        """
        Test: Mezcla de datos válidos e inválidos

        Given: Una lista con un hermano con Nº registro (10) y otro sin él (None).
        When: Se genera el PDF.
        Then: La tabla debe contener "10" en la primera fila y "Sin N.R." en la segunda.
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



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_añade_multiples_filas_a_la_tabla(self, mock_filter, mock_table):
        """
        Test: Asignaciones múltiples

        Given: Una lista de 50 asignaciones en la base de datos.
        When: Se llama a generar_pdf_asignados.
        Then: La tabla debe construirse con 51 filas (encabezado + 50 registros).
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        papeletas = [
            MagicMock(hermano=MagicMock(numero_registro=i), puesto=MagicMock(nombre=f"Puesto {i}"))
            for i in range(50)
        ]
        
        mock_query = mock_filter.return_value.select_related.return_value.order_by.return_value
        mock_query.__iter__.return_value = papeletas

        service.generar_pdf_asignados(mock_acto)

        data_enviada = mock_table.call_args[0][0]
        self.assertEqual(len(data_enviada), 51)
        self.assertEqual(data_enviada[0], ["Nº Registro", "Insignia Asignada"])



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_garantiza_cabecera_en_tabla_con_datos(self, mock_filter, mock_table):
        """
        Test: Validación de estructura de tabla

        Given: Un acto con asignaciones.
        When: Se construye la matriz de datos para la tabla.
        Then: La primera fila (índice 0) debe ser siempre el encabezado: 
            ["Nº Registro", "Insignia Asignada"].
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        mock_papeleta = MagicMock(hermano=MagicMock(numero_registro=1), puesto=MagicMock(nombre="Vara"))
        mock_query = mock_filter.return_value.select_related.return_value.order_by.return_value
        mock_query.__iter__.return_value = [mock_papeleta]

        service.generar_pdf_asignados(mock_acto)

        data_enviada = mock_table.call_args[0][0]
        self.assertEqual(data_enviada[0], ["Nº Registro", "Insignia Asignada"])



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_aplica_estilos_visuales_a_la_tabla(self, mock_filter, mock_table):
        """
        Test: Validación de estilos

        Given: Un proceso de generación de tabla exitoso.
        When: Se instancia el objeto Table.
        Then: Se debe llamar al método setStyle con una configuración que incluya 
            el color corporativo, el fondo beige y la rejilla.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)
        
        mock_papeleta = MagicMock()
        mock_query = mock_filter.return_value.select_related.return_value.order_by.return_value
        mock_query.__iter__.return_value = [mock_papeleta]

        service.generar_pdf_asignados(mock_acto)

        instancia_tabla = mock_table.return_value
        instancia_tabla.setStyle.assert_called_once()

        estilo_aplicado = instancia_tabla.setStyle.call_args[0][0]
        comandos = estilo_aplicado.getCommands()

        has_corporate_color = any(
            c[0] == 'BACKGROUND' and c[1] == (0, 0) and c[2] == (-1, 0) 
            for c in comandos
        )
        self.assertTrue(has_corporate_color, "Falta el fondo del encabezado")

        has_grid = any(c[0] == 'GRID' for c in comandos)
        self.assertTrue(has_grid, "Falta la configuración de la rejilla (GRID)")

        has_beige = any(
            c[0] == 'BACKGROUND' and c[1] == (0, 1) and c[2] == (-1, -1)
            for c in comandos
        )
        self.assertTrue(has_beige, "Falta el fondo beige para las filas de datos")



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_con_gran_volumen_de_datos(self, mock_filter, mock_table):
        """
        Test: PDF con gran volumen de datos

        Given: Un acto con 500 papeletas asignadas.
        When: Se genera el PDF.
        Then: 
            - El bucle debe procesar las 500 entradas.
            - La tabla enviada a ReportLab debe tener 501 filas (header + 500 datos).
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        papeletas_masivas = [
            MagicMock(hermano=MagicMock(numero_registro=i), puesto=MagicMock(nombre=f"Insignia {i}"))
            for i in range(500)
        ]
        
        mock_query = mock_filter.return_value.select_related.return_value.order_by.return_value
        mock_query.__iter__.return_value = papeletas_masivas

        service.generar_pdf_asignados(mock_acto)

        args, _ = mock_table.call_args
        data_enviada = args[0]
        self.assertEqual(len(data_enviada), 501)



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Paragraph')
    @patch('api.models.PapeletaSitio.objects.filter')
    def test_generar_pdf_utiliza_el_nombre_del_acto_en_el_titulo(self, mock_filter, mock_paragraph):
        """
        Test: Dependencia de acto.nombre

        Given: Un acto llamado "Vía Crucis Oficial 2026".
        When: Se genera el PDF.
        Then: El primer párrafo creado (el título) debe contener el nombre exacto del acto.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)
        mock_acto.nombre = "Vía Crucis Oficial 2026"

        mock_query = mock_filter.return_value.select_related.return_value.order_by.return_value
        mock_query.__iter__.return_value = []

        service.generar_pdf_asignados(mock_acto)

        args_titulo, _ = mock_paragraph.call_args_list[0]
        texto_titulo = args_titulo[0]
        
        self.assertIn("Vía Crucis Oficial 2026", texto_titulo)
        self.assertIn("Asignación de Insignias", texto_titulo)
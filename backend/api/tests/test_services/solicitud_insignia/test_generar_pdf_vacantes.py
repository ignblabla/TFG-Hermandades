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

        Given: Un acto con un puesto que tiene 5 plazas máximas y 2 ocupadas.
        When: Se llama a generar_pdf_vacantes.
        Then: 
            - Se calcula correctamente que hay 3 vacantes.
            - Se añade la fila ["Vara", "Paso de Cristo", "3"] a la tabla.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)
        mock_acto.nombre = "Semana Santa 2026"

        mock_puesto = MagicMock()
        mock_puesto.nombre = "Vara"
        mock_puesto.cortejo_cristo = True
        mock_puesto.numero_maximo_asignaciones = 5
        mock_puesto.ocupacion_real = 2

        mock_query = mock_filter.return_value.annotate.return_value.order_by.return_value
        mock_query.__iter__.return_value = [mock_puesto]

        service.generar_pdf_vacantes(mock_acto)

        args, _ = mock_table.call_args
        data_enviada = args[0]
        
        self.assertEqual(len(data_enviada), 2)
        self.assertEqual(data_enviada[1], ["Vara", "Paso de Cristo", "3"])
        mock_doc.return_value.build.assert_called_once()



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_excluye_puestos_llenos(self, mock_filter, mock_table):
        """
        Test: Excluye puestos sin vacantes

        Given: Un puesto donde numero_maximo_asignaciones (2) es igual a ocupacion_real (2).
        When: Se genera el PDF.
        Then: La lista 'data' solo debe contener el encabezado (longitud 1).
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        mock_puesto_lleno = MagicMock(
            nombre="Bocina",
            numero_maximo_asignaciones=2,
            ocupacion_real=2
        )
        
        mock_query = mock_filter.return_value.annotate.return_value.order_by.return_value
        mock_query.__iter__.return_value = [mock_puesto_lleno]

        service.generar_pdf_vacantes(mock_acto)

        mock_table.assert_not_called()



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_calcula_y_formatea_valor_correctamente(self, mock_filter, mock_table):
        """
        Test: Cálculo correcto de vacantes

        Given: Un puesto con 10 plazas máximas y 4 ocupadas.
        When: Se procesa el puesto en el bucle.
        Then: 
            - Se calcula que vacantes = 6.
            - El tercer elemento de la fila de datos debe ser el string "6".
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        mock_puesto = MagicMock(
            nombre="Bocina",
            numero_maximo_asignaciones=10,
            ocupacion_real=4,
            cortejo_cristo=True
        )
        
        mock_query = mock_filter.return_value.annotate.return_value.order_by.return_value
        mock_query.__iter__.return_value = [mock_puesto]

        service.generar_pdf_vacantes(mock_acto)

        data_enviada = mock_table.call_args[0][0]

        self.assertEqual(data_enviada[1][2], "6")
        self.assertIsInstance(data_enviada[1][2], str, "El valor de vacantes debe ser un string para ReportLab")



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_traduce_booleano_a_nombre_de_paso(self, mock_filter, mock_table):
        """
        Test: Traducción de cortejo correcto

        Given: Dos puestos, uno de Cristo (True) y otro de Virgen (False).
        When: Se genera el PDF.
        Then: 
            - El de Cristo debe mostrar "Paso de Cristo".
            - El de Virgen debe mostrar "Paso de Virgen".
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)
        
        p_cristo = MagicMock(nombre="Vara Cristo", cortejo_cristo=True, numero_maximo_asignaciones=1, ocupacion_real=0)
        p_virgen = MagicMock(nombre="Vara Virgen", cortejo_cristo=False, numero_maximo_asignaciones=1, ocupacion_real=0)
        
        mock_query = mock_filter.return_value.annotate.return_value.order_by.return_value
        mock_query.__iter__.return_value = [p_cristo, p_virgen]

        service.generar_pdf_vacantes(mock_acto)

        data_enviada = mock_table.call_args[0][0]

        self.assertEqual(data_enviada[1][1], "Paso de Cristo")
        self.assertEqual(data_enviada[2][1], "Paso de Virgen")



    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_aplica_ordenacion_jerarquica(self, mock_filter):
        """
        Test: Ordenación del queryset

        Given: Un acto válido.
        When: Se genera el listado de vacantes.
        Then: El queryset debe ordenar primero por cortejo_cristo (descendente, 
            para que Cristo salga antes que Virgen) y luego por nombre (ascendente).
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        service.generar_pdf_vacantes(mock_acto)

        mock_order_by = mock_filter.return_value.annotate.return_value.order_by
        
        args, _ = mock_order_by.call_args

        self.assertEqual(args[0], '-cortejo_cristo')
        self.assertEqual(args[1], 'nombre')



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_configura_tabla_con_dimensiones_correctas(self, mock_filter, mock_table):
        """
        Test: Rama con vacantes → genera tabla

        Given: Un puesto con vacantes disponibles.
        When: Se procesan los datos para el PDF.
        Then: 
            - Se debe instanciar la clase Table.
            - Los anchos de columna deben ser exactamente [250, 150, 100].
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        puesto = MagicMock(numero_maximo_asignaciones=1, ocupacion_real=0, cortejo_cristo=True)
        mock_query = mock_filter.return_value.annotate.return_value.order_by.return_value
        mock_query.__iter__.return_value = [puesto]

        service.generar_pdf_vacantes(mock_acto)

        mock_table.assert_called_once()
        _, kwargs = mock_table.call_args
        self.assertEqual(kwargs.get('colWidths'), [250, 150, 100])



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Paragraph')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_muestra_mensaje_cuando_todo_esta_asignado(self, mock_filter, mock_paragraph, mock_doc):
        """
        Test: Rama sin vacantes → mensaje alternativo

        Given: Un escenario donde todos los puestos tienen vacantes <= 0.
        When: Se llama a generar_pdf_vacantes.
        Then: 
            - La matriz 'data' solo contiene el header.
            - Se añade al PDF el mensaje: "Todas las insignias han sido asignadas. No hay vacantes."
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        puesto_lleno = MagicMock(numero_maximo_asignaciones=1, ocupacion_real=1)
        mock_query = mock_filter.return_value.annotate.return_value.order_by.return_value
        mock_query.__iter__.return_value = [puesto_lleno]

        service.generar_pdf_vacantes(mock_acto)

        args_aviso = mock_paragraph.call_args_list[1][0]
        self.assertEqual(args_aviso[0], "Todas las insignias han sido asignadas. No hay vacantes.")



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_mantiene_siempre_cabecera_en_la_matriz(self, mock_filter, mock_table):
        """
        Test: Header siempre presente

        Given: Un acto con puestos disponibles.
        When: Se genera la tabla para el PDF.
        Then: La primera posición de la lista de datos enviada a Table() 
            debe ser ["Puesto / Insignia", "Cortejo", "Plazas Vacantes"].
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        puesto = MagicMock(numero_maximo_asignaciones=5, ocupacion_real=0, cortejo_cristo=True)
        mock_query = mock_filter.return_value.annotate.return_value.order_by.return_value
        mock_query.__iter__.return_value = [puesto]

        service.generar_pdf_vacantes(mock_acto)

        args, _ = mock_table.call_args
        data_enviada = args[0]
        
        self.assertEqual(data_enviada[0], ["Puesto / Insignia", "Cortejo", "Plazas Vacantes"])



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_ejecuta_build_del_documento(self, mock_filter, mock_doc):
        """
        Test: PDF se genera correctamente

        Given: Un acto con datos listos para procesar.
        When: El servicio termina de organizar los elementos.
        Then: Se debe llamar al método build() de la instancia de SimpleDocTemplate.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        service.generar_pdf_vacantes(mock_acto)

        instancia_doc = mock_doc.return_value
        instancia_doc.build.assert_called_once()

        args, _ = instancia_doc.build.call_args
        self.assertGreater(len(args[0]), 0)



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.BytesIO')
    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_rebobina_el_buffer_antes_de_retornar(self, mock_filter, mock_doc, mock_bytesio):
        """
        Test: Buffer reset correcto

        Given: Un proceso de generación de PDF que ha terminado de escribir.
        When: Se va a retornar el objeto buffer.
        Then: Se debe llamar a buffer.seek(0) para permitir la lectura desde el inicio.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        instancia_buffer = mock_bytesio.return_value

        service.generar_pdf_vacantes(mock_acto)

        instancia_buffer.seek.assert_called_once_with(0)



    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_propaga_error_de_base_de_datos(self, mock_filter):
        """
        Test: Queryset falla

        Given: Un fallo de conexión o error de sintaxis en la base de datos.
        When: Se llama a generar_pdf_vacantes.
        Then: La excepción (DatabaseError) debe propagarse hacia arriba.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        mock_filter.side_effect = DatabaseError("Fallo crítico en DB")

        with self.assertRaises(DatabaseError) as cm:
            service.generar_pdf_vacantes(mock_acto)
        
        self.assertEqual(str(cm.exception), "Fallo crítico en DB")



    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_falla_si_la_agregacion_es_invalida(self, mock_filter):
        """
        Test: Error en annotate

        Given: Una configuración de Count o Q que genera un error en el ORM.
        When: El servicio intenta ejecutar el annotate().
        Then: Se debe capturar y propagar el error de configuración (FieldError/AttributeError).
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        mock_filter.return_value.annotate.side_effect = Exception("Campo de agregación no válido")

        with self.assertRaises(Exception) as cm:
            service.generar_pdf_vacantes(mock_acto)
        
        self.assertIn("agregación no válido", str(cm.exception))



    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_falla_si_el_puesto_no_tiene_atributos_necesarios(self, mock_filter):
        """
        Test: AttributeError en puesto

        Given: Un objeto puesto al que le falta el atributo 'numero_maximo_asignaciones'.
        When: El servicio intenta calcular las vacantes.
        Then: Debe lanzarse un AttributeError, indicando un fallo en el contrato del modelo.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        mock_puesto_invalido = MagicMock(spec=['nombre', 'ocupacion_real']) 
        
        mock_query = mock_filter.return_value.annotate.return_value.order_by.return_value
        mock_query.__iter__.return_value = [mock_puesto_invalido]

        with self.assertRaises(AttributeError):
            service.generar_pdf_vacantes(mock_acto)



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.SimpleDocTemplate')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_falla_si_reportlab_colapsa(self, mock_filter, mock_doc):
        """
        Test: Error en doc.build

        Given: Una configuración de ReportLab que falla durante la construcción.
        When: Se llama a doc.build(elementos).
        Then: La excepción debe propagarse íntegramente.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        instancia_doc = mock_doc.return_value
        instancia_doc.build.side_effect = RuntimeError("Error interno de ReportLab al renderizar")

        with self.assertRaises(RuntimeError) as cm:
            service.generar_pdf_vacantes(mock_acto)
        
        self.assertIn("Error interno de ReportLab", str(cm.exception))



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_excluye_puesto_cuando_es_cero_exacto(self, mock_filter, mock_table):
        """
        Test: vacantes = 0 exacto

        Given: Un puesto donde numero_maximo_asignaciones (5) es igual a ocupacion_real (5).
        When: Se calcula vacantes = 0.
        Then: La condición 'if vacantes > 0' debe ser False y el puesto NO debe añadirse a 'data'.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        puesto_lleno = MagicMock(
            nombre="Bocina",
            numero_maximo_asignaciones=5,
            ocupacion_real=5
        )
        
        mock_query = mock_filter.return_value.annotate.return_value.order_by.return_value
        mock_query.__iter__.return_value = [puesto_lleno]

        service.generar_pdf_vacantes(mock_acto)

        mock_table.assert_not_called()



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_excluye_puestos_con_sobreasignacion_negativa(self, mock_filter, mock_table):
        """
        Test: vacantes negativas

        Given: Un puesto con sobreasignación (Max: 2, Real: 3).
        When: Se calcula vacantes = -1.
        Then: El puesto NO debe aparecer en el PDF, ya que -1 no es > 0.
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        puesto_sobreasignado = MagicMock(
            nombre="Vara Presidencia",
            numero_maximo_asignaciones=2,
            ocupacion_real=3
        )
        
        mock_query = mock_filter.return_value.annotate.return_value.order_by.return_value
        mock_query.__iter__.return_value = [puesto_sobreasignado]

        service.generar_pdf_vacantes(mock_acto)

        mock_table.assert_not_called()



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_agrupa_y_ordena_correctamente_ambos_pasos(self, mock_filter, mock_table):
        """
        Test: mezcla de Cristo y Virgen

        Given: Cuatro puestos desordenados (2 de Cristo, 2 de Virgen).
        When: Se genera el PDF.
        Then: La tabla debe mostrar primero los de Cristo (A-Z) y luego los de Virgen (A-Z).
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        p1 = MagicMock(nombre="Bocina", cortejo_cristo=True, numero_maximo_asignaciones=1, ocupacion_real=0)
        p2 = MagicMock(nombre="Vara", cortejo_cristo=True, numero_maximo_asignaciones=1, ocupacion_real=0)
        p3 = MagicMock(nombre="Canasto", cortejo_cristo=False, numero_maximo_asignaciones=1, ocupacion_real=0)
        p4 = MagicMock(nombre="Vara", cortejo_cristo=False, numero_maximo_asignaciones=1, ocupacion_real=0)
        
        mock_query = mock_filter.return_value.annotate.return_value.order_by.return_value
        mock_query.__iter__.return_value = [p1, p2, p3, p4]

        service.generar_pdf_vacantes(mock_acto)

        data_enviada = mock_table.call_args[0][0]

        self.assertEqual(data_enviada[1][0], "Bocina")
        self.assertEqual(data_enviada[1][1], "Paso de Cristo")
        self.assertEqual(data_enviada[2][0], "Vara")
        self.assertEqual(data_enviada[2][1], "Paso de Cristo")

        self.assertEqual(data_enviada[3][0], "Canasto")
        self.assertEqual(data_enviada[3][1], "Paso de Virgen")



    @patch('api.servicios.solicitud_insignia.solicitud_insignia_service.Table')
    @patch('api.models.Puesto.objects.filter')
    def test_generar_pdf_vacantes_procesa_volumen_elevado_de_puestos(self, mock_filter, mock_table):
        """
        Test: muchos puestos

        Given: Un acto con 200 puestos diferentes con vacantes.
        When: Se genera el reporte de vacantes.
        Then: La tabla resultante debe tener 201 filas (header + 200 puestos).
        """
        service = SolicitudInsigniaService()
        mock_acto = MagicMock(spec=Acto)

        puestos_masivos = [
            MagicMock(nombre=f"Insignia {i}", cortejo_cristo=True, numero_maximo_asignaciones=1, ocupacion_real=0)
            for i in range(200)
        ]
        
        mock_query = mock_filter.return_value.annotate.return_value.order_by.return_value
        mock_query.__iter__.return_value = puestos_masivos

        service.generar_pdf_vacantes(mock_acto)

        data_enviada = mock_table.call_args[0][0]
        self.assertEqual(len(data_enviada), 201)
        self.assertEqual(data_enviada[-1][0], "Insignia 199")
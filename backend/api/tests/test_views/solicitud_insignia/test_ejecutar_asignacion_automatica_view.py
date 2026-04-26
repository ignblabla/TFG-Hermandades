from unittest.mock import patch, MagicMock
from io import BytesIO
from django.http import Http404
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError

from api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view import EjecutarRepartoView


class TestEjecutarRepartoView(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EjecutarRepartoView.as_view()
        self.url = '/reparto/1/reparto-automatico/'

    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.base64')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.PapeletaSitio')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.Puesto')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_flujo_completo_ok_retorna_200(
        self, 
        mock_get_object, 
        mock_reparto_service, 
        mock_puesto, 
        mock_papeleta, 
        mock_solicitud_service, 
        mock_base64
    ):
        """
        Test: Flujo completo OK → 200

        Given: Un acto válido y todos los servicios/ORM respondiendo correctamente.
        When: Se ejecuta la petición POST para realizar el reparto automático.
        Then: La vista debe retornar un status 200 y la estructura JSON con las estadísticas y el PDF en base64.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())

        mock_acto = MagicMock()
        mock_acto.id = 1
        mock_get_object.return_value = mock_acto

        resultado_inicial = {"algoritmo": "completado"}
        mock_reparto_service.ejecutar_asignacion_automatica.return_value = resultado_inicial

        puesto_1 = MagicMock(numero_maximo_asignaciones=5)
        puesto_2 = MagicMock(numero_maximo_asignaciones=5)
        mock_puesto.objects.filter.return_value = [puesto_1, puesto_2]

        mock_papeleta.objects.filter.return_value.count.return_value = 4

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"%PDF-1.4 mock_data"
        mock_solicitud_service.generar_pdf_asignados.return_value = mock_buffer

        mock_base64.b64encode.return_value = b"base64_string_mockeado"

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("mensaje", response.data)
        self.assertEqual(response.data["mensaje"], "Reparto ejecutado con éxito.")
        
        self.assertIn("pdf_base64", response.data)
        self.assertEqual(response.data["pdf_base64"], "base64_string_mockeado")
        
        self.assertIn("filename", response.data)
        self.assertEqual(response.data["filename"], "asignacion_insignias_1.pdf")

        self.assertIn("detalle_algoritmo", response.data)
        stats = response.data["detalle_algoritmo"]
        self.assertEqual(stats["total_insignias"], 10)
        self.assertEqual(stats["total_asignados"], 4)
        self.assertEqual(stats["total_no_asignados"], 6)
        self.assertEqual(stats["algoritmo"], "completado")

        mock_reparto_service.ejecutar_asignacion_automatica.assert_called_once_with(acto_id=1)
        mock_buffer.close.assert_called_once()



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.base64')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.PapeletaSitio')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.Puesto')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_se_ejecuta_el_servicio_de_reparto_con_id_correcto(
        self, 
        mock_get_object, 
        mock_reparto_service, 
        mock_puesto, 
        mock_papeleta, 
        mock_solicitud_service, 
        mock_base64
    ):
        """
        Test: Se ejecuta el servicio de reparto

        Given: Un ID de acto (pk=55) enviado en la URL.
        When: La vista procesa la petición POST.
        Then: Se debe invocar a RepartoService.ejecutar_asignacion_automatica pasando acto_id=55.
        """
        pk_test = 55
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())

        mock_get_object.return_value = MagicMock(id=pk_test)

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"bytes"
        mock_solicitud_service.generar_pdf_asignados.return_value = mock_buffer

        self.view(request, pk=pk_test)

        mock_reparto_service.ejecutar_asignacion_automatica.assert_called_once_with(acto_id=pk_test)



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.base64')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.PapeletaSitio')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.Puesto')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_calculo_correcto_de_estadisticas_reparto(
        self, 
        mock_get_object, 
        mock_reparto_service, 
        mock_puesto, 
        mock_papeleta, 
        mock_solicitud_service, 
        mock_base64
    ):
        """
        Test: Cálculo correcto de estadísticas

        Given: Un cupo total de 10 (2 puestos de 5) y 7 insignias ya asignadas.
        When: Se ejecuta la vista de reparto.
        Then: El diccionario 'detalle_algoritmo' debe contener:
            total_asignados: 7, total_no_asignados: 3, total_insignias: 10.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_object.return_value = MagicMock(id=1)

        puesto_1 = MagicMock(numero_maximo_asignaciones=5)
        puesto_2 = MagicMock(numero_maximo_asignaciones=5)
        mock_puesto.objects.filter.return_value = [puesto_1, puesto_2]

        mock_papeleta.objects.filter.return_value.count.return_value = 7

        mock_reparto_service.ejecutar_asignacion_automatica.return_value = {"status": "ok"}
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"pdf"
        mock_solicitud_service.generar_pdf_asignados.return_value = mock_buffer

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        stats = response.data["detalle_algoritmo"]

        self.assertEqual(stats["total_insignias"], 10)
        self.assertEqual(stats["total_asignados"], 7)
        self.assertEqual(stats["total_no_asignados"], 3)

        self.assertEqual(stats["status"], "ok")



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.base64')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.PapeletaSitio')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.Puesto')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_merge_de_stats_cuando_algoritmo_devuelve_dict(
        self, mock_get_object, mock_reparto, mock_puesto, mock_papeleta, mock_solicitud, mock_base64
    ):
        """
        Test: Merge de stats con resultado del algoritmo

        Given: El servicio de reparto devuelve un diccionario con datos propios.
        When: La vista genera la respuesta.
        Then: Se debe aplicar .update(), fusionando los datos del algoritmo con las estadísticas de la vista.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_object.return_value = MagicMock(id=1)

        resultado_servicio = {"duracion_segundos": 1.5, "iteraciones": 10}
        mock_reparto.ejecutar_asignacion_automatica.return_value = resultado_servicio

        mock_puesto.objects.filter.return_value = [MagicMock(numero_maximo_asignaciones=10)]
        mock_papeleta.objects.filter.return_value.count.return_value = 0

        mock_solicitud.generar_pdf_asignados.return_value = MagicMock(getvalue=lambda: b"")

        response = self.view(request, pk=1)

        detalle = response.data["detalle_algoritmo"]
        self.assertEqual(detalle["duracion_segundos"], 1.5)
        self.assertEqual(detalle["total_insignias"], 10)



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.base64')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.PapeletaSitio')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.Puesto')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_resultado_es_solo_stats_cuando_algoritmo_no_devuelve_dict(
        self, mock_get_object, mock_reparto, mock_puesto, mock_papeleta, mock_solicitud, mock_base64
    ):
        """
        Test: Algoritmo NO devuelve dict (None o string)

        Given: El servicio de reparto devuelve algo que no es un diccionario (ej. None).
        When: La vista genera la respuesta.
        Then: La clave 'detalle_algoritmo' debe contener únicamente las estadísticas generadas por la vista.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_object.return_value = MagicMock(id=1)

        mock_reparto.ejecutar_asignacion_automatica.return_value = None

        mock_puesto.objects.filter.return_value = [MagicMock(numero_maximo_asignaciones=5)]
        mock_papeleta.objects.filter.return_value.count.return_value = 2
        
        mock_solicitud.generar_pdf_asignados.return_value = MagicMock(getvalue=lambda: b"")

        response = self.view(request, pk=1)

        detalle = response.data["detalle_algoritmo"]
        self.assertIsInstance(detalle, dict)
        self.assertEqual(detalle["total_insignias"], 5)
        self.assertEqual(detalle["total_asignados"], 2)



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.Puesto')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.PapeletaSitio')
    def test_generacion_de_pdf_llamada_correcta(
        self, mock_papeleta, mock_puesto, mock_reparto, mock_get_object, mock_solicitud_service
    ):
        """
        Test: Generación de PDF

        Given: Un proceso de reparto que termina exitosamente.
        When: La vista prepara los documentos de salida.
        Then: Se debe llamar a generar_pdf_asignados pasando la instancia del acto recuperada.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())
        
        mock_acto = MagicMock(id=1)
        mock_get_object.return_value = mock_acto

        mock_puesto.objects.filter.return_value = []
        mock_papeleta.objects.filter.return_value.count.return_value = 0
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"pdf_content"
        mock_solicitud_service.generar_pdf_asignados.return_value = mock_buffer

        self.view(request, pk=1)

        mock_solicitud_service.generar_pdf_asignados.assert_called_once_with(mock_acto)



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.base64')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.PapeletaSitio')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.Puesto')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_codificacion_base64_y_conversion_string(
        self, mock_get_object, mock_reparto, mock_puesto, mock_papeleta, mock_solicitud, mock_base64
    ):
        """
        Test: Codificación base64

        Given: Los bytes generados por el servicio de PDF.
        When: La vista prepara el campo pdf_base64 para el JSON.
        Then: Se debe llamar a b64encode y el resultado debe convertirse a string (utf-8).
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_object.return_value = MagicMock(id=1)

        mock_reparto.ejecutar_asignacion_automatica.return_value = {}
        mock_puesto.objects.filter.return_value = []
        mock_papeleta.objects.filter.return_value.count.return_value = 0

        bytes_pdf = b"fake_pdf_bytes"
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = bytes_pdf
        mock_solicitud.generar_pdf_asignados.return_value = mock_buffer

        mock_b64_bytes = MagicMock()
        mock_base64.b64encode.return_value = mock_b64_bytes
        mock_b64_bytes.decode.return_value = "string_base64_final"

        response = self.view(request, pk=1)

        mock_base64.b64encode.assert_called_once_with(bytes_pdf)
        mock_b64_bytes.decode.assert_called_once_with('utf-8')
        self.assertEqual(response.data["pdf_base64"], "string_base64_final")



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.base64')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.PapeletaSitio')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.Puesto')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_nombre_del_fichero_es_correcto_segun_acto(
        self, mock_get_object, mock_reparto, mock_puesto, mock_papeleta, mock_solicitud, mock_base64
    ):
        """
        Test: Nombre del fichero correcto

        Given: Un acto con un ID específico (por ejemplo, ID 123).
        When: El reparto finaliza y se construye la respuesta JSON.
        Then: El campo 'filename' debe ser exactamente "asignacion_insignias_123.pdf".
        """
        acto_id_test = 123
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())

        mock_get_object.return_value = MagicMock(id=acto_id_test)

        mock_reparto.ejecutar_asignacion_automatica.return_value = {}
        mock_puesto.objects.filter.return_value = []
        mock_papeleta.objects.filter.return_value.count.return_value = 0
        
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"pdf"
        mock_solicitud.generar_pdf_asignados.return_value = mock_buffer

        response = self.view(request, pk=acto_id_test)

        nombre_esperado = f"asignacion_insignias_{acto_id_test}.pdf"
        self.assertEqual(response.data["filename"], nombre_esperado)



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_acto_no_existe_retorna_404(self, mock_get_object):
        """
        Test: Acto no existe → 404

        Given: Un ID de acto que no existe en el sistema.
        When: Se intenta ejecutar el reparto.
        Then: La vista debe retornar status 404 Not Found.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())
        
        mock_get_object.side_effect = Http404

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_error_validacion_reparto_retorna_400(self, mock_get_object, mock_reparto_service):
        """
        Test: Error de validación del reparto → 400

        Given: Un acto válido pero condiciones que el servicio de reparto no acepta.
        When: RepartoService lanza DjangoValidationError.
        Then: La vista debe capturarla y devolver status 400 con el mensaje de error.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())
        
        mock_get_object.return_value = MagicMock(id=1)

        mensaje_validacion = "No hay papeletas de sitio solicitadas para este acto."
        mock_reparto_service.ejecutar_asignacion_automatica.side_effect = DjangoValidationError(mensaje_validacion)

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn(mensaje_validacion, response.data["error"])



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_error_interno_inesperado_retorna_500(self, mock_get_object, mock_reparto_service):
        """
        Test: Error inesperado → 500

        Given: Un fallo catastrófico e imprevisto en el servicio de reparto.
        When: Se lanza una Exception genérica.
        Then: La vista debe capturarla, devolver status 500 y el detalle del error.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())
        
        mock_get_object.return_value = MagicMock(id=1)
        
        error_raro = "Fallo de conexión con la base de datos externa"
        mock_reparto_service.ejecutar_asignacion_automatica.side_effect = Exception(error_raro)

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "Error interno del servidor")
        self.assertEqual(response.data["detalle"], error_raro)



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_error_inesperado_retorna_500_con_estructura_correcta(self, mock_get_object, mock_reparto):
        """
        Test: Error inesperado → 500

        Given: Un escenario donde ocurre una excepción no controlada dentro de la lógica principal.
        When: La vista captura la excepción genérica en el bloque except.
        Then: Debe retornar status 500, un mensaje de error amigable y el detalle técnico.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())

        mock_get_object.return_value = MagicMock(id=1)

        mensaje_error_tecnico = "Database connection lost during transaction"
        mock_reparto.ejecutar_asignacion_automatica.side_effect = Exception(mensaje_error_tecnico)

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "Error interno del servidor")
        self.assertEqual(response.data["detalle"], mensaje_error_tecnico)



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.base64')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.PapeletaSitio')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.Puesto')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_insignias_no_asignadas_no_es_negativo(
        self, mock_get_object, mock_reparto, mock_puesto, mock_papeleta, mock_solicitud, mock_base64
    ):
        """
        Test: insignias_no_asignadas negativo

        Given: Un escenario inconsistente donde hay más asignaciones (12) que cupo total (10).
        When: La vista calcula las estadísticas.
        Then: El valor de 'total_no_asignados' debe ser 0 (gracias al max(0, ...)) y no -2.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_object.return_value = MagicMock(id=1)

        mock_puesto.objects.filter.return_value = [MagicMock(numero_maximo_asignaciones=10)]

        mock_papeleta.objects.filter.return_value.count.return_value = 12

        mock_reparto.ejecutar_asignacion_automatica.return_value = {}
        mock_solicitud.generar_pdf_asignados.return_value = MagicMock(getvalue=lambda: b"")

        response = self.view(request, pk=1)

        stats = response.data["detalle_algoritmo"]
        self.assertEqual(stats["total_asignados"], 12)
        self.assertEqual(stats["total_insignias"], 10)

        self.assertEqual(stats["total_no_asignados"], 0)



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.base64')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.PapeletaSitio')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.Puesto')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_reparto_sin_puestos_configurados(
        self, mock_get_object, mock_reparto, mock_puesto, mock_papeleta, mock_solicitud, mock_base64
    ):
        """
        Test: Sin puestos

        Given: Un acto que no tiene puestos de tipo insignia definidos.
        When: Se ejecuta el reparto.
        Then: total_insignias debe ser 0 y la vista no debe lanzar error por suma de lista vacía.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_object.return_value = MagicMock(id=1)

        mock_puesto.objects.filter.return_value = []
        mock_papeleta.objects.filter.return_value.count.return_value = 0

        mock_reparto.ejecutar_asignacion_automatica.return_value = {}
        mock_solicitud.generar_pdf_asignados.return_value = MagicMock(getvalue=lambda: b"")

        response = self.view(request, pk=1)

        stats = response.data["detalle_algoritmo"]
        self.assertEqual(stats["total_insignias"], 0)
        self.assertEqual(stats["total_asignados"], 0)
        self.assertEqual(stats["total_no_asignados"], 0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.base64')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.PapeletaSitio')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.Puesto')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_sin_asignaciones_realizadas(
        self, mock_get_object, mock_reparto, mock_puesto, mock_papeleta, mock_solicitud, mock_base64
    ):
        """
        Test: Sin asignaciones

        Given: Un acto con cupos pero donde el algoritmo no ha asignado ninguna insignia.
        When: Se calculan las estadísticas.
        Then: total_asignados debe ser 0 y total_no_asignados debe ser igual al cupo total.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_object.return_value = MagicMock(id=1)

        mock_puesto.objects.filter.return_value = [MagicMock(numero_maximo_asignaciones=5)]
        mock_papeleta.objects.filter.return_value.count.return_value = 0

        mock_reparto.ejecutar_asignacion_automatica.return_value = {}
        mock_solicitud.generar_pdf_asignados.return_value = MagicMock(getvalue=lambda: b"")

        response = self.view(request, pk=1)

        stats = response.data["detalle_algoritmo"]
        self.assertEqual(stats["total_asignados"], 0)
        self.assertEqual(stats["total_no_asignados"], 5)
        self.assertEqual(response.status_code, status.HTTP_200_OK)



    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.base64')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.PapeletaSitio')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.Puesto')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.RepartoService')
    @patch('api.vistas.solicitud_insignia.ejecutar_asignacion_automatica_view.get_object_or_404')
    def test_pdf_vacio_genera_base64_valido(
        self, mock_get_object, mock_reparto, mock_puesto, mock_papeleta, mock_solicitud, mock_base64
    ):
        """
        Test: PDF vacío

        Given: Un servicio de PDF que devuelve un buffer sin contenido (0 bytes).
        When: La vista intenta codificar el PDF en base64.
        Then: La vista no debe fallar y debe devolver la cadena base64 resultante (aunque sea la de un string vacío).
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_object.return_value = MagicMock(id=1)

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b""
        mock_solicitud.generar_pdf_asignados.return_value = mock_buffer

        mock_b64_bytes = MagicMock()
        mock_base64.b64encode.return_value = mock_b64_bytes
        mock_b64_bytes.decode.return_value = ""

        mock_reparto.ejecutar_asignacion_automatica.return_value = {}
        mock_puesto.objects.filter.return_value = []
        mock_papeleta.objects.filter.return_value.count.return_value = 0

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_base64.b64encode.assert_called_once_with(b"")
        self.assertEqual(response.data["pdf_base64"], "")
        mock_buffer.close.assert_called_once()
from unittest.mock import patch, MagicMock
import base64
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from django.core.exceptions import ValidationError as DjangoValidationError

from api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view import EjecutarRepartoCiriosView

class TestEjecutarRepartoCiriosView(APITestCase):

    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.ejecutar_asignacion_automatica_cirios")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.base64.b64encode")
    def test_ejecucion_correcta_completa(self, mock_base64, mock_gen_pdf, mock_ejecutar, mock_get_obj):
        """
        Test: Ejecución correcta completa

        Given: Un acto_id válido y un usuario administrativo autenticado.
        When: Se realiza una petición POST al endpoint de reparto.
        Then: La vista debe ejecutar el algoritmo, generar el PDF, codificarlo en base64 y 
            retornar un status 200 con el mensaje y los datos del archivo.
        """
        factory = APIRequestFactory()
        user_admin = MagicMock(name="AdminUser")
        acto_id = 1
        request = factory.post(f"/actos/{acto_id}/reparto-cirios/")
        force_authenticate(request, user=user_admin)

        mock_acto = MagicMock(name="Acto_Mock")
        mock_acto.id = acto_id
        mock_get_obj.return_value = mock_acto

        mock_ejecutar.return_value = 10

        mock_buffer = MagicMock(name="PDF_Buffer")
        mock_buffer.getvalue.return_value = b"contenido_pdf_raw"
        mock_gen_pdf.return_value = mock_buffer

        mock_base64.return_value = b"pdf_codificado_base64"

        view = EjecutarRepartoCiriosView.as_view()

        response = view(request, acto_id=acto_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Se han asignado 10 papeletas", response.data["mensaje"])

        self.assertEqual(response.data["pdf_base64"], "pdf_codificado_base64")
        self.assertEqual(response.data["asignadas"], 10)
        self.assertEqual(response.data["filename"], f"asignacion_cirios_tramos_{acto_id}.pdf")

        mock_buffer.close.assert_called_once()

        mock_ejecutar.assert_called_once_with(acto_id)
        mock_gen_pdf.assert_called_once_with(mock_acto)



    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.ejecutar_asignacion_automatica_cirios")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_mensaje_contiene_numero_asignaciones(self, mock_gen_pdf, mock_ejecutar, mock_get_obj):
        """
        Test: Mensaje contiene número de asignaciones

        Given: Una ejecución de reparto que asigna un número específico de papeletas (ej. 42).
        When: La vista construye la respuesta de éxito.
        Then: El campo 'mensaje' debe incluir dinámicamente el número 42 y el campo 'asignadas' debe reflejarlo.
        """
        factory = APIRequestFactory()
        request = factory.post("/actos/1/reparto-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_get_obj.return_value = MagicMock(id=1)

        cantidad_test = 42
        mock_ejecutar.return_value = cantidad_test

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"fake-pdf"
        mock_gen_pdf.return_value = mock_buffer

        view = EjecutarRepartoCiriosView.as_view()

        response = view(request, acto_id=1)

        mensaje_esperado = f"El reparto se ha ejecutado con éxito. Se han asignado {cantidad_test} papeletas de sitio en los tramos."
        self.assertEqual(response.data["mensaje"], mensaje_esperado)
        self.assertEqual(response.data["asignadas"], cantidad_test)



    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.ejecutar_asignacion_automatica_cirios")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.base64.b64encode")
    def test_pdf_convertido_a_base64_correctamente(self, mock_b64encode, mock_gen_pdf, mock_ejecutar, mock_get_obj):
        """
        Test: PDF convertido a base64 correctamente

        Given: Un buffer de PDF con contenido binario generado por el servicio.
        When: La vista procesa el buffer para enviarlo en el JSON.
        Then: Debe llamar a base64.b64encode con los bytes del PDF y posteriormente ejecutar .decode('utf-8') 
            para transformarlo en un string válido para JSON.
        """
        factory = APIRequestFactory()
        request = factory.post("/actos/1/reparto-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_get_obj.return_value = MagicMock(id=1)

        mock_ejecutar.return_value = 10 
        
        pdf_raw_bytes = b"%PDF-1.4-test-content"
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = pdf_raw_bytes
        mock_gen_pdf.return_value = mock_buffer

        mock_bytes_retornados = MagicMock(spec=bytes)
        mock_bytes_retornados.decode.return_value = "string_base64_final"
        mock_b64encode.return_value = mock_bytes_retornados

        view = EjecutarRepartoCiriosView.as_view()

        response = view(request, acto_id=1)

        self.assertTrue(mock_b64encode.called, "b64encode no fue llamado")
        mock_b64encode.assert_called_once_with(pdf_raw_bytes)
        mock_bytes_retornados.decode.assert_called_once_with('utf-8')
        self.assertEqual(response.data["pdf_base64"], "string_base64_final")



    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.ejecutar_asignacion_automatica_cirios")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_nombre_fichero_correcto(self, mock_gen_pdf, mock_ejecutar, mock_get_obj):
        """
        Test: Nombre de fichero correcto

        Given: Un acto con un ID específico (ej. 99).
        When: La vista genera la respuesta exitosa tras el reparto.
        Then: El campo 'filename' en el JSON debe seguir el patrón 'asignacion_cirios_tramos_99.pdf'.
        """
        factory = APIRequestFactory()
        request = factory.post("/actos/99/reparto-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_acto = MagicMock(name="Acto_99")
        mock_acto.id = 99
        mock_get_obj.return_value = mock_acto

        mock_ejecutar.return_value = 5
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"pdf-data"
        mock_gen_pdf.return_value = mock_buffer

        view = EjecutarRepartoCiriosView.as_view()

        response = view(request, acto_id=99)

        nombre_esperado = "asignacion_cirios_tramos_99.pdf"
        self.assertEqual(response.data["filename"], nombre_esperado)



    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.ejecutar_asignacion_automatica_cirios")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_se_llama_al_algoritmo_con_acto_id_correcto(self, mock_gen_pdf, mock_ejecutar, mock_get_obj):
        """
        Test: Se llama al algoritmo con acto_id correcto

        Given: Un acto_id proporcionado en la URL (ej. 500).
        When: Se ejecuta el método POST de la vista.
        Then: La vista debe delegar la ejecución al servicio ReportesCiriosService pasando exactamente el ID 500.
        """
        factory = APIRequestFactory()
        acto_id_test = 500
        request = factory.post(f"/actos/{acto_id_test}/reparto-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_get_obj.return_value = MagicMock(id=acto_id_test)

        mock_ejecutar.return_value = 0
        mock_gen_pdf.return_value = MagicMock()

        view = EjecutarRepartoCiriosView.as_view()

        view(request, acto_id=acto_id_test)

        mock_ejecutar.assert_called_once_with(acto_id_test)



    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.ejecutar_asignacion_automatica_cirios")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_genera_pdf_con_acto_correcto(self, mock_gen_pdf, mock_ejecutar, mock_get_obj):
        """
        Test: Se genera el PDF con el acto correcto

        Given: Un acto recuperado exitosamente por su ID.
        When: Se procede a la generación del reporte PDF tras el reparto.
        Then: Se debe llamar a generar_pdf_cirios_asignados pasando el objeto 'acto' 
            recuperado previamente.
        """
        factory = APIRequestFactory()
        acto_id = 7
        request = factory.post(f"/actos/{acto_id}/reparto-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_acto_instancia = MagicMock(name="Instancia_Acto_7")
        mock_get_obj.return_value = mock_acto_instancia

        mock_ejecutar.return_value = 1
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"fake-pdf"
        mock_gen_pdf.return_value = mock_buffer

        view = EjecutarRepartoCiriosView.as_view()

        view(request, acto_id=acto_id)

        mock_gen_pdf.assert_called_once_with(mock_acto_instancia)



    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.ejecutar_asignacion_automatica_cirios")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.print")
    def test_validation_error_algoritmo_devuelve_400(self, mock_print, mock_ejecutar, mock_get_obj):
        """
        Test: ValidationError del algoritmo

        Given: Un acto válido pero un estado que impide el reparto (ej. no hay tramos configurados).
        When: El servicio lanza una ValidationError.
        Then: La vista debe capturar el error y retornar un status 400 BAD REQUEST con el mensaje de la excepción.
        """
        factory = APIRequestFactory()
        request = factory.post("/actos/1/reparto-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_get_obj.return_value = MagicMock(id=1)

        mensaje_error = "No se puede ejecutar el reparto: el acto no tiene tramos configurados."
        mock_ejecutar.side_effect = DjangoValidationError(mensaje_error)

        view = EjecutarRepartoCiriosView.as_view()

        response = view(request, acto_id=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn(mensaje_error, str(response.data["error"]))



    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.ejecutar_asignacion_automatica_cirios")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.print")
    def test_validation_error_con_mensaje_complejo(self, mock_print, mock_ejecutar, mock_get_obj):
        """
        Test: ValidationError con mensaje complejo

        Given: Una excepción que contiene una estructura de datos o múltiples mensajes.
        When: La vista captura el ValidationError.
        Then: La vista debe aplicar str(e) para asegurar que el contenido se transforme en una cadena legible antes de enviarla en el JSON de respuesta.
        """
        factory = APIRequestFactory()
        request = factory.post("/actos/1/reparto-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_get_obj.return_value = MagicMock(id=1)

        errores_multiples = ["Error 1: Falta configuración", "Error 2: Plazas insuficientes"]
        mock_ejecutar.side_effect = DjangoValidationError(errores_multiples)

        view = EjecutarRepartoCiriosView.as_view()

        response = view(request, acto_id=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIsInstance(response.data["error"], str)
        self.assertIn("Error 1", response.data["error"])
        self.assertIn("Error 2", response.data["error"])



    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.ejecutar_asignacion_automatica_cirios")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.print")
    def test_exception_en_algoritmo_devuelve_500(self, mock_print, mock_ejecutar, mock_get_obj):
        """
        Test: Exception en el algoritmo

        Given: Un acto válido.
        When: El servicio de asignación lanza una excepción genérica (error inesperado).
        Then: La vista debe retornar un status 500 INTERNAL SERVER ERROR con un mensaje genérico y el detalle del error.
        """
        factory = APIRequestFactory()
        request = factory.post("/actos/1/reparto-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_get_obj.return_value = MagicMock(id=1)

        error_mensaje = "Fallo de conexión con el motor de asignación"
        mock_ejecutar.side_effect = Exception(error_mensaje)

        view = EjecutarRepartoCiriosView.as_view()

        response = view(request, acto_id=1)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "Error interno del servidor durante el reparto.")
        self.assertEqual(response.data["detalle"], error_mensaje)



    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.ejecutar_asignacion_automatica_cirios")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.print")
    def test_exception_al_generar_pdf_devuelve_500(self, mock_print, mock_gen_pdf, mock_ejecutar, mock_get_obj):
        """
        Test: Exception al generar PDF

        Given: Un algoritmo de asignación que se ejecuta correctamente.
        When: El servicio de generación de PDF lanza una excepción (ej. falta de permisos en carpeta temporal).
        Then: La vista debe capturar el error y retornar un status 500, a pesar de que la asignación tuvo éxito.
        """
        factory = APIRequestFactory()
        request = factory.post("/actos/1/reparto-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_get_obj.return_value = MagicMock(id=1)

        mock_ejecutar.return_value = 10

        error_pdf = "Error en el motor de renderizado PDF"
        mock_gen_pdf.side_effect = Exception(error_pdf)

        view = EjecutarRepartoCiriosView.as_view()

        response = view(request, acto_id=1)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["detalle"], error_pdf)



    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.ejecutar_asignacion_automatica_cirios")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.base64.b64encode")
    def test_exception_al_hacer_base64_devuelve_500(self, mock_b64, mock_gen_pdf, mock_ejecutar, mock_get_obj):
        """
        Test: Exception al hacer base64

        Given: Un flujo donde el PDF se genera bien pero la codificación falla.
        When: base64.b64encode lanza una Exception.
        Then: La vista captura el error y retorna un status 500.
        """
        factory = APIRequestFactory()
        request = factory.post("/actos/1/reparto-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_get_obj.return_value = MagicMock(id=1)
        mock_ejecutar.return_value = 5
        
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"bytes"
        mock_gen_pdf.return_value = mock_buffer

        error_msg = "Error crítico de memoria en codificación"
        mock_b64.side_effect = Exception(error_msg)

        view = EjecutarRepartoCiriosView.as_view()

        response = view(request, acto_id=1)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["detalle"], error_msg)



    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.ejecutar_asignacion_automatica_cirios")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.print")
    def test_pdf_vacio_no_rompe_la_vista(self, mock_print, mock_gen_pdf, mock_ejecutar, mock_get_obj):
        """
        Test: PDF vacío (Edge Case)

        Given: Un servicio que por algún motivo genera un PDF sin contenido (0 bytes).
        When: La vista intenta codificar este contenido.
        Then: La vista debe completar el flujo con éxito, devolviendo un string base64 vacío y cerrando el buffer.
        """
        factory = APIRequestFactory()
        request = factory.post("/actos/1/reparto-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_get_obj.return_value = MagicMock(id=1)
        mock_ejecutar.return_value = 0

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"" 
        mock_gen_pdf.return_value = mock_buffer

        view = EjecutarRepartoCiriosView.as_view()

        response = view(request, acto_id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["pdf_base64"], "")

        mock_buffer.close.assert_called_once()
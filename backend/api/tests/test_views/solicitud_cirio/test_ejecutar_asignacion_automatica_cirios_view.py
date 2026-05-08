from unittest.mock import patch, MagicMock
import base64
from django.http import Http404
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from django.core.exceptions import ValidationError

from api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view import EjecutarRepartoCiriosView


class TestEjecutarRepartoCiriosView(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.acto_id = 1
        self.url = f"/api/actos/{self.acto_id}/reparto-cirios/"
        self.vista_callable = EjecutarRepartoCiriosView.as_view()
        
        self.admin_user = MagicMock(name="AdminUser")
        self.admin_user.is_authenticated = True
        self.admin_user.esAdmin = True



    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.base64.b64encode")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.ejecutar_asignacion_automatica_cirios")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.get_object_or_404")
    def test_post_reparto_exitoso_devuelve_pdf_200(self, mock_get_obj, mock_ejecutar, mock_gen_pdf, mock_b64encode):
        """
        Test: Reparto exitoso devuelve PDF (200)

        Given: Un acto válido y un usuario autenticado.
        When: La vista ejecuta el algoritmo, genera el PDF y lo codifica.
        Then: Retorna status 200 OK con las métricas de asignación y el archivo en base64.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=self.admin_user)

        mock_acto = MagicMock(id=self.acto_id)
        mock_get_obj.return_value = mock_acto
        mock_ejecutar.return_value = 10

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"pdf_bytes"
        mock_gen_pdf.return_value = mock_buffer

        mock_b64encode.return_value.decode.return_value = "pdf_base64_string"

        response = self.vista_callable(request, acto_id=self.acto_id)

        mock_ejecutar.assert_called_once_with(self.acto_id)
        mock_gen_pdf.assert_called_once_with(mock_acto)
        mock_buffer.close.assert_called_once()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["asignadas"], 10)
        self.assertEqual(response.data["pdf_base64"], "pdf_base64_string")
        self.assertEqual(response.data["filename"], f"asignacion_cirios_tramos_{self.acto_id}.pdf")



    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.get_object_or_404")
    def test_post_acto_no_existe_lanza_404(self, mock_get_obj):
        """
        Test: Acto no existe (404)

        Given: Un acto_id proporcionado en la URL que no existe en la base de datos.
        When: Se invoca get_object_or_404.
        Then: DRF captura el Http404 y devuelve status 404 Not Found.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=self.admin_user)

        mock_get_obj.side_effect = Http404()

        response = self.vista_callable(request, acto_id=self.acto_id)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.ejecutar_asignacion_automatica_cirios")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.get_object_or_404")
    def test_post_validation_error_devuelve_400(self, mock_get_obj, mock_ejecutar):
        """
        Test: ValidationError devuelve 400

        Given: Un acto válido pero inconsistente para el reparto (ej. sin tramos).
        When: El servicio lanza ValidationError.
        Then: La vista captura la excepción y devuelve status 400 BAD REQUEST.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=self.admin_user)
        
        mock_get_obj.return_value = MagicMock()
        
        mensaje_error = "El acto no tiene tramos configurados."
        mock_ejecutar.side_effect = ValidationError(mensaje_error)

        response = self.vista_callable(request, acto_id=self.acto_id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(mensaje_error, response.data["error"])



    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.ReportesCiriosService.ejecutar_asignacion_automatica_cirios")
    @patch("api.vistas.solicitud_cirio.ejecutar_asignacion_automatica_cirios_view.get_object_or_404")
    def test_post_excepcion_inesperada_devuelve_500(self, mock_get_obj, mock_ejecutar):
        """
        Test: Excepción inesperada devuelve 500

        Given: Un estado válido en el acto.
        When: Ocurre un error crítico e inesperado (en el reparto, el buffer o la codificación).
        Then: La vista captura la Exception general y retorna status 500.
        """
        request = self.factory.post(self.url)
        force_authenticate(request, user=self.admin_user)
        
        mock_get_obj.return_value = MagicMock()
        mock_ejecutar.side_effect = Exception("Fallo de memoria")

        response = self.vista_callable(request, acto_id=self.acto_id)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "Error interno del servidor durante el reparto.")
        self.assertEqual(response.data["detalle"], "Fallo de memoria")



    def test_post_seguridad_bloquea_accesos_no_permitidos(self):
        """
        Test: Seguridad bloquea accesos no permitidos

        Given: Peticiones realizadas por un usuario no autenticado y un hermano estándar.
        When: Intentan ejecutar el endpoint administrativo.
        Then: La clase de permiso EsAdministrador bloquea el acceso (401/403).
        """
        request_anon = self.factory.post(self.url)
        response_anon = self.vista_callable(request_anon, acto_id=self.acto_id)
        self.assertIn(response_anon.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        request_hermano = self.factory.post(self.url)
        hermano_normal = MagicMock(is_authenticated=True, esAdmin=False)
        force_authenticate(request_hermano, user=hermano_normal)
        
        response_hermano = self.vista_callable(request_hermano, acto_id=self.acto_id)
        self.assertEqual(response_hermano.status_code, status.HTTP_403_FORBIDDEN)
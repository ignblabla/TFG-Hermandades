from unittest.mock import ANY, patch, MagicMock
from io import BytesIO
from django.http import Http404
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework import status

from api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view import DescargarListadoInsigniasView


class TestDescargarListadoInsigniasView(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = DescargarListadoInsigniasView.as_view()
        self.url = '/actos/1/descargar-listado-insignias/'



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.get_object_or_404')
    def test_descarga_pdf_asignados_exitosamente_200(self, mock_get_404, mock_service_class):
        """
        Test: Genera PDF correctamente → 200

        Given: Un acto existente en base de datos.
        When: Se solicita la descarga del listado de insignias asignadas.
        Then: Retorna status 200, contenido binario exacto, headers correctos y cierra el buffer de memoria.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())

        mock_acto = MagicMock(id=1)
        mock_get_404.return_value = mock_acto

        contenido_pdf = b"%PDF-1.4 listado asignaciones"

        mock_buffer = MagicMock(spec=BytesIO)
        mock_buffer.getvalue.return_value = contenido_pdf
        mock_service_class.generar_pdf_asignados.return_value = mock_buffer

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, contenido_pdf)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="asignacion_insignias_1.pdf"')
        
        mock_service_class.generar_pdf_asignados.assert_called_once_with(mock_acto)
        mock_buffer.close.assert_called_once()



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.SolicitudInsigniaService')
    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.get_object_or_404')
    def test_error_generando_pdf_retorna_500(self, mock_get_404, mock_service_class):
        """
        Test: Error generando PDF → 500

        Given: Un acto válido pero un error inesperado durante la generación del buffer.
        When: El servicio lanza una excepción genérica.
        Then: La vista captura el error, retorna status 500 y un JSON con el detalle.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_404.return_value = MagicMock(id=1)

        mensaje_error = "Error crítico en el motor de PDF"
        mock_service_class.generar_pdf_asignados.side_effect = Exception(mensaje_error)

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "Error al generar el documento")
        self.assertEqual(response.data["detalle"], mensaje_error)



    @patch('api.vistas.solicitud_insignia.descargar_listado_insignias_asignadas_view.get_object_or_404')
    def test_acto_no_existe_retorna_404(self, mock_get_404):
        """
        Test: Acto no existe (404)

        Given: Un ID de acto que no se encuentra en la base de datos.
        When: Se procesa la petición y get_object_or_404 falla.
        Then: Se propaga la excepción Http404 resultando en un status 404.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=MagicMock())
        mock_get_404.side_effect = Http404

        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    def test_usuario_no_autenticado_retorna_401(self):
        """
        Test: Usuario no autenticado (401/403)
        
        Given: Una petición GET anónima (sin token o sesión).
        When: Se intenta descargar el listado.
        Then: El permiso IsAuthenticated deniega el acceso devolviendo 401 o 403.
        """
        request = self.factory.get(self.url)

        response = self.view(request, pk=1)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
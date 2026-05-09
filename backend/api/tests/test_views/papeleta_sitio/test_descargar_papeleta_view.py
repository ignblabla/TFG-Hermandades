from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from django.http import FileResponse, Http404
from django.test import TestCase

from unittest.mock import patch, MagicMock
import io

from api.vistas.papeleta_sitio.descargar_papeleta_view import DescargarPapeletaPDFView


class TestDescargarPapeletaPDFView(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = DescargarPapeletaPDFView.as_view()
        self.papeleta_id = 1
        self.path = f"/api/papeletas/{self.papeleta_id}/descargar/"

        self.mock_user = MagicMock()
        self.mock_user.is_authenticated = True
        self.mock_user.dni = "12345678X"



    @patch('api.vistas.papeleta_sitio.descargar_papeleta_view.get_object_or_404')
    @patch('api.vistas.papeleta_sitio.descargar_papeleta_view.generar_pdf_papeleta')
    def test_descarga_pdf_correcta(self, mock_generar_service, mock_get_object):
        """
        Test: Descarga del PDF correcta
        
        Given: Un usuario autenticado que solicita su propia papeleta en estado 'EMITIDA'.
        When: Se llama al servicio de generación de PDF.
        Then: La vista devuelve un FileResponse con el PDF, status 200 y el nombre de archivo correcto.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_papeleta = MagicMock()
        mock_papeleta.estado_papeleta = 'EMITIDA'
        mock_papeleta.anio = 2026
        mock_papeleta.hermano = self.mock_user
        mock_get_object.return_value = mock_papeleta

        buffer_fake = io.BytesIO(b"CONTENIDO_PDF_DUMMY")
        mock_generar_service.return_value = buffer_fake

        response = self.view(request, pk=self.papeleta_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response, FileResponse)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn(f"Papeleta_2026_{self.mock_user.dni}.pdf", response['Content-Disposition'])
        mock_generar_service.assert_called_once_with(mock_papeleta)



    @patch('api.vistas.papeleta_sitio.descargar_papeleta_view.get_object_or_404')
    def test_error_403_si_papeleta_no_disponible(self, mock_get_object):
        """
        Test: Error 403 si el estado de la papeleta no permite descarga
        
        Given: Una papeleta que existe y pertenece al usuario, pero está en estado 'SOLICITADA'.
        When: El usuario intenta descargarla.
        Then: La vista devuelve un status 403 indicando que no está disponible.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_papeleta = MagicMock()
        mock_papeleta.estado_papeleta = 'SOLICITADA'
        mock_get_object.return_value = mock_papeleta

        response = self.view(request, pk=self.papeleta_id)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertIn(b"La papeleta aun no esta disponible", response.content)



    @patch('api.vistas.papeleta_sitio.descargar_papeleta_view.get_object_or_404')
    def test_error_404_si_papeleta_no_existe_o_no_es_suya(self, mock_get_object):
        """
        Test: Error 404 si la papeleta no existe o no pertenece al usuario
        
        Given: Un ID de papeleta que no existe o no vincula con el request.user.
        When: Se ejecuta get_object_or_404 lanzando un Http404.
        Then: DRF captura la excepción y devuelve un status 404 Not Found.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_get_object.side_effect = Http404

        response = self.view(request, pk=999)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    def test_acceso_denegado_anonimo(self):
        """
        Test: Acceso denegado a usuarios no autenticados
        
        Given: Una petición sin token de autenticación.
        When: Se intenta acceder a la descarga.
        Then: La vista devuelve status 401 Unauthorized.
        """
        request = self.factory.get(self.path)

        response = self.view(request, pk=self.papeleta_id)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
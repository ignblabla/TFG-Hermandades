from unittest.mock import patch, MagicMock
from django.http import Http404
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view import DescargarListadoCiriosView


class TestDescargarListadoCiriosView(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.acto_id = 1
        self.url = f"/api/actos/{self.acto_id}/descargar-listado-cirios/"
        self.vista_callable = DescargarListadoCiriosView.as_view()
        
        self.user = MagicMock()
        self.user.is_authenticated = True



    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_get_descarga_sin_filtro_200(self, mock_gen_pdf, mock_get_obj):
        """
        Test: Descarga sin filtro (200)

        Given: Una petición GET válida sin el parámetro 'paso'.
        When: La vista genera el PDF mediante el servicio.
        Then: Retorna HttpResponse (200) con el nombre de archivo genérico, el buffer se cierra y el tipo es application/pdf.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)

        mock_acto = MagicMock(id=self.acto_id)
        mock_get_obj.return_value = mock_acto

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"pdf_data"
        mock_gen_pdf.return_value = mock_buffer
        
        response = self.vista_callable(request, pk=self.acto_id)

        mock_gen_pdf.assert_called_once_with(mock_acto, None)
        mock_buffer.close.assert_called_once()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response['Content-Disposition'], f'attachment; filename="asignacion_cirios_{self.acto_id}.pdf"')
        self.assertEqual(response.content, b"pdf_data")



    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_get_descarga_con_filtro_cristo_200(self, mock_gen_pdf, mock_get_obj):
        """
        Test: Descarga con filtro CRISTO (200)

        Given: Una petición GET con el parámetro '?paso=CRISTO'.
        When: La vista intercepta el query param y lo pasa al servicio.
        Then: Retorna el PDF y el Content-Disposition modifica el filename incluyendo 'cristo'.
        """
        request = self.factory.get(self.url, {'paso': 'CRISTO'})
        force_authenticate(request, user=self.user)

        mock_acto = MagicMock(id=self.acto_id)
        mock_get_obj.return_value = mock_acto
        mock_gen_pdf.return_value = MagicMock()

        response = self.vista_callable(request, pk=self.acto_id)

        mock_gen_pdf.assert_called_once_with(mock_acto, 'CRISTO')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Disposition'], f'attachment; filename="asignacion_cirios_cristo_{self.acto_id}.pdf"')



    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_get_descarga_con_filtro_virgen_200(self, mock_gen_pdf, mock_get_obj):
        """
        Test: Descarga con filtro VIRGEN (200)

        Given: Una petición GET con el parámetro '?paso=VIRGEN'.
        When: La vista intercepta el query param y lo pasa al servicio.
        Then: Retorna el PDF y el Content-Disposition modifica el filename incluyendo 'virgen'.
        """
        request = self.factory.get(self.url, {'paso': 'VIRGEN'})
        force_authenticate(request, user=self.user)

        mock_acto = MagicMock(id=self.acto_id)
        mock_get_obj.return_value = mock_acto
        mock_gen_pdf.return_value = MagicMock()

        response = self.vista_callable(request, pk=self.acto_id)

        mock_gen_pdf.assert_called_once_with(mock_acto, 'VIRGEN')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Disposition'], f'attachment; filename="asignacion_cirios_virgen_{self.acto_id}.pdf"')



    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.get_object_or_404")
    def test_get_acto_no_existe_404(self, mock_get_obj):
        """
        Test: Acto no existe (404)

        Given: Un ID de acto que no se encuentra en base de datos.
        When: Se invoca get_object_or_404.
        Then: La vista retorna status 404 Not Found gestionado por DRF.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)

        mock_get_obj.side_effect = Http404()

        response = self.vista_callable(request, pk=self.acto_id)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_get_error_generando_pdf_500(self, mock_gen_pdf, mock_get_obj):
        """
        Test: Error generando PDF (500)

        Given: Un acto válido.
        When: Falla el proceso de generación del PDF lanzando una Exception general.
        Then: El bloque try/except captura la excepción y retorna un Response 500 con el detalle.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)

        mock_get_obj.return_value = MagicMock(id=self.acto_id)
        
        error_msg = "Error de motor ReportLab"
        mock_gen_pdf.side_effect = Exception(error_msg)

        response = self.vista_callable(request, pk=self.acto_id)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "Error al generar el documento de cirios")
        self.assertEqual(response.data["detalle"], error_msg)



    def test_get_usuario_no_autenticado_acceso_denegado(self):
        """
        Test: Usuario no autenticado -> acceso denegado

        Given: Una petición GET sin token ni credenciales.
        When: Intenta descargar el documento.
        Then: DRF bloquea el acceso en la capa IsAuthenticated (401/403).
        """
        request = self.factory.get(self.url)
        
        response = self.vista_callable(request, pk=self.acto_id)
        
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view import DescargarListadoCiriosView

class TestDescargarListadoCiriosView(APITestCase):

    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_descarga_correcta_sin_filtro(self, mock_gen_pdf, mock_get_obj):
        """
        Test: Descarga correcta sin filtro

        Given: Una petición GET válida sin el parámetro de consulta 'paso'.
        When: La vista procesa la solicitud de descarga para un acto específico.
        Then: Debe retornar una HttpResponse con status 200, Content-Type 'application/pdf', 
            el nombre de archivo genérico y llamar al servicio con filtro_paso=None.
        """
        factory = APIRequestFactory()
        acto_id = 1

        request = factory.get(f"/actos/{acto_id}/descargar-listado-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_acto = MagicMock(name="Acto_Mock")
        mock_acto.id = acto_id
        mock_get_obj.return_value = mock_acto

        mock_buffer = MagicMock(name="PDF_Buffer")
        mock_buffer.getvalue.return_value = b"contenido_falso_del_pdf"
        mock_gen_pdf.return_value = mock_buffer
        
        view = DescargarListadoCiriosView.as_view()

        response = view(request, pk=acto_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response['Content-Type'], 'application/pdf')

        nombre_esperado = f'attachment; filename="asignacion_cirios_{acto_id}.pdf"'
        self.assertEqual(response['Content-Disposition'], nombre_esperado)

        self.assertEqual(response.content, b"contenido_falso_del_pdf")

        mock_gen_pdf.assert_called_once_with(mock_acto, None)

        mock_buffer.close.assert_called_once()



    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_descarga_con_filtro_cristo(self, mock_gen_pdf, mock_get_obj):
        """
        Test: Descarga con filtro CRISTO

        Given: Una petición GET con el parámetro query '?paso=CRISTO'.
        When: La vista procesa la solicitud.
        Then: El nombre del archivo en la cabecera Content-Disposition debe incluir '_cristo_' 
            y el servicio debe recibir 'CRISTO' como argumento de filtro.
        """
        factory = APIRequestFactory()
        acto_id = 5
        request = factory.get(f"/actos/{acto_id}/descargar-listado-cirios/", {'paso': 'CRISTO'})
        force_authenticate(request, user=MagicMock())

        mock_acto = MagicMock(id=acto_id)
        mock_get_obj.return_value = mock_acto

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"pdf_cristo"
        mock_gen_pdf.return_value = mock_buffer

        view = DescargarListadoCiriosView.as_view()

        response = view(request, pk=acto_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        nombre_esperado = f'attachment; filename="asignacion_cirios_cristo_{acto_id}.pdf"'
        self.assertEqual(response['Content-Disposition'], nombre_esperado)

        mock_gen_pdf.assert_called_once_with(mock_acto, 'CRISTO')



    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_descarga_con_filtro_virgen(self, mock_gen_pdf, mock_get_obj):
        """
        Test: Descarga con filtro VIRGEN

        Given: Una petición GET con el parámetro query '?paso=VIRGEN'.
        When: La vista procesa la solicitud.
        Then: El nombre del archivo en la cabecera Content-Disposition debe incluir '_virgen_' 
            y el servicio debe recibir 'VIRGEN' como argumento de filtro.
        """
        factory = APIRequestFactory()
        acto_id = 12
        request = factory.get(f"/actos/{acto_id}/descargar-listado-cirios/", {'paso': 'VIRGEN'})
        force_authenticate(request, user=MagicMock())

        mock_acto = MagicMock(id=acto_id)
        mock_get_obj.return_value = mock_acto

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"pdf_virgen"
        mock_gen_pdf.return_value = mock_buffer

        view = DescargarListadoCiriosView.as_view()

        response = view(request, pk=acto_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        nombre_esperado = f'attachment; filename="asignacion_cirios_virgen_{acto_id}.pdf"'
        self.assertEqual(response['Content-Disposition'], nombre_esperado)

        mock_gen_pdf.assert_called_once_with(mock_acto, 'VIRGEN')



    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_se_llama_al_servicio_con_filtro_cristo(self, mock_gen_pdf, mock_get_obj):
        """
        Test: Se llama al servicio con filtro

        Given: Un acto válido y un parámetro de consulta 'paso=CRISTO'.
        When: Se ejecuta la petición GET.
        Then: La vista debe delegar la generación al servicio pasando el objeto acto 
            y el string 'CRISTO' exactamente.
        """
        factory = APIRequestFactory()
        acto_id = 10
        request = factory.get(f"/actos/{acto_id}/descargar-listado-cirios/", {'paso': 'CRISTO'})
        force_authenticate(request, user=MagicMock())

        mock_acto_instancia = MagicMock(name="Acto_Instancia")
        mock_get_obj.return_value = mock_acto_instancia

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"pdf-content"
        mock_gen_pdf.return_value = mock_buffer

        view = DescargarListadoCiriosView.as_view()

        view(request, pk=acto_id)

        mock_gen_pdf.assert_called_once_with(mock_acto_instancia, 'CRISTO')



    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_se_llama_al_servicio_sin_filtro(self, mock_gen_pdf, mock_get_obj):
        """
        Test: Se llama al servicio sin filtro

        Given: Una petición GET donde no se proporciona el parámetro 'paso'.
        When: La vista recupera el parámetro usando .get('paso', None).
        Then: La vista debe llamar al servicio de generación de PDF pasando None 
            como segundo argumento.
        """
        factory = APIRequestFactory()
        acto_id = 20
        request = factory.get(f"/actos/{acto_id}/descargar-listado-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_acto_instancia = MagicMock(name="Acto_Instancia_Sin_Filtro")
        mock_get_obj.return_value = mock_acto_instancia

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"pdf-content-full"
        mock_gen_pdf.return_value = mock_buffer

        view = DescargarListadoCiriosView.as_view()

        view(request, pk=acto_id)

        mock_gen_pdf.assert_called_once_with(mock_acto_instancia, None)



    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_content_disposition_header_formato_correcto(self, mock_gen_pdf, mock_get_obj):
        """
        Test: Content-Disposition correcto

        Given: Una solicitud de descarga exitosa.
        When: La vista construye la HttpResponse.
        Then: La cabecera 'Content-Disposition' debe tener el formato exacto 
            'attachment; filename="..."' para forzar la descarga en el cliente.
        """
        factory = APIRequestFactory()
        acto_id = 45
        request = factory.get(f"/actos/{acto_id}/descargar-listado-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_acto = MagicMock(id=acto_id)
        mock_get_obj.return_value = mock_acto

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"%PDF-1.4"
        mock_gen_pdf.return_value = mock_buffer

        view = DescargarListadoCiriosView.as_view()

        response = view(request, pk=acto_id)

        self.assertTrue(response.has_header('Content-Disposition'))

        header_value = response['Content-Disposition']
        self.assertIn('attachment', header_value)
        self.assertIn(f'filename="asignacion_cirios_{acto_id}.pdf"', header_value)



    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_error_al_generar_pdf_devuelve_500(self, mock_gen_pdf, mock_get_obj):
        """
        Test: Error al generar PDF

        Given: Un acto válido pero un fallo inesperado en el servicio de reportes.
        When: El servicio lanza una excepción genérica durante la creación del PDF.
        Then: La vista debe capturar la excepción y retornar un status 500 INTERNAL SERVER ERROR 
            con el mensaje de error y el detalle técnico.
        """
        factory = APIRequestFactory()
        acto_id = 1
        request = factory.get(f"/actos/{acto_id}/descargar-listado-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_get_obj.return_value = MagicMock(id=acto_id)

        error_mensaje = "Fallo crítico en el motor ReportLab"
        mock_gen_pdf.side_effect = Exception(error_mensaje)

        view = DescargarListadoCiriosView.as_view()

        response = view(request, pk=acto_id)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

        self.assertEqual(response.data["error"], "Error al generar el documento de cirios")
        self.assertEqual(response.data["detalle"], error_mensaje)



    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_error_sin_mensaje_en_excepcion_no_rompe_vista(self, mock_gen_pdf, mock_get_obj):
        """
        Test: Error sin mensaje en excepción

        Given: Una excepción lanzada por el servicio que no contiene un string descriptivo.
        When: La vista ejecuta str(e) para rellenar el campo 'detalle'.
        Then: La vista no debe romper y debe devolver una representación en string de la excepción 
            junto con el status 500.
        """
        factory = APIRequestFactory()
        request = factory.get("/actos/1/descargar-listado-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_get_obj.return_value = MagicMock(id=1)

        mock_gen_pdf.side_effect = Exception() 

        view = DescargarListadoCiriosView.as_view()

        response = view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

        self.assertIn("error", response.data)
        self.assertIsInstance(response.data["detalle"], str)



    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_pdf_buffer_getvalue_returns_none_captured_as_200(self, mock_gen_pdf, mock_get_obj):
        """
        Test corregido: PDF buffer devuelve None

        Given: Un servicio que devuelve un buffer cuyo método getvalue() retorna None.
        When: La vista intenta construir la HttpResponse con ese valor.
        Then: Django convierte el objeto None a su representación en string ("None"), 
            no rompe el flujo, devuelve status 200 y el contenido son los bytes b'None'.
        """
        factory = APIRequestFactory()
        acto_id = 1
        request = factory.get(f"/actos/{acto_id}/descargar-listado-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_get_obj.return_value = MagicMock(id=acto_id)

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = None
        mock_gen_pdf.return_value = mock_buffer

        view = DescargarListadoCiriosView.as_view()

        response = view(request, pk=acto_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.content, b"None")
        
        mock_buffer.close.assert_called_once()



    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_filtro_paso_invalido_usa_nombre_generico(self, mock_gen_pdf, mock_get_obj):
        """
        Test: Filtro inválido (ej: "OTRO")

        Given: Una petición con un parámetro 'paso' que no es ni 'CRISTO' ni 'VIRGEN'.
        When: La vista evalúa la lógica condicional del nombre de archivo.
        Then: No debe entrar en los bloques específicos y debe usar el nombre genérico 
            'asignacion_cirios_{id}.pdf', pasando el valor "OTRO" al servicio.
        """
        factory = APIRequestFactory()
        acto_id = 100

        request = factory.get(f"/actos/{acto_id}/descargar-listado-cirios/", {'paso': 'OTRO'})
        force_authenticate(request, user=MagicMock())

        mock_acto = MagicMock(id=acto_id)
        mock_get_obj.return_value = mock_acto

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"pdf-data"
        mock_gen_pdf.return_value = mock_buffer

        view = DescargarListadoCiriosView.as_view()

        response = view(request, pk=acto_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        nombre_esperado = f'attachment; filename="asignacion_cirios_{acto_id}.pdf"'
        self.assertEqual(response['Content-Disposition'], nombre_esperado)

        mock_gen_pdf.assert_called_once_with(mock_acto, 'OTRO')



    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_pdf_vacio_sigue_siendo_respuesta_valida(self, mock_gen_pdf, mock_get_obj):
        """
        Test: PDF vacío

        Given: Un servicio que devuelve un buffer vacío (b"").
        When: La vista construye la HttpResponse.
        Then: La respuesta debe tener status 200 y el contenido (response.content) debe ser b"".
        """
        factory = APIRequestFactory()
        request = factory.get("/actos/1/descargar-listado-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_get_obj.return_value = MagicMock(id=1)

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b""
        mock_gen_pdf.return_value = mock_buffer

        view = DescargarListadoCiriosView.as_view()

        response = view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, b"")
        self.assertEqual(response['Content-Type'], 'application/pdf')

        mock_buffer.close.assert_called_once()



    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.get_object_or_404")
    @patch("api.vistas.solicitud_cirio.descargar_listado_cirios_cofradia_view.ReportesCiriosService.generar_pdf_cirios_asignados")
    def test_verificar_que_se_cierra_el_buffer(self, mock_gen_pdf, mock_get_obj):
        """
        Test: Verificar que se cierra el buffer

        Given: Una ejecución normal de la vista de descarga.
        When: La respuesta HttpResponse se ha construido con éxito.
        Then: La vista debe llamar obligatoriamente al método .close() del buffer 
            para liberar los recursos de memoria.
        """
        factory = APIRequestFactory()
        request = factory.get("/actos/1/descargar-listado-cirios/")
        force_authenticate(request, user=MagicMock())

        mock_get_obj.return_value = MagicMock(id=1)

        mock_buffer = MagicMock(name="PDF_Buffer_Resource")
        mock_buffer.getvalue.return_value = b"contenido_binario"
        mock_gen_pdf.return_value = mock_buffer

        view = DescargarListadoCiriosView.as_view()

        view(request, pk=1)

        mock_buffer.close.assert_called_once()
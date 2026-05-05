from unittest import TestCase
from unittest.mock import patch, MagicMock
from rest_framework.exceptions import PermissionDenied

from api.servicios.papeleta_sitio.papeleta_sitio_service import get_historial_papeletas_hermano_service


class TestObtenerHistorialPapeletasHermanoService(TestCase):

    def setUp(self):
        self.mock_usuario = MagicMock()
        self.mock_usuario.is_authenticated = True



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_devuelve_el_queryset_correctamente(self, mock_papeleta_sitio_model):
        """
        Test: Devuelve el queryset correctamente

        Given: Un usuario debidamente autenticado en la llamada.
        When: Se solicita el histórico de papeletas del hermano.
        Then: Se debe devolver el queryset resultante tras aplicar filter, select_related y order_by.
        """
        mock_queryset_esperado = MagicMock()

        mock_papeleta_sitio_model.objects.filter.return_value \
            .select_related.return_value \
            .order_by.return_value = mock_queryset_esperado

        resultado = get_historial_papeletas_hermano_service(self.mock_usuario)

        self.assertEqual(resultado, mock_queryset_esperado)

        mock_papeleta_sitio_model.objects.filter.assert_called_once_with(
            hermano=self.mock_usuario
        )
        mock_papeleta_sitio_model.objects.filter.return_value.select_related.assert_called_once_with(
            'acto', 'puesto', 'puesto__tipo_puesto', 'tramo'
        )
        mock_papeleta_sitio_model.objects.filter.return_value.select_related.return_value.order_by.assert_called_once_with(
            '-anio', '-acto__fecha'
        )



    def test_usuario_es_none(self):
        """
        Test: Usuario es None

        Given: Un valor None en lugar de un objeto usuario.
        When: Se intenta recuperar el historial de papeletas.
        Then: El servicio debe lanzar una excepción PermissionDenied de DRF.
        """
        with self.assertRaises(PermissionDenied) as context:
            get_historial_papeletas_hermano_service(None)
        
        self.assertIn("Usuario no identificado", str(context.exception))



    def test_usuario_no_autenticado(self):
        """
        Test: Usuario no autenticado (is_authenticated=False)

        Given: Un objeto usuario con is_authenticated en False.
        When: Se solicita el historial del hermano.
        Then: Se debe denegar el acceso lanzando PermissionDenied.
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = False

        with self.assertRaises(PermissionDenied) as context:
            get_historial_papeletas_hermano_service(mock_usuario)
            
        self.assertIn("Usuario no identificado", str(context.exception))
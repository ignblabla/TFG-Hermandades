from unittest import TestCase
from unittest.mock import patch, MagicMock
from rest_framework.exceptions import PermissionDenied

from api.servicios.papeleta_sitio.papeleta_sitio_service import get_ultima_papeleta_hermano_service


class TestObtenerUltimaPapeletaHermanoService(TestCase):

    def setUp(self):
        self.mock_usuario = MagicMock()
        self.mock_usuario.is_authenticated = True



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_devuelve_ultima_papeleta(self, mock_papeleta_sitio_model):
        """
        Test: Devuelve la última papeleta

        Given: Un usuario debidamente autenticado en la llamada.
        When: Se procesa la solicitud de obtener la última papeleta exitosamente.
        Then: Se debe devolver el objeto de la papeleta tras realizar la consulta encadenada a base de datos.
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = True

        mock_papeleta_esperada = MagicMock()
        mock_papeleta_sitio_model.objects.filter.return_value \
            .select_related.return_value \
            .order_by.return_value \
            .first.return_value = mock_papeleta_esperada

        resultado = get_ultima_papeleta_hermano_service(mock_usuario)

        self.assertEqual(resultado, mock_papeleta_esperada)

        mock_papeleta_sitio_model.objects.filter.assert_called_once_with(
            hermano=mock_usuario
        )
        mock_papeleta_sitio_model.objects.filter.return_value.select_related.assert_called_once_with(
            'acto', 'puesto', 'puesto__tipo_puesto', 'tramo'
        )
        mock_papeleta_sitio_model.objects.filter.return_value.select_related.return_value.order_by.assert_called_once_with(
            '-anio', '-acto__fecha'
        )
        mock_papeleta_sitio_model.objects.filter.return_value.select_related.return_value.order_by.return_value.first.assert_called_once()



    @patch('api.servicios.papeleta_sitio.papeleta_sitio_service.PapeletaSitio')
    def test_devuelve_none_si_no_hay_papeletas(self, mock_papeleta_sitio_model):
        """
        Test: Devuelve None si no hay papeletas

        Given: Un usuario sin historial de papeletas en la base de datos.
        When: Se consulta la última papeleta del hermano.
        Then: El método .first() debe retornar None y el servicio debe devolver None.
        """
        mock_papeleta_sitio_model.objects.filter.return_value \
            .select_related.return_value \
            .order_by.return_value \
            .first.return_value = None

        resultado = get_ultima_papeleta_hermano_service(self.mock_usuario)

        self.assertIsNone(resultado)



    def test_usuario_es_none(self):
        """
        Test: Usuario es None

        Given: Un valor None en lugar de un objeto usuario.
        When: Se intenta recuperar la última papeleta.
        Then: El servicio debe lanzar una excepción PermissionDenied por falta de identificación.
        """
        with self.assertRaises(PermissionDenied) as context:
            get_ultima_papeleta_hermano_service(None)
        
        self.assertEqual(str(context.exception), "Usuario no identificado")



    def test_usuario_no_autenticado(self):
        """
        Test: Usuario no autenticado (is_authenticated=False)

        Given: Un objeto usuario con el atributo is_authenticated establecido en False.
        When: Se procesa la solicitud del servicio.
        Then: Se debe denegar el acceso lanzando PermissionDenied.
        """
        mock_usuario = MagicMock()
        mock_usuario.is_authenticated = False

        with self.assertRaises(PermissionDenied) as context:
            get_ultima_papeleta_hermano_service(mock_usuario)
            
        self.assertEqual(str(context.exception), "Usuario no identificado")
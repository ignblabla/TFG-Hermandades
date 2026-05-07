import unittest
from unittest.mock import MagicMock, patch

from api.servicios.tipo_acto.tipo_acto_service import get_tipos_acto_service


class TestGetTiposActoService(unittest.TestCase):

    @patch("api.servicios.tipo_acto.tipo_acto_service.TipoActo.objects")
    def test_get_tipos_acto_exito(self, mock_tipo_acto_objects):
        """
        Test: Retorno de QuerySet (Happy Path)
        
        Given: Un estado normal de la aplicación.
        When: Se llama al servicio get_tipos_acto_service().
        Then: Debe delegar en objects.all() y devolver el objeto QuerySet 
            sin alterarlo.
        """
        mock_queryset = MagicMock()
        mock_tipo_acto_objects.all.return_value = mock_queryset

        resultado = get_tipos_acto_service()

        mock_tipo_acto_objects.all.assert_called_once()
        self.assertIs(resultado, mock_queryset)
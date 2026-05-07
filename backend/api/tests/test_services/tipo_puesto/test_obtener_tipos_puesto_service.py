import unittest
from unittest.mock import MagicMock, patch

from api.servicios.tipo_puesto.tipo_puesto_service import get_tipos_puesto_service


class TestGetTiposPuestoService(unittest.TestCase):

    @patch("api.servicios.tipo_puesto.tipo_puesto_service.TipoPuesto.objects")
    def test_get_tipos_puesto_exito(self, mock_tipo_puesto_objects):
        """
        Test: Retorno de QuerySet (Happy Path)
        
        Given: Un estado operativo normal del ORM.
        When: Se invoca al servicio get_tipos_puesto_service().
        Then: Se debe delegar en objects.all() y devolver la referencia 
            del QuerySet sin alterarlo.
        """
        mock_queryset = MagicMock()
        mock_tipo_puesto_objects.all.return_value = mock_queryset

        resultado = get_tipos_puesto_service()

        mock_tipo_puesto_objects.all.assert_called_once()
        self.assertIs(resultado, mock_queryset)
import unittest
from unittest.mock import patch, MagicMock

from api.servicios.puesto.puesto_service import obtener_puestos_por_acto


class TestObtenerPuestosPorActo(unittest.TestCase):

    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_devuelve_queryset_correctamente(self, mock_puesto_model):
        """
        Test: Devuelve queryset correctamente
        
        Given: Un ID de acto válido.
        When: Se invoca la función obtener_puestos_por_acto.
        Then: Se verifica que se encadenan correctamente los métodos select_related (para optimizar consultas) y filter (para filtrar por acto_id), retornando el queryset final.
        """
        acto_id = 1

        mock_objects = mock_puesto_model.objects
        mock_select_related = mock_objects.select_related.return_value
        mock_queryset_final = MagicMock()
        
        mock_select_related.filter.return_value = mock_queryset_final

        resultado = obtener_puestos_por_acto(acto_id)

        mock_objects.select_related.assert_called_once_with(
            'tipo_puesto', 
            'acto', 
            'acto__tipo_acto'
        )

        mock_select_related.filter.assert_called_once_with(acto_id=acto_id)

        self.assertEqual(resultado, mock_queryset_final)
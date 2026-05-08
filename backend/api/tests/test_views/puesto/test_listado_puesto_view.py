import unittest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIRequestFactory

from api.vistas.puesto.listado_puesto_view import PuestosPorActoListView


class TestPuestosPorActoListView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.acto_id = 1
        self.url = f'/actos/{self.acto_id}/puestos/'
        self.user = MagicMock()

        self.request = self.factory.get(self.url)
        self.request.user = self.user

        self.vista = PuestosPorActoListView()



    @patch('api.vistas.puesto.listado_puesto_view.PuestoListadoSerializer')
    @patch('api.vistas.puesto.listado_puesto_view.StandardResultsSetPagination')
    @patch('api.vistas.puesto.listado_puesto_view.obtener_puestos_por_acto')
    def test_devuelve_respuesta_paginada_correctamente(self, mock_obtener_puestos, mock_paginator_class, mock_serializer_class):
        """
        Test: Devuelve respuesta paginada correctamente
        
        Given: Una solicitud GET válida para listar los puestos de un acto específico.
        When: Se procesa la petición a través del método get de la vista PuestosPorActoListView.
        Then: El servicio recupera el queryset, el paginador recorta los resultados, el serializador los transforma y se retorna la respuesta paginada formateada.
        """
        mock_queryset = MagicMock()
        mock_obtener_puestos.return_value = mock_queryset

        mock_paginator_instance = MagicMock()
        mock_paginator_class.return_value = mock_paginator_instance
        puestos_paginados_mock = [MagicMock()]
        mock_paginator_instance.paginate_queryset.return_value = puestos_paginados_mock

        mock_serializer_instance = MagicMock()
        mock_serializer_class.return_value = mock_serializer_instance
        mock_serializer_instance.data = [{'id': 1, 'nombre': 'Puesto 1'}]

        mock_response = MagicMock()
        mock_paginator_instance.get_paginated_response.return_value = mock_response

        resultado = self.vista.get(self.request, acto_id=self.acto_id)

        mock_obtener_puestos.assert_called_once_with(acto_id=self.acto_id)
        mock_paginator_instance.paginate_queryset.assert_called_once_with(mock_queryset, self.request, view=self.vista)
        mock_serializer_class.assert_called_once_with(puestos_paginados_mock, many=True)
        mock_paginator_instance.get_paginated_response.assert_called_once_with(mock_serializer_instance.data)
        self.assertEqual(resultado, mock_response)



    @patch('api.vistas.puesto.listado_puesto_view.obtener_puestos_por_acto')
    def test_error_en_el_servicio_lanza_excepcion(self, mock_servicio):
        """
        Test: Error en el servicio
        
        Given: Un fallo inesperado en la lógica del servicio obtener_puestos_por_acto (o cualquier dependencia).
        When: La vista intenta recuperar los puestos del acto.
        Then: La excepción se propaga, interrumpiendo la ejecución de la vista para que sea manejada por el middleware de DRF.
        """
        error_msg = "Error de base de datos en el servicio"
        mock_servicio.side_effect = Exception(error_msg)

        with self.assertRaises(Exception) as context:
            self.vista.get(self.request, acto_id=self.acto_id)
            
        self.assertEqual(str(context.exception), error_msg)
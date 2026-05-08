import unittest
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate
from rest_framework.response import Response

from api.vistas.puesto.listado_puesto_view import PuestosPorActoListView


class TestPuestosPorActoListView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.client = APIClient()
        self.acto_id = 1
        self.url = f'/actos/{self.acto_id}/puestos/'

        self.user = MagicMock()

        self.vista = PuestosPorActoListView.as_view()



    def test_acceso_denegado_si_no_esta_autenticado(self):
        """
        Test: Acceso denegado si no está autenticado
        
        Given: Una solicitud GET de un usuario no identificado (anónimo).
        When: Se intenta acceder a la vista PuestosPorActoListView.
        Then: La API devuelve un error 401 Unauthorized debido a que falta la autenticación requerida.
        """
        request = self.factory.get(self.url)

        respuesta = self.vista(request, acto_id=self.acto_id)

        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)



    @patch('api.vistas.puesto.listado_puesto_view.PuestoListadoSerializer')
    @patch('api.vistas.puesto.listado_puesto_view.StandardResultsSetPagination')
    @patch('api.vistas.puesto.listado_puesto_view.obtener_puestos_por_acto')
    def test_devuelve_respuesta_paginada_correctamente(self, mock_obtener_puestos, mock_paginator_class, mock_serializer_class):
        """
        Test: Devuelve respuesta paginada correctamente
        
        Given: Una solicitud GET de un usuario autenticado para listar los puestos de un acto.
        When: Se procesa la petición a través de la vista.
        Then: El servicio recupera los datos, el paginador los procesa y se retorna una respuesta 200 OK con los datos serializados.
        """
        mock_queryset = MagicMock()
        mock_obtener_puestos.return_value = mock_queryset

        mock_paginator_instance = MagicMock()
        mock_paginator_class.return_value = mock_paginator_instance
        
        puestos_paginados_mock = [MagicMock()]
        mock_paginator_instance.paginate_queryset.return_value = puestos_paginados_mock

        mock_serializer_instance = MagicMock()
        mock_serializer_class.return_value = mock_serializer_instance
        datos_esperados = [{'id': 1, 'nombre': 'Puesto 1'}]
        mock_serializer_instance.data = datos_esperados

        mock_response = Response(datos_esperados, status=status.HTTP_200_OK)
        mock_paginator_instance.get_paginated_response.return_value = mock_response

        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)
        resultado = self.vista(request, acto_id=self.acto_id)

        mock_obtener_puestos.assert_called_once_with(acto_id=self.acto_id)
        self.assertEqual(resultado.status_code, status.HTTP_200_OK)
        self.assertEqual(resultado.data, datos_esperados)



    @patch('api.vistas.puesto.listado_puesto_view.obtener_puestos_por_acto')
    def test_error_en_el_servicio_lanza_excepcion(self, mock_servicio):
        """
        Test: Error en el servicio lanza excepción
        
        Given: Un usuario autenticado y un fallo inesperado en la lógica del servicio.
        When: La vista intenta recuperar los puestos.
        Then: La excepción se propaga para ser capturada por el manejador de excepciones de DRF.
        """
        error_msg = "Error de base de datos en el servicio"
        mock_servicio.side_effect = Exception(error_msg)

        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)

        with self.assertRaises(Exception) as context:
            self.vista(request, acto_id=self.acto_id)
            
        self.assertEqual(str(context.exception), error_msg)
import unittest
from unittest.mock import MagicMock, patch, ANY
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.response import Response

from api.vistas.cuota.cuota_view import MisCuotasListView
from api.models import Cuota


class TestMisCuotasListView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.url = '/mis-cuotas/'
        self.user = MagicMock()
        self.user.is_authenticated = True

        self.view = MisCuotasListView.as_view()



    @patch("api.vistas.cuota.cuota_view.Cuota.objects")
    @patch("api.vistas.cuota.cuota_view.MisCuotasListView.get_serializer")
    @patch("api.vistas.cuota.cuota_view.MisCuotasListView.get_paginated_response")
    @patch("api.vistas.cuota.cuota_view.MisCuotasListView.paginate_queryset")
    def test_get_cuotas_flujo_paginado_exitoso(
        self, mock_paginate, mock_get_paginated, mock_get_serializer, mock_cuota_objects
    ):
        """
        Test: Flujo paginado con resumen (Rama 1)
        
        Given: Un usuario autenticado con múltiples cuotas.
        When: Se solicita el listado y el paginador devuelve una página válida.
        Then: Se filtra por usuario, se calcula el resumen, se serializa la página
            y se inyecta el resumen en la respuesta paginada de DRF.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)

        mock_queryset = MagicMock(name="QuerySetCuotas")
        mock_cuota_objects.filter.return_value.order_by.return_value = mock_queryset
        mock_queryset.aggregate.return_value = {
            'total_cuotas': 10,
            'total_pagadas': 6,
            'total_pendientes': 4,
            'total_importe_pendiente': None 
        }

        mock_page = ["cuota_1", "cuota_2"]
        mock_paginate.return_value = mock_page

        mock_get_paginated.return_value = Response({
            "count": 10, 
            "results": [{"id": 1}]
        })

        mock_serializer = MagicMock()
        mock_serializer.data = [{"id": 1}]
        mock_get_serializer.return_value = mock_serializer

        response = self.view(request)

        mock_cuota_objects.filter.assert_called_once_with(hermano=self.user)

        mock_get_serializer.assert_called_once_with(mock_page, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("resumen", response.data)
        self.assertEqual(response.data["resumen"]["total_pendiente_euros"], 0.00)



    @patch("api.vistas.cuota.cuota_view.Cuota.objects")
    @patch("api.vistas.cuota.cuota_view.MisCuotasListView.get_serializer")
    @patch("api.vistas.cuota.cuota_view.MisCuotasListView.paginate_queryset")
    def test_get_cuotas_flujo_sin_paginacion(self, mock_paginate, mock_get_serializer, mock_cuota_objects):
        """
        Test: Flujo sin paginación (Rama 2)
        
        Given: Un usuario con pocas cuotas.
        When: El paginador devuelve None.
        Then: La vista retorna una respuesta manual con 'results' y 'resumen'.
        """
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)

        mock_queryset = MagicMock()
        mock_cuota_objects.filter.return_value.order_by.return_value = mock_queryset
        mock_queryset.aggregate.return_value = {
            'total_cuotas': 1, 'total_pagadas': 1, 'total_pendientes': 0, 'total_importe_pendiente': 30.0
        }

        mock_paginate.return_value = None
        
        mock_serializer = MagicMock()
        mock_serializer.data = [{"id": 1}]
        mock_get_serializer.return_value = mock_serializer

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("resumen", response.data)

        mock_get_serializer.assert_called_with(mock_queryset, many=True)



    def test_get_cuotas_usuario_no_autenticado_bloqueado(self):
        """
        Test: Seguridad - Usuario no autenticado
        
        Given: Una petición GET sin credenciales.
        When: Se intenta acceder a 'Mis Cuotas'.
        Then: Las permission_classes (IsAuthenticated) bloquean el acceso (401/403).
        """
        request = self.factory.get(self.url)

        response = MisCuotasListView.as_view()(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
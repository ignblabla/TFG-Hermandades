from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from api.servicios.acto.acto_service import ActoService

class ActoServiceGetTodosTests(TestCase):

    @patch('api.servicios.acto.acto_service.Acto.objects')
    @patch('api.servicios.acto.acto_service.timezone')
    def test_get_todos_los_actos_devuelve_queryset_filtrado_y_ordenado(self, mock_timezone, mock_objects):
        """
        Test: Devuelve queryset ordenado por fecha y filtrado por actos futuros

        Given: El servicio ActoService y una fecha actual fija.
        When: Se llama al método get_todos_los_actos.
        Then: Se debe invocar a Acto.objects.filter con fecha mayor o igual a la actual.
                Se debe encadenar el método order_by con el argumento 'fecha'.
                El método debe retornar el queryset final mockeado.
        """
        ahora = timezone.now()
        mock_timezone.now.return_value = ahora

        mock_queryset_filtrado = MagicMock()
        mock_queryset_ordenado = MagicMock()

        mock_objects.filter.return_value = mock_queryset_filtrado
        mock_queryset_filtrado.order_by.return_value = mock_queryset_ordenado

        resultado = ActoService.get_todos_los_actos()

        mock_objects.filter.assert_called_once_with(fecha__gte=ahora)
        mock_queryset_filtrado.order_by.assert_called_once_with('fecha')
        self.assertEqual(resultado, mock_queryset_ordenado)
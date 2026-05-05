from unittest.mock import patch, MagicMock
from django.test import TestCase
from api.servicios.hermano.hermano_service import get_estadisticas_hermanos_service

class TestEstadisticasHermanosService(TestCase):

    @patch('api.servicios.hermano.hermano_service.timezone')
    @patch('api.servicios.hermano.hermano_service.User')
    def test_get_estadisticas_hermanos_service_calculo_correcto(self, mock_user, mock_timezone):
        """
        Test: Cálculo correcto de estadísticas con datos válidos
        
        Given: Un año actual y simulaciones de conteos para altas, bajas e ingresos.
        When: Se llama al servicio de estadísticas de hermanos.
        Then: Retorna un diccionario con las claves correctas y los valores que coinciden con los conteos.
        """
        mock_now = MagicMock()
        mock_now.year = 2026
        mock_timezone.now.return_value = mock_now

        mock_user.EstadoHermano.ALTA = 'ALTA'
        mock_user.EstadoHermano.BAJA = 'BAJA'

        mock_queryset = MagicMock()
        mock_user.objects.filter.return_value = mock_queryset

        mock_queryset.count.side_effect = [150, 20, 15]

        resultado = get_estadisticas_hermanos_service()

        self.assertEqual(resultado, {
            'total_alta': 150,
            'total_baja': 20,
            'ingresos_anio_actual': 15
        })

        self.assertEqual(mock_user.objects.filter.call_count, 3)
        mock_timezone.now.assert_called_once()



    @patch('api.servicios.hermano.hermano_service.User')
    def test_get_estadisticas_hermanos_service_verificacion_filtros_estado(self, mock_user):
        """
        Test: Verificación de filtros por estado (ALTA y BAJA)
        
        Given: El servicio de estadísticas.
        When: Se ejecuta el servicio.
        Then: Se debe llamar a filter con estado_hermano=ALTA y luego con estado_hermano=BAJA.
        """
        mock_user.EstadoHermano.ALTA = 'A'
        mock_user.EstadoHermano.BAJA = 'B'
        
        mock_queryset = MagicMock()
        mock_user.objects.filter.return_value = mock_queryset
        mock_queryset.count.return_value = 0

        get_estadisticas_hermanos_service()

        mock_user.objects.filter.assert_any_call(estado_hermano='A')
        mock_user.objects.filter.assert_any_call(estado_hermano='B')



    @patch('api.servicios.hermano.hermano_service.timezone')
    @patch('api.servicios.hermano.hermano_service.User')
    def test_get_estadisticas_hermanos_service_verificacion_filtro_anio(self, mock_user, mock_timezone):
        """
        Test: Verificación de filtro por año actual
        
        Given: Una fecha específica retornada por timezone.now().
        When: Se ejecuta el cálculo de ingresos del año.
        Then: El filtro del queryset debe usar la clave fecha_ingreso_corporacion__year con el año actual.
        """
        anio_test = 2026
        mock_now = MagicMock()
        mock_now.year = anio_test
        mock_timezone.now.return_value = mock_now

        mock_queryset = MagicMock()
        mock_user.objects.filter.return_value = mock_queryset
        mock_queryset.count.return_value = 0

        get_estadisticas_hermanos_service()

        mock_user.objects.filter.assert_any_call(
            fecha_ingreso_corporacion__year=anio_test
        )
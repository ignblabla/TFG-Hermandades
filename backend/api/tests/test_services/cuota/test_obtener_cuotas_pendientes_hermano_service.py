import unittest
from unittest.mock import MagicMock, patch
from api.servicios.cuota.cuota_service import CuotaService

class TestCuotaService(unittest.TestCase):

    @patch('api.servicios.cuota.cuota_service.Cuota.objects.filter')
    def test_obtener_cuotas_pendientes_hermano_exito(self, mock_filter):
        """
        Test: Obtener cuotas pendientes de un hermano con éxito (Happy Path)
        
        Given: Un objeto hermano válido y estados 'PENDIENTE' y 'DEVUELTA'.
        When: Se solicitan las cuotas pendientes del hermano.
        Then: Se aplica el filtro por hermano y estados, se ordena por año y fecha de emisión, y se retorna el QuerySet resultante.
        """
        mock_hermano = MagicMock()

        estado_pendiente = 'PENDIENTE'
        estado_devuelta = 'DEVUELTA'

        mock_query_final = MagicMock()
        mock_filter.return_value.order_by.return_value = mock_query_final

        resultado = CuotaService.obtener_cuotas_pendientes_hermano(mock_hermano)

        mock_filter.assert_called_once_with(
            hermano=mock_hermano,
            estado__in=[estado_pendiente, estado_devuelta]
        )

        mock_filter.return_value.order_by.assert_called_once_with(
            'anio', 
            'fecha_emision'
        )

        self.assertEqual(resultado, mock_query_final)



    @patch('api.servicios.cuota.cuota_service.Cuota.objects.filter')
    def test_obtener_cuotas_pendientes_hermano_con_none(self, mock_filter):
        """
        Test: Obtener cuotas con hermano = None
        
        Given: Un valor de hermano igual a None.
        When: Se intenta obtener las cuotas pendientes.
        Then: El servicio no lanza excepciones y delega la consulta al ORM pasando el valor None en el filtro.
        """
        mock_filter.return_value.order_by.return_value = MagicMock()

        try:
            CuotaService.obtener_cuotas_pendientes_hermano(None)
        except Exception as e:
            self.fail(f"El servicio lanzó una excepción inesperada con hermano=None: {e}")

        mock_filter.assert_called_once()
        args, kwargs = mock_filter.call_args
        self.assertIsNone(kwargs.get('hermano'))



    @patch('api.servicios.cuota.cuota_service.Cuota.objects.filter')
    def test_obtener_cuotas_pendientes_contrato_retorno(self, mock_filter):
        """
        Test: Integridad del retorno del QuerySet
        
        Given: Un objeto hermano y una respuesta definida del ORM.
        When: Se ejecuta la lógica del servicio.
        Then: El servicio retorna exactamente el mismo objeto QuerySet que entrega el ORM, garantizando que no se rompa el lazy loading.
        """
        mock_hermano = MagicMock()

        mock_queryset_final = MagicMock()
        mock_filter.return_value.order_by.return_value = mock_queryset_final

        resultado = CuotaService.obtener_cuotas_pendientes_hermano(mock_hermano)

        self.assertIs(resultado, mock_queryset_final, "El servicio debe retornar el QuerySet original del ORM")
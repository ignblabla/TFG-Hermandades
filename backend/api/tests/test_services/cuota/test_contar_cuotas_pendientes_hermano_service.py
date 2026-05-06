import unittest
from unittest.mock import MagicMock, patch
from api.servicios.cuota.cuota_service import CuotaService


class TestCuotaServiceConteo(unittest.TestCase):

    @patch('api.servicios.cuota.cuota_service.CuotaService.obtener_cuotas_pendientes_hermano')
    def test_contar_cuotas_pendientes_hermano_exito(self, mock_obtener):
        """
        Test: Conteo exitoso de cuotas pendientes (Happy Path)
        
        Given: Un objeto hermano y un QuerySet que simula contener 10 cuotas.
        When: Se solicita el conteo de cuotas pendientes para dicho hermano.
        Then: Se invoca la obtención de cuotas, se ejecuta el método .count() del ORM y se retorna el valor exacto (10).
        """
        mock_hermano = MagicMock()
        valor_esperado = 10

        mock_queryset = MagicMock()
        mock_queryset.count.return_value = valor_esperado
        mock_obtener.return_value = mock_queryset

        resultado = CuotaService.contar_cuotas_pendientes_hermano(mock_hermano)

        mock_obtener.assert_called_once_with(mock_hermano)
        mock_queryset.count.assert_called_once()
        self.assertEqual(resultado, valor_esperado)



    @patch('api.servicios.cuota.cuota_service.CuotaService.obtener_cuotas_pendientes_hermano')
    def test_contar_cuotas_pendientes_hermano_vacio(self, mock_obtener):
        """
        Test: Conteo con resultado vacío
        
        Given: Un escenario donde el hermano no tiene cuotas de deuda registradas.
        When: Se solicita el conteo de cuotas pendientes.
        Then: El servicio retorna 0 como un valor entero, asegurando que no hay efectos secundarios ante resultados vacíos.
        """
        mock_queryset = MagicMock()
        mock_queryset.count.return_value = 0
        mock_obtener.return_value = mock_queryset

        resultado = CuotaService.contar_cuotas_pendientes_hermano(MagicMock())

        self.assertEqual(resultado, 0)
        self.assertIsInstance(resultado, int)



    @patch('api.servicios.cuota.cuota_service.CuotaService.contar_cuotas_pendientes_hermano')
    def test_contar_cuotas_pendientes_hermano_delegacion_excepciones(self, mock_obtener):
        """
        Test: Propagación de excepciones en el conteo
        
        Given: Un fallo crítico en el método base de obtención de cuotas (ej. error de BD).
        When: Se intenta realizar el conteo de cuotas.
        Then: La excepción original se propaga hacia arriba sin ser capturada o silenciada por el servicio.
        """
        excepcion_esperada = ValueError("Error de conexión a base de datos")
        mock_obtener.side_effect = excepcion_esperada

        with self.assertRaises(ValueError) as context:
            CuotaService.contar_cuotas_pendientes_hermano(MagicMock())
        
        self.assertEqual(str(context.exception), "Error de conexión a base de datos")
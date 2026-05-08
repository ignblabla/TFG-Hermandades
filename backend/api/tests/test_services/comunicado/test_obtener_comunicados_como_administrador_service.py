from unittest.mock import ANY, call, patch, MagicMock
from django.test import TestCase
from django.core.exceptions import PermissionDenied

from api.servicios.comunicado.comunicado_service import ComunicadoService


class TestObtenerTodosLosComunicadosPositivos(TestCase):

    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_devuelve_todos_los_comunicados_si_es_admin(self, mock_comunicado_model):
        """
        Test: Devuelve todos los comunicados correctamente si el usuario es admin
        
        Given: Un usuario con el atributo esAdmin en True.
        When: Se llama al servicio obtener_todos_los_comunicados(usuario).
        Then: Se construye la cadena del QuerySet con select_related, prefetch_related,
            all y order_by descendente por fecha, retornando el resultado esperado.
        """
        mock_usuario = MagicMock()
        mock_usuario.esAdmin = True

        mock_select_related_qs = MagicMock(name="SelectRelatedQS")
        mock_prefetch_related_qs = MagicMock(name="PrefetchRelatedQS")
        mock_all_qs = MagicMock(name="AllQS")
        mock_order_by_qs = MagicMock(name="OrderByQS")
        mock_resultado_esperado = [MagicMock(), MagicMock()]

        mock_comunicado_model.objects.select_related.return_value = mock_select_related_qs
        mock_select_related_qs.prefetch_related.return_value = mock_prefetch_related_qs
        mock_prefetch_related_qs.all.return_value = mock_all_qs
        mock_all_qs.order_by.return_value = mock_order_by_qs
        mock_order_by_qs.__iter__.return_value = iter(mock_resultado_esperado)

        resultado = ComunicadoService.obtener_todos_los_comunicados(mock_usuario)

        mock_comunicado_model.objects.select_related.assert_called_once_with('autor')
        mock_select_related_qs.prefetch_related.assert_called_once_with('areas_interes')
        mock_prefetch_related_qs.all.assert_called_once()
        mock_all_qs.order_by.assert_called_once_with('-fecha_emision')
        
        self.assertEqual(list(resultado), mock_resultado_esperado)



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_transversal_flujo_completo_orm_comunicados(self, mock_comunicado_model):
        """
        Test: Flujo completo del ORM para comunicados
        
        Given: Un usuario administrador.
        When: Se ejecuta el servicio.
        Then: Se verifica que el orden de las optimizaciones (select_related -> prefetch)
            y el ordenamiento final siguen la secuencia lógica definida.
        """
        mock_usuario = MagicMock()
        mock_usuario.esAdmin = True
        
        mock_select = MagicMock(name="SelectQS")
        mock_prefetch = MagicMock(name="PrefetchQS")
        mock_all = MagicMock(name="AllQS")
        mock_order = MagicMock(name="OrderQS")

        mock_comunicado_model.objects.select_related.return_value = mock_select
        mock_select.prefetch_related.return_value = mock_prefetch
        mock_prefetch.all.return_value = mock_all
        mock_all.order_by.return_value = mock_order

        manager = MagicMock()
        manager.attach_mock(mock_comunicado_model.objects.select_related, 'select_related')
        manager.attach_mock(mock_select.prefetch_related, 'prefetch_related')
        manager.attach_mock(mock_all.order_by, 'order_by')

        ComunicadoService.obtener_todos_los_comunicados(mock_usuario)

        expected_calls = [
            call.select_related('autor'),
            call.prefetch_related('areas_interes'),
            call.order_by('-fecha_emision')
        ]
        manager.assert_has_calls(expected_calls, any_order=False)



    def test_usuario_no_admin_lanza_excepcion(self):
        """
        Test: Usuario no administrador → lanza PermissionDenied
        
        Given: Un usuario con esAdmin en False o inexistente.
        When: Se llama al servicio.
        Then: Se eleva una excepción PermissionDenied con el mensaje correspondiente.
        """
        mock_usuario = MagicMock()
        mock_usuario.esAdmin = False

        with self.assertRaises(PermissionDenied) as cm:
            ComunicadoService.obtener_todos_los_comunicados(mock_usuario)
        
        self.assertEqual(str(cm.exception), "No tienes permisos para consultar el listado total de comunicados.")



    def test_usuario_sin_atributo_admin_lanza_excepcion(self):
        """
        Test: Usuario sin atributo 'esAdmin' → lanza PermissionDenied
        
        Given: Un objeto usuario que no posee el atributo 'esAdmin'.
        When: Se llama al servicio.
        Then: getattr devuelve False por defecto y se lanza la excepción.
        """
        mock_usuario = object() 

        with self.assertRaises(PermissionDenied):
            ComunicadoService.obtener_todos_los_comunicados(mock_usuario)
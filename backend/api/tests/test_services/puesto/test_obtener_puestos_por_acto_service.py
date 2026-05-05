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



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_filtra_correctamente_por_acto_id(self, mock_puesto):
        """
        Test: Filtra correctamente por acto_id
        
        Given: Un identificador de acto.
        When: Se ejecuta la consulta a través del servicio.
        Then: Se verifica que el método filter recibe exactamente el parámetro 'acto_id' con el valor proporcionado.
        """
        id_esperado = 42
        mock_qs = mock_puesto.objects.select_related.return_value

        obtener_puestos_por_acto(id_esperado)

        mock_qs.filter.assert_called_once_with(acto_id=id_esperado)



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_usa_correctamente_select_related(self, mock_puesto):
        """
        Test: Usa correctamente select_related
        
        Given: La necesidad de optimizar la consulta para evitar el problema de N+1.
        When: Se accede al gestor de objetos del modelo Puesto.
        Then: Se verifica que select_related se invoca con las relaciones 'tipo_puesto', 'acto' y la relación anidada 'acto__tipo_acto'.
        """
        obtener_puestos_por_acto(1)

        mock_puesto.objects.select_related.assert_called_once_with(
            'tipo_puesto', 
            'acto', 
            'acto__tipo_acto'
        )



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_encadenamiento_correcto_select_related_filter(self, mock_puesto):
        """
        Test: Encadenamiento correcto (select_related -> filter)
        
        Given: La implementación del servicio que busca optimizar antes de filtrar.
        When: Se llama a obtener_puestos_por_acto.
        Then: Se asegura que el método filter se llama sobre el objeto retornado por select_related, garantizando que el orden de los componentes del queryset es el esperado.
        """
        mock_select_related = MagicMock()
        mock_filter_result = MagicMock()

        mock_puesto.objects.select_related.return_value = mock_select_related
        mock_select_related.filter.return_value = mock_filter_result

        resultado = obtener_puestos_por_acto(10)

        self.assertEqual(resultado, mock_filter_result)

        mock_select_related.filter.assert_called_once()



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_devuelve_exactamente_el_resultado_de_filter(self, mock_puesto):
        """
        Test: Devuelve exactamente el resultado de filter
        
        Given: Un flujo de ejecución sin errores.
        When: Se invoca obtener_puestos_por_acto.
        Then: El objeto retornado debe ser idéntico al mock devuelto por el método .filter(), asegurando que no hay transformaciones intermedias no deseadas.
        """
        mock_qs_select = MagicMock()
        mock_qs_filter = MagicMock(spec=['__iter__', 'count'])
        
        mock_puesto.objects.select_related.return_value = mock_qs_select
        mock_qs_select.filter.return_value = mock_qs_filter

        resultado = obtener_puestos_por_acto(1)

        self.assertIs(resultado, mock_qs_filter)



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_error_en_select_related_lanza_excepcion(self, mock_puesto):
        """
        Test: Error en select_related
        
        Given: Un error inesperado de base de datos o de configuración de campos en select_related.
        When: Se intenta construir el queryset.
        Then: La excepción debe propagarse hacia arriba para ser manejada por el llamador.
        """
        mock_puesto.objects.select_related.side_effect = Exception("Campo de relación inválido")

        with self.assertRaises(Exception) as context:
            obtener_puestos_por_acto(1)
        self.assertEqual(str(context.exception), "Campo de relación inválido")



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_error_en_filter_lanza_excepcion(self, mock_puesto):
        """
        Test: Error en filter
        
        Given: Una base de datos no disponible o un error en los parámetros de filtrado.
        When: Se ejecuta el método .filter() tras el select_related.
        Then: El sistema debe lanzar la excepción correspondiente sin capturarla internamente.
        """
        mock_qs_select = MagicMock()
        mock_puesto.objects.select_related.return_value = mock_qs_select
        mock_qs_select.filter.side_effect = Exception("Database connection lost")

        with self.assertRaises(Exception) as context:
            obtener_puestos_por_acto(1)
        self.assertEqual(str(context.exception), "Database connection lost")



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_acto_id_es_none(self, mock_puesto):
        """
        Test: acto_id es None
        
        Given: Un valor None pasado como identificador de acto.
        When: Se ejecuta la función obtener_puestos_por_acto.
        Then: El servicio debe seguir su flujo normal y pasar el valor None al filtro de Django, permitiendo que el ORM maneje la consulta (que resultará en un queryset vacío o filtrado por NULL).
        """
        acto_id_nulo = None
        mock_qs_select = mock_puesto.objects.select_related.return_value

        obtener_puestos_por_acto(acto_id_nulo)

        mock_qs_select.filter.assert_called_once_with(acto_id=None)



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_queryset_vacio(self, mock_puesto):
        """
        Test: Queryset vacío
        
        Given: Un acto_id que no tiene puestos asociados en la base de datos.
        When: Se ejecuta el filtro.
        Then: El servicio debe retornar un queryset vacío (o el objeto mock que lo representa) sin lanzar excepciones.
        """
        mock_qs_select = MagicMock()
        mock_qs_vacio = MagicMock()
        mock_qs_vacio.__len__.return_value = 0
        
        mock_puesto.objects.select_related.return_value = mock_qs_select
        mock_qs_select.filter.return_value = mock_qs_vacio

        resultado = obtener_puestos_por_acto(999)

        self.assertEqual(len(resultado), 0)
        self.assertIs(resultado, mock_qs_vacio)



    @patch('api.servicios.puesto.puesto_service.Puesto')
    def test_verificar_campos_incluidos_en_select_related(self, mock_puesto):
        """
        Test: Verificar que se incluyen correctamente los campos en select_related
        
        Given: La necesidad de optimizar las claves foráneas principales y anidadas.
        When: Se construye el queryset base.
        Then: Se verifica que select_related incluye exactamente 'tipo_puesto', 'acto' y la relación profunda 'acto__tipo_acto' para evitar múltiples hits a la base de datos.
        """
        obtener_puestos_por_acto(1)

        args, kwargs = mock_puesto.objects.select_related.call_args
        self.assertIn('tipo_puesto', args)
        self.assertIn('acto', args)
        self.assertIn('acto__tipo_acto', args)
        self.assertEqual(len(args), 3)
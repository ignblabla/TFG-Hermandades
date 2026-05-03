import unittest
from unittest.mock import MagicMock, patch

from api.servicios.tipo_acto.tipo_acto_service import get_tipos_acto_service


class TestGetTiposActoService(unittest.TestCase):

    @patch("api.servicios.tipo_acto.tipo_acto_service.TipoActo.objects")
    def test_flujo_feliz_retorna_queryset_sin_modificar(self, mock_tipo_acto_objects):
        """
        Test: Flujo feliz (retorna queryset)
            Se llama a objects.all()
            No modifica el queryset
        
        Given: Un estado normal de la aplicación donde el ORM está operativo.
        When: Se llama al servicio get_tipos_acto_service().
        Then: Debe consultar todos los registros (all()) y devolver exactamente 
            el mismo objeto QuerySet que generó el ORM, sin clonarlo ni alterarlo.
        """
        mock_queryset = MagicMock()
        mock_tipo_acto_objects.all.return_value = mock_queryset

        resultado = get_tipos_acto_service()

        mock_tipo_acto_objects.all.assert_called_once()

        self.assertIs(resultado, mock_queryset)



    @patch("api.servicios.tipo_acto.tipo_acto_service.TipoActo.objects")
    def test_orm_lanza_excepcion_propaga_error(self, mock_tipo_acto_objects):
        """
        Test: ORM lanza excepción
        
        Given: Un problema de conectividad con la base de datos.
        When: El ORM intenta resolver TipoActo.objects.all().
        Then: La excepción no es capturada silenciosamente, sino que 
            se propaga hacia la capa superior (vista/controlador).
        """
        mock_tipo_acto_objects.all.side_effect = Exception("db error")

        with self.assertRaisesRegex(Exception, "db error"):
            get_tipos_acto_service()



    @patch("api.servicios.tipo_acto.tipo_acto_service.TipoActo.objects")
    def test_queryset_vacio_retorna_lista_vacia_sin_error(self, mock_tipo_acto_objects):
        """
        Test: queryset vacío
        
        Given: Una base de datos que aún no tiene tipos de actos definidos.
        When: Se invoca al servicio.
        Then: Retorna una lista o queryset vacío sin lanzar excepciones.
        """
        mock_tipo_acto_objects.all.return_value = []

        resultado = get_tipos_acto_service()

        self.assertEqual(resultado, [])



    @patch("api.servicios.tipo_acto.tipo_acto_service.TipoActo.objects")
    def test_mantiene_lazy_evaluation(self, mock_tipo_acto_objects):
        """
        Test: Se mantiene lazy evaluation (QuerySet)
        
        Given: El servicio devuelve un QuerySet de Django.
        When: Se realiza la llamada a objects.all().
        Then: Garantizamos que el servicio no itera ni evalúa el QuerySet prematuramente.
        """
        mock_queryset = MagicMock(name="QuerySet")
        mock_tipo_acto_objects.all.return_value = mock_queryset

        get_tipos_acto_service()

        mock_queryset.__iter__.assert_not_called()
        mock_queryset.__len__.assert_not_called()



    @patch("api.servicios.tipo_acto.tipo_acto_service.TipoActo")
    def test_objects_mal_configurado_lanza_error(self, mock_tipo_acto_class):
        """
        Test: objects mal configurado
        
        Given: Un problema a nivel de carga del modelo o un manager custom mal asignado.
        When: TipoActo.objects no está disponible (None).
        Then: Se levanta un AttributeError al intentar invocar .all().
        """
        mock_tipo_acto_class.objects = None

        with self.assertRaises(AttributeError):
            get_tipos_acto_service()



    @patch("api.servicios.tipo_acto.tipo_acto_service.TipoActo.objects")
    def test_idempotencia_multiples_llamadas(self, mock_tipo_acto_objects):
        """
        Test: Se puede usar múltiples veces (idempotencia)
        
        Given: La necesidad de obtener los tipos de acto en distintos puntos del código.
        When: Se llama al servicio varias veces consecutivas.
        Then: Cada llamada delega correctamente en objects.all().
        """
        get_tipos_acto_service()
        get_tipos_acto_service()

        self.assertEqual(mock_tipo_acto_objects.all.call_count, 2)
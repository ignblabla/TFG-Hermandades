import unittest
from unittest.mock import MagicMock, patch

from api.servicios.tipo_puesto.tipo_puesto_service import get_tipos_puesto_service


class TestGetTiposPuestoService(unittest.TestCase):

    @patch("api.servicios.tipo_puesto.tipo_puesto_service.TipoPuesto.objects")
    def test_flujo_feliz_retorna_queryset_sin_modificar(self, mock_tipo_puesto_objects):
        """
        Test: Flujo feliz (retorna queryset)
            Se llama a objects.all()
            No modifica el queryset (referencia)
        
        Given: Un estado operativo normal del ORM.
        When: Se invoca al servicio get_tipos_puesto_service().
        Then: Se debe consultar el modelo sin filtros (all()) y devolver 
            exactamente la misma referencia del objeto QuerySet.
        """
        mock_queryset = MagicMock()
        mock_tipo_puesto_objects.all.return_value = mock_queryset

        resultado = get_tipos_puesto_service()

        mock_tipo_puesto_objects.all.assert_called_once()

        self.assertIs(resultado, mock_queryset)



    @patch("api.servicios.tipo_puesto.tipo_puesto_service.TipoPuesto.objects")
    def test_orm_lanza_excepcion_propaga_error(self, mock_tipo_puesto_objects):
        """
        Test: ORM lanza excepción
        
        Given: Un fallo de conexión a la base de datos o un error en la consulta.
        When: El ORM intenta resolver TipoPuesto.objects.all().
        Then: La excepción no se silencia, sino que se propaga a la capa superior.
        """
        mock_tipo_puesto_objects.all.side_effect = Exception("db error")

        with self.assertRaisesRegex(Exception, "db error"):
            get_tipos_puesto_service()



    @patch("api.servicios.tipo_puesto.tipo_puesto_service.TipoPuesto.objects")
    def test_queryset_vacio_retorna_lista_vacia(self, mock_tipo_puesto_objects):
        """
        Test: queryset vacío
        
        Given: Una base de datos que aún no tiene tipos de puesto.
        When: Se invoca al servicio.
        Then: Retorna una lista o queryset vacío sin lanzar excepciones.
        """
        mock_tipo_puesto_objects.all.return_value = []

        resultado = get_tipos_puesto_service()

        self.assertEqual(resultado, [])



    @patch("api.servicios.tipo_puesto.tipo_puesto_service.TipoPuesto.objects")
    def test_idempotencia_multiples_llamadas(self, mock_tipo_puesto_objects):
        """
        Test: Idempotencia (múltiples llamadas)
        
        Given: Distintas partes de la aplicación requiriendo los tipos de puesto.
        When: Se invoca el servicio en repetidas ocasiones.
        Then: Cada llamada genera una consulta independiente al ORM.
        """
        get_tipos_puesto_service()
        get_tipos_puesto_service()

        self.assertEqual(mock_tipo_puesto_objects.all.call_count, 2)



    @patch("api.servicios.tipo_puesto.tipo_puesto_service.TipoPuesto")
    def test_objects_mal_configurado_lanza_error(self, mock_tipo_puesto_class):
        """
        Test: objects mal configurado
        
        Given: Un error de carga del modelo o alteración del atributo objects.
        When: TipoPuesto.objects es None.
        Then: La aplicación levanta un AttributeError.
        """
        mock_tipo_puesto_class.objects = None

        with self.assertRaises(AttributeError):
            get_tipos_puesto_service()



    @patch("api.servicios.tipo_puesto.tipo_puesto_service.TipoPuesto.objects")
    def test_lazy_evaluation_no_itera(self, mock_tipo_puesto_objects):
        """
        Test: Lazy evaluation (no itera)
        
        Given: El retorno de un QuerySet desde el ORM.
        When: El servicio pasa el resultado hacia la vista.
        Then: Garantizamos que el servicio devuelve la misma referencia 
            sin forzar la evaluación de la consulta SQL.
        """
        mock_queryset = MagicMock(name="QuerySet")
        mock_tipo_puesto_objects.all.return_value = mock_queryset
        
        result = get_tipos_puesto_service()

        self.assertIs(result, mock_queryset)

        mock_queryset.__iter__.assert_not_called()
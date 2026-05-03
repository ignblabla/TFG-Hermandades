import unittest
from unittest.mock import MagicMock, patch, ANY
from rest_framework.test import APIRequestFactory
from rest_framework.response import Response

from api.vistas.cuota.cuota_view import MisCuotasListView
from api.models import Cuota


class TestMisCuotasListView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.url = '/mis-cuotas/'
        self.user = MagicMock()

        self.request = self.factory.get(self.url)
        self.request.user = self.user



    @patch("api.vistas.cuota.cuota_view.Cuota.objects")
    @patch("api.vistas.cuota.cuota_view.CuotaSerializer")
    @patch("api.vistas.cuota.cuota_view.MisCuotasListView.get_paginated_response")
    @patch("api.vistas.cuota.cuota_view.MisCuotasListView.paginate_queryset")
    def test_flujo_paginado_correcto(
        self, mock_paginate, mock_get_paginated, mock_serializer, mock_cuota_objects
    ):
        """
        Test: Flujo paginado correcto
        
        Given: Un usuario autenticado que realiza una petición GET a sus cuotas.
        When: La vista ejecuta el método list() y la paginación devuelve una página válida.
        Then: Se calcula el resumen mediante ORM aggregate, se empaqueta en la respuesta 
            paginada junto con los resultados del serializador.
        """
        request = self.factory.get(self.url)
        request.user = self.user 

        mock_queryset = MagicMock()
        mock_cuota_objects.filter.return_value.order_by.return_value = mock_queryset
        
        mock_queryset.aggregate.return_value = {
            'total_cuotas': 10,
            'total_pagadas': 6,
            'total_pendientes': 4,
            'total_importe_pendiente': 120.50
        }

        mock_paginate.return_value = ["cuota_mock_1", "cuota_mock_2"]
        
        response_data = {"count": 10, "next": None, "previous": None, "results": []}
        mock_get_paginated.return_value = Response(response_data)

        mock_serializer_instance = MagicMock()
        datos_serializados = [{"id": 1, "importe": 30.0}, {"id": 2, "importe": 30.0}]
        mock_serializer_instance.data = datos_serializados
        mock_serializer.return_value = mock_serializer_instance

        vista = MisCuotasListView()
        vista.request = request
        vista.format_kwarg = None

        vista.serializer_class = mock_serializer

        respuesta = vista.list(request)

        mock_paginate.assert_called_once_with(mock_queryset)

        mock_serializer.assert_called_once_with(
            ["cuota_mock_1", "cuota_mock_2"], 
            many=True, 
            context=ANY
        )
        
        mock_get_paginated.assert_called_once_with(datos_serializados)

        self.assertIn("resumen", respuesta.data)
        self.assertEqual(respuesta.data["resumen"]["total_cuotas"], 10)
        self.assertEqual(respuesta.data["resumen"]["total_pendiente_euros"], 120.50)
        self.assertIn("count", respuesta.data)



    @patch("api.vistas.cuota.cuota_view.Cuota.objects")
    @patch("api.vistas.cuota.cuota_view.CuotaSerializer")
    @patch("api.vistas.cuota.cuota_view.MisCuotasListView.paginate_queryset")
    def test_flujo_sin_paginacion(self, mock_paginate, mock_serializer, mock_cuota_objects):
        """
        Test: Flujo sin paginación
        
        Given: Un usuario con pocas cuotas que no llegan al mínimo para paginar.
        When: paginate_queryset devuelve None.
        Then: La vista retorna un objeto Response plano que contiene el resumen 
            y la lista de resultados directamente.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_queryset = MagicMock()
        mock_cuota_objects.filter.return_value.order_by.return_value = mock_queryset
        mock_queryset.aggregate.return_value = {
            'total_cuotas': 2, 'total_pagadas': 2, 'total_pendientes': 0, 'total_importe_pendiente': 0
        }

        mock_paginate.return_value = None

        mock_serializer_instance = MagicMock()
        mock_serializer_instance.data = [{"id": 1}]
        mock_serializer.return_value = mock_serializer_instance

        vista = MisCuotasListView()
        vista.request = request
        vista.serializer_class = mock_serializer

        vista.format_kwarg = None
        vista.kwargs = {}

        respuesta = vista.list(request)

        self.assertIn("resumen", respuesta.data)
        self.assertIn("results", respuesta.data)
        self.assertEqual(len(respuesta.data["results"]), 1)



    @patch("api.vistas.cuota.cuota_view.Cuota.objects")
    def test_get_queryset_filtra_y_ordena_correctamente(self, mock_cuota_objects):
        """
        Test: get_queryset filtra por usuario
            Orden correcto aplicado
        
        Given: Una petición de un usuario específico.
        When: Se invoca al método get_queryset de la vista.
        Then: Se debe filtrar el modelo Cuota por el objeto 'user' del request 
            y aplicar el orden descendente por año y fecha de emisión.
        """
        request = self.factory.get(self.url)
        request.user = self.user
        
        vista = MisCuotasListView()
        vista.request = request

        vista.get_queryset()

        mock_cuota_objects.filter.assert_called_once_with(hermano=self.user)

        mock_cuota_objects.filter.return_value.order_by.assert_called_once_with(
            '-anio', '-fecha_emision'
        )



    @patch("api.vistas.cuota.cuota_view.Cuota.objects")
    @patch("api.vistas.cuota.cuota_view.CuotaSerializer")
    @patch("api.vistas.cuota.cuota_view.MisCuotasListView.paginate_queryset")
    def test_aggregate_y_resumen_calculados_correctamente(self, mock_paginate, mock_serializer, mock_cuota_objects):
        """
        Test: aggregate ejecutado correctamente
        
        Given: Un queryset con múltiples cuotas.
        When: Se ejecuta el método list().
        Then: Se deben llamar a las funciones de agregación del ORM y 
            mapear correctamente los resultados al diccionario de resumen.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_queryset = MagicMock()
        mock_cuota_objects.filter.return_value.order_by.return_value = mock_queryset

        mock_queryset.aggregate.return_value = {
            "total_cuotas": 10,
            "total_pagadas": 5,
            "total_pendientes": 3,
            "total_importe_pendiente": 100.0
        }

        mock_paginate.return_value = None

        vista = MisCuotasListView()
        vista.request = request
        vista.format_kwarg = None
        vista.serializer_class = mock_serializer

        respuesta = vista.list(request)

        self.assertEqual(respuesta.data["resumen"]["total_pendiente_euros"], 100.0)
        self.assertEqual(respuesta.data["resumen"]["total_cuotas"], 10)



    @patch("api.vistas.cuota.cuota_view.Cuota.objects")
    @patch("api.vistas.cuota.cuota_view.CuotaSerializer")
    @patch("api.vistas.cuota.cuota_view.MisCuotasListView.paginate_queryset")
    def test_calculo_importe_pendiente_none_safe(self, mock_paginate, mock_serializer, mock_cuota_objects):
        """
        Test: cálculo de importe pendiente None-safe
        
        Given: Un usuario sin deudas o con datos inconsistentes.
        When: El ORM devuelve None en la agregación de Sum (comportamiento por defecto de Django si no hay filas).
        Then: La vista debe convertir ese None a 0.00 para evitar errores en el frontend.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_queryset = MagicMock()
        mock_cuota_objects.filter.return_value.order_by.return_value = mock_queryset

        mock_queryset.aggregate.return_value = {
            "total_cuotas": 0,
            "total_pagadas": 0,
            "total_pendientes": 0,
            "total_importe_pendiente": None
        }

        mock_paginate.return_value = None

        vista = MisCuotasListView()
        vista.request = request
        vista.format_kwarg = None
        vista.serializer_class = mock_serializer

        respuesta = vista.list(request)

        self.assertEqual(respuesta.data["resumen"]["total_pendiente_euros"], 0.00)



    @patch("api.vistas.cuota.cuota_view.Cuota.objects")
    @patch("api.vistas.cuota.cuota_view.CuotaSerializer")
    @patch("api.vistas.cuota.cuota_view.MisCuotasListView.paginate_queryset")
    def test_queryset_vacio_no_falla(self, mock_paginate, mock_serializer, mock_cuota_objects):
        """
        Test: queryset vacío
        
        Given: Un hermano recién dado de alta sin cuotas generadas.
        When: Se accede a la vista.
        Then: La respuesta debe ser exitosa (200 OK) con todos los contadores en cero.
        """
        request = self.factory.get(self.url)
        request.user = self.user

        mock_queryset = MagicMock()
        mock_cuota_objects.filter.return_value.order_by.return_value = mock_queryset

        mock_queryset.aggregate.return_value = {
            "total_cuotas": 0,
            "total_pagadas": 0,
            "total_pendientes": 0,
            "total_importe_pendiente": 0.0
        }
        
        mock_paginate.return_value = None
        mock_serializer.return_value.data = []

        vista = MisCuotasListView()
        vista.request = request
        vista.format_kwarg = None
        vista.serializer_class = mock_serializer

        respuesta = vista.list(request)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["resumen"]["total_cuotas"], 0)
        self.assertEqual(respuesta.data["results"], [])



    @patch("api.vistas.cuota.cuota_view.Cuota.objects")
    @patch("api.vistas.cuota.cuota_view.CuotaSerializer")
    @patch("api.vistas.cuota.cuota_view.MisCuotasListView.paginate_queryset")
    def test_serializer_llamado_correctamente(self, mock_paginate, mock_serializer, mock_cuota_objects):
        """
        Test: serializer llamado correctamente
        
        Given: Una petición válida donde no aplica la paginación.
        When: Se prepara la respuesta.
        Then: El serializador debe instanciarse recibiendo el queryset, many=True 
            y el contexto de DRF.
        """
        mock_queryset = MagicMock()
        mock_cuota_objects.filter.return_value.order_by.return_value = mock_queryset
        mock_queryset.aggregate.return_value = {
            "total_cuotas": 1, "total_pagadas": 1, "total_pendientes": 0, "total_importe_pendiente": 0.0
        }
        mock_paginate.return_value = None

        vista = MisCuotasListView()
        vista.request = self.request
        vista.format_kwarg = None
        vista.serializer_class = mock_serializer

        vista.list(self.request)

        mock_serializer.assert_called_with(mock_queryset, many=True, context=ANY)



    @patch("api.vistas.cuota.cuota_view.Cuota.objects")
    @patch("api.vistas.cuota.cuota_view.MisCuotasListView.paginate_queryset")
    def test_paginate_queryset_lanza_excepcion(self, mock_paginate, mock_cuota_objects):
        """
        Test: paginate_queryset lanza excepción
        
        Given: Un error interno durante la paginación de DRF.
        When: paginate_queryset lanza una Exception.
        Then: La excepción se propaga hacia arriba (donde DRF la capturará para un 500).
        """
        mock_queryset = MagicMock()
        mock_cuota_objects.filter.return_value.order_by.return_value = mock_queryset
        mock_queryset.aggregate.return_value = {
            "total_cuotas": 1, "total_pagadas": 1, "total_pendientes": 0, "total_importe_pendiente": 0.0
        }

        mock_paginate.side_effect = Exception("pagination error")

        vista = MisCuotasListView()
        vista.request = self.request

        with self.assertRaisesRegex(Exception, "pagination error"):
            vista.list(self.request)



    @patch("api.vistas.cuota.cuota_view.Cuota.objects")
    def test_aggregate_falla_lanza_error_500(self, mock_cuota_objects):
        """
        Test: aggregate falla
        
        Given: Un problema de conexión a la base de datos o un timeout.
        When: El método aggregate() del ORM lanza una excepción.
        Then: La excepción sube para que el middleware de DRF devuelva un 500.
        """
        mock_queryset = MagicMock()
        mock_cuota_objects.filter.return_value.order_by.return_value = mock_queryset

        mock_queryset.aggregate.side_effect = Exception("db error")

        vista = MisCuotasListView()
        vista.request = self.request

        with self.assertRaisesRegex(Exception, "db error"):
            vista.list(self.request)



    @patch("api.vistas.cuota.cuota_view.Cuota.objects")
    @patch("api.vistas.cuota.cuota_view.CuotaSerializer")
    @patch("api.vistas.cuota.cuota_view.MisCuotasListView.get_paginated_response")
    @patch("api.vistas.cuota.cuota_view.MisCuotasListView.paginate_queryset")
    def test_resumen_incluido_en_response_paginado(self, mock_paginate, mock_get_paginated, mock_serializer, mock_cuota_objects):
        """
        Test: resumen incluido en response paginado
        
        Given: Una respuesta exitosa que activa la paginación.
        When: Se construye el Response final usando get_paginated_response.
        Then: Se debe inyectar manualmente la clave "resumen" dentro de response.data.
        """
        mock_queryset = MagicMock()
        mock_cuota_objects.filter.return_value.order_by.return_value = mock_queryset
        mock_queryset.aggregate.return_value = {
            "total_cuotas": 10, "total_pagadas": 10, "total_pendientes": 0, "total_importe_pendiente": 0.0
        }
        
        mock_paginate.return_value = ["cuota"]
        mock_get_paginated.return_value = Response({"results": []})
        mock_serializer.return_value = MagicMock(data=[])

        vista = MisCuotasListView()
        vista.request = self.request
        vista.format_kwarg = None
        vista.serializer_class = mock_serializer

        respuesta = vista.list(self.request)

        self.assertIn("resumen", respuesta.data)
        self.assertEqual(respuesta.data["resumen"]["total_cuotas"], 10)



    @patch("api.vistas.cuota.cuota_view.Cuota.objects")
    @patch("api.vistas.cuota.cuota_view.CuotaSerializer")
    @patch("api.vistas.cuota.cuota_view.MisCuotasListView.paginate_queryset")
    def test_usuario_sin_cuotas(self, mock_paginate, mock_serializer, mock_cuota_objects):
        """
        Test: usuario sin cuotas
        
        Given: Un usuario que no tiene registros en el modelo Cuota.
        When: Se realiza la consulta y agregación.
        Then: La lista de results está vacía y los contadores del resumen están en cero.
        """
        mock_queryset = MagicMock()
        mock_cuota_objects.filter.return_value.order_by.return_value = mock_queryset

        mock_queryset.aggregate.return_value = {
            "total_cuotas": 0, "total_pagadas": 0, "total_pendientes": 0, "total_importe_pendiente": None
        }
        mock_paginate.return_value = None
        mock_serializer.return_value.data = []

        vista = MisCuotasListView()
        vista.request = self.request
        vista.format_kwarg = None
        vista.serializer_class = mock_serializer

        respuesta = vista.list(self.request)

        self.assertEqual(respuesta.data["results"], [])
        self.assertEqual(respuesta.data["resumen"]["total_cuotas"], 0)
        self.assertEqual(respuesta.data["resumen"]["total_pendiente_euros"], 0.00)
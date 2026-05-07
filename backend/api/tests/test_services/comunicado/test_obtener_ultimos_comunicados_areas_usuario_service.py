from unittest.mock import MagicMock, patch

from django.test import TestCase

from api.servicios.comunicado.comunicado_service import ComunicadoService


class ObtenerUltimosComunicadosAreasServiceTests(TestCase):


    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_con_areas_filtra_por_areas_del_usuario(self, mock_Comunicado):
        """
        Test: Usuario con áreas -> filtra por áreas del usuario

        Given: Un usuario que tiene áreas de interés asignadas (exists() = True).
        When: Se llama a obtener_ultimos_comunicados_areas_usuario.
        Then: Se filtra usando areas_interes__in=areas_usuario.
                Se aplican los métodos distinct() y order_by('-fecha_emision').
                Se aplica el slicing [:2] para obtener solo los 2 últimos.
                Retorna el queryset resultante.
        """
        usuario = MagicMock()
        mock_areas_queryset = MagicMock()
        mock_areas_queryset.exists.return_value = True
        usuario.areas_interes.all.return_value = mock_areas_queryset

        mock_filter = MagicMock()
        mock_distinct = MagicMock()
        mock_order_by = MagicMock()
        resultado_esperado = ['comunicado_1', 'comunicado_2']

        mock_Comunicado.objects.filter.return_value = mock_filter
        mock_filter.distinct.return_value = mock_distinct
        mock_distinct.order_by.return_value = mock_order_by
        mock_order_by.__getitem__.return_value = resultado_esperado

        resultado = ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)

        usuario.areas_interes.all.assert_called_once()
        mock_areas_queryset.exists.assert_called_once()

        mock_Comunicado.objects.filter.assert_called_once_with(
            areas_interes__in=mock_areas_queryset
        )

        mock_filter.distinct.assert_called_once()
        mock_distinct.order_by.assert_called_once_with('-fecha_emision')
        mock_order_by.__getitem__.assert_called_once_with(slice(None, 2, None))

        self.assertEqual(resultado, resultado_esperado)



    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_sin_areas_usa_fallback_todos_hermanos(self, mock_Comunicado, mock_AreaInteres):
        """
        Test: Usuario sin áreas -> fallback a TODOS_HERMANOS

        Given: Un usuario que NO tiene áreas de interés (exists() = False).
        When: Se llama a obtener_ultimos_comunicados_areas_usuario.
        Then: Se utiliza el filtro por defecto: areas_interes__nombre_area=TODOS_HERMANOS.
                Se ejecuta la misma cadena de ORM: distinct() -> order_by() -> slice [:2].
        """
        usuario = MagicMock()
        mock_areas_queryset = MagicMock()
        mock_areas_queryset.exists.return_value = False
        usuario.areas_interes.all.return_value = mock_areas_queryset

        mock_filter = MagicMock()
        mock_distinct = MagicMock()
        mock_order_by = MagicMock()
        resultado_esperado = ['comunicado_default_1', 'comunicado_default_2']

        mock_Comunicado.objects.filter.return_value = mock_filter
        mock_filter.distinct.return_value = mock_distinct
        mock_distinct.order_by.return_value = mock_order_by
        mock_order_by.__getitem__.return_value = resultado_esperado

        resultado = ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)

        usuario.areas_interes.all.assert_called_once()
        mock_areas_queryset.exists.assert_called_once()

        mock_Comunicado.objects.filter.assert_called_once_with(
            areas_interes__nombre_area=mock_AreaInteres.NombreArea.TODOS_HERMANOS
        )

        mock_filter.distinct.assert_called_once()
        mock_distinct.order_by.assert_called_once_with('-fecha_emision')
        mock_order_by.__getitem__.assert_called_once_with(slice(None, 2, None))

        self.assertEqual(resultado, resultado_esperado)



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_si_falla_acceso_a_areas_propaga_excepcion(self, mock_Comunicado):
        """
        Test: Error en obtención de áreas (Fallo de relación)

        Given: Un usuario cuya relación 'areas_interes' lanza un error (ej. DatabaseError).
        When: Se llama a obtener_ultimos_comunicados_areas_usuario.
        Then: La excepción se propaga hacia arriba sin ser capturada por el servicio.
                ❗ No se llega a ejecutar ninguna consulta sobre Comunicado.
        """
        usuario = MagicMock()

        error_db = Exception("Error de conexión al acceder a la tabla de relación")
        usuario.areas_interes.all.side_effect = error_db

        with self.assertRaises(Exception) as context:
            ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)
        
        self.assertEqual(str(context.exception), "Error de conexión al acceder a la tabla de relación")

        mock_Comunicado.objects.filter.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_evalua_areas_del_usuario_una_sola_vez(self, mock_Comunicado):
        """
        Test: areas_usuario evaluado solo una vez

        Given: Un usuario con áreas de interés.
        When: Se llama a obtener_ultimos_comunicados_areas_usuario.
        Then: El método .all() de la relación areas_interes debe llamarse EXACTAMENTE una vez.
                Se valida que el servicio reutiliza la referencia local para evitar 
                consultas redundantes.
        """
        usuario = MagicMock()
        mock_areas_queryset = MagicMock()

        mock_areas_queryset.exists.return_value = True
        usuario.areas_interes.all.return_value = mock_areas_queryset

        ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)

        self.assertEqual(usuario.areas_interes.all.call_count, 1)



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_se_guia_estrictamente_por_exists_aunque_queryset_este_vacio(self, mock_Comunicado):
        """
        Test: Usuario con queryset vacío pero exists()=True (Caso Límite)

        Given: Un usuario cuya relación 'areas_interes.all()' devuelve un 
                QuerySet vacío pero, por una inconsistencia del mock, .exists() es True.
        When: Se llama a obtener_ultimos_comunicados_areas_usuario.
        Then: El servicio DEBE seguir la ruta de 'Usuario con áreas'.
                Se valida que la lógica depende exclusivamente de la veracidad de .exists().
        """
        usuario = MagicMock()
        mock_areas_queryset = MagicMock()

        mock_areas_queryset.__len__.return_value = 0
        mock_areas_queryset.exists.return_value = True 
        
        usuario.areas_interes.all.return_value = mock_areas_queryset

        ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)

        mock_Comunicado.objects.filter.assert_called_once_with(
            areas_interes__in=mock_areas_queryset
        )
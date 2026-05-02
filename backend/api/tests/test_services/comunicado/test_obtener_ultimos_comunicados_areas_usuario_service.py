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
    def test_obtener_ultimos_aplica_orden_descendente_por_fecha(self, mock_Comunicado):
        """
        Test: Verificar orden descendente por fecha

        Given: Un usuario con áreas de interés.
        When: Se llama a obtener_ultimos_comunicados_areas_usuario.
        Then: Se debe llamar a .order_by() con el argumento '-fecha_emision'.
                Esto asegura que los resultados sean los más recientes.
        """
        usuario = MagicMock()
        mock_areas_queryset = MagicMock()
        mock_areas_queryset.exists.return_value = True
        usuario.areas_interes.all.return_value = mock_areas_queryset

        mock_filter = MagicMock()
        mock_distinct = MagicMock()
        mock_order_by = MagicMock()

        mock_Comunicado.objects.filter.return_value = mock_filter
        mock_filter.distinct.return_value = mock_distinct
        mock_distinct.order_by.return_value = mock_order_by

        ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)

        mock_distinct.order_by.assert_called_once_with('-fecha_emision')



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_limita_resultados_a_dos_mediante_slicing(self, mock_Comunicado):
        """
        Test: Verificar límite de resultados (slice)

        Given: Un usuario con áreas de interés.
        When: Se llama a obtener_ultimos_comunicados_areas_usuario.
        Then: Se debe aplicar el slicing [:2] al final de la cadena del QuerySet.
                Se verifica que el método mágico __getitem__ recibe el objeto slice(None, 2, None).
        """
        usuario = MagicMock()
        mock_areas_queryset = MagicMock()
        mock_areas_queryset.exists.return_value = True
        usuario.areas_interes.all.return_value = mock_areas_queryset

        mock_filter = MagicMock()
        mock_distinct = MagicMock()
        mock_order_by = MagicMock()

        mock_Comunicado.objects.filter.return_value = mock_filter
        mock_filter.distinct.return_value = mock_distinct
        mock_distinct.order_by.return_value = mock_order_by

        ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)

        mock_order_by.__getitem__.assert_called_once_with(slice(None, 2, None))



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_sigue_el_encadenamiento_de_queryset_correcto(self, mock_Comunicado):
        """
        Test: Encadenamiento correcto de queryset

        Valida que el flujo de datos en el ORM siga este orden:
        1. filter (Reduce el universo de datos)
        2. distinct (Elimina duplicados por la relación M2M)
        3. order_by (Organiza cronológicamente)
        4. slice (Limita el resultado final)
        """
        usuario = MagicMock()
        mock_areas = MagicMock()
        mock_areas.exists.return_value = True
        usuario.areas_interes.all.return_value = mock_areas

        manager = MagicMock()
        
        mock_filter = MagicMock()
        mock_distinct = MagicMock()
        mock_order_by = MagicMock()

        mock_Comunicado.objects.filter.return_value = mock_filter
        manager.attach_mock(mock_Comunicado.objects.filter, 'filter')
        
        mock_filter.distinct.return_value = mock_distinct
        manager.attach_mock(mock_filter.distinct, 'distinct')
        
        mock_distinct.order_by.return_value = mock_order_by
        manager.attach_mock(mock_distinct.order_by, 'order_by')

        mock_order_by.__getitem__.return_value = [MagicMock(), MagicMock()]
        manager.attach_mock(mock_order_by.__getitem__, 'slice')

        ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)

        nombres_llamadas = [call[0] for call in manager.mock_calls]

        orden_esperado = [
            'filter',
            'distinct',
            'order_by',
            'slice'
        ]

        self.assertEqual(nombres_llamadas, orden_esperado)



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_retorna_exactamente_el_queryset_final(self, mock_Comunicado):
        """
        Test: Retorno correcto

        Given: Una cadena de QuerySet que termina en un slice.
        When: Se ejecuta obtener_ultimos_comunicados_areas_usuario.
        Then: El valor retornado debe ser idéntico al objeto final de la cadena del ORM.
                Se verifica la integridad de la referencia del objeto.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True

        mock_queryset_final = MagicMock(spec=list)

        mock_order_by = MagicMock()
        mock_order_by.__getitem__.return_value = mock_queryset_final

        mock_Comunicado.objects.filter.return_value.distinct.return_value.order_by.return_value = mock_order_by

        resultado = ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)

        self.assertIs(resultado, mock_queryset_final)
        self.assertEqual(len(mock_Comunicado.objects.filter.call_args_list), 1)



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
    def test_obtener_ultimos_si_falla_exists_propaga_excepcion(self, mock_Comunicado):
        """
        Test: Error en exists() (Fallo en evaluación de QuerySet)

        Given: Un usuario cuya relación de áreas lanza un error al ejecutar .exists().
        When: Se llama a obtener_ultimos_comunicados_areas_usuario.
        Then: La excepción se propaga hacia arriba.
                ❗ No se llega a la lógica de filtrado de Comunicado.
        """
        usuario = MagicMock()
        mock_areas_queryset = MagicMock()

        usuario.areas_interes.all.return_value = mock_areas_queryset
        mock_areas_queryset.exists.side_effect = RuntimeError("Database timeout en evaluación de existencia")

        with self.assertRaises(RuntimeError) as context:
            ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)
        
        self.assertEqual(str(context.exception), "Database timeout en evaluación de existencia")

        mock_Comunicado.objects.filter.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_si_falla_filter_inicial_propaga_excepcion(self, mock_Comunicado):
        """
        Test: Error en ORM (Fallo en filter inicial)

        Given: Un usuario con áreas de interés válidas.
        When: Comunicado.objects.filter() lanza una excepción (ej. FieldError o DatabaseError).
        Then: La excepción se propaga hacia arriba de forma transparente.
                ❗ No se llama a distinct(), order_by() ni al slicing.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True

        error_orm = Exception("Error de base de datos en la cláusula WHERE")
        mock_Comunicado.objects.filter.side_effect = error_orm

        with self.assertRaises(Exception) as context:
            ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)
        
        self.assertEqual(str(context.exception), "Error de base de datos en la cláusula WHERE")

        mock_Comunicado.objects.filter.assert_called_once()

        mock_Comunicado.objects.filter.return_value.distinct.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_si_falla_distinct_propaga_excepcion(self, mock_Comunicado):
        """
        Test: .distinct() lanza excepción (Fallo de QuerySet)

        Given: Un usuario con áreas de interés.
        When: Se llama a obtener_ultimos_comunicados_areas_usuario y .distinct() falla.
        Then: La excepción se propaga hacia arriba.
                ❗ No se ejecutan los pasos posteriores de la cadena (order_by, slice).
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True

        mock_filter = MagicMock()
        mock_Comunicado.objects.filter.return_value = mock_filter
        
        error_db = Exception("Error de base de datos: DISTINCT fallido")
        mock_filter.distinct.side_effect = error_db

        with self.assertRaises(Exception) as context:
            ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)
        
        self.assertEqual(str(context.exception), "Error de base de datos: DISTINCT fallido")

        mock_Comunicado.objects.filter.assert_called_once()

        mock_filter.distinct.assert_called_once()

        mock_filter.order_by.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_si_falla_order_by_propaga_excepcion(self, mock_Comunicado):
        """
        Test: .order_by() lanza excepción

        Given: Un usuario con áreas de interés.
        When: Se construye la consulta y .order_by() falla (ej. campo inexistente).
        Then: La excepción se propaga hacia arriba.
                ❗ No se llega a aplicar el slicing final.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True

        mock_filter = MagicMock()
        mock_distinct = MagicMock()
        
        mock_Comunicado.objects.filter.return_value = mock_filter
        mock_filter.distinct.return_value = mock_distinct
        
        error_db = Exception("Error de ordenación: campo '-fecha_emision' no reconocido")
        mock_distinct.order_by.side_effect = error_db

        with self.assertRaises(Exception) as context:
            ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)
        
        self.assertEqual(str(context.exception), "Error de ordenación: campo '-fecha_emision' no reconocido")

        mock_filter.distinct.assert_called_once()

        mock_distinct.order_by.assert_called_once_with('-fecha_emision')

        mock_distinct.order_by.return_value.__getitem__.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_si_falla_slicing_final_propaga_excepcion(self, mock_Comunicado):
        """
        Test: slicing [:2] falla (Fallo en acceso final)

        Given: Un usuario con áreas de interés válidas.
        When: Se intenta aplicar el slicing [:2] y ocurre un error (__getitem__ lanza excepción).
        Then: La excepción se propaga hacia arriba.
                Se confirma que el servicio no intenta mitigar fallos en el límite de resultados.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True

        mock_order_by = MagicMock()
        mock_Comunicado.objects.filter.return_value.distinct.return_value.order_by.return_value = mock_order_by

        error_slice = RuntimeError("Error al limitar los resultados del QuerySet")
        mock_order_by.__getitem__.side_effect = error_slice

        with self.assertRaises(RuntimeError) as context:
            ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)
        
        self.assertEqual(str(context.exception), "Error al limitar los resultados del QuerySet")

        mock_order_by.__getitem__.assert_called_once_with(slice(None, 2, None))



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



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_aplica_distinct_para_evitar_comunicados_duplicados(self, mock_Comunicado):
        """
        Test: Usuario con áreas duplicadas

        Given: Un usuario con múltiples áreas que podrían solaparse.
        When: Se ejecuta obtener_ultimos_comunicados_areas_usuario.
        Then: Se debe llamar al método .distinct() en la cadena del QuerySet.
                Esto garantiza que cada comunicado aparezca una sola vez,
                independientemente de a cuántas áreas del usuario pertenezca.
        """
        usuario = MagicMock()
        mock_areas = MagicMock()
        mock_areas.exists.return_value = True
        usuario.areas_interes.all.return_value = mock_areas

        mock_filter = MagicMock()
        mock_distinct = MagicMock()
        
        mock_Comunicado.objects.filter.return_value = mock_filter
        mock_filter.distinct.return_value = mock_distinct

        ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)

        mock_filter.distinct.assert_called_once()

        mock_distinct.order_by.assert_called_once_with('-fecha_emision')



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_funciona_si_hay_menos_de_dos_resultados(self, mock_Comunicado):
        """
        Test: Queryset devuelve menos de 2 resultados (Caso Límite)

        Given: Un usuario cuya consulta solo encuentra 1 comunicado.
        When: Se aplica el slicing [:2].
        Then: El servicio debe retornar el único comunicado encontrado sin errores.
                Se valida que el slicing del ORM maneja correctamente conjuntos pequeños.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True

        resultado_unico = ['comunicado_solitario']
        
        mock_order_by = MagicMock()
        mock_order_by.__getitem__.return_value = resultado_unico
        
        mock_Comunicado.objects.filter.return_value.distinct.return_value.order_by.return_value = mock_order_by

        resultado = ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado, resultado_unico)

        mock_order_by.__getitem__.assert_called_once_with(slice(None, 2, None))



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_devuelve_exactamente_dos_resultados_cuando_existen(self, mock_Comunicado):
        """
        Test: Queryset devuelve exactamente 2 resultados

        Given: Un usuario con áreas de interés y una base de datos con 2 comunicados que coinciden.
        When: Se llama a obtener_ultimos_comunicados_areas_usuario.
        Then: Se debe retornar una lista/queryset con exactamente esos 2 elementos.
                Se confirma que el límite coincide con la disponibilidad de datos.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True

        resultado_exacto = ['comunicado_reciente_1', 'comunicado_reciente_2']
        
        mock_order_by = MagicMock()
        mock_order_by.__getitem__.return_value = resultado_exacto
        
        mock_Comunicado.objects.filter.return_value.distinct.return_value.order_by.return_value = mock_order_by

        resultado = ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)

        self.assertEqual(len(resultado), 2)
        self.assertEqual(resultado, resultado_exacto)

        mock_order_by.__getitem__.assert_called_once_with(slice(None, 2, None))



    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_limita_a_dos_aunque_existan_muchos_resultados(self, mock_Comunicado):
        """
        Test: Queryset devuelve más de 2 resultados

        Given: Un usuario con áreas de interés y una base de datos con 10 comunicados coincidentes.
        When: Se llama a obtener_ultimos_comunicados_areas_usuario.
        Then: El resultado final debe contener exactamente 2 elementos.
                Se confirma que el slicing [:2] filtra el excedente de datos.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = True

        resultado_limitado = ['comunicado_reciente_1', 'comunicado_reciente_2']
        
        mock_order_by = MagicMock()

        mock_order_by.__getitem__.return_value = resultado_limitado
        
        mock_Comunicado.objects.filter.return_value.distinct.return_value.order_by.return_value = mock_order_by

        resultado = ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)

        self.assertEqual(len(resultado), 2)
        self.assertEqual(resultado, resultado_limitado)

        mock_order_by.__getitem__.assert_called_once_with(slice(None, 2, None))



    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_ejecuta_una_sola_rama_logica_exclusivamente(self, mock_Comunicado, mock_AreaInteres):
        """
        Test: Verificar que NO mezcla ambas ramas

        Given: Un usuario con áreas de interés (exists() = True).
        When: Se llama a obtener_ultimos_comunicados_areas_usuario.
        Then: Solo se debe ejecutar la rama de filtrado por áreas del usuario.
            ❗ NO debe llamarse al filtro de fallback (TODOS_HERMANOS).
        """
        usuario = MagicMock()
        mock_areas = MagicMock()
        mock_areas.exists.return_value = True
        usuario.areas_interes.all.return_value = mock_areas

        ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)

        mock_Comunicado.objects.filter.assert_called_once_with(
            areas_interes__in=mock_areas
        )

        for call in mock_Comunicado.objects.filter.call_args_list:
            args, kwargs = call
            self.assertNotIn('areas_interes__nombre_area', kwargs, 
                            "Se ejecutó el filtro de fallback cuando no correspondía")
            self.assertNotEqual(kwargs.get('areas_interes__nombre_area'), 
                                mock_AreaInteres.NombreArea.TODOS_HERMANOS)



    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado')
    def test_obtener_ultimos_usa_la_constante_exacta_en_el_filtro_de_fallback(self, mock_Comunicado, mock_AreaInteres):
        """
        Test: Verificar argumento exacto en fallback

        Given: Un usuario sin áreas de interés (exists() = False).
        When: Se llama a obtener_ultimos_comunicados_areas_usuario.
        Then: El filtro 'areas_interes__nombre_area' debe recibir exactamente 
                el valor AreaInteres.NombreArea.TODOS_HERMANOS.
        """
        usuario = MagicMock()
        usuario.areas_interes.all.return_value.exists.return_value = False

        valor_constante_esperado = "TODOS_HERMANOS_VALUE"
        mock_AreaInteres.NombreArea.TODOS_HERMANOS = valor_constante_esperado

        ComunicadoService.obtener_ultimos_comunicados_areas_usuario(usuario)

        mock_Comunicado.objects.filter.assert_called_once_with(
            areas_interes__nombre_area=valor_constante_esperado
        )



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
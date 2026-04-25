from django.test import TestCase
from unittest.mock import Mock, PropertyMock, patch, MagicMock

from django.core.exceptions import PermissionDenied

from api.servicios.comunicado.comunicado_service import ComunicadoService
from api.models import CuerpoPertenencia


class ComunicadoServiceTests(TestCase):

    # -----------------------------------------------------------------------------------------------------
    # CREAR COMUNICADO 
    # -----------------------------------------------------------------------------------------------------

    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_flujo_completo_correcto_sin_areas_sin_podcast(self, mock_create, mock_on_commit):
        """
        Test: Flujo completo correcto (sin áreas, sin podcast)

        Given: Un usuario válido.
                Un payload sin 'areas_interes' y con generar_podcast=False.
        When: Se llama a create_comunicado del servicio.
        Then: Se verifican permisos.
                Se crea el comunicado en BD asociado al autor.
                NO se asocian áreas de interés.
                Se notifica a Telegram con una lista de áreas vacía.
                Se registra en transaction.on_commit el embedding.
                NO se registra la tarea del podcast.
                Se retorna el objeto creado.
        """
        servicio = ComunicadoService()

        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()

        usuario = MagicMock()

        data_validada = {
            'titulo': 'Nuevo comunicado',
            'contenido': 'Texto importante',
            'generar_podcast': False
        }

        mock_comunicado = MagicMock()
        mock_comunicado.id = 1
        mock_comunicado.generar_podcast = False
        mock_create.return_value = mock_comunicado

        resultado = servicio.create_comunicado(usuario, data_validada.copy())

        servicio._verificar_permisos.assert_called_once_with(usuario)

        mock_create.assert_called_once_with(autor=usuario, **data_validada)

        mock_comunicado.areas_interes.set.assert_not_called()

        servicio._notificar_telegram.assert_called_once_with(mock_comunicado, [])

        mock_on_commit.assert_called_once()

        self.assertEqual(resultado, mock_comunicado)



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_flujo_con_areas_interes_asigna_m2m_y_notifica(self, mock_create, mock_on_commit):
        """
        Test: Flujo con áreas_interes

        Given: Un usuario válido.
                Un payload que incluye una lista de IDs en 'areas_interes'.
        When: Se llama a create_comunicado.
        Then: Las áreas se extraen del payload y NO se pasan al create().
                Se llama al método .set() del manager M2M con las áreas.
                Se llama a _notificar_telegram pasando las áreas correctas.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()

        usuario = MagicMock()

        areas_lista = [1, 2]
        data_validada = {
            'titulo': 'Comunicado segmentado',
            'contenido': 'Texto para ciertas áreas',
            'areas_interes': areas_lista,
            'generar_podcast': False
        }

        mock_comunicado = MagicMock()
        mock_comunicado.id = 1
        mock_comunicado.generar_podcast = False

        mock_m2m_manager = MagicMock()
        mock_comunicado.areas_interes = mock_m2m_manager
        
        mock_create.return_value = mock_comunicado

        resultado = servicio.create_comunicado(usuario, data_validada.copy())

        mock_create.assert_called_once_with(
            autor=usuario, 
            titulo='Comunicado segmentado',
            contenido='Texto para ciertas áreas',
            generar_podcast=False
        )

        mock_m2m_manager.set.assert_called_once_with(areas_lista)

        servicio._notificar_telegram.assert_called_once_with(mock_comunicado, areas_lista)



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_flujo_con_podcast_activado_registra_ambas_tareas_en_commit(self, mock_create, mock_on_commit):
        """
        Test: Flujo con podcast activado

        Given: Un usuario con permisos.
                Un payload donde 'generar_podcast' es True.
        When: Se llama a create_comunicado.
        Then: Se deben registrar dos llamadas a transaction.on_commit.
                La primera para la generación del embedding.
                La segunda específicamente para la generación del podcast.
                Se verifica que ambas lambdas se registran correctamente.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()

        usuario = MagicMock()
        data_validada = {
            'titulo': 'Comunicado con Audio',
            'generar_podcast': True
        }

        mock_comunicado = MagicMock()
        mock_comunicado.id = 42
        mock_comunicado.generar_podcast = True
        mock_create.return_value = mock_comunicado

        servicio.create_comunicado(usuario, data_validada.copy())

        self.assertEqual(mock_on_commit.call_count, 2)

        with patch('api.servicios.comunicado.comunicado_service.generar_y_guardar_embedding_async') as mock_emb, \
            patch('api.servicios.comunicado.comunicado_service.generar_y_guardar_podcast_async') as mock_pod:

            func_embedding = mock_on_commit.call_args_list[0][0][0]
            func_embedding()
            mock_emb.assert_called_once_with(mock_comunicado.id)

            func_podcast = mock_on_commit.call_args_list[1][0][0]
            func_podcast()
            mock_pod.assert_called_once_with(mock_comunicado.id)



    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_create_comunicado_inyecta_autor_proporcionado_ignora_suplantacion(self, mock_create):
        """
        Test: Verificar uso de autor=usuario

        Given: Un usuario autenticado (autor_real).
                Un payload de datos que malintencionadamente intenta incluir 
                un campo 'autor' o 'autor_id' (suplantación).
        When: Se llama al método create_comunicado.
        Then: El servicio debe llamar a Comunicado.objects.create usando 
                explícitamente autor=autor_real.
                Se garantiza que la identidad del autor proviene del contexto 
                del sistema y no del payload del usuario.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()

        autor_real = MagicMock()
        data_validada = {
            'titulo': 'Título legal',
            'autor': 999,
            'generar_podcast': False
        }

        mock_comunicado = MagicMock()
        mock_create.return_value = mock_comunicado

        servicio.create_comunicado(autor_real, data_validada.copy())

        args, kwargs = mock_create.call_args
        
        self.assertEqual(kwargs['autor'], autor_real)
        self.assertNotEqual(kwargs['autor'], 999)

        self.assertEqual(kwargs['titulo'], 'Título legal')



    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_areas_interes_se_elimina_de_data_validada_antes_del_create(self, mock_create):
        """
        Test: Verificar que data_validada se modifica correctamente

        Given: Un usuario con permisos.
                Un diccionario data_validada que contiene 'areas_interes'.
        When: Se llama a create_comunicado.
        Then: El campo 'areas_interes' debe ser extraído (pop) del diccionario.
                El método Comunicado.objects.create NO debe recibir 'areas_interes' 
                como argumento, evitando errores de integridad del ORM.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()
        
        usuario = MagicMock()
        data_validada = {
            'titulo': 'Comunicado de Prueba',
            'contenido': 'Contenido',
            'areas_interes': [1, 2, 3],
            'generar_podcast': False
        }

        mock_comunicado = MagicMock()
        mock_create.return_value = mock_comunicado

        servicio.create_comunicado(usuario, data_validada)

        args, kwargs = mock_create.call_args

        self.assertNotIn('areas_interes', kwargs, 
            "Error: 'areas_interes' se pasó al método create y debería haber sido extraído.")

        self.assertEqual(kwargs['titulo'], 'Comunicado de Prueba')
        self.assertEqual(kwargs['autor'], usuario)



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_verificar_permisos_lanza_excepcion_detiene_ejecucion_total(self, mock_create, mock_on_commit):
        """
        Test: Permisos -> _verificar_permisos lanza PermissionDenied

        Given: Un usuario que no tiene los permisos necesarios.
                El método _verificar_permisos está configurado para lanzar PermissionDenied.
        When: Se intenta llamar a create_comunicado.
        Then: La excepción PermissionDenied se propaga.
                Garantiza que NO se llama a Comunicado.objects.create (no hay persistencia).
                Garantiza que NO se llama a _notificar_telegram.
                Garantiza que NO se registra ninguna tarea en on_commit.
        """
        servicio = ComunicadoService()

        servicio._verificar_permisos = MagicMock(side_effect=PermissionDenied("No tienes permiso"))
        servicio._notificar_telegram = MagicMock()
        
        usuario_no_autorizado = MagicMock()
        data_validada = {'titulo': 'Intento fallido', 'generar_podcast': True}

        with self.assertRaises(PermissionDenied):
            servicio.create_comunicado(usuario_no_autorizado, data_validada)

        mock_create.assert_not_called()

        servicio._notificar_telegram.assert_not_called()

        mock_on_commit.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_create_lanza_excepcion_y_detiene_flujo_posterior(self, mock_create, mock_on_commit):
        """
        Test: Errores en creación -> Comunicado.objects.create lanza excepción

        Given: Un usuario con permisos.
        When: El método Comunicado.objects.create lanza una excepción (ej. DatabaseError).
        Then: La excepción se propaga hacia arriba.
                ❗ NO se llama al método de notificación a Telegram.
                ❗ NO se registran lambdas en transaction.on_commit.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()
        
        usuario = MagicMock()
        data_validada = {'titulo': 'Comunicado Fallido', 'generar_podcast': True}

        mensaje_error = "Error de integridad o conexión en BD"
        mock_create.side_effect = Exception(mensaje_error)

        with self.assertRaises(Exception) as context:
            servicio.create_comunicado(usuario, data_validada)
        
        self.assertEqual(str(context.exception), mensaje_error)

        mock_create.assert_called_once()

        servicio._notificar_telegram.assert_not_called()

        mock_on_commit.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_set_areas_interes_lanza_excepcion_y_detiene_flujo_posterior(self, mock_create, mock_on_commit):
        """
        Test: Errores en asignación de áreas -> .areas_interes.set lanza excepción

        Given: Un usuario con permisos y un payload con áreas.
                El comunicado se crea correctamente.
        When: El método .set() de la relación areas_interes falla.
        Then: La excepción se propaga hacia arriba.
                ❗ NO se llama al método de notificación a Telegram.
                ❗ NO se registran las tareas asíncronas en on_commit.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()
        
        usuario = MagicMock()
        data_validada = {
            'titulo': 'Comunicado con Áreas Fallidas',
            'areas_interes': [1, 2],
            'generar_podcast': True
        }

        mock_comunicado = MagicMock()
        mock_m2m = MagicMock()
        mensaje_error = "Fallo en tabla intermedia M2M"
        mock_m2m.set.side_effect = Exception(mensaje_error)
        
        mock_comunicado.areas_interes = mock_m2m
        mock_create.return_value = mock_comunicado

        with self.assertRaises(Exception) as context:
            servicio.create_comunicado(usuario, data_validada)
        
        self.assertEqual(str(context.exception), mensaje_error)

        mock_create.assert_called_once()
        mock_m2m.set.assert_called_once()

        servicio._notificar_telegram.assert_not_called()

        mock_on_commit.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_notificar_telegram_lanza_excepcion_y_detiene_on_commit(self, mock_create, mock_on_commit):
        """
        Test: Errores en notificación -> _notificar_telegram lanza excepción

        Given: Un usuario con permisos.
                El comunicado y sus áreas se procesan correctamente.
        When: El método _notificar_telegram lanza una excepción.
        Then: La excepción se propaga hacia arriba.
                ❗ NO se registran las tareas en transaction.on_commit.
                Nota: Al no haber manejo de errores, esto provocará un rollback 
                del comunicado en la base de datos debido al decorador @transaction.atomic.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        
        usuario = MagicMock()
        data_validada = {'titulo': 'Comunicado con Telegram Roto', 'generar_podcast': True}

        mock_comunicado = MagicMock()
        mock_create.return_value = mock_comunicado

        mensaje_error = "Error de conexión con la API de Telegram"
        servicio._notificar_telegram = MagicMock(side_effect=Exception(mensaje_error))

        with self.assertRaises(Exception) as context:
            servicio.create_comunicado(usuario, data_validada)
        
        self.assertEqual(str(context.exception), mensaje_error)

        mock_create.assert_called_once()
        servicio._notificar_telegram.assert_called_once()

        mock_on_commit.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_on_commit_lanza_excepcion_y_propaga_error(self, mock_create, mock_on_commit):
        """
        Test: Errores en transaction.on_commit -> lanza excepción

        Given: Un usuario con permisos y datos válidos (generar_podcast=True).
                El comunicado se crea y se notifica correctamente.
        When: La primera llamada a transaction.on_commit (para el embedding) falla.
        Then: La excepción se propaga hacia arriba.
                ❗ NO se llega a procesar la lógica del podcast (segundo on_commit).
                Garantiza que el flujo se detiene ante fallos de infraestructura de transacciones.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()
        
        usuario = MagicMock()
        data_validada = {
            'titulo': 'Comunicado con Fallo en Commit',
            'generar_podcast': True 
        }
        
        mock_comunicado = MagicMock()
        mock_comunicado.generar_podcast = True
        mock_create.return_value = mock_comunicado

        mensaje_error = "Error al registrar hook de on_commit"
        mock_on_commit.side_effect = Exception(mensaje_error)

        with self.assertRaises(Exception) as context:
            servicio.create_comunicado(usuario, data_validada)
        
        self.assertEqual(str(context.exception), mensaje_error)

        self.assertEqual(mock_on_commit.call_count, 1)



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_areas_interes_ausente_usa_lista_vacia_por_defecto_y_no_rompe(self, mock_create, mock_on_commit):
        """
        Test: Casos límite -> areas_interes no viene en data_validada

        Given: Un usuario con permisos.
                Un payload donde la clave 'areas_interes' no existe en el diccionario.
        When: Se llama al método create_comunicado.
        Then: El servicio no debe lanzar KeyError.
                Se debe usar una lista vacía [] por defecto para las áreas.
                NO se debe llamar a comunicado.areas_interes.set().
                Se llama a _notificar_telegram con la lista vacía.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()
        
        usuario = MagicMock()
        data_parcial = {
            'titulo': 'Comunicado sin áreas',
            'generar_podcast': False
        }
        
        mock_comunicado = MagicMock()
        mock_comunicado.generar_podcast = False
        mock_create.return_value = mock_comunicado

        resultado = servicio.create_comunicado(usuario, data_parcial)

        mock_create.assert_called_once()

        mock_comunicado.areas_interes.set.assert_not_called()

        servicio._notificar_telegram.assert_called_once_with(mock_comunicado, [])
        
        self.assertEqual(resultado, mock_comunicado)



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_areas_interes_es_none_no_ejecuta_set_y_continua_flujo(self, mock_create, mock_on_commit):
        """
        Test: areas_interes = None

        Given: Un usuario con permisos.
                Un payload donde 'areas_interes' es explícitamente None.
        When: Se llama al método create_comunicado.
        Then: El valor None se extrae correctamente.
                La condición 'if areas:' evalúa a False.
                ❗ NO se llama a comunicado.areas_interes.set().
                Se llama a _notificar_telegram pasando None (o el valor extraído).
                El flujo termina correctamente.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()
        
        usuario = MagicMock()
        data_con_none = {
            'titulo': 'Comunicado con None',
            'areas_interes': None,
            'generar_podcast': False
        }
        
        mock_comunicado = MagicMock()
        mock_comunicado.generar_podcast = False
        mock_create.return_value = mock_comunicado

        servicio.create_comunicado(usuario, data_con_none)

        mock_create.assert_called_once()

        mock_comunicado.areas_interes.set.assert_not_called()

        servicio._notificar_telegram.assert_called_once_with(mock_comunicado, None)



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_generar_podcast_false_no_registra_segundo_on_commit(self, mock_create, mock_on_commit):
        """
        Test: generar_podcast = False

        Given: Un usuario con permisos.
                Un payload donde 'generar_podcast' es False.
        When: Se llama al método create_comunicado.
        Then: Se debe registrar exactamente UN transaction.on_commit (para el embedding).
                NO se debe registrar un segundo on_commit para el podcast.
                Se garantiza que la lógica condicional de tareas asíncronas es correcta.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()
        
        usuario = MagicMock()
        data_validada = {
            'titulo': 'Comunicado solo texto',
            'generar_podcast': False
        }

        mock_comunicado = MagicMock()
        mock_comunicado.id = 100
        mock_comunicado.generar_podcast = False
        mock_create.return_value = mock_comunicado

        servicio.create_comunicado(usuario, data_validada)

        self.assertEqual(mock_on_commit.call_count, 1)

        with patch('api.servicios.comunicado.comunicado_service.generar_y_guardar_embedding_async') as mock_emb:
            func_registrada = mock_on_commit.call_args[0][0]
            func_registrada()

            mock_emb.assert_called_once_with(mock_comunicado.id)

        with patch('api.servicios.comunicado.comunicado_service.generar_y_guardar_podcast_async') as mock_pod:
            mock_pod.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_generar_podcast_ausente_en_objeto_lanza_attribute_error(self, mock_create, mock_on_commit):
        """
        Test: generar_podcast no existe en el objeto

        Given: Un usuario con permisos.
                El ORM crea un objeto comunicado que, por error de esquema o mock,
                no posee el atributo 'generar_podcast'.
        When: Se llama al método create_comunicado.
        Then: Se debe lanzar un AttributeError al intentar evaluar la condición final.
                Se garantiza que el servicio no silencia errores de estructura del modelo.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()
        
        usuario = MagicMock()
        data_validada = {'titulo': 'Test de Atributo Faltante'}

        mock_comunicado_incompleto = MagicMock(spec=[]) 
        
        mock_create.return_value = mock_comunicado_incompleto

        with self.assertRaises(AttributeError):
            servicio.create_comunicado(usuario, data_validada)

        mock_create.assert_called_once()
        servicio._notificar_telegram.assert_called_once()

        self.assertEqual(mock_on_commit.call_count, 1)



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_on_commit_recibe_objetos_llamables_no_resultados(self, mock_create, mock_on_commit):
        """
        Test: Verificar que on_commit recibe funciones (no ejecución inmediata)

        Given: Un flujo de creación de comunicado estándar.
        When: El servicio registra las tareas en transaction.on_commit.
        Then: El primer argumento de cada llamada a on_commit debe ser un 
                objeto 'callable' (lambda o función).
                Se garantiza que no se están ejecutando las tareas de embedding 
                o podcast de forma síncrona durante la creación.
        """
        servicio = ComunicadoService()
        servicio._verificar_permisos = MagicMock()
        servicio._notificar_telegram = MagicMock()

        mock_comunicado = MagicMock()
        mock_comunicado.generar_podcast = True
        mock_create.return_value = mock_comunicado

        servicio.create_comunicado(MagicMock(), {'generar_podcast': True})

        self.assertEqual(mock_on_commit.call_count, 2)

        for i, call in enumerate(mock_on_commit.call_args_list):
            func_registrada = call[0][0]

            self.assertTrue(
                callable(func_registrada), 
                f"El registro {i} en on_commit no es un callable. ¿Se ejecutó por error?"
            )



    @patch('api.servicios.comunicado.comunicado_service.transaction.on_commit')
    @patch('api.servicios.comunicado.comunicado_service.Comunicado.objects.create')
    def test_verificar_orden_logico_de_pasos_del_servicio(self, mock_create, mock_on_commit):
        """
        Test: Verificar orden lógico de llamadas

        Given: Un flujo de creación con todos los elementos (áreas y podcast).
        When: Se ejecuta create_comunicado.
        Then: Se debe respetar estrictamente el orden:
                1. Verificar permisos (Seguridad primero).
                2. Crear objeto en BD (Persistencia).
                3. Asignar áreas M2M (Relaciones).
                4. Notificar a Telegram (Comunicación).
                5. Registrar tareas en on_commit (Post-procesamiento).
        """
        servicio = ComunicadoService()
        manager = Mock()

        servicio._verificar_permisos = manager.verificar_permisos
        servicio._notificar_telegram = manager.notificar_telegram
        mock_create.side_effect = lambda **kwargs: manager.create(**kwargs)
        mock_on_commit.side_effect = lambda func: manager.on_commit(func)
        mock_comunicado = MagicMock(name="Comunicado_Mock")
        mock_comunicado.generar_podcast = True
        mock_comunicado.areas_interes.set = manager.set_areas
        manager.create.return_value = mock_comunicado

        data_validada = {
            'titulo': 'Test de Orden',
            'areas_interes': [1],
            'generar_podcast': True
        }

        servicio.create_comunicado(MagicMock(), data_validada)

        nombres_llamadas = [call[0] for call in manager.mock_calls]

        orden_esperado = [
            'verificar_permisos',
            'create',
            'set_areas',
            'notificar_telegram',
            'on_commit',
            'on_commit'
        ]

        self.assertEqual(nombres_llamadas, orden_esperado, 
            f"El orden de ejecución es incorrecto. Se ejecutó: {nombres_llamadas}")
        


    # -----------------------------------------------------------------------------------------------------
    # VERIFICAR PERMISOS COMUNICADO
    # -----------------------------------------------------------------------------------------------------

    def test_usuario_admin_tiene_acceso_permitido_inmediato(self):
        """
        Test: Usuario admin → acceso permitido inmediato

        Given: Un usuario autenticado con esAdmin = True.
        When: Se llama al método auxiliar _verificar_permisos.
        Then: Retorna silenciosamente (None, no lanza excepción).
                ❗ NO evalúa la relación 'cuerpos' (verificando el early return).
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = True

        mock_cuerpos = MagicMock()
        usuario.cuerpos = mock_cuerpos

        try:
            resultado = servicio._verificar_permisos(usuario)
        except PermissionDenied:
            self.fail("_verificar_permisos bloqueó incorrectamente a un Administrador.")

        self.assertIsNone(resultado)

        mock_cuerpos.filter.assert_not_called()



    def test_usuario_junta_gobierno_acceso_permitido_tras_evaluar_cuerpos(self):
        """
        Test: Usuario junta de gobierno → acceso permitido

        Given: Un usuario autenticado.
                Que NO es administrador (esAdmin = False).
                Que posee el atributo 'cuerpos'.
        When: Se llama al método _verificar_permisos.
        Then: Se evalúa la rama de la Junta correctamente.
                El método filter().exists() devuelve True.
                Retorna sin error (None).
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = False

        mock_cuerpos = MagicMock()
        mock_cuerpos.filter.return_value.exists.return_value = True
        usuario.cuerpos = mock_cuerpos

        try:
            resultado = servicio._verificar_permisos(usuario)
        except PermissionDenied:
            self.fail("_verificar_permisos debería haber permitido el acceso al miembro de la Junta.")

        self.assertIsNone(resultado)

        from api.models import CuerpoPertenencia
        mock_cuerpos.filter.assert_called_once_with(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        )
        mock_cuerpos.filter.return_value.exists.assert_called_once()



    def test_usuario_admin_con_atributos_adicionales_ignora_evaluacion_de_junta(self):
        """
        Test: Usuario admin con atributos adicionales irrelevantes

        Given: Un usuario con esAdmin = True.
                El usuario también posee el atributo 'cuerpos' (que en este flujo es irrelevante).
        When: Se llama a _verificar_permisos.
        Then: El acceso se concede inmediatamente.
                ❗ No se realiza ninguna consulta al filtro de 'cuerpos'.
                Se valida que la lógica de Admin tiene prioridad y eficiencia sobre la de Junta.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = True

        mock_cuerpos = MagicMock()
        usuario.cuerpos = mock_cuerpos

        servicio._verificar_permisos(usuario)

        mock_cuerpos.filter.assert_not_called()
        mock_cuerpos.filter.return_value.exists.assert_not_called()



    def test_usuario_junta_aunque_tenga_esadmin_false(self):
        """
        Test: Usuario junta aunque tenga esAdmin=False

        Given: Un usuario autenticado con esAdmin = False (o ausente).
                El usuario pertenece al cuerpo de la Junta de Gobierno (exists = True).
        When: Se llama a _verificar_permisos.
        Then: El acceso se concede correctamente.
                Se valida que la lógica continúa hacia el chequeo de cuerpos 
                cuando el check de admin falla.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = False

        mock_cuerpos = MagicMock()
        mock_cuerpos.filter.return_value.exists.return_value = True
        usuario.cuerpos = mock_cuerpos

        try:
            resultado = servicio._verificar_permisos(usuario)
        except PermissionDenied:
            self.fail("El acceso debería permitirse por pertenencia a la Junta si no es Admin.")

        self.assertIsNone(resultado)

        from api.models import CuerpoPertenencia
        mock_cuerpos.filter.assert_called_once_with(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        )



    def test_usuario_con_cuerpos_pero_no_pertenece_a_junta_lanza_permission_denied(self):
        """
        Test: Usuario con cuerpos pero no junta

        Given: Un usuario autenticado con esAdmin = False.
                El usuario posee el atributo 'cuerpos'.
                Pero la consulta filter(JUNTA_GOBIERNO).exists() devuelve False.
        When: Se llama a _verificar_permisos.
        Then: Se lanza PermissionDenied.
                Se valida que el flujo agota la vía de Junta y llega al bloqueo final.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = False

        mock_cuerpos = MagicMock()
        mock_cuerpos.filter.return_value.exists.return_value = False
        usuario.cuerpos = mock_cuerpos

        with self.assertRaises(PermissionDenied) as context:
            servicio._verificar_permisos(usuario)

        self.assertEqual(str(context.exception), "No tienes permisos para gestionar comunicados.")

        mock_cuerpos.filter.assert_called_once()



    def test_usuario_no_autenticado_detiene_ejecucion_inmediatamente(self):
        """
        Test: Usuario no autenticado → PermissionDenied

        Given: Un objeto usuario donde is_authenticated = False.
        When: Se llama al método _verificar_permisos.
        Then: Se lanza PermissionDenied.
                ❗ No se accede al atributo 'esAdmin'.
                ❗ No se evalúa el atributo 'cuerpos'.
                Se garantiza que el anonimato es un bloqueo absoluto y prematuro.
        """
        servicio = ComunicadoService()

        usuario = MagicMock()
        usuario.is_authenticated = False

        with self.assertRaises(PermissionDenied) as context:
            servicio._verificar_permisos(usuario)
        
        self.assertEqual(str(context.exception), "No tienes permisos para gestionar comunicados.")

        self.assertFalse(usuario.esAdmin.called, 
            "Error: Se evaluó 'esAdmin' en un usuario no autenticado.")

        self.assertFalse(usuario.cuerpos.called, 
            "Error: Se intentó acceder a 'cuerpos' en un usuario no autenticado.")
        


    def test_usuario_autenticado_sin_permisos_lanza_permission_denied(self):
        """
        Test: Usuario autenticado sin permisos

        Given: Un usuario autenticado (is_authenticated = True).
                No es administrador (esAdmin = False).
                Posee el atributo 'cuerpos'.
                La consulta exists() para Junta de Gobierno devuelve False.
        When: Se llama al método _verificar_permisos.
        Then: Se lanza PermissionDenied.
                Se garantiza que un usuario común no puede saltarse las restricciones.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = False

        mock_cuerpos = MagicMock()
        mock_cuerpos.filter.return_value.exists.return_value = False
        usuario.cuerpos = mock_cuerpos

        with self.assertRaises(PermissionDenied) as context:
            servicio._verificar_permisos(usuario)

        self.assertEqual(str(context.exception), "No tienes permisos para gestionar comunicados.")

        mock_cuerpos.filter.assert_called_once()



    def test_usuario_sin_atributo_cuerpos_y_no_admin_lanza_permission_denied(self):
        """
        Test: Usuario sin atributo cuerpos

        Given: Un usuario autenticado.
                Que NO es administrador (esAdmin = False).
                Que NO posee el atributo 'cuerpos' (hasattr = False).
        When: Se llama a _verificar_permisos.
        Then: Se lanza PermissionDenied.
                Se valida que el código salta el bloque de la Junta y llega 
                al raise final de forma segura.
        """
        servicio = ComunicadoService()

        usuario = MagicMock(spec=['is_authenticated', 'esAdmin'])
        usuario.is_authenticated = True
        usuario.esAdmin = False

        with self.assertRaises(PermissionDenied) as context:
            servicio._verificar_permisos(usuario)

        self.assertEqual(str(context.exception), "No tienes permisos para gestionar comunicados.")



    def test_es_admin_falsy_no_activa_early_return_y_continua_verificacion(self):
        """
        Test: Casos límite de atributos falsy (esAdmin = None o False)

        Given: Un usuario autenticado.
                El atributo 'esAdmin' es None o False.
        When: Se llama a _verificar_permisos.
        Then: El early return de Admin NO se ejecuta.
                El flujo continúa para evaluar el atributo 'cuerpos'.
                Se garantiza que solo un True explícito (o evaluable como True) 
                concede el acceso inmediato.
        """
        for valor_falsy in [None, False]:
            with self.subTest(valor=valor_falsy):
                # 1. Setup
                servicio = ComunicadoService()
                usuario = MagicMock()
                usuario.is_authenticated = True
                usuario.esAdmin = valor_falsy

                mock_cuerpos = MagicMock()
                mock_cuerpos.filter.return_value.exists.return_value = False
                usuario.cuerpos = mock_cuerpos

                with self.assertRaises(PermissionDenied):
                    servicio._verificar_permisos(usuario)

                self.assertTrue(hasattr(usuario, 'cuerpos'))
                mock_cuerpos.filter.assert_called_once()



    def test_is_authenticated_es_none_se_trata_como_no_autenticado(self):
        """
        Test: is_authenticated = None (Falsy)

        Given: Un usuario donde is_authenticated es None.
        When: Se llama al método _verificar_permisos.
        Then: Se lanza PermissionDenied.
                Se garantiza que el sistema no es laxo con valores nulos 
                en la propiedad de autenticación.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        usuario.is_authenticated = None

        with self.assertRaises(PermissionDenied) as context:
            servicio._verificar_permisos(usuario)

        self.assertEqual(str(context.exception), "No tienes permisos para gestionar comunicados.")

        self.assertFalse(usuario.esAdmin.called)



    def test_filter_cuerpos_lanza_excepcion_y_se_propaga(self):
        """
        Test: Errores en queryset -> .filter() lanza excepción

        Given: Un usuario autenticado que no es administrador.
        When: Se intenta filtrar sus cuerpos de pertenencia.
                El ORM lanza una excepción (ej. DatabaseError).
        Then: La excepción se propaga hacia arriba sin ser silenciada.
                Se garantiza que el servicio no asume un 'False' ante un error técnico.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = False

        mensaje_error = "Error crítico de conexión con la base de datos"
        mock_cuerpos = MagicMock()
        mock_cuerpos.filter.side_effect = Exception(mensaje_error)
        usuario.cuerpos = mock_cuerpos

        with self.assertRaises(Exception) as context:
            servicio._verificar_permisos(usuario)
        
        self.assertEqual(str(context.exception), mensaje_error)

        mock_cuerpos.filter.assert_called_once()



    def test_exists_en_cuerpos_lanza_excepcion_y_se_propaga(self):
        """
        Test: .exists() lanza excepción

        Given: Un usuario autenticado que no es administrador.
        When: Se ejecuta la consulta final .exists() para verificar la Junta.
                La base de datos lanza un error de conexión (DatabaseError).
        Then: La excepción NO se captura dentro del método y se propaga.
                Se garantiza que el servicio no enmascara problemas de infraestructura.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = False

        mensaje_error = "Database Connection Timeout"
        mock_queryset = MagicMock()
        mock_queryset.exists.side_effect = Exception(mensaje_error)
        
        mock_cuerpos = MagicMock()
        mock_cuerpos.filter.return_value = mock_queryset
        usuario.cuerpos = mock_cuerpos

        with self.assertRaises(Exception) as context:
            servicio._verificar_permisos(usuario)
        
        self.assertEqual(str(context.exception), mensaje_error)

        mock_cuerpos.filter.assert_called_once()
        mock_queryset.exists.assert_called_once()



    def test_usuario_admin_con_cuerpos_roto_no_falla_por_early_return(self):
        """
        Test: Usuario admin con cuerpos roto

        Given: Un usuario autenticado con esAdmin = True.
                El atributo 'cuerpos' está en un estado corrupto o lanzaría 
                un error si se intentara acceder a él.
        When: Se llama al método _verificar_permisos.
        Then: El acceso se concede inmediatamente (None).
                ❗ NUNCA se accede al atributo 'cuerpos'.
                Se garantiza que un fallo en datos secundarios no bloquea al administrador.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = True

        type(usuario).cuerpos = PropertyMock(side_effect=RuntimeError("Acceso prohibido"))

        try:
            resultado = servicio._verificar_permisos(usuario)
        except RuntimeError:
            self.fail("El Admin fue bloqueado porque el código intentó acceder a 'cuerpos' innecesariamente.")
        except PermissionDenied:
            self.fail("El Admin fue denegado a pesar de tener privilegios superiores.")

        self.assertIsNone(resultado)



    def test_filter_devuelve_objeto_sin_exists_lanza_attribute_error(self):
        """
        Test: Usuario junta pero sin .exists()

        Given: Un usuario autenticado que no es administrador.
                El método .filter() de cuerpos devuelve, por error de mock o 
                de lógica, un objeto que carece de .exists() (ej. una lista o None).
        When: Se llama a _verificar_permisos.
        Then: Se lanza un AttributeError.
                Se valida que el servicio espera un contrato estricto con el ORM 
                y no silencia errores de tipos de datos.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = False

        mock_cuerpos = MagicMock()
        mock_cuerpos.filter.return_value = ["no_soy_un_queryset"] 
        usuario.cuerpos = mock_cuerpos

        with self.assertRaises(AttributeError):
            servicio._verificar_permisos(usuario)

        mock_cuerpos.filter.assert_called_once()



    def test_verificar_permisos_usa_el_filtro_de_cuerpo_correcto(self):
        """
        Test: Verificar que Junta usa filtro correcto

        Given: Un usuario autenticado que no es administrador.
        When: Se evalúa la pertenencia a cuerpos.
        Then: La llamada a .filter() debe incluir exactamente el argumento 
                nombre_cuerpo = CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = False
        
        mock_cuerpos = MagicMock()
        usuario.cuerpos = mock_cuerpos

        servicio._verificar_permisos(usuario)

        mock_cuerpos.filter.assert_called_once_with(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        )



    def test_prioridad_de_acceso_admin_corta_ejecucion_antes_de_consultar_junta(self):
        """
        Test: Flujo correcto de prioridad (Admin sobre Junta)

        Given: Un usuario que cumple AMBAS condiciones (esAdmin=True y pertenece a Junta).
        When: Se llama a _verificar_permisos.
        Then: El método debe retornar en la validación de Admin.
                ❗ No debe ejecutarse la consulta a la relación 'cuerpos'.
                Se garantiza que la vía más rápida tiene prioridad absoluta.
        """
        servicio = ComunicadoService()
        
        usuario = MagicMock()
        usuario.is_authenticated = True
        usuario.esAdmin = True

        mock_cuerpos = MagicMock()
        usuario.cuerpos = mock_cuerpos

        servicio._verificar_permisos(usuario)

        mock_cuerpos.filter.assert_not_called()



    # -----------------------------------------------------------------------------------------------------
    # NOTIFICAR TELEGRAM
    # -----------------------------------------------------------------------------------------------------

    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_envio_correcto_con_imagen_flujo_completo(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Envío correcto con imagen (flujo completo)

        Given: El token de Telegram está configurado.
                El comunicado tiene imagen_portada.
                Las áreas tienen canales de Telegram configurados.
        When: Se llama a _notificar_telegram.
        Then: Se valida la cadena del ORM (filter -> exclude).
                Se abre el archivo en modo binario.
                Se usa la API /sendPhoto con el timeout de 10s.
                Se adjuntan los files y el payload correctamente.
        """
        servicio = ComunicadoService()

        mock_settings.TELEGRAM_BOT_TOKEN = 'token_secreto_123'

        area_input_1 = MagicMock(id=10)
        area_input_2 = MagicMock(id=20)
        areas_ids = [area_input_1, area_input_2]

        area_db_1 = MagicMock(telegram_channel_id='@canal_general')
        area_db_2 = MagicMock(telegram_channel_id='@canal_socios')

        mock_exclude = mock_area_interes.objects.filter.return_value.exclude
        mock_exclude.return_value = [area_db_1, area_db_2]

        comunicado = MagicMock()
        comunicado.titulo = "Gran Evento"
        comunicado.contenido = "Contenido de prueba"

        mock_file_handler = MagicMock()
        comunicado.imagen_portada.open.return_value.__enter__.return_value = mock_file_handler

        servicio._notificar_telegram(comunicado, areas_ids)

        mock_area_interes.objects.filter.assert_called_once_with(
            id__in=[10, 20],
            telegram_channel_id__isnull=False
        )
        mock_exclude.assert_called_once_with(telegram_channel_id__exact='')

        self.assertEqual(comunicado.imagen_portada.open.call_count, 2)
        comunicado.imagen_portada.open.assert_called_with('rb')

        self.assertEqual(mock_post.call_count, 2)

        url_esperada = "https://api.telegram.org/bottoken_secreto_123/sendPhoto"
        
        args, kwargs = mock_post.call_args

        self.assertEqual(args[0], url_esperada)

        self.assertEqual(kwargs.get('timeout'), 10)

        self.assertEqual(kwargs.get('files'), {'photo': mock_file_handler})

        payload = kwargs.get('data')
        self.assertIn('chat_id', payload)
        self.assertEqual(payload['parse_mode'], 'HTML')
        self.assertIn("<b>🔔 Nuevo Comunicado: Gran Evento</b>", payload['caption'])



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_envio_correcto_sin_imagen(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Envío correcto sin imagen

        Given: El token de Telegram está configurado.
                El comunicado NO tiene imagen_portada (None).
                Hay un canal de Telegram configurado en el área.
        When: Se llama a _notificar_telegram.
        Then: Se utiliza el endpoint 'sendMessage'.
                El texto del comunicado se envía en el campo 'text' del payload.
                Se utiliza el timeout estándar de 5s para mensajes de texto.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'bot_token_abc'

        area_db = MagicMock(telegram_channel_id='@canal_solo_texto')
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_db]

        comunicado = MagicMock()
        comunicado.titulo = "Aviso Urgente"
        comunicado.contenido = "Este es un mensaje sin foto."
        comunicado.imagen_portada = None

        servicio._notificar_telegram(comunicado, [MagicMock(id=1)])

        url_esperada = "https://api.telegram.org/botbot_token_abc/sendMessage"
        args, kwargs = mock_post.call_args
        
        self.assertEqual(args[0], url_esperada)

        payload = kwargs.get('data')
        self.assertEqual(payload['chat_id'], '@canal_solo_texto')
        self.assertIn("Aviso Urgente", payload['text'])
        self.assertNotIn('caption', payload)

        self.assertEqual(kwargs.get('timeout'), 5)

        self.assertNotIn('files', kwargs, "Se adjuntó un archivo cuando no debía haber ninguno.")



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_token_configurado_construye_urls_correctamente(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Token configurado correctamente -> Construcción de URLs

        Given: Un token de Telegram específico configurado en settings.
        When: Se procesan envíos con y sin imagen.
        Then: Las URLs generadas deben seguir el formato estricto:
                https://api.telegram.org/bot<token>/<metodo>
        """
        servicio = ComunicadoService()
        token_test = "123456789:ABCDEFGH"
        mock_settings.TELEGRAM_BOT_TOKEN = token_test

        area_db = MagicMock(telegram_channel_id='@test_channel')
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_db]

        comunicado_con_foto = MagicMock()
        comunicado_con_foto.imagen_portada = MagicMock()

        comunicado_con_foto.imagen_portada.open.return_value.__enter__.return_value = MagicMock()
        
        servicio._notificar_telegram(comunicado_con_foto, [MagicMock(id=1)])
        
        expected_photo_url = f"https://api.telegram.org/bot{token_test}/sendPhoto"
        self.assertEqual(mock_post.call_args_list[0][0][0], expected_photo_url)

        mock_post.reset_mock()
        comunicado_sin_foto = MagicMock()
        comunicado_sin_foto.imagen_portada = None
        
        servicio._notificar_telegram(comunicado_sin_foto, [MagicMock(id=1)])
        
        expected_message_url = f"https://api.telegram.org/bot{token_test}/sendMessage"
        self.assertEqual(mock_post.call_args_list[0][0][0], expected_message_url)



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_envio_a_multiples_canales_de_telegram(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Múltiples canales de Telegram

        Given: El token de Telegram está configurado.
                Existen múltiples áreas con diferentes IDs de canal.
        When: Se llama a _notificar_telegram.
        Then: Se itera sobre todos los canales únicos.
                Se llama a requests.post tantas veces como canales haya.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'

        area_db_1 = MagicMock(telegram_channel_id='@canal_A')
        area_db_2 = MagicMock(telegram_channel_id='@canal_B')
        area_db_3 = MagicMock(telegram_channel_id='@canal_A')
        
        mock_area_interes.objects.filter.return_value.exclude.return_value = [
            area_db_1, area_db_2, area_db_3
        ]

        comunicado = MagicMock()
        comunicado.imagen_portada = None

        servicio._notificar_telegram(comunicado, [MagicMock(id=1)])

        self.assertEqual(mock_post.call_count, 2)

        llamadas = [call.kwargs['data']['chat_id'] for call in mock_post.call_args_list]
        self.assertIn('@canal_A', llamadas)
        self.assertIn('@canal_B', llamadas)



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_mensaje_corto_no_se_trunca_en_ningun_flujo(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Mensaje normal (< límites)

        Given: Un comunicado con título y contenido cortos.
        When: Se envía con imagen (límite 1000) y sin imagen (límite 3000).
        Then: El texto llega completo al payload.
                No se añade el sufijo de truncado "...".
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        
        area_db = MagicMock(telegram_channel_id='@canal_test')
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_db]

        titulo = "Aviso Corto"
        contenido = "Este contenido es breve."
        texto_esperado = f"<b>🔔 Nuevo Comunicado: {titulo}</b>\n\n{contenido}"

        comunicado_foto = MagicMock()
        comunicado_foto.titulo = titulo
        comunicado_foto.contenido = contenido
        comunicado_foto.imagen_portada.open.return_value.__enter__.return_value = MagicMock()

        servicio._notificar_telegram(comunicado_foto, [MagicMock(id=1)])
        
        payload_foto = mock_post.call_args.kwargs['data']
        self.assertEqual(payload_foto['caption'], texto_esperado)
        self.assertNotIn("... (ver web)", payload_foto['caption'])

        mock_post.reset_mock()
        comunicado_texto = MagicMock()
        comunicado_texto.titulo = titulo
        comunicado_texto.contenido = contenido
        comunicado_texto.imagen_portada = None

        servicio._notificar_telegram(comunicado_texto, [MagicMock(id=1)])

        payload_texto = mock_post.call_args.kwargs['data']
        self.assertEqual(payload_texto['text'], texto_esperado)
        self.assertNotIn("...", payload_texto['text'])



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_mensaje_con_lista_de_areas_vacia_no_realiza_envios(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Mensaje con áreas vacías

        Given: Una lista de areas_ids vacía [].
        When: Se llama a _notificar_telegram.
        Then: La consulta al ORM devuelve un QuerySet vacío.
                No se inicia el bucle de envío.
                NUNCA se llama a requests.post.
                El flujo termina sin errores.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'

        mock_area_interes.objects.filter.return_value.exclude.return_value = []
        
        comunicado = MagicMock()
        areas_ids_vacias = []

        servicio._notificar_telegram(comunicado, areas_ids_vacias)

        mock_area_interes.objects.filter.assert_called_once_with(
            id__in=[], 
            telegram_channel_id__isnull=False
        )

        mock_post.assert_not_called()

        self.assertFalse(comunicado.titulo.called)



    @patch('builtins.print')
    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_telegram_token_no_configurado_aborta_ejecucion(self, mock_area_interes, mock_settings, mock_post, mock_print):
        """
        Test: Token no configurado (Early Return)

        Given: TELEGRAM_BOT_TOKEN es None o no existe en settings.
        When: Se llama a _notificar_telegram.
        Then: Se imprime un mensaje de advertencia específico.
                El método termina inmediatamente (return).
                ❗ No se realiza ninguna petición HTTP (requests.post).
        """
        servicio = ComunicadoService()

        mock_settings.TELEGRAM_BOT_TOKEN = None
        
        comunicado = MagicMock()
        areas_ids = [MagicMock(id=1)]

        servicio._notificar_telegram(comunicado, areas_ids)

        mock_print.assert_called_once_with("TELEGRAM_BOT_TOKEN no configurado.")

        mock_post.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_fallo_orm_en_filtro_de_areas_propaga_excepcion(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Errores en áreas -> AreaInteres.objects.filter falla

        Given: El token de Telegram está configurado.
        When: Se intenta filtrar las áreas en la base de datos.
                El ORM lanza una excepción (ej. DatabaseError).
        Then: La excepción se propaga y corta la ejecución del método.
                ❗ No se llega a la sección de envío (requests.post).
                Se garantiza que no se ignoran errores de infraestructura.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'token_test'

        error_db = Exception("Error de conexión a la base de datos")
        mock_area_interes.objects.filter.side_effect = error_db
        
        comunicado = MagicMock()
        areas_ids = [MagicMock(id=1)]

        with self.assertRaises(Exception) as context:
            servicio._notificar_telegram(comunicado, areas_ids)
            
        self.assertEqual(str(context.exception), "Error de conexión a la base de datos")

        mock_post.assert_not_called()



    @patch('builtins.print')
    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_error_en_un_envio_no_detiene_el_bucle_de_otros_canales(self, mock_area_interes, mock_settings, mock_post, mock_print):
        """
        Test: Excepción en requests (Resiliencia)

        Given: Dos canales de Telegram configurados.
        When: La primera petición a requests.post lanza una excepción (ej. Timeout).
                La segunda petición es exitosa.
        Then: Se captura el error del primer canal y se imprime por consola.
                El bucle continúa y se realiza el segundo envío correctamente.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'token_test'

        canal_A = "@canal_A"
        canal_B = "@canal_B"
        
        area_1 = MagicMock(telegram_channel_id=canal_A)
        area_2 = MagicMock(telegram_channel_id=canal_B)
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_1, area_2]

        error_msg = "Connection Timeout"
        mock_post.side_effect = [Exception(error_msg), MagicMock()]
        
        comunicado = MagicMock(imagen_portada=None)

        servicio._notificar_telegram(comunicado, [MagicMock(id=1), MagicMock(id=2)])

        self.assertEqual(mock_post.call_count, 2)

        canal_que_fallo = mock_post.call_args_list[0].kwargs['data']['chat_id']
        canal_que_tuvo_exito = mock_post.call_args_list[1].kwargs['data']['chat_id']

        mock_print.assert_called_with(f"Error enviando telegram al canal {canal_que_fallo}: {error_msg}")

        self.assertCountEqual(
            [canal_que_fallo, canal_que_tuvo_exito], 
            [canal_A, canal_B]
        )



    @patch('builtins.print')
    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_error_al_abrir_imagen_se_captura_y_continua_bucle(self, mock_area_interes, mock_settings, mock_post, mock_print):
        """
        Test: Error en open imagen (Resiliencia I/O)

        Given: Un comunicado con imagen_portada.
                Existen dos canales de Telegram.
        When: El método .open('rb') de la imagen lanza un IOError en el primer canal.
        Then: La excepción se captura en el bloque except.
                Se imprime el error en consola.
                El bucle continúa e intenta procesar el siguiente canal.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'token_test'
        
        canal_1 = "@canal_fallido"
        canal_2 = "@canal_exitoso"
        
        area_1 = MagicMock(telegram_channel_id=canal_1)
        area_2 = MagicMock(telegram_channel_id=canal_2)
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_1, area_2]

        comunicado = MagicMock()
        comunicado.titulo = "Test I/O"

        error_io = IOError("No se pudo leer el archivo de imagen")
        comunicado.imagen_portada.open.side_effect = error_io

        servicio._notificar_telegram(comunicado, [MagicMock(id=1)])

        self.assertEqual(comunicado.imagen_portada.open.call_count, 2)

        mock_print.assert_any_call(f"Error enviando telegram al canal {canal_1}: {error_io}")

        mock_post.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_areas_sin_configuracion_telegram_no_producen_envios(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: áreas_con_telegram vacío

        Given: El token de Telegram está configurado.
                Se pasan IDs de áreas, pero el ORM devuelve una lista vacía 
                (porque no tienen channel_id o están vacíos).
        When: Se llama a _notificar_telegram.
        Then: El conjunto 'canales_a_enviar' resulta vacío.
                No se realiza ninguna llamada a requests.post.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'

        mock_area_interes.objects.filter.return_value.exclude.return_value = []
        
        comunicado = MagicMock()
        areas_ids = [MagicMock(id=1), MagicMock(id=2)]

        servicio._notificar_telegram(comunicado, areas_ids)

        mock_area_interes.objects.filter.assert_called_once()

        mock_post.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_canales_con_string_vacio_son_excluidos_y_no_reciben_notificacion(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Telegram channels inválidos (string vacío)

        Given: El token de Telegram está configurado.
                Existen áreas donde telegram_channel_id es una cadena vacía ('').
        When: Se llama a _notificar_telegram.
        Then: La consulta al ORM utiliza .exclude(telegram_channel_id__exact='') correctamente.
                No se realiza ninguna petición a requests.post para esos registros.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'token_test'

        mock_area_interes.objects.filter.return_value.exclude.return_value = []
        
        comunicado = MagicMock()
        areas_ids = [MagicMock(id=1)]

        servicio._notificar_telegram(comunicado, areas_ids)

        mock_area_interes.objects.filter.return_value.exclude.assert_called_once_with(
            telegram_channel_id__exact=''
        )

        mock_post.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_truncado_de_caption_cuando_supera_limite_de_imagen(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Texto demasiado largo -> Caption > 1000 caracteres (con imagen)

        Given: Un comunicado con un contenido muy extenso (ej. 1500 caracteres).
                El comunicado tiene imagen_portada.
        When: Se llama a _notificar_telegram.
        Then: El campo 'caption' enviado a Telegram no supera los 1011 caracteres 
                (1000 del recorte + el sufijo "... (ver web)").
                Se verifica que el texto termina con el sufijo de truncado.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'token_test'
        
        area_db = MagicMock(telegram_channel_id='@canal_test')
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_db]

        contenido_extenso = "A" * 1500
        comunicado = MagicMock()
        comunicado.titulo = "Noticia Larga"
        comunicado.contenido = contenido_extenso

        comunicado.imagen_portada.open.return_value.__enter__.return_value = MagicMock()

        servicio._notificar_telegram(comunicado, [MagicMock(id=1)])

        payload = mock_post.call_args.kwargs['data']
        caption_enviado = payload['caption']

        self.assertEqual(len(caption_enviado), 1013)
        self.assertTrue(caption_enviado.endswith("... (ver web)"))

        self.assertIn("<b>🔔 Nuevo Comunicado: Noticia Larga</b>", caption_enviado)



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_truncado_de_mensaje_cuando_supera_limite_de_texto_plano(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Texto > 3000 caracteres (sin imagen)

        Given: Un comunicado con un contenido extremadamente largo (ej. 5000 caracteres).
                El comunicado NO tiene imagen_portada.
        When: Se llama a _notificar_telegram.
        Then: El campo 'text' enviado a Telegram se corta a 3000 caracteres.
                Se verifica que se añade el sufijo de truncado "...".
                El tamaño final del mensaje es controlado para evitar errores 400.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'token_test'
        
        area_db = MagicMock(telegram_channel_id='@canal_texto_largo')
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_db]

        contenido_gigante = "B" * 5000
        comunicado = MagicMock()
        comunicado.titulo = "Boletín Extenso"
        comunicado.contenido = contenido_gigante
        comunicado.imagen_portada = None

        servicio._notificar_telegram(comunicado, [MagicMock(id=1)])

        payload = mock_post.call_args.kwargs['data']
        texto_enviado = payload['text']

        self.assertEqual(len(texto_enviado), 3003) 
        self.assertTrue(texto_enviado.endswith("..."))

        self.assertIn("<b>🔔 Nuevo Comunicado: Boletín Extenso</b>", texto_enviado)



    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_areas_ids_con_objetos_mal_formados_lanza_attribute_error(self, mock_area_interes, mock_settings):
        """
        Test: Datos mal formados -> areas_ids sin .id

        Given: El token de Telegram está configurado.
                Se pasa una lista 'areas_ids' que contiene objetos inválidos 
                (ej. strings) que no tienen el atributo .id.
        When: Se intenta construir la lista para el filtro del ORM.
        Then: Se lanza un AttributeError.
                Se valida que el método requiere objetos con una estructura específica.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        
        comunicado = MagicMock()
        areas_ids_corruptos = ["area_1", "area_2"] 

        with self.assertRaises(AttributeError):
            servicio._notificar_telegram(comunicado, areas_ids_corruptos)

        mock_area_interes.objects.filter.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_comunicado_sin_atributos_necesarios_lanza_error_al_construir_mensaje(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Comunicado sin título o contenido (Atributos faltantes)

        Given: Un objeto 'comunicado' que carece del atributo 'titulo' o 'contenido'.
        When: El servicio intenta construir el 'texto_mensaje'.
        Then: Se lanza un AttributeError.
                Se valida que el servicio depende de un objeto comunicado completo 
                y no gestiona la ausencia de campos obligatorios de plantilla.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'

        area_db = MagicMock(telegram_channel_id='@canal_test')
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_db]

        comunicado_incompleto = MagicMock(spec=[])

        with self.assertRaises(AttributeError):
            servicio._notificar_telegram(comunicado_incompleto, [MagicMock(id=1)])

        mock_post.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_mezcla_canales_validos_e_invalidos_solo_procesa_los_validos(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Un canal válido + uno inválido (Mezcla de canales)

        Given: El token de Telegram está configurado.
                Existen tres áreas: una válida, una con channel_id None 
                y una con channel_id vacío ('').
        When: Se llama a _notificar_telegram.
        Then: Solo se realiza una petición requests.post (la del canal válido).
                Se valida que los filtros .filter() y .exclude() limpian 
                correctamente la lista de destinatarios.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'

        canal_valido = "@canal_valido"
        area_valida = MagicMock(telegram_channel_id=canal_valido)

        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_valida]
        
        comunicado = MagicMock(imagen_portada=None)
        areas_ids = [MagicMock(id=1), MagicMock(id=2), MagicMock(id=3)]

        servicio._notificar_telegram(comunicado, areas_ids)

        self.assertEqual(mock_post.call_count, 1)

        payload = mock_post.call_args.kwargs['data']
        self.assertEqual(payload['chat_id'], canal_valido)

        mock_area_interes.objects.filter.assert_called_once_with(
            id__in=[a.id for a in areas_ids],
            telegram_channel_id__isnull=False
        )
        mock_area_interes.objects.filter.return_value.exclude.assert_called_once_with(
            telegram_channel_id__exact=''
        )



    @patch('builtins.print')
    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_excepcion_en_un_canal_no_detiene_envio_a_otros(self, mock_area_interes, mock_settings, mock_post, mock_print):
        """
        Test: Excepción en un canal no afecta otros

        Given: Dos canales de Telegram configurados.
        When: El primer envío de requests.post lanza una excepción (ej. ConnectionError).
        Then: Se captura el error y se imprime por consola.
                El bucle continúa con el siguiente canal.
                Se verifica que se realizaron ambos intentos de envío.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'token_test'
        
        canal_1 = "@canal_con_error"
        canal_2 = "@canal_exitoso"
        
        area_1 = MagicMock(telegram_channel_id=canal_1)
        area_2 = MagicMock(telegram_channel_id=canal_2)

        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_1, area_2]

        mock_post.side_effect = [Exception("Error de red"), MagicMock()]
        
        comunicado = MagicMock(imagen_portada=None)

        servicio._notificar_telegram(comunicado, [MagicMock(id=1)])

        self.assertEqual(mock_post.call_count, 2)

        llamadas_print = [call.args[0] for call in mock_print.call_args_list]
        self.assertTrue(any("Error enviando telegram al canal" in s for s in llamadas_print))

        chat_ids_procesados = [call.kwargs['data']['chat_id'] for call in mock_post.call_args_list]
        self.assertIn(canal_1, chat_ids_procesados)
        self.assertIn(canal_2, chat_ids_procesados)



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_mensaje_se_construye_una_sola_vez_fuera_del_bucle(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Orden correcto de construcción del mensaje

        Given: El token de Telegram está configurado.
                Existen múltiples canales de Telegram (3 canales).
        When: Se llama a _notificar_telegram.
        Then: El título y contenido del comunicado solo se acceden una vez.
                Se garantiza que la construcción del string es externa al bucle for,
                optimizando el uso de CPU y memoria.
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'

        canales = ['@canal_1', '@canal_2', '@canal_3']
        areas_db = [MagicMock(telegram_channel_id=c) for c in canales]
        mock_area_interes.objects.filter.return_value.exclude.return_value = areas_db

        comunicado = MagicMock()

        mock_titulo = PropertyMock(return_value="Título Único")
        mock_contenido = PropertyMock(return_value="Contenido Único")

        type(comunicado).titulo = mock_titulo
        type(comunicado).contenido = mock_contenido
        comunicado.imagen_portada = None

        servicio._notificar_telegram(comunicado, [MagicMock(id=1)])

        self.assertEqual(mock_post.call_count, 3)

        mock_titulo.assert_called_once()
        mock_contenido.assert_called_once()



    @patch('api.servicios.comunicado.comunicado_service.requests.post')
    @patch('api.servicios.comunicado.comunicado_service.settings')
    @patch('api.servicios.comunicado.comunicado_service.AreaInteres')
    def test_siempre_se_utiliza_html_como_parse_mode(self, mock_area_interes, mock_settings, mock_post):
        """
        Test: Uso correcto de HTML parse_mode

        Given: El token de Telegram está configurado.
        When: Se realiza un envío tanto con imagen como sin imagen.
        Then: El parámetro 'parse_mode' en el payload de la petición 
                debe ser siempre exactamente "HTML".
        """
        servicio = ComunicadoService()
        mock_settings.TELEGRAM_BOT_TOKEN = 'token_test'
        
        area_db = MagicMock(telegram_channel_id='@canal_test')
        mock_area_interes.objects.filter.return_value.exclude.return_value = [area_db]

        comunicado_con_foto = MagicMock()
        comunicado_con_foto.imagen_portada.open.return_value.__enter__.return_value = MagicMock()
        
        servicio._notificar_telegram(comunicado_con_foto, [MagicMock(id=1)])
        
        payload_foto = mock_post.call_args.kwargs['data']
        self.assertEqual(payload_foto.get('parse_mode'), "HTML", "sendPhoto debe usar parse_mode HTML")

        mock_post.reset_mock()
        comunicado_sin_foto = MagicMock()
        comunicado_sin_foto.imagen_portada = None
        
        servicio._notificar_telegram(comunicado_sin_foto, [MagicMock(id=1)])
        
        payload_texto = mock_post.call_args.kwargs['data']
        self.assertEqual(payload_texto.get('parse_mode'), "HTML", "sendMessage debe usar parse_mode HTML")
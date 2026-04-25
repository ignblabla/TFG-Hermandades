from unittest.mock import MagicMock, patch
from django.test import TestCase
from api.servicios.comunicado.comunicado_service import ComunicadoService


class UpdateComunicadoServiceTests(TestCase):

    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_update_basico_sin_cambios_relevantes(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Update básico sin cambios relevantes

        Given: Un usuario con permisos válidos.
                Un comunicado existente.
                Un diccionario 'data_validada' que modifica un campo simple (ej. estado), 
                pero NO modifica título, contenido ni areas_interes.
        When: Se llama a update_comunicado.
        Then: Se verifican los permisos.
                Se actualiza el atributo dinámicamente con setattr.
                Se llama al método save() del modelo.
                ❗ No se llama a transaction.on_commit (no hay regeneración de IA).
                Se retorna el mismo objeto actualizado.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        comunicado_instance = MagicMock()
        comunicado_instance.titulo = "Título Original"
        comunicado_instance.contenido = "Contenido Original"
        comunicado_instance.estado = "BORRADOR"

        data_validada = {
            'estado': 'PUBLICADO'
        }

        resultado = servicio.update_comunicado(usuario, comunicado_instance, data_validada.copy())

        mock_verificar_permisos.assert_called_once_with(usuario)

        comunicado_instance.areas_interes.set.assert_not_called()

        self.assertEqual(comunicado_instance.estado, 'PUBLICADO')

        comunicado_instance.save.assert_called_once()

        mock_transaction.on_commit.assert_not_called()

        self.assertEqual(resultado, comunicado_instance)



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_update_con_areas_interes_se_procesa_y_elimina_del_payload(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Update con áreas_interes

        Given: Un comunicado y un diccionario con 'areas_interes'.
        When: Se llama a update_comunicado.
        Then: Se extrae 'areas_interes' del diccionario (pop).
                Se llama al método .set() del gestor de la relación.
                ❗ El campo NO llega al bucle de setattr (evitando errores).
                Se guarda el modelo correctamente.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        comunicado_instance = MagicMock()
        comunicado_instance.areas_interes = MagicMock()
        
        areas_input = [1, 2, 3]
        data_validada = {
            'titulo': 'Mismo Titulo',
            'areas_interes': areas_input,
            'otro_campo': 'valor'
        }

        servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        comunicado_instance.areas_interes.set.assert_called_once_with(areas_input)

        self.assertNotIn('areas_interes', data_validada)

        comunicado_instance.save.assert_called_once()



    @patch('api.servicios.comunicado.comunicado_service.generar_y_guardar_embedding_async')
    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_cambio_de_titulo_dispara_regeneracion_de_embedding(self, mock_verificar_permisos, mock_transaction, mock_embedding_task):
        """
        Test: Cambio de título -> genera embedding

        Given: Un comunicado con título "A".
        When: Se actualiza el título a "B".
        Then: La bandera generar_nuevo_vector se activa.
                Se registra un transaction.on_commit.
                ❗ Al ejecutarse el callback del commit, se llama a la tarea de embedding.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        comunicado_instance = MagicMock()
        comunicado_instance.id = 99
        comunicado_instance.titulo = "Título Viejo"
        comunicado_instance.contenido = "Mismo contenido"
        comunicado_instance.generar_podcast = False

        data_validada = {
            'titulo': 'Título Nuevo (Cambiado)'
        }

        servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        mock_transaction.on_commit.assert_called_once()

        callback_embedding = mock_transaction.on_commit.call_args[0][0]
        callback_embedding()

        mock_embedding_task.assert_called_once_with(99)

        self.assertEqual(comunicado_instance.titulo, 'Título Nuevo (Cambiado)')
        comunicado_instance.save.assert_called_once()



    @patch('api.servicios.comunicado.comunicado_service.generar_y_guardar_embedding_async')
    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_cambio_de_contenido_dispara_regeneracion_de_embedding(self, mock_verificar_permisos, mock_transaction, mock_embedding_task):
        """
        Test: Cambio de contenido -> genera embedding

        Given: Un comunicado con contenido "Texto antiguo".
        When: Se actualiza el contenido a "Texto nuevo".
        Then: La bandera generar_nuevo_vector se activa (True).
                Se registra la tarea de embedding en el on_commit de la transacción.
                Se verifica que el objeto guarda el nuevo contenido.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        comunicado_instance = MagicMock()
        comunicado_instance.id = 101
        comunicado_instance.titulo = "Mismo Título"
        comunicado_instance.contenido = "Texto antiguo"
        comunicado_instance.generar_podcast = False

        data_validada = {
            'contenido': 'Texto nuevo actualizado'
        }

        servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        mock_transaction.on_commit.assert_called_once()

        callback = mock_transaction.on_commit.call_args[0][0]
        callback()
        
        mock_embedding_task.assert_called_once_with(101)

        self.assertEqual(comunicado_instance.contenido, 'Texto nuevo actualizado')
        comunicado_instance.save.assert_called_once()



    @patch('api.servicios.comunicado.comunicado_service.generar_y_guardar_embedding_async')
    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_cambio_de_titulo_y_contenido_solo_dispara_un_embedding(self, mock_verificar_permisos, mock_transaction, mock_embedding_task):
        """
        Test: Cambio de título y contenido (Eficiencia de triggers)

        Given: Un comunicado con título "A" y contenido "X".
        When: Se actualizan AMBOS a "B" e "Y".
        Then: La bandera generar_nuevo_vector se activa.
                ❗ transaction.on_commit se llama EXACTAMENTE una vez para el embedding.
                Se evita el encolamiento de tareas duplicadas.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        comunicado_instance = MagicMock(id=202)
        comunicado_instance.titulo = "Título Viejo"
        comunicado_instance.contenido = "Contenido Viejo"
        comunicado_instance.generar_podcast = False

        data_validada = {
            'titulo': 'Título Nuevo',
            'contenido': 'Contenido Nuevo'
        }

        servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        self.assertEqual(mock_transaction.on_commit.call_count, 1)

        callback = mock_transaction.on_commit.call_args[0][0]
        callback()
        
        mock_embedding_task.assert_called_once_with(202)

        self.assertEqual(comunicado_instance.titulo, 'Título Nuevo')
        self.assertEqual(comunicado_instance.contenido, 'Contenido Nuevo')



    @patch('api.servicios.comunicado.comunicado_service.generar_y_guardar_podcast_async')
    @patch('api.servicios.comunicado.comunicado_service.generar_y_guardar_embedding_async')
    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_cambio_relevante_con_podcast_activado_encola_ambas_tareas(
        self, mock_verificar_permisos, mock_transaction, mock_embedding_task, mock_podcast_task
    ):
        """
        Test: Podcast activado + embedding

        Given: Un comunicado con 'generar_podcast' en True.
        When: Se actualiza el título (lo que activa generar_nuevo_vector).
        Then: Se registran dos llamadas a transaction.on_commit.
                Se verifica que una tarea genera el embedding y la otra el podcast.
                Ambas tareas reciben el ID correcto del comunicado.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        comunicado_instance = MagicMock(id=303)
        comunicado_instance.titulo = "Título Original"
        comunicado_instance.generar_podcast = True

        data_validada = {
            'titulo': 'Nuevo Título para Podcast'
        }

        servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        self.assertEqual(mock_transaction.on_commit.call_count, 2)

        callback_embedding = mock_transaction.on_commit.call_args_list[0][0][0]
        callback_podcast = mock_transaction.on_commit.call_args_list[1][0][0]

        callback_embedding()
        callback_podcast()

        mock_embedding_task.assert_called_once_with(303)
        mock_podcast_task.assert_called_once_with(303)



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_update_completo_aplica_todos_los_setattr_dinamicamente(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Update completo con múltiples campos

        Given: Un comunicado con valores iniciales.
                Un diccionario 'data_validada' con múltiples atributos (titulo, contenido, estado, generar_podcast).
        When: Se llama a update_comunicado.
        Then: Se recorre el diccionario y se aplica setattr para cada clave.
                La instancia del comunicado refleja todos los nuevos valores.
                Se llama a save() para persistir los cambios.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        comunicado_instance = MagicMock()
        comunicado_instance.titulo = "Viejo"
        comunicado_instance.contenido = "Viejo"
        comunicado_instance.estado = "BORRADOR"
        comunicado_instance.generar_podcast = False

        data_validada = {
            'titulo': 'Nuevo Título',
            'contenido': 'Nuevo Contenido',
            'estado': 'PUBLICADO',
            'generar_podcast': True
        }

        servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        self.assertEqual(comunicado_instance.titulo, 'Nuevo Título')
        self.assertEqual(comunicado_instance.contenido, 'Nuevo Contenido')
        self.assertEqual(comunicado_instance.estado, 'PUBLICADO')
        self.assertEqual(comunicado_instance.generar_podcast, True)

        comunicado_instance.save.assert_called_once()



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_update_comunicado_retorna_la_instancia_correcta(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Retorno correcto

        Given: Un usuario y una instancia de comunicado.
        When: Se completa la actualización exitosamente.
        Then: El método debe devolver exactamente el mismo objeto comunicado_instance.
                Se verifica la identidad del objeto (mismo ID de memoria).
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        comunicado_instance = MagicMock()
        
        data_validada = {'estado': 'PUBLICADO'}

        resultado = servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        self.assertIs(resultado, comunicado_instance)

        self.assertEqual(resultado.estado, 'PUBLICADO')



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_verificar_permisos_se_ejecuta_antes_que_cualquier_logica(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Permisos correctos (Orden de ejecución)

        Given: Un usuario sin permisos suficientes.
        When: Se llama a update_comunicado.
                _verificar_permisos lanza una excepción (ej. PermissionDenied).
        Then: El flujo se corta inmediatamente.
                ❗ No se llama a .save() del comunicado.
                ❗ No se procesan las áreas de interés.
                ❗ No se registra nada en on_commit.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        mock_verificar_permisos.side_effect = PermissionError("No tienes permiso")
        
        comunicado_instance = MagicMock()
        comunicado_instance.areas_interes = MagicMock()
        
        data_validada = {
            'titulo': 'Nuevo Titulo',
            'areas_interes': [1, 2]
        }

        with self.assertRaises(PermissionError):
            servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        mock_verificar_permisos.assert_called_once_with(usuario)

        comunicado_instance.areas_interes.set.assert_not_called()
        comunicado_instance.save.assert_not_called()
        mock_transaction.on_commit.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_update_sin_areas_interes_no_toca_la_relacion_m2m(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Sin áreas_interes -> flujo normal

        Given: Un diccionario de datos que NO contiene la clave 'areas_interes'.
        When: Se llama a update_comunicado.
        Then: No se entra en el bloque condicional de áreas.
                ❗ NUNCA se llama al método .set() del gestor de relaciones.
                El resto del flujo (setattr y save) continúa normalmente.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        comunicado_instance = MagicMock()
        comunicado_instance.areas_interes = MagicMock()

        data_validada = {
            'titulo': 'Mismo Titulo',
            'estado': 'PUBLICADO'
        }

        servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        mock_verificar_permisos.assert_called_once_with(usuario)

        comunicado_instance.areas_interes.set.assert_not_called()

        comunicado_instance.save.assert_called_once()



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_fallo_en_permisos_aborta_toda_la_operacion_de_update(self, mock_verificar_permisos, mock_transaction):
        """
        Test: _verificar_permisos lanza excepción (Negativo)

        Given: Un usuario que no cumple los requisitos de seguridad.
        When: Se llama a update_comunicado.
                _verificar_permisos lanza una excepción (ej. PermissionDenied).
        Then: El flujo se interrumpe y la excepción se propaga.
                ❗ No se llama a .save() ni a .set() de áreas.
                ❗ No se registra ninguna tarea en on_commit.
                ❗ No se modifica ningún atributo de la instancia (setattr).
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        error_permisos = PermissionError("Acceso denegado")
        mock_verificar_permisos.side_effect = error_permisos

        comunicado_instance = MagicMock()
        comunicado_instance.titulo = "Titulo Original"
        comunicado_instance.areas_interes = MagicMock()
        
        data_validada = {
            'titulo': 'Titulo Hackeado',
            'areas_interes': [1, 2, 3]
        }

        with self.assertRaises(PermissionError) as context:
            servicio.update_comunicado(usuario, comunicado_instance, data_validada)
        
        self.assertEqual(str(context.exception), "Acceso denegado")

        self.assertEqual(comunicado_instance.titulo, "Titulo Original")

        comunicado_instance.areas_interes.set.assert_not_called()
        comunicado_instance.save.assert_not_called()
        mock_transaction.on_commit.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_update_con_campo_inexistente_lanza_attribute_error_y_no_guarda(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Campos inválidos (Atributo no existente en modelo)

        Given: Un diccionario 'data_validada' que contiene una clave inexistente 
                en el modelo Comunicado (ej. 'campo_fantasma').
        When: Se itera el payload para aplicar los cambios.
        Then: Se lanza un AttributeError con el mensaje descriptivo programado.
                ❗ El proceso se detiene y NO se llama a comunicado_instance.save().
                Se garantiza la integridad del modelo de datos.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        class ComunicadoFake:
            def __init__(self):
                self.titulo = "Titulo Viejo"
                self.contenido = "Contenido Viejo"
                self.generar_podcast = False
                self.save = MagicMock()

        comunicado_instance = ComunicadoFake() 
        
        data_validada = {
            'titulo': 'Nuevo Titulo',
            'campo_fantasma': 'valor'
        }

        with self.assertRaises(AttributeError) as context:
            servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        self.assertIn("El campo 'campo_fantasma' no existe en el modelo Comunicado.", str(context.exception))

        comunicado_instance.save.assert_not_called()
        mock_transaction.on_commit.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_fallo_en_set_de_areas_interes_interrumpe_ejecucion_y_no_guarda(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Fallos en áreas_interes (.set() falla)

        Given: Un diccionario con 'areas_interes' inválidas.
        When: Se llama al método .set() del ORM y este lanza una excepción (ej. ValueError).
        Then: La excepción se propaga hacia arriba.
                ❗ La ejecución se interrumpe inmediatamente.
                ❗ NO se llega a ejecutar el bucle setattr.
                ❗ NO se llama a comunicado_instance.save().
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        comunicado_instance = MagicMock()
        comunicado_instance.areas_interes = MagicMock()

        error_db = ValueError("Tipos de datos incorrectos para la relación M2M")
        comunicado_instance.areas_interes.set.side_effect = error_db

        data_validada = {
            'titulo': 'Título que nunca se guardará',
            'areas_interes': ['id_invalido_1', 'id_invalido_2']
        }

        with self.assertRaises(ValueError) as context:
            servicio.update_comunicado(usuario, comunicado_instance, data_validada)
            
        self.assertEqual(str(context.exception), "Tipos de datos incorrectos para la relación M2M")

        comunicado_instance.areas_interes.set.assert_called_once_with(['id_invalido_1', 'id_invalido_2'])

        comunicado_instance.save.assert_not_called()
        mock_transaction.on_commit.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_fallo_en_save_impide_registro_de_tareas_asincronas(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Fallos en save (save() lanza excepción)

        Given: Un usuario con permisos y datos que activarían la generación de IA.
        When: Se llama a update_comunicado y el método .save() del modelo lanza una excepción.
        Then: La excepción se propaga hacia arriba.
                ❗ No se llega a ejecutar la lógica de transaction.on_commit.
                Se verifica que no se encolan tareas de IA si la persistencia falló.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        comunicado_instance = MagicMock(id=500)
        comunicado_instance.titulo = "Título Antiguo"
        comunicado_instance.save.side_effect = Exception("Error crítico de base de datos")

        data_validada = {
            'titulo': 'Nuevo Título Semántico'
        }

        with self.assertRaises(Exception) as context:
            servicio.update_comunicado(usuario, comunicado_instance, data_validada)
        
        self.assertEqual(str(context.exception), "Error crítico de base de datos")

        comunicado_instance.save.assert_called_once()

        mock_transaction.on_commit.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_fallo_en_registro_de_on_commit_propaga_excepcion(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Fallos en embedding trigger (on_commit falla)

        Given: Un cambio de título que activa 'generar_nuevo_vector'.
        When: El método transaction.on_commit lanza una excepción al intentar registrar el callback.
        Then: La excepción se propaga hacia arriba.
                Se verifica que el sistema no ignora fallos en el encolado de tareas críticas.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        comunicado_instance = MagicMock(id=600)
        comunicado_instance.titulo = "Título Original"

        error_registro = RuntimeError("Error registrando callback de transacción")
        mock_transaction.on_commit.side_effect = error_registro

        data_validada = {'titulo': 'Título con Error en Commit'}

        with self.assertRaises(RuntimeError) as context:
            servicio.update_comunicado(usuario, comunicado_instance, data_validada)
            
        self.assertEqual(str(context.exception), "Error registrando callback de transacción")

        comunicado_instance.save.assert_called_once()

        mock_transaction.on_commit.assert_called_once()



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_no_genera_embedding_si_titulo_y_contenido_son_identicos(self, mock_verificar_permisos, mock_transaction):
        """
        Test: No generación de embedding cuando no hay cambios

        Given: Un comunicado con un título y contenido específicos.
        When: Se recibe un payload con los MISMOS valores existentes.
        Then: La variable 'generar_nuevo_vector' debe permanecer en False.
                ❗ NO se debe llamar a transaction.on_commit para el embedding.
                El registro se guarda, pero la IA no se dispara.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        comunicado_instance = MagicMock(id=700)
        comunicado_instance.titulo = "Título estático"
        comunicado_instance.contenido = "Contenido sin cambios"
        comunicado_instance.generar_podcast = False

        data_validada = {
            'titulo': "Título estático",
            'contenido': "Contenido sin cambios"
        }

        servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        comunicado_instance.save.assert_called_once()

        mock_transaction.on_commit.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.generar_y_guardar_podcast_async')
    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_podcast_activado_pero_sin_cambios_en_texto_no_dispara_tareas(
        self, mock_verificar_permisos, mock_transaction, mock_podcast_task
    ):
        """
        Test: Podcast sin embedding trigger (generar_podcast=True pero sin cambios)

        Given: Un comunicado que YA tiene generar_podcast=True.
        When: Se recibe una actualización (ej. cambio de estado) pero el título 
                y contenido son los mismos.
        Then: generar_nuevo_vector permanece en False.
                ❗ No se entra al bloque de tareas asíncronas.
                ❗ No se llama a generar_y_guardar_podcast_async.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        comunicado_instance = MagicMock(id=800)
        comunicado_instance.titulo = "Título Actual"
        comunicado_instance.contenido = "Contenido Actual"
        comunicado_instance.generar_podcast = True

        data_validada = {
            'titulo': "Título Actual",
            'contenido': "Contenido Actual",
            'estado': 'PUBLICADO'
        }

        servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        self.assertEqual(comunicado_instance.estado, 'PUBLICADO')
        comunicado_instance.save.assert_called_once()

        mock_transaction.on_commit.assert_not_called()
        mock_podcast_task.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_update_con_data_vacia_solo_ejecuta_save(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Data vacío (data_validada = {})

        Given: Un diccionario de datos vacío.
        When: Se llama a update_comunicado.
        Then: Se verifican los permisos.
                No se procesan áreas de interés.
                No se entra en la lógica de generación de IA (embedding/podcast).
                ❗ Se llama a .save() para garantizar consistencia (ej. actualizar updated_at).
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        comunicado_instance = MagicMock(id=999)
        comunicado_instance.titulo = "Título Original"
        comunicado_instance.generar_podcast = True
        
        data_validada = {}

        servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        mock_verificar_permisos.assert_called_once_with(usuario)

        comunicado_instance.save.assert_called_once()

        mock_transaction.on_commit.assert_not_called()

        self.assertEqual(comunicado_instance.titulo, "Título Original")



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_cambio_exclusivo_de_areas_no_dispara_ia(self, mock_verificar_permisos, mock_transaction):
        """
        Test: Solo áreas_interes cambia (Caso Límite)

        Given: Un comunicado con título y contenido existentes.
        When: Se actualiza ÚNICAMENTE la lista de 'areas_interes'.
        Then: Se procesa el .set() de las áreas.
                La bandera 'generar_nuevo_vector' permanece en False.
                ❗ NO se registra ninguna tarea en transaction.on_commit.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        comunicado_instance = MagicMock(id=1001)
        comunicado_instance.titulo = "Título que no cambia"
        comunicado_instance.contenido = "Contenido que no cambia"
        comunicado_instance.areas_interes = MagicMock()

        nuevas_areas = [10, 20]
        data_validada = {
            'areas_interes': nuevas_areas
        }

        servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        comunicado_instance.areas_interes.set.assert_called_once_with(nuevas_areas)

        comunicado_instance.save.assert_called_once()

        mock_transaction.on_commit.assert_not_called()



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_contenido_none_o_vacio_no_dispara_ia(self, mock_verificar_permisos, mock_transaction):
        """
        Test: contenido None o vacío (Evitar falsos positivos)

        Given: Un comunicado con contenido "Texto existente".
        When: Se recibe un payload donde el contenido es None o una cadena vacía.
        Then: La condición (contenido_nuevo and contenido_nuevo != actual) debe ser False.
                ❗ NO se debe llamar a transaction.on_commit.
                Se garantiza que solo valores con sustancia disparan la IA.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        comunicado_instance = MagicMock(id=1100)
        comunicado_instance.titulo = "Título"
        comunicado_instance.contenido = "Texto existente"

        data_validada_none = {'contenido': None}
        data_validada_vacia = {'contenido': ""}

        servicio.update_comunicado(usuario, comunicado_instance, data_validada_none)
        mock_transaction.on_commit.assert_not_called()

        mock_transaction.reset_mock()
        servicio.update_comunicado(usuario, comunicado_instance, data_validada_vacia)
        mock_transaction.on_commit.assert_not_called()

        self.assertEqual(comunicado_instance.save.call_count, 2)



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_titulo_none_o_vacio_no_dispara_ia(self, mock_verificar_permisos, mock_transaction):
        """
        Test: titulo None o vacío (Evitar disparos accidentales)

        Given: Un comunicado con título "Título Real".
        When: Se recibe un payload con título None o "".
        Then: La condición (titulo_nuevo and titulo_nuevo != actual) debe ser False.
                ❗ NO se debe registrar nada en transaction.on_commit.
                Se evita el gasto de recursos en contenido sin valor.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        comunicado_instance = MagicMock(id=1200)
        comunicado_instance.titulo = "Título Real"
        comunicado_instance.contenido = "Contenido"

        data_none = {'titulo': None}
        servicio.update_comunicado(usuario, comunicado_instance, data_none)
        mock_transaction.on_commit.assert_not_called()

        mock_transaction.reset_mock()
        data_vacia = {'titulo': ""}
        servicio.update_comunicado(usuario, comunicado_instance, data_vacia)
        mock_transaction.on_commit.assert_not_called()

        self.assertEqual(comunicado_instance.save.call_count, 2)



    @patch('api.servicios.comunicado.comunicado_service.generar_y_guardar_embedding_async')
    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_update_comunicado_sigue_orden_logico_de_ejecucion(
        self, mock_verificar_permisos, mock_transaction, mock_embedding_task
    ):
        """
        Test: Orden de ejecución correcto

        Valida la secuencia:
        1. Permisos (Barrera de entrada)
        2. Procesamiento de M2M (áreas_interes)
        3. Aplicación de atributos (setattr)
        4. Persistencia (save)
        5. Registro de tareas (on_commit)
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        manager = MagicMock()
        manager.attach_mock(mock_verificar_permisos, 'permisos')
        manager.attach_mock(mock_transaction.on_commit, 'on_commit')
        
        comunicado_instance = MagicMock(id=1300)
        comunicado_instance.titulo = "Viejo"

        comunicado_instance.generar_podcast = False 
        
        manager.attach_mock(comunicado_instance.save, 'save')
        manager.attach_mock(comunicado_instance.areas_interes.set, 'set_m2m')
        
        data_validada = {
            'titulo': 'Nuevo',
            'areas_interes': [1]
        }

        servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        nombres_llamadas = [call[0] for call in manager.mock_calls]

        orden_esperado = [
            'permisos',
            'set_m2m',
            'save',
            'on_commit'
        ]
        
        self.assertEqual(nombres_llamadas, orden_esperado)



    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_pop_de_areas_interes_elimina_el_campo_antes_del_bucle_setattr(self, mock_verificar_permisos, mock_transaction):
        """
        Test: pop de areas_interes elimina del update

        Given: Un payload con 'titulo' y 'areas_interes'.
        When: Se llama a update_comunicado.
        Then: 'areas_interes' debe ser extraído (pop) para el proceso M2M.
                ❗ No debe existir en el diccionario cuando empiece el bucle setattr.
                Se verifica que la instancia NO tiene un atributo 'areas_interes' asignado por valor.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()

        class ComunicadoFake:
            def __init__(self):
                self.id = 1400
                self.titulo = "Original"
                self.generar_podcast = False
                self.areas_interes = MagicMock()
            def save(self): pass

        instancia = ComunicadoFake()

        data_validada = {
            'titulo': 'Nuevo Título',
            'areas_interes': [1, 2, 3]
        }

        servicio.update_comunicado(usuario, instancia, data_validada)

        self.assertNotIn('areas_interes', data_validada)
        self.assertIn('titulo', data_validada)

        self.assertIsInstance(instancia.areas_interes, MagicMock)

        instancia.areas_interes.set.assert_called_once_with([1, 2, 3])



    @patch('api.servicios.comunicado.comunicado_service.generar_y_guardar_podcast_async')
    @patch('api.servicios.comunicado.comunicado_service.generar_y_guardar_embedding_async')
    @patch('api.servicios.comunicado.comunicado_service.transaction')
    @patch.object(ComunicadoService, '_verificar_permisos')
    def test_doble_trigger_controlado_respeta_orden_de_dependencia(
        self, mock_verificar_permisos, mock_transaction, mock_embedding_task, mock_podcast_task
    ):
        """
        Test: Doble trigger controlado (Cambios + Podcast)

        Given: Un comunicado con 'generar_podcast=True'.
        When: Se actualiza el título o contenido, activando la IA.
        Then: Se registran EXACTAMENTE dos tareas en on_commit.
                ❗ Se verifica el orden estricto: primero el embedding, luego el podcast.
        """
        servicio = ComunicadoService()
        usuario = MagicMock()
        
        comunicado_instance = MagicMock(id=1500)
        comunicado_instance.titulo = "Título Viejo"
        comunicado_instance.generar_podcast = True
        
        data_validada = {
            'titulo': 'Nuevo Título que dispara IA'
        }

        servicio.update_comunicado(usuario, comunicado_instance, data_validada)

        self.assertEqual(mock_transaction.on_commit.call_count, 2, "Deberían registrarse exactamente dos callbacks")

        llamadas = mock_transaction.on_commit.call_args_list

        callback_primero = llamadas[0][0][0]
        callback_segundo = llamadas[1][0][0]

        callback_primero()
        mock_embedding_task.assert_called_once_with(1500)
        mock_podcast_task.assert_not_called()

        callback_segundo()
        mock_podcast_task.assert_called_once_with(1500)
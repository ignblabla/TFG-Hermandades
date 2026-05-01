from unittest.mock import MagicMock, PropertyMock, patch
from django.test import TestCase
from api.servicios.hermano.hermano_service import update_mi_perfil_service


class TestUpdateMiPerfilService(TestCase):

    def test_update_mi_perfil_atributos_basicos(self):
        """
        Test: Actualización de atributos básicos (sin password ni relaciones)
        
        Given: Un usuario y un diccionario con datos básicos (sin password, áreas ni datos bancarios).
        When: Se ejecuta la actualización del perfil.
        Then: Se asignan atributos con setattr, se llama a save() y retorna el usuario modificado.
        """
        usuario = MagicMock()
        data_validada = {
            'nombre': 'Elena',
            'telefono': '123456789'
        }

        resultado = update_mi_perfil_service(usuario, data_validada)

        self.assertEqual(usuario.nombre, 'Elena')
        self.assertEqual(usuario.telefono, '123456789')

        usuario.save.assert_called_once()

        usuario.set_password.assert_not_called()

        self.assertEqual(resultado, usuario)



    def test_update_mi_perfil_password_valido(self):
        """
        Test: Actualización con password válido
        
        Given: Un usuario y un diccionario de datos que contiene únicamente 'password'.
        When: Se ejecuta la actualización del perfil.
        Then: Se llama a set_password con el valor correcto, se llama a save() y retorna el usuario.
        """
        usuario = MagicMock()
        data_validada = {
            'password': 'mi_nueva_contraseña_segura'
        }

        resultado = update_mi_perfil_service(usuario, data_validada)

        usuario.set_password.assert_called_once_with('mi_nueva_contraseña_segura')

        usuario.save.assert_called_once()
        self.assertEqual(resultado, usuario)



    def test_update_mi_perfil_password_vacio(self):
        """
        Test: Password vacío -> no se actualiza
        
        Given: Un usuario y un diccionario de datos donde 'password' es un string vacío o None.
        When: Se ejecuta la actualización del perfil.
        Then: NO se llama a set_password para evitar cambios involuntarios, pero se llama a save() para el resto de atributos.
        """
        usuario = MagicMock()
        data_validada = {
            'nombre': 'Maria',
            'password': ''
        }

        update_mi_perfil_service(usuario, data_validada)

        usuario.set_password.assert_not_called()

        self.assertEqual(usuario.nombre, 'Maria')
        usuario.save.assert_called_once()



    def test_update_mi_perfil_areas_interes(self):
        """
        Test: Actualización de áreas de interés
        
        Given: Un usuario y una lista de IDs de áreas de interés.
        When: Se procesa la actualización.
        Then: Se llama al método .set() del gestor de la relación areas_interes con la lista proporcionada.
        """
        usuario = MagicMock()

        usuario.areas_interes = MagicMock()
        
        lista_areas = [1, 2, 5]
        data_validada = {
            'areas_interes': lista_areas
        }

        update_mi_perfil_service(usuario, data_validada)

        usuario.areas_interes.set.assert_called_once_with(lista_areas)

        usuario.save.assert_called_once()



    @patch('api.servicios.hermano.hermano_service.DatosBancarios.objects.update_or_create')
    def test_update_mi_perfil_datos_bancarios(self, mock_update_or_create):
        """
        Test: Actualización de datos bancarios
        
        Given: Un usuario y un diccionario con información para 'datos_bancarios'.
        When: Se ejecuta la actualización del perfil.
        Then: Se llama a update_or_create con el usuario como clave de búsqueda y el resto como 'defaults'.
        """
        usuario = MagicMock()
        info_bancaria = {'iban': 'ES1234', 'titular': 'Juan Perez'}
        data_validada = {
            'datos_bancarios': info_bancaria
        }

        update_mi_perfil_service(usuario, data_validada)

        mock_update_or_create.assert_called_once_with(
            hermano=usuario,
            defaults=info_bancaria
        )

        usuario.save.assert_called_once()



    @patch('api.servicios.hermano.hermano_service.DatosBancarios.objects.update_or_create')
    def test_update_mi_perfil_completo(self, mock_update_or_create):
        """
        Test: Actualización completa (atributos + password + áreas + datos bancarios)
        
        Given: Un usuario y un diccionario con todos los tipos de campos soportados.
        When: Se procesa la actualización integral.
        Then: Se ejecutan todas las operaciones (setattr, set_password, save, set M2M y update_or_create) correctamente.
        """
        usuario = MagicMock()
        usuario.areas_interes = MagicMock()
        
        data_validada = {
            'nombre': 'Luis',
            'password': 'new_pass_123',
            'areas_interes': [1, 2],
            'datos_bancarios': {'iban': 'ES99'}
        }

        resultado = update_mi_perfil_service(usuario, data_validada)

        self.assertEqual(usuario.nombre, 'Luis')

        usuario.set_password.assert_called_once_with('new_pass_123')

        usuario.save.assert_called_once()

        usuario.areas_interes.set.assert_called_once_with([1, 2])

        mock_update_or_create.assert_called_once_with(
            hermano=usuario,
            defaults={'iban': 'ES99'}
        )

        self.assertEqual(resultado, usuario)



    def test_update_mi_perfil_areas_vacias(self):
        """
        Test: areas_interes = [] (lista vacía)
        
        Given: Un usuario con áreas previamente asignadas y una lista vacía en los datos.
        When: Se ejecuta la actualización.
        Then: Se llama a .set([]) correctamente, lo que en Django limpia las relaciones existentes.
        """
        usuario = MagicMock()
        usuario.areas_interes = MagicMock()
        data_validada = {
            'areas_interes': []
        }

        update_mi_perfil_service(usuario, data_validada)

        usuario.areas_interes.set.assert_called_once_with([])
        usuario.save.assert_called_once()



    @patch('api.servicios.hermano.hermano_service.DatosBancarios.objects.update_or_create')
    def test_update_mi_perfil_datos_bancarios_vacios(self, mock_update_or_create):
        """
        Test: datos_bancarios vacío pero presente
        
        Given: Un usuario y un diccionario 'datos_bancarios' inicializado pero sin contenido.
        When: Se procesa la actualización.
        Then: Se llama a update_or_create con defaults vacíos, manteniendo la integridad del flujo.
        """
        usuario = MagicMock()
        datos_bancarios_vacios = {}
        data_validada = {
            'datos_bancarios': datos_bancarios_vacios
        }

        update_mi_perfil_service(usuario, data_validada)

        mock_update_or_create.assert_called_once_with(
            hermano=usuario,
            defaults={}
        )
        usuario.save.assert_called_once()



    @patch('api.servicios.hermano.hermano_service.DatosBancarios.objects.update_or_create')
    def test_update_mi_perfil_data_vacia(self, mock_update_or_create):
        """
        Test: data_validada vacío
        
        Given: Un usuario y un diccionario de datos vacío.
        When: Se intenta actualizar el perfil.
        Then: Solo se llama a save() en el objeto usuario y no se ejecutan otras acciones (set_password, relaciones, etc.).
        """
        usuario = MagicMock()
        usuario.areas_interes = MagicMock()
        data_validada = {}

        resultado = update_mi_perfil_service(usuario, data_validada)

        usuario.save.assert_called_once()

        usuario.set_password.assert_not_called()
        usuario.areas_interes.set.assert_not_called()
        mock_update_or_create.assert_not_called()

        self.assertEqual(resultado, usuario)



    def test_update_mi_perfil_error_set_password(self):
        """
        Test: Error en set_password
        
        Given: Un usuario y datos que incluyen una nueva contraseña.
        When: El método set_password lanza una excepción (ej. fallo de validación interna).
        Then: La excepción se propaga y no se llega a llamar al método save().
        """
        usuario = MagicMock()
        data_validada = {'password': 'nueva_password'}

        usuario.set_password.side_effect = ValueError("Password no cumple criterios")

        with self.assertRaises(ValueError):
            update_mi_perfil_service(usuario, data_validada)

        usuario.save.assert_not_called()



    def test_update_mi_perfil_error_save(self):
        """
        Test: Error en save
        
        Given: Un usuario y datos de actualización válidos.
        When: El método save() del modelo lanza una excepción (ej. error de base de datos).
        Then: La excepción se propaga correctamente hacia el llamador.
        """
        usuario = MagicMock()
        data_validada = {'nombre': 'Nuevo Nombre'}

        usuario.save.side_effect = RuntimeError("Fallo de conexión con la base de datos")

        with self.assertRaises(RuntimeError) as cm:
            update_mi_perfil_service(usuario, data_validada)
        
        self.assertEqual(str(cm.exception), "Fallo de conexión con la base de datos")

        usuario.save.assert_called_once()



    def test_update_mi_perfil_error_areas_interes_set(self):
        """
        Test: Error en areas_interes.set
        
        Given: Un usuario y una lista de áreas de interés.
        When: El método .set() del gestor de la relación lanza una excepción.
        Then: La excepción se propaga y se verifica que save() se llamó previamente (ya que ocurre antes en el código).
        """
        usuario = MagicMock()
        usuario.areas_interes = MagicMock()
        data_validada = {'areas_interes': [1, 2]}

        usuario.areas_interes.set.side_effect = Exception("Error al sincronizar áreas")

        with self.assertRaises(Exception) as cm:
            update_mi_perfil_service(usuario, data_validada)
        
        self.assertEqual(str(cm.exception), "Error al sincronizar áreas")

        usuario.save.assert_called_once()



    @patch('api.servicios.hermano.hermano_service.DatosBancarios.objects.update_or_create')
    def test_update_mi_perfil_error_update_or_create(self, mock_update_or_create):
        """
        Test: Error en update_or_create
        
        Given: Un usuario y datos bancarios para actualizar.
        When: El método update_or_create del modelo DatosBancarios lanza una excepción.
        Then: La excepción se propaga y se confirma que el usuario base ya había sido guardado.
        """
        usuario = MagicMock()
        data_validada = {'datos_bancarios': {'iban': 'ES123'}}

        mock_update_or_create.side_effect = RuntimeError("Fallo de validación en DatosBancarios")

        with self.assertRaises(RuntimeError) as cm:
            update_mi_perfil_service(usuario, data_validada)
            
        self.assertEqual(str(cm.exception), "Fallo de validación en DatosBancarios")

        usuario.save.assert_called_once()



    def test_update_mi_perfil_atributo_invalido(self):
        """
        Test: Atributo inválido en data_validada
        
        Given: Un usuario y un diccionario con un atributo que provoca un error al ser asignado.
        When: setattr intenta realizar la asignación dinámica.
        Then: setattr falla, se propaga la excepción y no se llega a ejecutar el save().
        """
        usuario = MagicMock()

        type(usuario).read_only_attr = PropertyMock(side_effect=AttributeError("No se puede modificar"))
        
        data_validada = {'read_only_attr': 'nuevo_valor'}

        with self.assertRaises(AttributeError):
            update_mi_perfil_service(usuario, data_validada)

        usuario.save.assert_not_called()



    @patch('api.servicios.hermano.hermano_service.DatosBancarios.objects.update_or_create')
    def test_update_mi_perfil_verificacion_orden(self, mock_update_or_create):
        """
        Test: Verificación de orden de ejecución
        
        Given: Un usuario y un set completo de datos de actualización.
        When: Se ejecuta el servicio.
        Then: El orden de llamadas debe ser: 1. setattr, 2. set_password, 3. save, 4. relaciones (areas), 5. modelos vinculados (bancarios).
        """
        usuario = MagicMock()
        usuario.areas_interes = MagicMock()
        
        data_validada = {
            'nombre': 'Test Orden',
            'password': 'pass',
            'areas_interes': [1],
            'datos_bancarios': {'iban': 'ES00'}
        }

        manager = MagicMock()
        manager.attach_mock(usuario.set_password, 'set_password')
        manager.attach_mock(usuario.save, 'save')
        manager.attach_mock(usuario.areas_interes.set, 'areas_set')
        manager.attach_mock(mock_update_or_create, 'bancarios_update')

        update_mi_perfil_service(usuario, data_validada)

        llamadas = [call[0] for call in manager.mock_calls]

        secuencia_esperada = [
            'set_password',
            'save',
            'areas_set',
            'bancarios_update'
        ]

        llamadas_filtradas = [name for name in llamadas if name in secuencia_esperada]
        
        self.assertEqual(llamadas_filtradas, secuencia_esperada)



    @patch('api.servicios.hermano.hermano_service.DatosBancarios.objects.update_or_create')
    def test_update_mi_perfil_rollback_por_error_bancario(self, mock_update_or_create):
        """
        Test: Atomicidad (rollback ante fallo en relaciones o datos bancarios)
        
        Given: Un usuario y datos bancarios que provocarán un error en la base de datos.
        When: Se ejecuta el servicio y update_or_create lanza una excepción.
        Then: La excepción se propaga al exterior, asegurando conceptualmente que el decorador @transaction.atomic ejecute el rollback de los cambios previos.
        """
        usuario = MagicMock()
        data_validada = {
            'nombre': 'Nombre Temporal',
            'datos_bancarios': {'iban': 'ES_ERROR'}
        }

        mock_update_or_create.side_effect = Exception("Fallo de integridad en base de datos")

        with self.assertRaises(Exception) as cm:
            update_mi_perfil_service(usuario, data_validada)

        self.assertEqual(str(cm.exception), "Fallo de integridad en base de datos")

        usuario.save.assert_called_once()
        mock_update_or_create.assert_called_once()



    def test_update_mi_perfil_rollback_por_error_m2m(self):
        """
        Test: Atomicidad (rollback ante fallo en relaciones ManyToMany)
        
        Given: Un usuario y una lista de áreas de interés.
        When: El método .set() de la relación lanza una excepción.
        Then: Se propaga la excepción inmediatamente, impidiendo que el servicio retorne el usuario y activando el rollback de la transacción.
        """
        usuario = MagicMock()
        usuario.areas_interes = MagicMock()
        data_validada = {
            'areas_interes': [1, 2, 3]
        }

        usuario.areas_interes.set.side_effect = RuntimeError("Error M2M")

        with self.assertRaises(RuntimeError):
            update_mi_perfil_service(usuario, data_validada)

        usuario.save.assert_called_once()
        usuario.areas_interes.set.assert_called_once_with([1, 2, 3])
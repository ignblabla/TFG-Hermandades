from unittest.mock import PropertyMock, patch, MagicMock
from django.http import Http404
from django.test import TestCase
from rest_framework.exceptions import PermissionDenied
from api.servicios.hermano.hermano_service import update_hermano_por_admin_service, User

class TestUpdateHermanoPorAdminService(TestCase):

    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_por_admin_service_atributos_normales(self, mock_get_object_or_404):
        """
        Test: Usuario administrador -> actualiza atributos correctamente
        
        Given: Un usuario administrador, el ID de un hermano existente y un diccionario con datos de actualización.
        When: Se ejecuta la actualización.
        Then: Se obtienen los datos mediante get_object_or_404, se actualizan los atributos, se llama a save() y retorna el objeto modificado.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        hermano_id = 1
        data_validada = {
            'nombre': 'Carlos',
            'email': 'carlos@example.com'
        }

        mock_hermano = MagicMock()
        mock_get_object_or_404.return_value = mock_hermano

        resultado = update_hermano_por_admin_service(usuario_admin, hermano_id, data_validada)

        mock_get_object_or_404.assert_called_once_with(User, pk=hermano_id)

        self.assertEqual(mock_hermano.nombre, 'Carlos')
        self.assertEqual(mock_hermano.email, 'carlos@example.com')

        mock_hermano.save.assert_called_once()
        self.assertEqual(resultado, mock_hermano)



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_password_valido(self, mock_get_object_or_404):
        """
        Test: Usuario administrador -> actualiza contraseña correctamente
        
        Given: Un usuario administrador y un diccionario de datos que incluye 'password'.
        When: Se ejecuta la actualización.
        Then: Se llama a set_password con el valor, no se usa setattr para password y se llama a save().
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        data_validada = {'password': 'nueva_password_segura'}
        
        mock_hermano = MagicMock()
        mock_get_object_or_404.return_value = mock_hermano

        update_hermano_por_admin_service(usuario_admin, 1, data_validada)

        mock_hermano.set_password.assert_called_once_with('nueva_password_segura')

        mock_hermano.save.assert_called_once()



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_password_vacio(self, mock_get_object_or_404):
        """
        Test: Usuario administrador -> password vacío no actualiza contraseña
        
        Given: Un usuario administrador y un diccionario con 'password' como string vacío o None.
        When: Se procesan los datos.
        Then: NO se llama a set_password para evitar sobreescribir con vacío, pero se llama a save() por el resto del flujo.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        data_validada = {'password': ''}
        
        mock_hermano = MagicMock()
        mock_get_object_or_404.return_value = mock_hermano

        update_hermano_por_admin_service(usuario_admin, 1, data_validada)

        mock_hermano.set_password.assert_not_called()
        mock_hermano.save.assert_called_once()



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_por_admin_service_mezcla(self, mock_get_object_or_404):
        """
        Test: Usuario administrador -> mezcla de campos (password + otros)
        
        Given: Un usuario administrador y un diccionario con password y otros campos (ej. email).
        When: Se ejecuta la actualización del hermano.
        Then: set_password se llama correctamente, los otros atributos se asignan con setattr y se llama a save().
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        data_validada = {
            'password': 'secret_password',
            'email': 'nuevo_email@test.com'
        }
        
        mock_hermano = MagicMock()
        mock_get_object_or_404.return_value = mock_hermano

        update_hermano_por_admin_service(usuario_admin, 1, data_validada)

        mock_hermano.set_password.assert_called_once_with('secret_password')

        self.assertEqual(mock_hermano.email, 'nuevo_email@test.com')

        mock_hermano.save.assert_called_once()

    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_por_admin_service_data_vacia(self, mock_get_object_or_404):
        """
        Test: Usuario administrador -> data_validada vacío
        
        Given: Un usuario administrador y un diccionario de datos vacío.
        When: Se solicita la actualización.
        Then: No se modifican atributos (el bucle no itera), pero se llama a save() según el flujo del servicio.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        data_validada = {}
        
        mock_hermano = MagicMock()
        mock_get_object_or_404.return_value = mock_hermano

        update_hermano_por_admin_service(usuario_admin, 1, data_validada)

        mock_hermano.set_password.assert_not_called()

        mock_hermano.save.assert_called_once()



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_por_admin_no_admin(self, mock_get_object_or_404):
        """
        Test: Usuario no administrador -> lanza PermissionDenied
        
        Given: Un usuario con esAdmin = False y unos datos de actualización.
        When: Se intenta ejecutar el servicio de actualización.
        Then: Se lanza PermissionDenied y no se llega a llamar a get_object_or_404.
        """
        usuario_no_admin = MagicMock()
        usuario_no_admin.esAdmin = False
        data = {'nombre': 'Nuevo Nombre'}

        with self.assertRaises(PermissionDenied) as cm:
            update_hermano_por_admin_service(usuario_no_admin, 1, data)

        self.assertEqual(str(cm.exception), "No tienes permisos para editar los datos de otros hermanos.")
        mock_get_object_or_404.assert_not_called()



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_por_admin_sin_atributo(self, mock_get_object_or_404):
        """
        Test: Usuario sin atributo esAdmin -> lanza PermissionDenied
        
        Given: Un usuario que no dispone del atributo 'esAdmin'.
        When: El servicio usa getattr(usuario, 'esAdmin', False).
        Then: Se evalúa como False, lanza la excepción y no se llama a get_object_or_404.
        """
        usuario_sin_atributo = MagicMock(spec=[])

        with self.assertRaises(PermissionDenied):
            update_hermano_por_admin_service(usuario_sin_atributo, 1, {})

        mock_get_object_or_404.assert_not_called()



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_por_admin_admin_none(self, mock_get_object_or_404):
        """
        Test: Usuario con esAdmin = None -> lanza PermissionDenied
        
        Given: Un usuario solicitante cuyo atributo esAdmin es None.
        When: Se intenta realizar la actualización.
        Then: El valor None se evalúa como falso, se lanza PermissionDenied y no se llama a get_object_or_404.
        """
        usuario_admin_none = MagicMock()
        usuario_admin_none.esAdmin = None

        with self.assertRaises(PermissionDenied):
            update_hermano_por_admin_service(usuario_admin_none, 1, {})
        
        mock_get_object_or_404.assert_not_called()



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_por_admin_no_encontrado(self, mock_get_object_or_404):
        """
        Test: Usuario no encontrado -> lanza excepción (404)
        
        Given: Un usuario administrador y un hermano_id que no existe en la base de datos.
        When: get_object_or_404 es invocado.
        Then: Se propaga la excepción Http404 (o la que lance el atajo) y no se continúa con la actualización.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        mock_get_object_or_404.side_effect = Http404("No se encontró el usuario")

        with self.assertRaises(Http404):
            update_hermano_por_admin_service(usuario_admin, 999, {"nombre": "Nuevo"})

        mock_get_object_or_404.assert_called_once()



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_error_en_set_password(self, mock_get_object_or_404):
        """
        Test: Error en set_password -> se propaga excepción
        
        Given: Un usuario administrador y una nueva contraseña.
        When: El método set_password del modelo User lanza una excepción.
        Then: Se interrumpe la ejecución, se propaga la excepción y no se llama a save().
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        
        mock_hermano = MagicMock()
        mock_get_object_or_404.return_value = mock_hermano

        mock_hermano.set_password.side_effect = ValueError("Contraseña no cumple requisitos")

        with self.assertRaises(ValueError):
            update_hermano_por_admin_service(usuario_admin, 1, {'password': '123'})

        mock_hermano.save.assert_not_called()

    

    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_error_en_save(self, mock_get_object_or_404):
        """
        Test: Error en save -> se propaga excepción
        
        Given: Un usuario administrador y datos válidos.
        When: El método save() falla (por ejemplo, por una restricción de integridad de BD).
        Then: Se lanza la excepción después de haber modificado los atributos en la instancia.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        
        mock_hermano = MagicMock()
        mock_get_object_or_404.return_value = mock_hermano

        mock_hermano.save.side_effect = RuntimeError("Error de escritura en disco")

        with self.assertRaises(RuntimeError) as cm:
            update_hermano_por_admin_service(usuario_admin, 1, {'nombre': 'Test'})
        
        self.assertEqual(str(cm.exception), "Error de escritura en disco")

        mock_hermano.save.assert_called_once()



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_atributo_inexistente(self, mock_get_object_or_404):
        """
        Test: data_validada contiene atributo inexistente
        
        Given: Un usuario administrador y datos que incluyen un campo no definido en el modelo (ej. 'campo_extra').
        When: Se ejecuta la actualización.
        Then: setattr se ejecuta igualmente creando el atributo dinámico en la instancia y se llama a save().
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        data_validada = {'campo_extra': 'valor_dinamico'}
        
        mock_hermano = MagicMock()
        mock_get_object_or_404.return_value = mock_hermano

        update_hermano_por_admin_service(usuario_admin, 1, data_validada)

        self.assertEqual(mock_hermano.campo_extra, 'valor_dinamico')
        mock_hermano.save.assert_called_once()



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_fallo_setattr(self, mock_get_object_or_404):
        """
        Test: Fallo en setattr (atributo protegido o error interno)
        
        Given: Un usuario administrador y un objeto hermano que restringe la modificación de ciertos campos.
        When: setattr intenta asignar un valor y lanza una excepción.
        Then: Se propaga la excepción y se detiene la ejecución.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        mock_hermano = MagicMock()
        type(mock_hermano).error_attr = PropertyMock(side_effect=AttributeError("Atributo protegido"))
        mock_get_object_or_404.return_value = mock_hermano

        with self.assertRaises(AttributeError):
            update_hermano_por_admin_service(usuario_admin, 1, {'error_attr': 'valor'})



    @patch('api.servicios.hermano.hermano_service.get_object_or_404')
    def test_update_hermano_verificacion_atomicidad(self, mock_get_object_or_404):
        """
        Test: Verificación de atomicidad (rollback en excepción)
        
        Given: Un entorno donde el método save() del modelo va a fallar.
        When: Se ejecuta el servicio bajo el decorador @transaction.atomic.
        Then: Ante el error en save(), la excepción se propaga, asegurando que la transacción no se complete.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        
        mock_hermano = MagicMock()
        mock_get_object_or_404.return_value = mock_hermano

        mock_hermano.save.side_effect = Exception("Fallo crítico de base de datos")

        with self.assertRaises(Exception):
            update_hermano_por_admin_service(usuario_admin, 1, {'nombre': 'Cambio'})

        mock_hermano.save.assert_called_once()
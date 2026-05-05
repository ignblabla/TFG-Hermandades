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
import unittest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import AnonymousUser
from rest_framework import status

from api.vistas.puesto.crear_puesto_view import CrearPuestoView


class TestCrearPuestoViewPermisos(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.url = '/puestos/'
        self.user = MagicMock()
        self.user.is_authenticated = True 

        self.vista_callable = CrearPuestoView.as_view()
        self.data_post = {"nombre": "Costalero", "acto": 1}



    @patch('api.vistas.puesto.crear_puesto_view.create_puesto_service')
    @patch('api.vistas.puesto.crear_puesto_view.PuestoSerializer')
    def test_usuario_autenticado_acceso_permitido(self, mock_serializer_class, mock_service):
        """
        Test: Usuario autenticado -> acceso permitido
        
        Given: Una petición POST a la vista de creación realizada por un usuario autenticado.
        When: La petición es procesada por el middleware de permisos de la vista.
        Then: La clase IsAuthenticated permite el acceso y la ejecución continúa (verificado al recibir el status 201).
        """
        request = self.factory.post(self.url, data={'nombre': 'Puesto 1'}, format='json')
        force_authenticate(request, user=self.user)

        mock_serializer_instance = mock_serializer_class.return_value
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.validated_data = {}
        mock_serializer_instance.data = {'id': 1, 'nombre': 'Puesto 1'}
        mock_service.return_value = MagicMock()

        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mock_serializer_class.assert_called()



    def test_usuario_no_autenticado_acceso_denegado(self):
        """
        Test: Usuario no autenticado -> acceso denegado
        
        Given: Una petición POST enviada por un usuario anónimo (sin autenticar).
        When: La petición entra en la vista y evalúa la clase IsAuthenticated.
        Then: La vista rechaza inmediatamente la petición con un error HTTP 401 (Unauthorized) sin llegar a ejecutar el POST.
        """
        request = self.factory.post(self.url, data={'nombre': 'Puesto 1'}, format='json')

        request.user = AnonymousUser()

        response = self.vista_callable(request)

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])



    @patch('api.vistas.puesto.crear_puesto_view.create_puesto_service')
    @patch('api.vistas.puesto.crear_puesto_view.PuestoSerializer')
    def test_crea_puesto_correctamente_201(self, mock_serializer_class, mock_service):
        """
        Test: Crea puesto correctamente (201)
        
        Given: Datos de entrada válidos y un usuario con permisos.
        When: Se realiza una petición POST.
        Then: La vista coordina la validación, ejecución del servicio y devuelve un estado HTTP 201.
        """
        request = self.factory.post(self.url, data=self.data_post, format='json')
        force_authenticate(request, user=self.user)

        mock_ser_in = MagicMock()
        mock_ser_in.validated_data = self.data_post
        
        mock_ser_out = MagicMock()
        mock_ser_out.data = {"id": 1, "nombre": "Costalero", "acto": 1}
        
        mock_serializer_class.side_effect = [mock_ser_in, mock_ser_out]
        mock_service.return_value = MagicMock()

        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)



    @patch('api.vistas.puesto.crear_puesto_view.create_puesto_service')
    @patch('api.vistas.puesto.crear_puesto_view.PuestoSerializer')
    def test_llama_al_servicio_con_usuario_y_datos_validados(self, mock_serializer_class, mock_service):
        """
        Test: Llama al servicio con request.user y validated_data
        
        Given: Un flujo donde el serializador ha validado los datos de entrada.
        When: Se llega al paso de ejecución del servicio.
        Then: Se verifica que create_puesto_service recibe el objeto user del request y el diccionario de datos validados.
        """
        request = self.factory.post(self.url, data=self.data_post, format='json')
        force_authenticate(request, user=self.user)
        
        mock_ser = MagicMock()
        datos_validados_mock = {"nombre": "Costalero", "acto": 1}
        mock_ser.validated_data = datos_validados_mock
        mock_serializer_class.return_value = mock_ser

        self.vista_callable(request)

        mock_service.assert_called_once_with(
            usuario=self.user,
            data_validada=datos_validados_mock
        )



    @patch('api.vistas.puesto.crear_puesto_view.create_puesto_service')
    @patch('api.vistas.puesto.crear_puesto_view.PuestoSerializer')
    def test_devuelve_datos_serializados_del_puesto_creado(self, mock_serializer_class, mock_service):
        """
        Test: Devuelve datos serializados del puesto creado
        
        Given: Un puesto recién creado por el servicio.
        When: Se prepara la respuesta.
        Then: La vista debe instanciar un nuevo serializador con el objeto retornado y devolver su atributo .data.
        """
        request = self.factory.post(self.url, data=self.data_post, format='json')
        force_authenticate(request, user=self.user)
        
        puesto_creado_mock = MagicMock()
        mock_service.return_value = puesto_creado_mock
        
        mock_ser_in = MagicMock()
        mock_ser_out = MagicMock()
        datos_respuesta = {"id": 99, "status": "creado"}
        mock_ser_out.data = datos_respuesta
        
        mock_serializer_class.side_effect = [mock_ser_in, mock_ser_out]

        response = self.vista_callable(request)

        mock_serializer_class.assert_called_with(puesto_creado_mock)
        self.assertEqual(response.data, datos_respuesta)



    @patch('api.vistas.puesto.crear_puesto_view.create_puesto_service')
    @patch('api.vistas.puesto.crear_puesto_view.PuestoSerializer')
    def test_serializer_is_valid_con_raise_exception(self, mock_serializer_class, mock_service):
        """
        Test: serializer.is_valid se llama con raise_exception=True
        
        Given: Datos en el cuerpo del POST.
        When: La vista instancia el serializador para validar.
        Then: Se verifica que se activa la propagación automática de errores de validación.
        """
        request = self.factory.post(self.url, data=self.data_post, format='json')
        force_authenticate(request, user=self.user)
        mock_ser_in = mock_serializer_class.return_value

        self.vista_callable(request)

        mock_ser_in.is_valid.assert_called_once_with(raise_exception=True)



    @patch('api.vistas.puesto.crear_puesto_view.create_puesto_service')
    @patch('api.vistas.puesto.crear_puesto_view.PuestoSerializer')
    def test_serializer_invalido_lanza_excepcion(self, mock_serializer_class, mock_service):
        """
        Test: Serializer inválido
        
        Given: Datos de entrada que no cumplen con las reglas de validación del serializador.
        When: La vista invoca is_valid(raise_exception=True) sobre los datos.
        Then: El serializador lanza una excepción y el flujo se interrumpe antes de llegar al servicio.
        """
        request = self.factory.post(self.url, data=self.data_post, format='json')
        force_authenticate(request, user=self.user)
        
        mock_ser_in = mock_serializer_class.return_value
        mock_ser_in.is_valid.side_effect = Exception("Datos de entrada inválidos")

        with self.assertRaises(Exception) as context:
            self.vista_callable(request)
            
        self.assertEqual(str(context.exception), "Datos de entrada inválidos")

        mock_service.assert_not_called()



    @patch('api.vistas.puesto.crear_puesto_view.create_puesto_service')
    @patch('api.vistas.puesto.crear_puesto_view.PuestoSerializer')
    def test_error_en_el_servicio_lanza_excepcion(self, mock_serializer_class, mock_service):
        """
        Test: Error en el servicio
        
        Given: Datos válidos enviados por un usuario autenticado.
        When: El servicio de negocio (create_puesto_service) encuentra un problema (ej. base de datos inaccesible o error de integridad).
        Then: La excepción generada en la capa de servicio se propaga sin ser enmascarada por la vista.
        """
        request = self.factory.post(self.url, data=self.data_post, format='json')
        force_authenticate(request, user=self.user)

        mock_ser_in = mock_serializer_class.return_value
        mock_ser_in.is_valid.return_value = True

        mock_service.side_effect = Exception("Fallo interno en la creación del puesto")

        with self.assertRaises(Exception) as context:
            self.vista_callable(request)
            
        self.assertEqual(str(context.exception), "Fallo interno en la creación del puesto")



    @patch('api.vistas.puesto.crear_puesto_view.create_puesto_service')
    @patch('api.vistas.puesto.crear_puesto_view.PuestoSerializer')
    def test_error_en_serializer_de_salida_lanza_excepcion(self, mock_serializer_class, mock_service):
        """
        Test: Error en serializer de salida
        
        Given: Un puesto que ha sido creado satisfactoriamente en base de datos.
        When: La vista intenta instanciar el serializador de respuesta pasándole la nueva instancia del modelo.
        Then: Si ocurre un fallo en el mapeo de los datos de salida, se lanza la excepción correspondiente.
        """
        request = self.factory.post(self.url, data=self.data_post, format='json')
        force_authenticate(request, user=self.user)

        mock_service.return_value = MagicMock()
        
        mock_ser_in = MagicMock()
        mock_ser_in.is_valid.return_value = True

        mock_serializer_class.side_effect = [
            mock_ser_in, 
            Exception("Error al serializar el objeto creado")
        ]

        with self.assertRaises(Exception) as context:
            self.vista_callable(request)
            
        self.assertEqual(str(context.exception), "Error al serializar el objeto creado")



    @patch('api.vistas.puesto.crear_puesto_view.create_puesto_service')
    @patch('api.vistas.puesto.crear_puesto_view.PuestoSerializer')
    def test_validated_data_vacio(self, mock_serializer_class, mock_service):
        """
        Test: validated_data vacío
        
        Given: Un payload que el serializador considera válido pero que resulta en un diccionario vacío (ej. campos opcionales omitidos).
        When: La vista invoca al servicio.
        Then: Se verifica que create_puesto_service maneja y recibe exactamente un diccionario vacío {}.
        """
        request = self.factory.post(self.url, data={}, format='json')
        force_authenticate(request, user=self.user)
        
        mock_ser_in = MagicMock()
        mock_ser_in.validated_data = {}
        mock_serializer_class.return_value = mock_ser_in

        self.vista_callable(request)

        mock_service.assert_called_once_with(
            usuario=self.user,
            data_validada={}
        )



    @patch('api.vistas.puesto.crear_puesto_view.create_puesto_service')
    @patch('api.vistas.puesto.crear_puesto_view.PuestoSerializer')
    def test_verificar_que_serializer_salida_usa_objeto_creado(self, mock_serializer_class, mock_service):
        """
        Test: Verificar que el serializer de salida usa el objeto creado
        
        Given: La ejecución exitosa del servicio de negocio, que retorna una instancia del modelo.
        When: Se prepara la respuesta para el cliente.
        Then: La vista debe instanciar un nuevo serializador pasando explícitamente el objeto retornado por el servicio.
        """
        request = self.factory.post(self.url, data=self.data_post, format='json')
        force_authenticate(request, user=self.user)
        
        puesto_creado_mock = MagicMock()
        mock_service.return_value = puesto_creado_mock
        
        mock_ser_in = MagicMock()
        mock_ser_out = MagicMock()
        mock_serializer_class.side_effect = [mock_ser_in, mock_ser_out]

        self.vista_callable(request)

        mock_serializer_class.assert_called_with(puesto_creado_mock)



    @patch('api.vistas.puesto.crear_puesto_view.create_puesto_service')
    @patch('api.vistas.puesto.crear_puesto_view.PuestoSerializer')
    def test_verificar_status_201_en_respuesta(self, mock_serializer_class, mock_service):
        """
        Test: Verificar status 201 en respuesta
        
        Given: Todo el flujo de creación completado exitosamente.
        When: La vista construye el objeto de respuesta de DRF.
        Then: Se verifica que la respuesta instanciada contiene explícitamente el código HTTP 201 y los datos correctos.
        """
        request = self.factory.post(self.url, data=self.data_post, format='json')
        force_authenticate(request, user=self.user)

        mock_ser_in = MagicMock()
        mock_ser_out = MagicMock()
        datos_respuesta = {"id": 1, "nombre": "Costalero"}
        mock_ser_out.data = datos_respuesta
        
        mock_serializer_class.side_effect = [mock_ser_in, mock_ser_out]

        mock_service.return_value = MagicMock()

        response = self.vista_callable(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, datos_respuesta)
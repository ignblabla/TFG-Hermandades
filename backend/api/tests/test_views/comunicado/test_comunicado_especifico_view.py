import unittest
from unittest.mock import ANY, MagicMock, patch
from django.http import Http404
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError

from api.vistas.comunicado.comunicado_view import ComunicadoDetailView
from api.models import Comunicado


class TestComunicadoDetailView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ComunicadoDetailView.as_view()
        self.pk = 1
        self.path = f"/api/comunicados/{self.pk}/"

        self.mock_user = MagicMock(spec=['is_authenticated'])
        self.mock_user.is_authenticated = True



    # ---------------------------------------------------------------------------
    # TESTS GET
    # ---------------------------------------------------------------------------

    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_flujo_feliz_detalle_correcto(self, mock_get_object, mock_serializer):
        """
        Test: Flujo feliz (detalle correcto)
        
        Given: Un ID de comunicado (pk) existente.
        When: Se solicita el detalle.
        Then: Se verifica la llamada al serializador con el objeto y el contexto.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_comunicado = MagicMock(name="ComunicadoInstance")
        mock_get_object.return_value = mock_comunicado

        datos_esperados = {"id": 1, "titulo": "Comunicado Test"}
        mock_serializer.return_value.data = datos_esperados

        response = self.view(request, pk=self.pk)

        mock_get_object.assert_called_once_with(Comunicado, pk=self.pk)

        mock_serializer.assert_called_once_with(mock_comunicado, context={'request': ANY})

        args, kwargs = mock_serializer.call_args
        self.assertIsInstance(kwargs['context']['request'], Request)
        self.assertEqual(kwargs['context']['request']._request, request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_esperados)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_se_llama_a_get_object_or_404_con_modelo_y_pk_correctos(self, mock_get_object, mock_serializer):
        """
        Test: Se llama a get_object_or_404 con modelo correcto
        
        Given: Una petición GET para un comunicado específico con ID 99.
        When: La vista ejecuta el método get.
        Then: Se debe invocar a get_object_or_404 pasando el modelo Comunicado 
            y el pk=99 extraído de la URL.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_get_object.return_value = MagicMock()

        self.view(request, pk=self.pk)

        mock_get_object.assert_called_once()

        args, kwargs = mock_get_object.call_args

        self.assertEqual(args[0], Comunicado)
        self.assertEqual(kwargs["pk"], self.pk)



    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_comunicado_no_existe_lanza_404(self, mock_get_object):
        """
        Test: Comunicado no existe
        
        Given: Un ID de comunicado que no existe.
        When: La vista intenta obtenerlo.
        Then: DRF captura el Http404 y devuelve una respuesta 404.
        """
        pk_inexistente = 999
        request = self.factory.get(f"/api/comunicados/{pk_inexistente}/")
        force_authenticate(request, user=self.mock_user)

        mock_get_object.side_effect = Http404()

        response = self.view(request, pk=pk_inexistente)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_pk_invalido_comportamiento_404(self, mock_get_object):
        """
        Test: pk inválido (string o None)
        
        Given: Un valor de PK inválido.
        When: get_object_or_404 es invocado.
        Then: Se debe retornar un status 404 manejado por el framework.
        """
        pk_invalido = "abc"
        request = self.factory.get(f"/api/comunicados/{pk_invalido}/")
        force_authenticate(request, user=self.mock_user)

        mock_get_object.side_effect = Http404("ID inválido")

        response = self.view(request, pk=pk_invalido)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_serializer_falla_lanza_excepcion(self, mock_get_object, mock_serializer):
        """
        Test: Serializer falla
        
        Given: Un objeto recuperado correctamente.
        When: La vista intenta instanciar el ComunicadoListSerializer.
        Then: El serializador lanza una excepción y, al no estar manejada en la vista,
            esta se propaga (resultando en un error 500).
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        mock_get_object.return_value = MagicMock()

        mock_serializer.side_effect = Exception("serializer error")

        with self.assertRaises(Exception) as context:
            self.view(request, pk=self.pk)
            
        self.assertEqual(str(context.exception), "serializer error")



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_serializer_data_rompe_lanza_excepcion(self, mock_get_object, mock_serializer):
        """
        Test: serializer.data rompe
        
        Given: Un serializador instanciado correctamente.
        When: La vista intenta acceder a la propiedad .data para la respuesta.
        Then: La excepción inyectada en la propiedad data se propaga, provocando un fallo 500.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        mock_get_object.return_value = MagicMock()

        mock_instance = mock_serializer.return_value
        type(mock_instance).data = property(
            lambda _: (_ for _ in ()).throw(Exception("data error"))
        )

        with self.assertRaises(Exception) as context:
            self.view(request, pk=self.pk)
            
        self.assertEqual(str(context.exception), "data error")



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_se_pasa_el_contexto_correctamente(self, mock_get_object, mock_serializer):
        """
        Test: Se pasa el contexto correctamente
        
        Given: Un comunicado existente.
        When: La vista instancia el serializador.
        Then: Debe incluir el 'request' en el diccionario de contexto para que el 
            serializador pueda generar URIs absolutas si fuera necesario.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_comunicado = MagicMock(name="ComunicadoInstance")
        mock_get_object.return_value = mock_comunicado
        mock_serializer.return_value.data = {}

        self.view(request, pk=self.pk)

        mock_serializer.assert_called_once_with(
            mock_comunicado,
            context={"request": ANY}
        )

        serializer_args = mock_serializer.call_args
        self.assertIsInstance(serializer_args.kwargs['context']['request'], Request)



    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_request_sin_autenticacion_falla_401(self, mock_get_object):
        """
        Test: Request sin autenticación (Realista)
        
        Given: Un usuario anónimo (sin autenticar).
        When: Se intenta acceder al detalle del comunicado.
        Then: La vista debe ejecutar permission_classes e interceptar 
            la petición devolviendo un status 401 Unauthorized.
        """
        request = self.factory.get(self.path)

        request.user = AnonymousUser()

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        mock_get_object.assert_not_called()



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_respuesta_no_modifica_objeto(self, mock_get_object, mock_serializer):
        """
        Test: Respuesta no modifica objeto
        
        Given: Un objeto comunicado obtenido de la base de datos.
        When: Se pasa al serializador para la respuesta GET.
        Then: Se verifica que el objeto comunicado se pase íntegro y no se 
            realicen llamadas a métodos de mutación (como .save()).
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_comunicado = MagicMock(name="ComunicadoOriginal")
        mock_get_object.return_value = mock_comunicado
        mock_serializer.return_value.data = {}

        self.view(request, pk=self.pk)

        mock_serializer.assert_called_once_with(mock_comunicado, context=ANY)

        self.assertEqual(mock_comunicado.save.call_count, 0)



    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_comunicado_modelo_wiring_correcto(self, mock_get_object):
        """
        Test: Comunicado modelo/patch correcto (Wiring test)
        
        Given: Una petición al detalle del comunicado.
        When: La vista ejecuta get_object_or_404.
        Then: El primer argumento de la llamada debe ser exactamente la clase 
            del modelo 'Comunicado' importada en la vista. Si alguien cambia 
            la importación o el modelo por error, este test fallará.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        self.view(request, pk=self.pk)

        args, _ = mock_get_object.call_args
        self.assertEqual(args[0], Comunicado, "La vista no está usando el modelo Comunicado en el shortcut")



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_get_object_returns_none_breaks_serializer(self, mock_get_object, mock_serializer):
        """
        Test: get_object_or_404 devuelve None (Simulación de error de lógica)
        
        Given: Un escenario donde el shortcut devuelve None (aunque usualmente lanza 404).
        When: El serializador intenta procesar ese None.
        Then: El serializador debería lanzar una excepción al intentar acceder a los 
            campos de un objeto inexistente, resultando en un error de la vista.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_get_object.return_value = None

        mock_serializer.side_effect = TypeError("No se puede serializar un objeto None")

        with self.assertRaises(TypeError):
            self.view(request, pk=self.pk)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_serializa_correctamente_objeto_unico_no_many(self, mock_get_object, mock_serializer):
        """
        Test: Serializa correctamente objeto único (no many=True)
        
        Given: Una petición de detalle de un solo objeto.
        When: Se instancia el serializador.
        Then: El parámetro 'many' debe ser False (o no estar presente, lo que por 
            defecto es False en DRF) para evitar errores de iteración.
        """
        request = self.factory.get(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_get_object.return_value = MagicMock()
        mock_serializer.return_value.data = {}

        self.view(request, pk=self.pk)

        _, kwargs = mock_serializer.call_args

        self.assertFalse(kwargs.get("many", False), "El serializador se llamó con many=True en una vista de detalle")



    # ---------------------------------------------------------------------------
    # TESTS PUT
    # ---------------------------------------------------------------------------

    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_actualizacion_total_exitosa(self, mock_get, mock_form, mock_service, mock_serializer_out):
        """
        Test: Flujo feliz (actualización correcta)
        
        Given: Un comunicado existente y datos de actualización válidos.
        When: Se realiza una petición PUT al endpoint de detalle.
        Then: Se debe validar el formulario, llamar al servicio de actualización 
            con la instancia original y devolver el objeto actualizado serializado.
        """
        datos_input = {"titulo": "Nuevo Título", "contenido": "Nuevo Contenido"}
        request = self.factory.put(self.path, data=datos_input, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_comunicado_original = MagicMock(name="ComunicadoOriginal")
        mock_get.return_value = mock_comunicado_original

        mock_form_instance = mock_form.return_value
        mock_form_instance.is_valid.return_value = True
        datos_validados = {"titulo": "Nuevo Título", "contenido": "Nuevo Contenido"}
        mock_form_instance.validated_data = datos_validados

        mock_service_instance = mock_service.return_value
        obj_actualizado_mock = MagicMock(name="obj_actualizado")
        mock_service_instance.update_comunicado.return_value = obj_actualizado_mock

        datos_respuesta = {"id": 1, "titulo": "Nuevo Título"}
        mock_serializer_out.return_value.data = datos_respuesta

        response = self.view(request, pk=self.pk)

        mock_form.assert_called_once_with(mock_comunicado_original, data=datos_input)

        mock_service_instance.update_comunicado.assert_called_once_with(
            usuario=self.mock_user,
            comunicado_instance=mock_comunicado_original,
            data_validada=datos_validados
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_respuesta)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_verificar_obtencion_objeto_y_validacion_serializer(self, mock_get, mock_form, mock_service):
        """
        Test: Se obtiene objeto con get_object_or_404
            Se valida serializer de entrada correctamente
        
        Given: Una petición PUT con datos de actualización.
        When: La vista procesa la solicitud.
        Then: Se debe llamar a get_object_or_404 con el modelo Comunicado y el pk correcto,
            y posteriormente ejecutar is_valid con raise_exception=True.
        """
        datos_input = {"titulo": "Update Test"}
        request = self.factory.put(self.path, data=datos_input, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_comunicado = MagicMock(name="InstanciaComunicado")
        mock_get.return_value = mock_comunicado
        
        mock_form_instance = mock_form.return_value
        mock_form_instance.is_valid.return_value = True

        self.view(request, pk=self.pk)

        mock_get.assert_called_once_with(Comunicado, pk=self.pk)

        mock_form_instance.is_valid.assert_called_once_with(raise_exception=True)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_se_pasa_instancia_al_serializer(self, mock_get, mock_form):
        """
        Test: Se pasa instancia al serializer
        
        Given: Un objeto recuperado de la base de datos y nuevos datos en el body.
        When: Se instancia el ComunicadoFormSerializer para un PUT.
        Then: El serializador debe recibir tanto la instancia original como 
            el diccionario de datos (data=request.data).
        """
        datos_input = {"titulo": "Título Editado"}
        request = self.factory.put(self.path, data=datos_input, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_comunicado = MagicMock(name="InstanciaOriginal")
        mock_get.return_value = mock_comunicado

        mock_form.return_value.is_valid.return_value = True

        self.view(request, pk=self.pk)

        mock_form.assert_called_once_with(
            mock_comunicado,
            data=datos_input
        )



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_validacion_falla_serializer_invalido(self, mock_get, mock_form):
        """
        Test: Validación falla (serializer inválido)
        
        Given: Datos que no cumplen con los requisitos del serializador.
        When: Se llama a is_valid(raise_exception=True).
        Then: DRF lanza automáticamente una ValidationError, lo que resulta 
            en una respuesta con status 400.
        """
        request = self.factory.put(self.path, data={}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_get.return_value = MagicMock()

        mock_form.return_value.is_valid.side_effect = ValidationError({"error": "campo requerido"})

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_validated_data_vacio_falla_en_servicio(self, mock_get, mock_form, mock_service):
        """
        Test: validated_data inválido o vacío
        
        Given: Un serializador que es válido pero devuelve datos vacíos.
        When: El servicio intenta actualizar con datos nulos.
        Then: El servicio lanza una excepción que la vista captura, devolviendo un 400.
        """
        request = self.factory.put(self.path, data={}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_get.return_value = MagicMock()
        mock_form.return_value.is_valid.return_value = True

        mock_form.return_value.validated_data = None

        mock_service.return_value.update_comunicado.side_effect = Exception("Datos de actualización no validos")

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_servicio_lanza_excepcion_capturada(self, mock_get, mock_form, mock_service):
        """
        Test: Servicio lanza excepción
        
        Given: Un flujo de validación correcto.
        When: El servicio update_comunicado falla (ej. error de base de datos).
        Then: La vista captura la excepción y devuelve un 400 con el detalle del error.
        """
        request = self.factory.put(self.path, data={"titulo": "test"}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_get.return_value = MagicMock()
        mock_form.return_value.is_valid.return_value = True

        mock_service.return_value.update_comunicado.side_effect = Exception("service error")

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "service error"})



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_serializer_salida_falla_capturado(self, mock_get, mock_form, mock_service, mock_serializer_out):
        """
        Test: Serializer de salida falla
        
        Given: Una actualización exitosa en el servicio.
        When: El serializador de respuesta lanza un error inesperado.
        Then: El error se captura en el bloque try/except y devuelve un 400.
        """
        request = self.factory.put(self.path, data={"titulo": "test"}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_get.return_value = MagicMock()
        mock_form.return_value.is_valid.return_value = True
        mock_service.return_value.update_comunicado.return_value = MagicMock()

        mock_serializer_out.side_effect = Exception("serializer error")

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "serializer error")



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_serializer_data_rompe_devuelve_400(self, mock_get, mock_form, mock_service, mock_serializer_out):
        """
        Test: serializer.data rompe
        
        Given: Un flujo de actualización que llega hasta la serialización de salida.
        When: Se accede a la propiedad .data pero esta lanza una excepción.
        Then: El bloque try/except de la vista debe capturarlo y devolver un 400.
        """
        request = self.factory.put(self.path, data={"titulo": "Test"}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_get.return_value = MagicMock()
        mock_form.return_value.is_valid.return_value = True
        mock_service.return_value.update_comunicado.return_value = MagicMock()

        mock_instance = mock_serializer_out.return_value
        type(mock_instance).data = property(
            lambda _: (_ for _ in ()).throw(Exception("data error"))
        )

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "data error")



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_se_llama_al_servicio_con_parametros_correctos(self, mock_get, mock_form, mock_service):
        """
        Test: Se llama al servicio con parámetros correctos
        
        Given: Una petición PUT válida.
        When: La vista delega en el servicio.
        Then: Se verifica que se pasen el usuario, la instancia original del 
            comunicado y los datos validados del formulario.
        """
        request = self.factory.put(self.path, data={"titulo": "Update"}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_comunicado = MagicMock(name="InstanciaOriginal")
        mock_get.return_value = mock_comunicado
        
        mock_form_instance = mock_form.return_value
        mock_form_instance.is_valid.return_value = True
        mock_form_instance.validated_data = {"titulo": "Update"}

        self.view(request, pk=self.pk)

        mock_service.return_value.update_comunicado.assert_called_once_with(
            usuario=self.mock_user,
            comunicado_instance=mock_comunicado,
            data_validada=mock_form_instance.validated_data
        )



    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_pk_invalido_o_no_existente_lanza_404(self, mock_get):
        """
        Test: pk inválido o no existente
        
        Given: Un PK que no corresponde a ningún registro.
        When: La vista llama a get_object_or_404.
        Then: Se devuelve automáticamente un status 404 manejado por el framework.
        """
        request = self.factory.put(self.path, data={"titulo": "test"}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_get.side_effect = Http404()

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_request_data_vacio_lanza_400(self, mock_get, mock_form):
        """
        Test: request.data vacío
        
        Given: Una petición PUT con un cuerpo vacío {}.
        When: El serializador valida los datos con raise_exception=True.
        Then: Se lanza una ValidationError que DRF convierte en status 400.
        """
        request = self.factory.put(self.path, data={}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_get.return_value = MagicMock()
        mock_form.return_value.is_valid.side_effect = ValidationError("Error de validación")

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    # ---------------------------------------------------------------------------
    # TESTS PATCH
    # ---------------------------------------------------------------------------

    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_actualizacion_parcial_exitosa(self, mock_get, mock_form, mock_service, mock_serializer_out):
        """
        Test: Flujo feliz (PATCH correcto)
        
        Given: Un comunicado existente y datos parciales (solo un campo).
        When: Se realiza una petición PATCH al endpoint de detalle.
        Then: El serializador debe instanciarse con partial=True, el servicio debe 
            procesar la actualización y devolver un status 200 con los datos.
        """
        datos_parciales = {"titulo": "Título modificado parcialmente"}
        request = self.factory.patch(self.path, data=datos_parciales, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_obj = MagicMock(name="ComunicadoOriginal")
        mock_get.return_value = mock_obj

        mock_form_instance = mock_form.return_value
        mock_form_instance.is_valid.return_value = True
        mock_form_instance.validated_data = datos_parciales

        obj_actualizado = MagicMock(name="ComunicadoActualizado")
        mock_service.return_value.update_comunicado.return_value = obj_actualizado

        datos_finales = {"id": 1, "titulo": "Título modificado parcialmente", "contenido": "Contenido original"}
        mock_serializer_out.return_value.data = datos_finales

        response = self.view(request, pk=self.pk)

        mock_form.assert_called_once_with(
            mock_obj, 
            data=datos_parciales, 
            partial=True
        )

        mock_service.return_value.update_comunicado.assert_called_once_with(
            usuario=self.mock_user,
            comunicado_instance=mock_obj,
            data_validada=datos_parciales
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, datos_finales)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_verificar_partial_true_y_obtencion_objeto(self, mock_get, mock_form, mock_service):
        """
        Test: partial=True se usa correctamente
            Se obtiene objeto con get_object_or_404
        
        Given: Una petición PATCH con datos parciales.
        When: La vista procesa la solicitud.
        Then: Debe recuperar el objeto correcto y pasarlo al serializador 
            activando explícitamente el modo de validación parcial.
        """
        datos_patch = {"contenido": "Solo actualizo el contenido"}
        request = self.factory.patch(self.path, data=datos_patch, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_obj = MagicMock(name="ComunicadoInstance")
        mock_get.return_value = mock_obj

        mock_form.return_value.is_valid.return_value = True

        self.view(request, pk=self.pk)

        mock_get.assert_called_once_with(Comunicado, pk=self.pk)

        mock_form.assert_called_once_with(
            mock_obj,
            data=datos_patch,
            partial=True
        )



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_se_valida_serializer_con_raise_exception_true(self, mock_get, mock_form):
        """
        Test: Se valida serializer con raise_exception=True
        
        Given: Una petición PATCH con datos válidos.
        When: La vista ejecuta la validación del serializador.
        Then: Se debe llamar a is_valid asegurando que DRF gestione 
            las excepciones de validación automáticamente.
        """
        request = self.factory.patch(self.path, data={"titulo": "test"}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_get.return_value = MagicMock()
        mock_form_instance = mock_form.return_value
        mock_form_instance.is_valid.return_value = True

        self.view(request, pk=self.pk)

        mock_form_instance.is_valid.assert_called_once_with(raise_exception=True)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_validacion_falla_parcial_devuelve_400(self, mock_get, mock_form):
        """
        Test: Validación falla
        
        Given: Datos que no cumplen las reglas de negocio del serializador.
        When: Se llama a is_valid.
        Then: DRF debe retornar automáticamente un status 400.
        """
        request = self.factory.patch(self.path, data={"campo_invalido": "valor"}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_get.return_value = MagicMock()

        mock_form.return_value.is_valid.side_effect = ValidationError({"error": "dato invalido"})

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_validated_data_vacio_patch_falla(self, mock_get, mock_form, mock_service):
        """
        Test: validated_data vacío
        
        Given: Un serializador que pasa la validación pero no genera datos útiles.
        When: Se intenta llamar al servicio con datos nulos.
        Then: El servicio lanza una excepción que es capturada por el try/except de la vista.
        """
        request = self.factory.patch(self.path, data={}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_get.return_value = MagicMock()
        mock_form_instance = mock_form.return_value
        mock_form_instance.is_valid.return_value = True

        mock_form_instance.validated_data = None

        mock_service.return_value.update_comunicado.side_effect = Exception("No hay datos para actualizar")

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "No hay datos para actualizar")



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_servicio_lanza_excepcion_en_patch(self, mock_get, mock_form, mock_service):
        """
        Test: Servicio lanza excepción
        
        Given: Un formulario válido.
        When: El servicio update_comunicado falla por una regla de negocio.
        Then: La vista debe capturar la excepción y responder con status 400.
        """
        request = self.factory.patch(self.path, data={"titulo": "error"}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_get.return_value = MagicMock()
        mock_form.return_value.is_valid.return_value = True

        mock_service.return_value.update_comunicado.side_effect = Exception("service error")

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "service error")



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_serializer_salida_falla_en_patch(self, mock_get, mock_form, mock_service, mock_serializer_out):
        """
        Test: Serializer de salida falla
        
        Given: Una actualización exitosa en el servicio.
        When: La instanciación del ComunicadoListSerializer falla.
        Then: La vista captura el error y responde con status 400.
        """
        request = self.factory.patch(self.path, data={"titulo": "test"}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_get.return_value = MagicMock()
        mock_form.return_value.is_valid.return_value = True
        mock_service.return_value.update_comunicado.return_value = MagicMock()

        mock_serializer_out.side_effect = Exception("serializer error")

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "serializer error")



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_serializer_data_rompe_en_patch(self, mock_get, mock_form, mock_service, mock_serializer_out):
        """
        Test: .data rompe
        
        Given: Un flujo de patch correcto hasta la respuesta final.
        When: Se intenta acceder a la propiedad .data y esta lanza una excepción.
        Then: La vista captura la excepción en el bloque try/except y retorna 400.
        """
        request = self.factory.patch(self.path, data={"titulo": "test"}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_get.return_value = MagicMock()
        mock_form.return_value.is_valid.return_value = True
        mock_service.return_value.update_comunicado.return_value = MagicMock()

        mock_instance = mock_serializer_out.return_value
        type(mock_instance).data = property(
            lambda _: (_ for _ in ()).throw(Exception("data error"))
        )

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "data error")



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_se_llama_al_service_correctamente_en_patch(self, mock_get, mock_form, mock_service):
        """
        Test: Se llama al service correctamente
        
        Given: Una petición PATCH con datos parciales válidos.
        When: La vista invoca la capa de servicio.
        Then: Se debe llamar a update_comunicado con el usuario de la petición,
            la instancia recuperada y los datos validados del serializador.
        """
        datos_input = {"titulo": "Nuevo Titulo"}
        request = self.factory.patch(self.path, data=datos_input, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_obj = MagicMock(name="ComunicadoOriginal")
        mock_get.return_value = mock_obj
        
        mock_form_instance = mock_form.return_value
        mock_form_instance.is_valid.return_value = True
        mock_form_instance.validated_data = {"titulo": "Nuevo Titulo"}

        self.view(request, pk=self.pk)

        mock_service.return_value.update_comunicado.assert_called_once_with(
            usuario=self.mock_user,
            comunicado_instance=mock_obj,
            data_validada=mock_form_instance.validated_data
        )



    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_pk_no_existe_en_patch_retorna_404(self, mock_get):
        """
        Test: pk no existe
        
        Given: Un ID de comunicado que no figura en la base de datos.
        When: Se intenta realizar un PATCH.
        Then: get_object_or_404 lanza Http404 y DRF responde con un status 404.
        """
        request = self.factory.patch(self.path, data={"titulo": "cambio"}, format='json')
        force_authenticate(request, user=self.mock_user)

        mock_get.side_effect = Http404()

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_request_data_vacio_en_patch_lanza_400(self, mock_get, mock_form):
        """
        Test: request.data vacío
        
        Given: Una petición PATCH con un body vacío {}.
        When: El serializador valida la entrada (aunque sea parcial).
        Then: Si las reglas del serializador consideran que el envío vacío es inválido,
            se lanza ValidationError y se retorna un status 400.
        """
        request = self.factory.patch(self.path, data={}, format='json')
        force_authenticate(request, user=self.mock_user)
        
        mock_get.return_value = MagicMock()

        mock_form.return_value.is_valid.side_effect = ValidationError("Body requerido")

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    # ---------------------------------------------------------------------------
    # TESTS DELETE
    # ---------------------------------------------------------------------------

    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_delete_flujo_feliz_correcto(self, mock_get, mock_service):
        """
        Test: Flujo feliz (DELETE correcto)
        
        Given: Un comunicado existente en la base de datos.
        When: Se envía una petición DELETE al endpoint.
        Then: El servicio procesa el borrado y se retorna un status 204 No Content sin cuerpo.
        """
        request = self.factory.delete(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_obj = MagicMock(name="ComunicadoAEliminar")
        mock_get.return_value = mock_obj
        
        mock_service_instance = mock_service.return_value
        mock_service_instance.delete_comunicado.return_value = None

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(response.data)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_delete_obtiene_objeto_y_llama_servicio_correctamente(self, mock_get, mock_service):
        """
        Test:  Se obtiene objeto con get_object_or_404
            Se llama al service con parámetros correctos
        
        Given: Un ID de comunicado válido.
        When: Se ejecuta la acción de borrado.
        Then: Se debe verificar que se buscó el objeto correcto y se pasó al 
            servicio junto con el usuario que realiza la acción.
        """
        request = self.factory.delete(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_obj = MagicMock(name="ComunicadoInstance")
        mock_get.return_value = mock_obj
        mock_service_instance = mock_service.return_value

        self.view(request, pk=self.pk)

        mock_get.assert_called_once_with(Comunicado, pk=self.pk)

        mock_service_instance.delete_comunicado.assert_called_once_with(
            usuario=self.mock_user,
            comunicado_instance=mock_obj
        )



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_servicio_lanza_excepcion_en_delete(self, mock_get, mock_service):
        """
        Test: Servicio lanza excepción
        
        Given: Un comunicado existente.
        When: El servicio delete_comunicado falla (ej. restricción de integridad).
        Then: La vista captura la excepción y responde con un status 400 y el detalle.
        """
        request = self.factory.delete(self.path)
        force_authenticate(request, user=self.mock_user)
        mock_get.return_value = MagicMock()

        mock_service.return_value.delete_comunicado.side_effect = Exception("service error")

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "service error"})



    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_delete_recurso_no_existente_falla_404(self, mock_get):
        """
        Test: get_object_or_404 falla
        
        Given: Un ID de comunicado que no existe.
        When: Se intenta eliminar el recurso.
        Then: Se dispara un 404 automático manejado por DRF.
        """
        request = self.factory.delete(self.path)
        force_authenticate(request, user=self.mock_user)

        mock_get.side_effect = Http404()

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    def test_delete_usuario_anonimo_bloqueado_401(self):
        """
        Test: usuario sin permisos (teórico)
        
        Given: Un usuario sin autenticar (AnonymousUser).
        When: Intenta realizar un DELETE.
        Then: DRF bloquea la petición antes de entrar a la lógica de la vista (401).
        """
        request = self.factory.delete(self.path)
        request.user = AnonymousUser()

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_delete_servicio_devuelve_error_inesperado(self, mock_get, mock_service):
        """
        Test: service devuelve error inesperado (no Exception)
        
        Given: Un servicio que devuelve un valor en lugar de lanzar excepción o None.
        When: Se procesa la eliminación.
        Then: La vista asume que todo fue bien (204) porque no hubo excepción capturada,
            lo cual podría ocultar un bug de lógica.
        """
        request = self.factory.delete(self.path)
        force_authenticate(request, user=self.mock_user)
        mock_get.return_value = MagicMock()

        mock_service.return_value.delete_comunicado.return_value = "error inesperado"

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)



    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_pk_invalido_en_delete_falla_404(self, mock_get):
        """
        Test: pk inválido (ej. "abc")
        
        Given: Un valor de PK que no es un entero.
        When: Se invoca get_object_or_404.
        Then: El shortcut falla y DRF lo convierte en un error 404.
        """
        pk_invalido = "abc"
        request = self.factory.delete(f"/api/comunicados/{pk_invalido}/")
        force_authenticate(request, user=self.mock_user)
        
        mock_get.side_effect = Http404()

        response = self.view(request, pk=pk_invalido)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_servicio_recibe_parametros_correctos(self, mock_get, mock_service):
        """
        Test: servicio no recibe parámetros correctos (Verificación de robustez)
        
        Given: Una petición de borrado válida.
        When: Se llama a delete_comunicado.
        Then: El servicio debe recibir exactamente el usuario de la request y la instancia.
        """
        request = self.factory.delete(self.path)
        force_authenticate(request, user=self.mock_user)
        
        mock_obj = MagicMock(name="InstanciaComunicado")
        mock_get.return_value = mock_obj
        
        self.view(request, pk=self.pk)

        call_args = mock_service.return_value.delete_comunicado.call_args
        self.assertEqual(call_args[1]["usuario"], self.mock_user)
        self.assertEqual(call_args[1]["comunicado_instance"], mock_obj)



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_excepcion_generica_no_controlada_da_400(self, mock_get, mock_service):
        """
        Test: excepción genérica no controlada en vista (ValueError)
        
        Given: Una excepción de tipo ValueError lanzada por el servicio.
        When: La vista captura cualquier 'Exception'.
        Then: Debe retornar status 400.
        """
        request = self.factory.delete(self.path)
        force_authenticate(request, user=self.mock_user)
        mock_get.return_value = MagicMock()

        mock_service.return_value.delete_comunicado.side_effect = ValueError("boom")

        response = self.view(request, pk=self.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "boom")



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_delete_no_devuelve_contenido(self, mock_get, mock_service):
        """
        Test: no devuelve contenido
        
        Given: Un borrado exitoso.
        When: Se genera la Response.
        Then: El cuerpo de la respuesta debe ser nulo siguiendo el estándar 204.
        """
        request = self.factory.delete(self.path)
        force_authenticate(request, user=self.mock_user)
        mock_get.return_value = MagicMock()

        response = self.view(request, pk=self.pk)

        self.assertTrue(response.data is None or response.data == "")



    @patch("api.vistas.comunicado.comunicado_view.ComunicadoListSerializer")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoFormSerializer")
    @patch("api.vistas.comunicado.comunicado_view.ComunicadoService")
    @patch("api.vistas.comunicado.comunicado_view.get_object_or_404")
    def test_delete_no_llama_serializer(self, mock_get, mock_service, mock_form, mock_list):
        """
        Test: no llama serializer (importante arquitectura)
        
        Given: Una petición DELETE.
        When: Se completa el proceso.
        Then: No debe haber ninguna interacción con los serializadores de entrada o salida.
        """
        request = self.factory.delete(self.path)
        force_authenticate(request, user=self.mock_user)
        mock_get.return_value = MagicMock()

        self.view(request, pk=self.pk)

        mock_form.assert_not_called()
        mock_list.assert_not_called()
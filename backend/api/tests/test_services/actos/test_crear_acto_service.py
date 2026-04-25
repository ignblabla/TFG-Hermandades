from django.db import IntegrityError
from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.core.exceptions import PermissionDenied

from api.servicios.acto.acto_service import crear_acto_service


class CrearActoServiceTests(TestCase):

    @patch('api.models.Acto.objects.create')
    def test_usuario_admin_creacion_exitosa(self, mock_acto_create):
        """
        Test: Usuario admin -> creación exitosa

        Given: Un usuario solicitante con el atributo esAdmin a True 
                y un diccionario con los datos validados del acto.
        When: Se llama al servicio crear_acto_service con estos parámetros.
        Then: El servicio invoca Acto.objects.create desempaquetando los datos (**data_validada)
                y retorna exactamente el objeto acto instanciado (sin tocar la base de datos).
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        data_validada = {
            'nombre': 'Ensayo Solidario',
            'lugar': 'Plaza Mayor',
            'fecha': '2026-10-10T10:00:00Z',
        }

        acto_esperado = MagicMock()
        mock_acto_create.return_value = acto_esperado

        resultado = crear_acto_service(usuario_admin, data_validada)

        mock_acto_create.assert_called_once_with(**data_validada)

        self.assertEqual(resultado, acto_esperado)



    @patch('api.services.Acto.objects.create')
    def test_usuario_admin_con_distintos_datos_validos(self, mock_acto_create):
        """
        Test: Usuario admin con distintos datos válidos

        Given: Un usuario administrador y diferentes estructuras de diccionarios 
                que representan distintos tipos de actos (mínimos y completos).
        When: Se llama al servicio crear_acto_service repetidamente con estas variantes.
        Then: El servicio debe invocar el ORM (Acto.objects.create) pasando 
                exactamente los kwargs correspondientes a cada variante, 
                sin depender de campos específicos.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        variantes_data = [
            {
                'nombre': 'Acto Mínimo',
                'lugar': 'Sede',
                'fecha': '2026-05-01T10:00:00Z',
                'tipo_acto_id': 1
            },
            {
                'nombre': 'Acto de Penitencia Completo',
                'lugar': 'Catedral',
                'descripcion': 'Salida procesional extraordinaria',
                'fecha': '2026-04-15T18:00:00Z',
                'modalidad': 'TRADICIONAL',
                'tipo_acto_id': 2,
                'inicio_solicitud': '2026-03-01T00:00:00Z',
                'fin_solicitud': '2026-03-15T00:00:00Z'
            }
        ]

        for data_prueba in variantes_data:
            crear_acto_service(usuario_admin, data_prueba)

            mock_acto_create.assert_called_with(**data_prueba)

        self.assertEqual(mock_acto_create.call_count, len(variantes_data))



    @patch('api.services.Acto.objects.create')
    def test_usuario_admin_con_es_admin_truthy_no_booleano(self, mock_acto_create):
        """
        Test: Usuario admin con esAdmin truthy no booleano

        Given: Un usuario cuyo atributo 'esAdmin' no es un booleano puro,
                sino un valor truthy (ej. el entero 1 o el string "True").
        When: Se llama al servicio crear_acto_service.
        Then: El servicio debe permitir la creación del acto, ya que la evaluación 
                booleana de Python (truthiness) acepta estos valores como válidos,
                invocando finalmente el método create del ORM.
        """
        valores_truthy = [1, "True", [True], {"admin": True}]

        for valor in valores_truthy:
            usuario_solicitante = MagicMock()
            usuario_solicitante.esAdmin = valor
            
            data_validada = {'nombre': f'Acto con admin {valor}', 'lugar': 'Sede'}
            mock_acto_create.return_value = MagicMock()

            resultado = crear_acto_service(usuario_solicitante, data_validada)

            mock_acto_create.assert_called_with(**data_validada)
            self.assertIsNotNone(resultado)

        self.assertEqual(mock_acto_create.call_count, len(valores_truthy))



    @patch('api.services.Acto.objects.create')
    def test_usuario_no_admin_lanza_permission_denied_y_no_crea_acto(self, mock_acto_create):
        """
        Test: Usuario NO admin -> PermissionDenied

        Given: Un usuario solicitante cuyo atributo 'esAdmin' es False.
        When: Se intenta llamar al servicio crear_acto_service para crear un nuevo acto.
        Then: El servicio debe elevar una excepción PermissionDenied con el mensaje 
                específico de restricción de administrador.
                Se debe garantizar que Acto.objects.create NO sea llamado, protegiendo 
                la integridad de la base de datos.
        """
        usuario_no_admin = MagicMock()
        usuario_no_admin.esAdmin = False
        
        data_validada = {
            'nombre': 'Acto Prohibido',
            'lugar': 'Ubicación Secreta'
        }

        with self.assertRaises(PermissionDenied) as context:
            crear_acto_service(usuario_no_admin, data_validada)

        self.assertEqual(
            str(context.exception), 
            "No tienes permisos para crear actos. Se requiere ser Administrador."
        )

        mock_acto_create.assert_not_called()



    @patch('api.services.Acto.objects.create')
    def test_usuario_sin_atributo_es_admin_lanza_permission_denied(self, mock_acto_create):
        """
        Test: Usuario sin atributo esAdmin -> PermissionDenied

        Given: Un objeto de usuario que no posee el atributo 'esAdmin' en absoluto.
        When: Se intenta llamar al servicio crear_acto_service.
        Then: La función getattr debe no encontrar el atributo y retornar el valor por defecto (False).
                El servicio lanza PermissionDenied.
                Acto.objects.create NO se ejecuta.
        """
        class UsuarioSinAtributos:
            pass
            
        usuario_vacio = UsuarioSinAtributos()
        
        data_validada = {
            'nombre': 'Acto Clandestino',
            'lugar': 'Catacumbas'
        }

        with self.assertRaises(PermissionDenied) as context:
            crear_acto_service(usuario_vacio, data_validada)

        self.assertEqual(
            str(context.exception), 
            "No tienes permisos para crear actos. Se requiere ser Administrador."
        )

        mock_acto_create.assert_not_called()



    @patch('api.services.Acto.objects.create')
    def test_usuario_con_es_admin_none_se_trata_como_no_admin(self, mock_acto_create):
        """
        Test: Usuario con esAdmin = None

        Given: Un usuario cuyo atributo 'esAdmin' es explícitamente None.
        When: Se llama al servicio crear_acto_service.
        Then: Python debe evaluar None como un valor falsy dentro de la condición 'if not'.
                El servicio debe lanzar PermissionDenied.
                No debe realizarse ninguna llamada al método create del ORM.
        """
        usuario_con_none = MagicMock()
        usuario_con_none.esAdmin = None
        
        data_validada = {
            'nombre': 'Acto de Prueba con None',
            'lugar': 'Sede Social'
        }

        with self.assertRaises(PermissionDenied) as context:
            crear_acto_service(usuario_con_none, data_validada)

        self.assertEqual(
            str(context.exception), 
            "No tienes permisos para crear actos. Se requiere ser Administrador."
        )

        mock_acto_create.assert_not_called()



    @patch('api.services.Acto.objects.create')
    def test_orm_lanza_excepcion_generica_se_propaga_hacia_arriba(self, mock_acto_create):
        """
        Test: Errores del ORM -> Acto.objects.create lanza excepción genérica

        Given: Un usuario administrador y datos válidos.
                El método create del ORM lanza una excepción genérica (ej. DatabaseError o Exception)
                debido a un fallo inesperado.
        When: Se llama al servicio crear_acto_service.
        Then: El servicio no debe capturar la excepción internamente. 
                La excepción debe propagarse hacia el llamador (la vista o el script),
                permitiendo que el error sea manejado por las capas superiores.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        
        data_validada = {'nombre': 'Acto con error de BD'}

        mensaje_error_bd = "Fallo crítico en la base de datos MariaDB"
        mock_acto_create.side_effect = Exception(mensaje_error_bd)

        with self.assertRaises(Exception) as context:
            crear_acto_service(usuario_admin, data_validada)

        self.assertEqual(str(context.exception), mensaje_error_bd)

        mock_acto_create.assert_called_once_with(**data_validada)



    @patch('api.services.Acto.objects.create')
    def test_orm_lanza_integrity_error_se_propaga_correctamente(self, mock_acto_create):
        """
        Test: Errores del ORM -> Acto.objects.create lanza IntegrityError

        Given: Un usuario administrador y datos que violan una restricción de base de datos
                (ej. un valor duplicado en un campo único o un nulo no permitido).
        When: Se llama al servicio crear_acto_service.
        Then: El servicio no debe capturar el IntegrityError internamente.
                La excepción debe propagarse hacia arriba para que la capa superior 
                (vista o middleware) gestione el error de integridad.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        
        data_validada = {'nombre': 'Acto Duplicado'}

        mensaje_error = "UNIQUE constraint failed: acto.nombre"
        mock_acto_create.side_effect = IntegrityError(mensaje_error)

        with self.assertRaises(IntegrityError) as context:
            crear_acto_service(usuario_admin, data_validada)

        self.assertIn(mensaje_error, str(context.exception))

        mock_acto_create.assert_called_once_with(**data_validada)



    @patch('api.services.Acto.objects.create')
    def test_data_validada_vacio_llama_a_create_sin_kwargs(self, mock_acto_create):
        """
        Test: Casos límite -> data_validada vacío

        Given: Un usuario administrador y un diccionario de datos totalmente vacío ({}).
        When: Se llama al servicio crear_acto_service.
        Then: El servicio debe llamar a Acto.objects.create() sin argumentos adicionales.
                Esto demuestra que el servicio no impone restricciones de estructura, 
                delegando esa responsabilidad al serializador y al esquema del modelo.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        
        data_vacia = {}

        mock_acto_default = MagicMock()
        mock_acto_create.return_value = mock_acto_default

        resultado = crear_acto_service(usuario_admin, data_vacia)

        mock_acto_create.assert_called_once_with()

        self.assertEqual(resultado, mock_acto_default)



    @patch('api.services.Acto.objects.create')
    def test_data_validada_con_claves_inesperadas_se_pasan_integramente_al_orm(self, mock_acto_create):
        """
        Test: Casos límite -> data_validada con claves inesperadas

        Given: Un usuario administrador y un diccionario de datos que contiene claves 
                arbitrarias o inesperadas (que no necesariamente existen en el modelo).
        When: Se llama al servicio crear_acto_service.
        Then: El servicio no debe filtrar ni transformar el diccionario.
                Debe invocar Acto.objects.create pasando exactamente los mismos datos 
                recibidos, permitiendo que sea el ORM quien valide la existencia de los campos.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True

        data_con_ruido = {
            'nombre': 'Acto con Metadatos',
            'campo_inexistente': 'valor_arbitrario',
            'metadata_extra': 12345
        }
        
        mock_acto_create.return_value = MagicMock()

        crear_acto_service(usuario_admin, data_con_ruido)

        mock_acto_create.assert_called_once_with(**data_con_ruido)



    @patch('api.services.Acto.objects.create')
    def test_orm_devuelve_none_el_servicio_retorna_none(self, mock_acto_create):
        """
        Test: Acto.objects.create devuelve None

        Given: Un usuario administrador y datos válidos.
                El método create del ORM está configurado para devolver None.
        When: Se llama al servicio crear_acto_service.
        Then: El servicio debe retornar exactamente el valor None recibido del ORM.
                Esto garantiza que el servicio no añade validaciones de salida innecesarias
                y confía plenamente en el resultado de la capa de persistencia.
        """
        usuario_admin = MagicMock()
        usuario_admin.esAdmin = True
        
        data_validada = {'nombre': 'Acto con retorno nulo'}

        mock_acto_create.return_value = None

        resultado = crear_acto_service(usuario_admin, data_validada)

        self.assertIsNone(resultado)

        mock_acto_create.assert_called_once_with(**data_validada)
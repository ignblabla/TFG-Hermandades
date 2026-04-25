from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from unittest.mock import patch

from api.servicios.acto.acto_service import crear_acto_service

from ....models import Acto, TipoActo, Hermano

User = get_user_model()


class CrearActoServiceTest(TestCase):

    def setUp(self):

        self.ahora = timezone.now()

        self.admin = Hermano.objects.create_user(
            dni="12345678A",
            username="12345678A",
            password="password",
            nombre="Admin",
            primer_apellido="Test",
            segundo_apellido="User",
            email="admin@example.com",
            telefono="600000000",
            estado_civil=Hermano.EstadoCivil.SOLTERO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=1,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1980-01-01",
            direccion="Calle Admin",
            codigo_postal="41001",
            localidad="Sevilla",
            provincia="Sevilla",
            comunidad_autonoma="Andalucía",
            esAdmin=True,
        )

        self.hermano = Hermano.objects.create_user(
            dni="87654321X",
            username="87654321X",
            password="password",
            nombre="Luis",
            primer_apellido="Ruiz",
            segundo_apellido="Díaz",
            email="luis@example.com",
            telefono="600654321",
            estado_civil=Hermano.EstadoCivil.CASADO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=1002,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1985-06-15",
            direccion="Calle Sierpes",
            codigo_postal="41004",
            localidad="Sevilla",
            provincia="Sevilla",
            comunidad_autonoma="Andalucía",
            esAdmin=False,
        )

        self.tipo_no_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.CONVIVENCIA,
            requiere_papeleta=False
        )

        self.tipo_con_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.ESTACION_PENITENCIA,
            requiere_papeleta=True
        )

        self.fecha_acto = self.ahora + timedelta(days=30)

        self.inicio_insignias = self.ahora + timedelta(days=1)
        self.fin_insignias = self.ahora + timedelta(days=3)

        self.inicio_cirios = self.fin_insignias + timedelta(hours=1)
        self.fin_cirios = self.inicio_cirios + timedelta(days=2)

        self.acto_no_papeleta_ok = {
            "nombre": "Convivencia febrero",
            "lugar": "Casa Hermandad",
            "descripcion": "Acto sin papeleta",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_no_papeleta,
            "modalidad": None,
            "inicio_solicitud": None,
            "fin_solicitud": None,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        }

        self.acto_tradicional_ok = {
            "nombre": "Estación de Penitencia 2026",
            "lugar": "Parroquia",
            "descripcion": "Acto con reparto tradicional",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.inicio_insignias,
            "fin_solicitud": self.fin_insignias,
            "inicio_solicitud_cirios": self.inicio_cirios,
            "fin_solicitud_cirios": self.fin_cirios,
        }

        self.acto_unificado_ok = {
            "nombre": "Cabildo General 2026",
            "lugar": "Salón de Actos",
            "descripcion": "Acto unificado",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.inicio_insignias,
            "fin_solicitud": self.fin_insignias,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        }



    def test_crear_acto_service_admin_success(self):
        """
        #     Test: Usuario administrador puede crear un acto

        #     Given: Un usuario con permisos de administrador (esAdmin = True)
        #            y una estructura de data_validada correcta.
        #     When: Se llama a la función crear_acto_service().
        #     Then: Se crea un registro de Acto en la base de datos
        #           y se devuelve la instancia recién creada.
        """
        usuario_ejecutor = self.admin
        data_validada = self.acto_tradicional_ok.copy()

        data_validada["nombre"] = "Acto Creado Por Admin"
        
        total_bd_antes = Acto.objects.count()

        nuevo_acto = crear_acto_service(
            usuario_solicitante=usuario_ejecutor, 
            data_validada=data_validada
        )

        self.assertIsInstance(
            nuevo_acto, 
            Acto, 
            "El servicio no devolvió una instancia del modelo Acto."
        )

        self.assertIsNotNone(
            nuevo_acto.id, 
            "El acto no tiene un ID asignado, parece que no se insertó en BD."
        )

        total_bd_despues = Acto.objects.count()
        self.assertEqual(
            total_bd_despues, 
            total_bd_antes + 1,
            "El conteo de actos no incrementó en la base de datos."
        )

        self.assertEqual(nuevo_acto.nombre, "Acto Creado Por Admin")
        self.assertEqual(nuevo_acto.tipo_acto, self.tipo_con_papeleta)



    def test_crear_acto_service_datos_correctos(self):
        """
        #     Test: Se pasan correctamente los datos al modelo

        #     Given: Una estructura data_validada con campos específicos (nombre, fecha, etc.).
        #     When: Se crea el acto llamando a crear_acto_service().
        #     Then: Los campos del objeto devuelto coinciden exactamente con los 
        #           datos enviados en el diccionario original.
        """
        usuario_ejecutor = self.admin
        data_validada = self.acto_tradicional_ok.copy()

        data_validada["nombre"] = "Acto Mapeo Exacto"
        data_validada["lugar"] = "Patio de los Naranjos"
        data_validada["descripcion"] = "Test para comprobar que no se pierde información."

        nuevo_acto = crear_acto_service(
            usuario_solicitante=usuario_ejecutor, 
            data_validada=data_validada
        )

        self.assertEqual(nuevo_acto.nombre, data_validada["nombre"])
        self.assertEqual(nuevo_acto.lugar, data_validada["lugar"])
        self.assertEqual(nuevo_acto.descripcion, data_validada["descripcion"])
        self.assertEqual(nuevo_acto.fecha, data_validada["fecha"])
        self.assertEqual(nuevo_acto.tipo_acto, data_validada["tipo_acto"])
        self.assertEqual(nuevo_acto.modalidad, data_validada["modalidad"])
        self.assertEqual(nuevo_acto.inicio_solicitud, data_validada["inicio_solicitud"])
        self.assertEqual(nuevo_acto.fin_solicitud, data_validada["fin_solicitud"])
        self.assertEqual(nuevo_acto.inicio_solicitud_cirios, data_validada["inicio_solicitud_cirios"])
        self.assertEqual(nuevo_acto.fin_solicitud_cirios, data_validada["fin_solicitud_cirios"])



    def test_crear_acto_service_devuelve_instancia_exacta(self):
        """
        #     Test: Devuelve exactamente la instancia creada

        #     Given: Una creación correcta de un acto con datos validados.
        #     When: Se ejecuta el servicio crear_acto_service().
        #     Then: El objeto retornado tiene una pk (primary key) no nula,
        #           y coincide exactamente con el registro consultado en la BD.
        """
        usuario_ejecutor = self.admin
        data_validada = self.acto_unificado_ok.copy()
        data_validada["nombre"] = "Acto PK y Mapeo BD"

        nuevo_acto = crear_acto_service(
            usuario_solicitante=usuario_ejecutor, 
            data_validada=data_validada
        )

        self.assertIsNotNone(
            nuevo_acto.pk, 
            "El objeto retornado no tiene 'pk' nulo, por lo que no se persistió correctamente."
        )

        acto_en_bd = Acto.objects.get(pk=nuevo_acto.pk)

        self.assertEqual(
            nuevo_acto, 
            acto_en_bd,
            "La instancia devuelta por el servicio no es equivalente al registro en BD."
        )

        self.assertEqual(
            nuevo_acto.nombre, 
            acto_en_bd.nombre,
            "Los datos de la instancia devuelta no coinciden con los leídos de la BD."
        )



    def test_crear_acto_service_permite_estructuras_validas(self):
        """
        #     Test: Permite cualquier estructura válida de datos

        #     Given: Diferentes combinaciones válidas de data_validada (Tradicional vs Unificado).
        #     When: Se llama al servicio crear_acto_service().
        #     Then: El servicio no filtra ni modifica los datos, persistiendo 
        #           exactamente lo que recibe en el diccionario.
        """
        casos = [
            ("Tradicional", self.acto_tradicional_ok),
            ("Unificado", self.acto_unificado_ok)
        ]

        for nombre_caso, data in casos:
            with self.subTest(caso=nombre_caso):
                data_validada = data.copy()
                data_validada["nombre"] = f"Test Estructura {nombre_caso}"

                nuevo_acto = crear_acto_service(
                    usuario_solicitante=self.admin,
                    data_validada=data_validada
                )

                self.assertEqual(
                    nuevo_acto.modalidad, 
                    data_validada["modalidad"],
                    f"La modalidad se alteró en el caso {nombre_caso}"
                )

                self.assertEqual(
                    nuevo_acto.inicio_solicitud_cirios, 
                    data_validada["inicio_solicitud_cirios"],
                    f"El campo inicio_solicitud_cirios se modificó en el caso {nombre_caso}"
                )

                self.assertEqual(nuevo_acto.nombre, data_validada["nombre"])



    def test_crear_acto_service_llama_una_vez_a_create(self):
        """
        #     Test: Llama una sola vez a Acto.objects.create

        #     Given: Un usuario administrador y un conjunto de datos válidos.
        #     When: Se invoca el servicio crear_acto_service().
        #     Then: Se ejecuta exactamente una vez el método de creación del modelo,
        #           garantizando eficiencia y evitando duplicados.
        """
        usuario_ejecutor = self.admin
        data_validada = self.acto_unificado_ok.copy()

        with patch("api.models.Acto.objects.create") as mock_create:

            mock_create.return_value = Acto(id=999, **data_validada)

            crear_acto_service(
                usuario_solicitante=usuario_ejecutor, 
                data_validada=data_validada
            )

            self.assertEqual(
                mock_create.call_count, 
                1, 
                f"Se esperaba 1 llamada a Acto.objects.create, pero se hicieron {mock_create.call_count}."
            )

            mock_create.assert_called_once_with(**data_validada)



    def test_crear_acto_service_no_admin_lanza_error(self):
        """
        #     Test: Usuario no administrador → error de permisos

        #     Given: Un usuario con el atributo esAdmin = False (self.hermano).
        #     When: Se intenta llamar a la función crear_acto_service().
        #     Then: El sistema debe elevar una excepción PermissionDenied, 
        #           impidiendo la creación del registro en la base de datos.
        """
        usuario_no_admin = self.hermano
        data_validada = self.acto_no_papeleta_ok.copy()
        
        total_antes = Acto.objects.count()

        with self.assertRaises(PermissionDenied) as cm:
            crear_acto_service(
                usuario_solicitante=usuario_no_admin, 
                data_validada=data_validada
            )

        self.assertEqual(
            str(cm.exception), 
            "No tienes permisos para crear actos. Se requiere ser Administrador."
        )

        self.assertEqual(
            Acto.objects.count(), 
            total_antes, 
            "Se creó un acto en BD a pesar de que el usuario no era administrador."
        )



    def test_crear_acto_service_usuario_sin_atributo_esadmin(self):
        """
        #     Test: Usuario sin atributo esAdmin

        #     Given: Un objeto de usuario (o cualquier objeto) que no posee 
        #           el atributo 'esAdmin' definido.
        #     When: Se intenta llamar a la función crear_acto_service().
        #     Then: El sistema lanza una excepción PermissionDenied gracias al uso 
        #           de getattr con valor por defecto False, bloqueando la creación.
        """
        class UsuarioAnonimo:
            pass
        
        usuario_incompleto = UsuarioAnonimo()
        data_validada = self.acto_no_papeleta_ok.copy()
        
        total_antes = Acto.objects.count()

        with self.assertRaises(PermissionDenied) as cm:
            crear_acto_service(
                usuario_solicitante=usuario_incompleto, 
                data_validada=data_validada
            )

        self.assertEqual(
            str(cm.exception), 
            "No tienes permisos para crear actos. Se requiere ser Administrador."
        )

        self.assertEqual(
            Acto.objects.count(), 
            total_antes, 
            "Se creó un acto con un usuario que no poseía el atributo de permisos."
        )



    def test_crear_acto_service_usuario_nulo(self):
        """
        #     Test: Usuario solicitante es None

        #     Given: Un valor de usuario_solicitante igual a None.
        #     When: Se ejecuta la función crear_acto_service().
        #     Then: El sistema lanza una excepción PermissionDenied, ya que getattr 
        #           no encontrará el atributo 'esAdmin' en None y usará el valor 
        #           por defecto False.
        """
        usuario_nulo = None
        data_validada = self.acto_no_papeleta_ok.copy()
        
        total_antes = Acto.objects.count()

        with self.assertRaises(PermissionDenied) as cm:
            crear_acto_service(
                usuario_solicitante=usuario_nulo, 
                data_validada=data_validada
            )
            
        self.assertEqual(
            str(cm.exception), 
            "No tienes permisos para crear actos. Se requiere ser Administrador."
        )

        self.assertEqual(
            Acto.objects.count(), 
            total_antes, 
            "Se creó un acto a pesar de que el usuario solicitante era None."
        )



    def test_crear_acto_service_no_crea_si_falla_permiso(self):
        """
        #     Test: No debe crear el acto si falla el permiso

        #     Given: Un usuario sin permisos de administrador (esAdmin = False).
        #     When: Se intenta llamar a crear_acto_service().
        #     Then: Se lanza la excepción PermissionDenied y se garantiza que 
        #           el método Acto.objects.create NUNCA llega a ejecutarse.
        """
        usuario_no_admin = self.hermano
        data_validada = self.acto_no_papeleta_ok.copy()

        with patch("api.models.Acto.objects.create") as mock_create:

            with self.assertRaises(PermissionDenied):
                crear_acto_service(
                    usuario_solicitante=usuario_no_admin, 
                    data_validada=data_validada
                )

            mock_create.assert_not_called()

            self.assertEqual(
                Acto.objects.filter(nombre=data_validada["nombre"]).count(), 
                0, 
                "Se encontró un registro en la base de datos que no debería existir."
            )



    def test_crear_acto_service_no_modifica_data_validada(self):
        """
        #     Test: No debe modificar data_validada

        #     Given: Un diccionario original con los datos validados del acto.
        #     When: Se llama al servicio crear_acto_service().
        #     Then: El diccionario original permanece intacto tras la ejecución,
        #           garantizando que el servicio no realiza mutaciones por referencia.
        """
        usuario_ejecutor = self.admin
        data_validada = self.acto_tradicional_ok.copy()

        snapshot_original = data_validada.copy()

        crear_acto_service(
            usuario_solicitante=usuario_ejecutor, 
            data_validada=data_validada
        )

        self.assertDictEqual(
            data_validada, 
            snapshot_original,
            "El servicio modificó el diccionario 'data_validada' original durante la creación."
        )
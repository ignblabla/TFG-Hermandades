from django.http import QueryDict
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.exceptions import ValidationError as DRFValidationError
from unittest.mock import patch
import datetime
from django.db import transaction
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError

from api.servicios.acto.acto_service import _normalizar_payload_acto, actualizar_acto_service

from ....models import Acto, Hermano, TipoActo, TipoPuesto, Puesto


class ActualizarActoServiceTest(TestCase):

    def setUp(self):
        # ---------------------------------------------------------------------
        # FECHA BASE
        # ---------------------------------------------------------------------
        self.ahora = timezone.now()

        # ---------------------------------------------------------------------
        # USUARIO ADMIN
        # ---------------------------------------------------------------------
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

        # ---------------------------------------------------------------------
        # USUARIO NO ADMIN
        # ---------------------------------------------------------------------
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

        # ---------------------------------------------------------------------
        # TIPOS DE ACTO
        # ---------------------------------------------------------------------
        self.tipo_no_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.CONVIVENCIA,
            requiere_papeleta=False
        )

        self.tipo_con_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.ESTACION_PENITENCIA,
            requiere_papeleta=True
        )

        self.tipo_con_papeleta_alt = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.CABILDO_GENERAL,
            requiere_papeleta=True
        )

        # ---------------------------------------------------------------------
        # FECHAS COHERENTES (ACTO FUTURO + PLAZOS FUTUROS)
        # ---------------------------------------------------------------------
        self.fecha_acto = self.ahora + timedelta(days=30)

        self.inicio_insignias = self.ahora + timedelta(days=1)
        self.fin_insignias = self.ahora + timedelta(days=3)

        self.inicio_cirios = self.fin_insignias + timedelta(hours=1)
        self.fin_cirios = self.inicio_cirios + timedelta(days=2)

        # ---------------------------------------------------------------------
        # PAYLOADS BASE (dicts) — útiles para tests, pero NO bastan para el service
        # ---------------------------------------------------------------------
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

        self.acto_con_plazo_iniciado = Acto.objects.create(
            nombre="Acto con plazo iniciado",
            lugar="Capilla",
            descripcion="Test cambio fecha bloqueado",
            fecha=self.ahora + timedelta(days=10),
            tipo_acto=self.tipo_con_papeleta,
            modalidad=Acto.ModalidadReparto.UNIFICADO,
            inicio_solicitud=self.ahora - timedelta(hours=1),
            fin_solicitud=self.ahora + timedelta(days=2),
            inicio_solicitud_cirios=None,
            fin_solicitud_cirios=None,
        )

        self.acto_unificado_ok = {
            "nombre": "Cabildo General 2026",
            "lugar": "Salón de actos",
            "descripcion": "Acto unificado",
            "fecha": self.fecha_acto,
            "tipo_acto": self.tipo_con_papeleta,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.inicio_insignias,
            "fin_solicitud": self.fin_insignias,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        }

        # ---------------------------------------------------------------------
        # ACTOS PERSISTIDOS EN BD (lo que el service necesita)
        # ---------------------------------------------------------------------
        self.acto_db_no_papeleta = Acto.objects.create(**self.acto_no_papeleta_ok)

        self.acto_db_tradicional = Acto.objects.create(**self.acto_tradicional_ok)

        self.acto_db_unificado = Acto.objects.create(**self.acto_unificado_ok)

        # ---------------------------------------------------------------------
        # ACTO EXTRA PARA TESTEAR UNICIDAD nombre+fecha (mismo día)
        # (sirve para probar el check de "Ya existe otro acto llamado ... en esa fecha")
        # ---------------------------------------------------------------------
        self.acto_db_otro_mismo_dia = Acto.objects.create(
            nombre="Acto existente mismo día",
            lugar="Capilla",
            descripcion="Para test de unicidad",
            fecha=self.fecha_acto.replace(hour=10, minute=0, second=0, microsecond=0),
            tipo_acto=self.tipo_con_papeleta,
            modalidad=Acto.ModalidadReparto.UNIFICADO,
            inicio_solicitud=self.inicio_insignias,
            fin_solicitud=self.fin_insignias,
            inicio_solicitud_cirios=None,
            fin_solicitud_cirios=None,
        )

        # ---------------------------------------------------------------------
        # ACTO PARA TESTEAR BLOQUEO DE CAMBIO DE FECHA (plazo YA EMPEZADO)
        # _validar_cambio_fecha mira el acto actual en BD: now >= acto.inicio_solicitud
        # ---------------------------------------------------------------------
        self.acto_db_plazo_empezado = Acto.objects.create(
            nombre="Acto con plazo ya empezado",
            lugar="Capilla",
            descripcion="Para test de bloqueo de cambio de fecha",
            fecha=self.ahora + timedelta(days=10),
            tipo_acto=self.tipo_con_papeleta,
            modalidad=Acto.ModalidadReparto.UNIFICADO,
            inicio_solicitud=self.ahora - timedelta(days=1),
            fin_solicitud=self.ahora + timedelta(days=2),
            inicio_solicitud_cirios=None,
            fin_solicitud_cirios=None,
        )

        # ---------------------------------------------------------------------
        # TIPOS DE PUESTO + PUESTO (para bloquear cambio de tipo_acto si hay puestos)
        # ---------------------------------------------------------------------
        self.tipo_puesto_generico = TipoPuesto.objects.create(
            nombre_tipo="Cirio",
            solo_junta_gobierno=False,
            es_insignia=False,
        )

        self.puesto_en_acto_tradicional = Puesto.objects.create(
            nombre="Cirio tramo 1",
            numero_maximo_asignaciones=10,
            disponible=True,
            acto=self.acto_db_tradicional,
            tipo_puesto=self.tipo_puesto_generico,
        )

        # ---------------------------------------------------------------------
        # HELPER PAYLOADS para tests frecuentes del service (opcional pero práctico)
        # ---------------------------------------------------------------------
        self.payload_cambiar_tipo_acto_con_puestos = {
            "tipo_acto_id": self.tipo_con_papeleta_alt.id
        }

        self.payload_cambiar_fecha = {
            "fecha": self.fecha_acto + timedelta(days=1)
        }

        self.payload_cambiar_a_no_papeleta = {
            "tipo_acto_id": self.tipo_no_papeleta.id,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.inicio_insignias,
            "fin_solicitud": self.fin_insignias,
            "inicio_solicitud_cirios": self.inicio_cirios,
            "fin_solicitud_cirios": self.fin_cirios,
        }

        self.payload_unificado_con_cirios = {
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud_cirios": self.inicio_cirios,
            "fin_solicitud_cirios": self.fin_cirios,
        }



    def test_admin_actualiza_nombre_acto_ok(self):
        """
        Test: Administrador actualiza nombre del acto correctamente

        Given: Un usuario administrador y un acto previamente creado en la base de datos.
        When: Se invoca el servicio de actualización de acto enviando un nuevo nombre en el payload.
        Then: El sistema debe permitir la operación y el nombre del acto debe quedar actualizado en la base de datos.
        """
        acto_a_actualizar = self.acto_db_unificado
        nuevo_nombre = "Cabildo General 2026 - Nombre Modificado"

        data_actualizar = self.acto_unificado_ok.copy()
        data_actualizar["nombre"] = nuevo_nombre

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_actualizar.id, 
            data_validada=data_actualizar
        )

        acto_a_actualizar.refresh_from_db()

        self.assertEqual(acto_a_actualizar.nombre, nuevo_nombre)
        self.assertEqual(acto_actualizado.nombre, nuevo_nombre)



    def test_admin_actualiza_descripcion_acto_ok(self):
        """
        Test: Administrador actualiza descripción del acto correctamente

        Given: Un usuario administrador y un acto previamente creado en la base de datos.
        When: Se invoca el servicio de actualización de acto enviando una nueva descripción en el payload.
        Then: El sistema debe permitir la operación y la descripción del acto debe quedar actualizada en la base de datos.
        """
        acto_a_actualizar = self.acto_db_tradicional
        nueva_descripcion = "Descripción completamente nueva y detallada para el test."

        data_actualizar = self.acto_tradicional_ok.copy()
        data_actualizar["descripcion"] = nueva_descripcion

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_actualizar.id, 
            data_validada=data_actualizar
        )

        acto_a_actualizar.refresh_from_db()

        self.assertEqual(acto_a_actualizar.descripcion, nueva_descripcion)
        self.assertEqual(acto_actualizado.descripcion, nueva_descripcion)



    def test_admin_actualiza_lugar_acto_ok(self):
        """
        Test: Administrador actualiza lugar del acto correctamente

        Given: Un usuario administrador y un acto previamente creado en la base de datos.
        When: Se invoca el servicio de actualización de acto enviando un nuevo lugar en el payload.
        Then: El sistema debe permitir la operación y el lugar del acto debe quedar actualizado en la base de datos.
        """
        acto_a_actualizar = self.acto_db_no_papeleta
        nuevo_lugar = "Catedral de Sevilla"

        data_actualizar = self.acto_no_papeleta_ok.copy()
        data_actualizar["lugar"] = nuevo_lugar

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_actualizar.id, 
            data_validada=data_actualizar
        )

        acto_a_actualizar.refresh_from_db()

        self.assertEqual(acto_a_actualizar.lugar, nuevo_lugar)
        self.assertEqual(acto_actualizado.lugar, nuevo_lugar)



    def test_admin_actualiza_varios_campos_simultaneamente_ok(self):
        """
        Test: Administrador actualiza varios campos válidos simultáneamente

        Given: Un usuario administrador y un acto unificado en la base de datos.
        When: Se invoca el servicio enviando un nuevo nombre, lugar y descripción en el mismo payload.
        Then: El sistema debe actualizar todos los campos proporcionados correctamente en una sola operación.
        """
        acto_a_actualizar = self.acto_db_unificado
        
        nuevos_datos = {
            "nombre": "Nombre Multicampo",
            "lugar": "Nuevo Lugar Multicampo",
            "descripcion": "Nueva Descripción Multicampo"
        }

        data_actualizar = self.acto_unificado_ok.copy()
        data_actualizar.update(nuevos_datos)

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_actualizar.id, 
            data_validada=data_actualizar
        )

        acto_a_actualizar.refresh_from_db()

        self.assertEqual(acto_a_actualizar.nombre, nuevos_datos["nombre"])
        self.assertEqual(acto_a_actualizar.lugar, nuevos_datos["lugar"])
        self.assertEqual(acto_a_actualizar.descripcion, nuevos_datos["descripcion"])

        self.assertEqual(acto_a_actualizar.fecha, self.acto_unificado_ok["fecha"])



    def test_usuario_no_admin_intenta_editar_acto_fail(self):
        """
        Test: Usuario no administrador intenta editar un acto → PermissionDenied

        Given: Un usuario sin privilegios de administrador y un acto existente.
        When: El usuario intenta invoca el servicio de actualización de acto.
        Then: El sistema debe lanzar una excepción PermissionDenied y no realizar ningún cambio.
        """
        acto_a_actualizar = self.acto_db_unificado
        nombre_original = acto_a_actualizar.nombre
        
        data_actualizar = self.acto_unificado_ok.copy()
        data_actualizar["nombre"] = "Intento de sabotaje"

        with self.assertRaises(PermissionDenied) as cm:
            actualizar_acto_service(
                usuario_solicitante=self.hermano,
                acto_id=acto_a_actualizar.id,
                data_validada=data_actualizar
            )

        self.assertEqual(str(cm.exception), "No tienes permisos para editar actos. Se requiere ser Administrador.")

        acto_a_actualizar.refresh_from_db()
        self.assertEqual(acto_a_actualizar.nombre, nombre_original)



    def test_usuario_sin_atributo_es_admin_intenta_editar_fail(self):
        """
        Test: Usuario autenticado sin atributo esAdmin intenta editar → PermissionDenied

        Given: Un usuario (hermano) que tiene esAdmin=False.
        When: Intenta ejecutar el servicio de actualización sobre un acto existente.
        Then: El servicio debe lanzar django.core.exceptions.PermissionDenied y los datos en BD no deben cambiar.
        """
        self.hermano.esAdmin = False
        self.hermano.save()

        acto_a_actualizar = self.acto_db_unificado
        nombre_original = acto_a_actualizar.nombre
        
        data_payload = {"nombre": "Intento de cambio sin ser admin"}

        with self.assertRaises(PermissionDenied) as context:
            actualizar_acto_service(
                usuario_solicitante=self.hermano,
                acto_id=acto_a_actualizar.id,
                data_validada=data_payload
            )

        self.assertEqual(
            str(context.exception), 
            "No tienes permisos para editar actos. Se requiere ser Administrador."
        )

        acto_a_actualizar.refresh_from_db()
        self.assertEqual(acto_a_actualizar.nombre, nombre_original)



    def test_usuario_anonimo_intenta_editar_acto_fail(self):
        """
        Test: Usuario anónimo intenta editar → PermissionDenied

        Given: Un objeto de usuario anónimo (sin autenticar).
        When: Se invoca el servicio de actualización de acto.
        Then: El sistema debe lanzar PermissionDenied debido a la falta del atributo esAdmin.
        """
        user_anon = AnonymousUser()
        acto_id = self.acto_db_unificado.id
        data_payload = {"nombre": "Nombre modificado por anónimo"}

        with self.assertRaises(PermissionDenied) as context:
            actualizar_acto_service(
                usuario_solicitante=user_anon,
                acto_id=acto_id,
                data_validada=data_payload
            )

        self.assertEqual(
            str(context.exception), 
            "No tienes permisos para editar actos. Se requiere ser Administrador."
        )



    def test_usuario_sin_propiedad_es_admin_intenta_editar_fail(self):
        """
        Test: Usuario autenticado sin atributo esAdmin intenta editar → PermissionDenied

        Given: Un usuario (u objeto) que carece por completo de la propiedad 'esAdmin'.
        When: Se invoca el servicio de actualización de acto.
        Then: El sistema debe lanzar PermissionDenied al fallar la comprobación de privilegios.
        """
        class UsuarioSinAtributos:
            pass

        usuario_incompleto = UsuarioSinAtributos()
        acto_a_actualizar = self.acto_db_unificado
        
        data_payload = {"nombre": "Intento de edición"}

        with self.assertRaises(PermissionDenied) as context:
            actualizar_acto_service(
                usuario_solicitante=usuario_incompleto,
                acto_id=acto_a_actualizar.id,
                data_validada=data_payload
            )

        self.assertEqual(
            str(context.exception), 
            "No tienes permisos para editar actos. Se requiere ser Administrador."
        )



    def test_actualizar_acto_existente_por_id_valido_ok(self):
        """
        Test: Actualizar un acto existente por ID válido

        Given: Un administrador y un acto guardado en la base de datos con un ID conocido.
        When: Se invoca al servicio pasando ese ID exacto y un payload con cambios.
        Then: El servicio debe encontrar el registro, actualizarlo y devolver la instancia del acto.
        """
        acto_db = self.acto_db_no_papeleta
        id_valido = acto_db.id
        nuevo_nombre = "Nombre Localizado por ID"

        data_actualizar = self.acto_no_papeleta_ok.copy()
        data_actualizar["nombre"] = nuevo_nombre

        acto_retornado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=id_valido,
            data_validada=data_actualizar
        )

        acto_db.refresh_from_db()
        self.assertEqual(acto_db.id, id_valido)
        self.assertEqual(acto_db.nombre, nuevo_nombre)
        self.assertEqual(acto_retornado.nombre, nuevo_nombre)
        self.assertEqual(acto_retornado.id, id_valido)



    def test_actualizar_acto_id_inexistente_fail(self):
        """
        Test: Intentar actualizar un acto con ID inexistente → ValidationError

        Given: Un ID que no corresponde a ningún acto en la base de datos (ej: 9999).
        When: Se invoca el servicio de actualización.
        Then: El sistema debe lanzar una ValidationError indicando que el acto no existe.
        """
        id_inexistente = 9999
        data_payload = self.acto_unificado_ok.copy()

        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=id_inexistente,
                data_validada=data_payload
            )

        self.assertIn('detail', context.exception.message_dict)
        self.assertEqual(
            context.exception.message_dict['detail'][0], 
            "El acto solicitado no existe."
        )



    def test_actualizar_acto_id_none_fail(self):
        """
        Test: Intentar actualizar con acto_id=None → ValidationError

        Given: Un administrador que intenta actualizar un acto pasando None como ID.
        When: Se invoca el servicio de actualización.
        Then: El sistema debe lanzar una ValidationError indicando que el acto no existe.
        """
        id_nulo = None
        data_payload = self.acto_unificado_ok.copy()

        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=id_nulo,
                data_validada=data_payload
            )

        self.assertIn('detail', context.exception.message_dict)
        self.assertEqual(
            context.exception.message_dict['detail'][0], 
            "El acto solicitado no existe."
        )



    def test_payload_formato_dict_valido_ok(self):
        """
        Test: Payload en formato dict válido

        Given: Un administrador y un payload en formato de diccionario estándar.
        When: Se invoca el servicio de actualización.
        Then: El sistema debe procesar el diccionario, normalizarlo y actualizar el acto correctamente.
        """
        acto_a_actualizar = self.acto_db_tradicional

        data_payload = {
            "nombre": "Nombre vía Diccionario",
            "lugar": "Lugar vía Diccionario"
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_actualizar.id,
            data_validada=data_payload
        )

        acto_a_actualizar.refresh_from_db()
        self.assertEqual(acto_a_actualizar.nombre, "Nombre vía Diccionario")
        self.assertEqual(acto_a_actualizar.lugar, "Lugar vía Diccionario")
        self.assertIsInstance(acto_actualizado, Acto)



    def test_payload_querydict_un_valor_por_campo_ok(self):
        """
        Test: Payload QueryDict con un solo valor por campo

        Given: Un administrador y los datos de actualización dentro de un QueryDict de Django.
        When: Cada clave del QueryDict tiene un único valor asociado.
        Then: El sistema debe normalizar el QueryDict a un diccionario estándar y actualizar el acto.
        """
        acto_a_actualizar = self.acto_db_unificado
        nuevo_lugar = "Sede Social - QueryDict Test"

        query_dict = QueryDict(mutable=True)
        query_dict.update({
            "lugar": nuevo_lugar,
            "descripcion": "Actualizado mediante QueryDict"
        })

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_actualizar.id,
            data_validada=query_dict
        )

        acto_a_actualizar.refresh_from_db()
        self.assertEqual(acto_a_actualizar.lugar, nuevo_lugar)
        self.assertEqual(acto_actualizado.lugar, nuevo_lugar)



    def test_payload_formato_invalido_fail(self):
        """
        Test: Payload no es dict ni QueryDict → ValidationError

        Given: Un administrador que intenta actualizar un acto enviando un string en lugar de un objeto de datos.
        When: El servicio recibe un formato de datos no soportado (ej: cadena de texto).
        Then: El sistema debe lanzar una ValidationError con el mensaje de formato inválido.
        """
        acto_id = self.acto_db_unificado.id
        payload_invalido = "nombre: Nuevo Nombre, lugar: Nuevo Lugar"

        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_id,
                data_validada=payload_invalido
            )

        self.assertIn('non_field_errors', context.exception.message_dict)
        self.assertEqual(
            context.exception.message_dict['non_field_errors'][0], 
            "Formato de datos inválido para actualizar el acto."
        )



    def test_payload_campo_con_lista_fail(self):
        """
        Test: Campo en payload con lista (["valor1", "valor2"]) → ValidationError

        Given: Un administrador que envía un payload donde uno de los campos (ej: nombre) es una lista.
        When: Se invoca el servicio de actualización.
        Then: El sistema debe detectar que no se permiten múltiples valores y lanzar ValidationError.
        """
        acto_id = self.acto_db_unificado.id

        payload_con_lista = {
            "nombre": ["Acto A", "Acto B"],
            "lugar": "Sede Social"
        }

        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_id,
                data_validada=payload_con_lista
            )

        self.assertIn('nombre', context.exception.message_dict)
        self.assertEqual(
            context.exception.message_dict['nombre'][0], 
            "No se permiten múltiples valores para este campo."
        )



    def test_payload_querydict_con_multiples_valores_fail(self):
        """
        Test: Campo en QueryDict con múltiples valores → ValidationError

        Given: Un administrador que envía un QueryDict donde una clave tiene más de un valor asignado.
        When: Se invoca el servicio de actualización.
        Then: El sistema debe detectar la duplicidad mediante getlist() y lanzar ValidationError.
        """
        acto_id = self.acto_db_unificado.id

        query_dict = QueryDict(mutable=True)
        query_dict.setlist('lugar', ['Sede Principal', 'Iglesia Mayor'])
        query_dict.update({'nombre': 'Cambio de Nombre'})

        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_id,
                data_validada=query_dict
            )

        self.assertIn('lugar', context.exception.message_dict)
        self.assertEqual(
            context.exception.message_dict['lugar'][0], 
            "No se permiten múltiples valores para este campo."
        )



    def test_payload_solo_campos_permitidos_ok(self):
        """
        Test: Payload contiene solo campos permitidos

        Given: Un administrador y un payload que contiene un subconjunto de campos 
            que están en la lista blanca (ej: nombre, lugar, descripcion).
        When: Se invoca el servicio de actualización.
        Then: El sistema debe validar que no hay claves desconocidas y proceder 
            con la actualización de esos campos específicos.
        """
        acto_a_actualizar = self.acto_db_no_papeleta

        data_payload = {
            "nombre": "Nombre Permitido",
            "lugar": "Lugar Permitido",
            "descripcion": "Descripción Permitida"
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_actualizar.id,
            data_validada=data_payload
        )

        acto_a_actualizar.refresh_from_db()
        self.assertEqual(acto_a_actualizar.nombre, "Nombre Permitido")
        self.assertEqual(acto_a_actualizar.lugar, "Lugar Permitido")
        self.assertEqual(acto_a_actualizar.descripcion, "Descripción Permitida")

        self.assertIsInstance(acto_actualizado, Acto)



    def test_payload_actualiza_unicamente_descripcion_ok(self):
        """
        Test: Payload actualiza únicamente descripción

        Given: Un administrador y un acto existente con datos completos.
        When: Se envía un payload que contiene exclusivamente la clave 'descripcion'.
        Then: El sistema debe actualizar solo la descripción y mantener el resto de campos (nombre, fecha, lugar) sin cambios.
        """
        acto_a_actualizar = self.acto_db_unificado
        nombre_previo = acto_a_actualizar.nombre
        fecha_previa = acto_a_actualizar.fecha
        nueva_desc = "Nueva descripción aislada."

        data_payload = {
            "descripcion": nueva_desc
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_actualizar.id,
            data_validada=data_payload
        )

        acto_a_actualizar.refresh_from_db()

        self.assertEqual(acto_a_actualizar.descripcion, nueva_desc)

        self.assertEqual(acto_a_actualizar.nombre, nombre_previo)
        self.assertEqual(acto_a_actualizar.fecha, fecha_previa)
        
        self.assertIsInstance(acto_actualizado, Acto)



    def test_payload_actualiza_unicamente_lugar_ok(self):
        """
        Test: Payload actualiza únicamente lugar

        Given: Un administrador y un acto existente con datos completos.
        When: Se envía un payload que contiene exclusivamente la clave 'lugar'.
        Then: El sistema debe actualizar solo el lugar y mantener el resto de campos (nombre, fecha, descripción) sin cambios.
        """
        acto_a_actualizar = self.acto_db_tradicional
        nombre_previo = acto_a_actualizar.nombre
        fecha_previa = acto_a_actualizar.fecha
        nuevo_lugar = "Nueva Ubicación para el Test"

        data_payload = {
            "lugar": nuevo_lugar
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_actualizar.id, 
            data_validada=data_payload
        )

        acto_a_actualizar.refresh_from_db()

        self.assertEqual(acto_a_actualizar.lugar, nuevo_lugar)

        self.assertEqual(acto_a_actualizar.nombre, nombre_previo)
        self.assertEqual(acto_a_actualizar.fecha, fecha_previa)

        self.assertIsInstance(acto_actualizado, Acto)



    def test_payload_contiene_campo_no_permitido_created_at_fail(self):
        """
        Test: Payload contiene campo no permitido (created_at) → ValidationError

        Given: Un administrador que intenta enviar el campo 'created_at' en el payload.
        When: Se invoca el servicio de actualización.
        Then: El sistema debe detectar que 'created_at' no está en la lista blanca y lanzar ValidationError.
        """
        acto_id = self.acto_db_unificado.id

        payload_con_intruso = {
            "nombre": "Nombre Válido",
            "created_at": "2020-01-01T00:00:00Z"
        }

        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_id,
                data_validada=payload_con_intruso
            )

        self.assertIn('non_field_errors', context.exception.message_dict)
        mensaje_error = context.exception.message_dict['non_field_errors'][0]
        
        self.assertIn("contiene campos no permitidos", mensaje_error)
        self.assertIn("created_at", mensaje_error)



    def test_payload_contiene_campo_no_permitido_id_fail(self):
        """
        Test: Payload contiene campo no permitido (id) → ValidationError

        Given: Un administrador que intenta enviar el campo 'id' en el payload de actualización.
        When: Se invoca el servicio de actualización.
        Then: El sistema debe detectar que 'id' no está en la lista blanca y lanzar ValidationError.
        """
        acto_id_original = self.acto_db_unificado.id

        payload_con_id = {
            "nombre": "Cambio de nombre con ID intruso",
            "id": 9999  
        }

        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_id_original,
                data_validada=payload_con_id
            )

        self.assertIn('non_field_errors', context.exception.message_dict)
        mensaje_error = context.exception.message_dict['non_field_errors'][0]

        self.assertIn("contiene campos no permitidos", mensaje_error)
        self.assertIn("id", mensaje_error)

        self.acto_db_unificado.refresh_from_db()
        self.assertEqual(self.acto_db_unificado.id, acto_id_original)



    def test_payload_contiene_campo_no_permitido_autor_fail(self):
        """
        Test: Payload contiene campo no permitido (autor) → ValidationError

        Given: Un administrador que intenta enviar el campo 'autor' en el payload.
        When: Se invoca el servicio de actualización de un acto.
        Then: El sistema debe detectar que 'autor' no es un campo editable para Actos y lanzar ValidationError.
        """
        acto_id = self.acto_db_unificado.id

        payload_con_autor = {
            "nombre": "Nombre Válido",
            "autor": self.admin.id  
        }

        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_id,
                data_validada=payload_con_autor
            )

        self.assertIn('non_field_errors', context.exception.message_dict)
        mensaje_error = context.exception.message_dict['non_field_errors'][0]

        self.assertIn("contiene campos no permitidos", mensaje_error)
        self.assertIn("autor", mensaje_error)



    def test_payload_contiene_multiples_campos_desconocidos_fail(self):
        """
        Test: Payload contiene múltiples campos desconocidos

        Given: Un administrador que envía un payload con varios campos que no están en la lista blanca 
            (ej: 'autor', 'is_active', 'campo_inventado').
        When: Se invoca el servicio de actualización.
        Then: El sistema debe lanzar una ValidationError que liste todos los campos no permitidos en el mensaje.
        """
        acto_id = self.acto_db_unificado.id

        payload_sucio = {
            "nombre": "Nuevo Nombre",
            "autor": self.admin.id,
            "is_active": True,
            "campo_inventado": "valor"
        }

        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_id,
                data_validada=payload_sucio
            )

        self.assertIn('non_field_errors', context.exception.message_dict)
        mensaje_error = context.exception.message_dict['non_field_errors'][0]

        self.assertIn("contiene campos no permitidos", mensaje_error)

        self.assertIn("autor", mensaje_error)
        self.assertIn("is_active", mensaje_error)
        self.assertIn("campo_inventado", mensaje_error)



    def test_actualizar_nombre_manteniendo_fecha_sin_duplicados_ok(self):
        """
        Test: Actualizar nombre manteniendo fecha sin duplicados

        Given: Un administrador y un acto existente ("Acto A").
        When: Se cambia el nombre a "Acto B" manteniendo la misma fecha, 
            y no existe otro "Acto B" en esa misma fecha.
        Then: El sistema debe permitir la actualización y persistir el nuevo nombre.
        """
        acto_a_editar = self.acto_db_unificado
        nuevo_nombre = "Nombre Totalmente Diferente y Único"
        fecha_original = acto_a_editar.fecha

        payload = {
            "nombre": nuevo_nombre,
            "fecha": fecha_original
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()
        self.assertEqual(acto_a_editar.nombre, nuevo_nombre)
        self.assertEqual(acto_a_editar.fecha, fecha_original)
        self.assertIsInstance(acto_actualizado, Acto)



    def test_actualizar_fecha_manteniendo_nombre_sin_duplicados_ok(self):
        """
        Test: Actualizar fecha manteniendo nombre sin duplicados

        Given: Un administrador y un acto existente ("Acto Original").
        When: Se cambia la fecha del acto manteniendo el mismo nombre, 
            y no existe otro "Acto Original" en la nueva fecha.
        Then: El sistema debe permitir el cambio de fecha y persistir el nombre original.
        """
        acto_a_editar = self.acto_db_tradicional
        nombre_original = acto_a_editar.nombre
        nueva_fecha = acto_a_editar.fecha + timezone.timedelta(days=365)

        payload = {
            "nombre": nombre_original,
            "fecha": nueva_fecha
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()
        self.assertEqual(acto_a_editar.fecha, nueva_fecha)
        self.assertEqual(acto_a_editar.nombre, nombre_original)
        self.assertIsInstance(acto_actualizado, Acto)



    def test_actualizar_nombre_y_fecha_sin_colision_ok(self):
        """
        Test: Actualizar ambos campos pero sin colisión con otros actos

        Given: Un administrador y un acto existente ("Acto A" en "Fecha 1").
        When: Se modifican tanto el nombre ("Acto B") como la fecha ("Fecha 2") 
            y no existe ningún otro acto con esa combinación en la BD.
        Then: El sistema debe permitir la actualización de ambos campos y persistir los cambios.
        """
        acto_a_editar = self.acto_db_unificado
        nuevo_nombre = "Vía Crucis Extraordinario Reformado"
        nueva_fecha = acto_a_editar.fecha + timezone.timedelta(days=2)

        payload = {
            "nombre": nuevo_nombre,
            "fecha": nueva_fecha,
            "lugar": "Parroquia de Santa María"
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()
        self.assertEqual(acto_a_editar.nombre, nuevo_nombre)
        self.assertEqual(acto_a_editar.fecha, nueva_fecha)
        self.assertEqual(acto_a_editar.lugar, "Parroquia de Santa María")

        self.assertIsInstance(acto_actualizado, Acto)



    def test_actualizar_nombre_y_fecha_creando_duplicado_fail(self):
        """
        Test: Cambiar nombre y fecha creando duplicado → ValidationError

        Given: Un administrador y dos actos existentes ("Acto A" y "Acto B").
        When: Se intenta actualizar el "Acto A" para que tenga exactamente 
            el mismo nombre y la misma fecha que el "Acto B".
        Then: El sistema debe detectar la colisión de integridad y lanzar ValidationError.
        """
        acto_a_editar = self.acto_db_unificado
        acto_objetivo = self.acto_db_tradicional

        payload_duplicado = {
            "nombre": acto_objetivo.nombre,
            "fecha": acto_objetivo.fecha
        }

        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload_duplicado
            )

        mensaje_error = context.exception.messages[0]
        self.assertIn(f"Ya existe otro acto llamado '{acto_objetivo.nombre}'", mensaje_error)

        acto_a_editar.refresh_from_db()
        self.assertNotEqual(acto_a_editar.nombre, acto_objetivo.nombre)



    def test_actualizar_solo_nombre_creando_duplicado_fail(self):
        """
        Test: Cambiar solo nombre creando duplicado en esa fecha → ValidationError

        Given: Un administrador y dos actos en la misma fecha ("Solemne Quinario" y "Misa de Hermandad").
        When: Se intenta renombrar "Misa de Hermandad" a "Solemne Quinario".
        Then: El sistema debe lanzar ValidationError indicando que el nombre ya existe para esa fecha.
        """
        fecha_comun = self.acto_db_unificado.fecha
        self.acto_db_tradicional.fecha = fecha_comun
        self.acto_db_tradicional.save()

        acto_a_editar = self.acto_db_tradicional
        nombre_ocupado = self.acto_db_unificado.nombre

        payload_duplicado = {
            "nombre": nombre_ocupado
        }

        # 3. Verificamos la excepción
        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload_duplicado
            )

        mensaje_error = context.exception.messages[0]
        self.assertIn(f"Ya existe otro acto llamado '{nombre_ocupado}'", mensaje_error)

        acto_a_editar.refresh_from_db()
        self.assertNotEqual(acto_a_editar.nombre, nombre_ocupado)



    def test_actualizar_solo_fecha_creando_duplicado_con_mismo_nombre_fail(self):
        """
        Test: Cambiar solo fecha creando duplicado con mismo nombre → ValidationError

        Given: Dos actos con el mismo nombre ("Misa Mensual") pero en distintos meses (Enero y Febrero).
        When: Se intenta mover la "Misa Mensual" de Febrero a la misma fecha que la de Enero.
        Then: El sistema debe lanzar ValidationError indicando la duplicidad.
        """
        nombre_comun = "Misa Mensual de Hermandad"

        self.acto_db_unificado.nombre = nombre_comun
        self.acto_db_unificado.save()
        
        fecha_ocupada = self.acto_db_unificado.fecha
        fecha_inicial_diferente = fecha_ocupada + timezone.timedelta(days=30)
        self.acto_db_tradicional.nombre = nombre_comun
        self.acto_db_tradicional.fecha = fecha_inicial_diferente
        self.acto_db_tradicional.save()

        acto_a_mover = self.acto_db_tradicional

        payload_solo_fecha = {
            "fecha": fecha_ocupada
        }

        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_mover.id,
                data_validada=payload_solo_fecha
            )

        mensaje_error = context.exception.messages[0]
        self.assertIn(f"Ya existe otro acto llamado '{nombre_comun}'", mensaje_error)

        acto_a_mover.refresh_from_db()
        self.assertEqual(acto_a_mover.fecha, fecha_inicial_diferente)



    def test_cambiar_tipo_acto_sin_puestos_generados_ok(self):
        """
        Test: Cambiar tipo de acto cuando no existen puestos generados.

        Given: Un administrador, un acto existente sin puestos asociados y un nuevo Tipo de Acto.
        When: Se envía un payload para modificar el 'tipo_acto_id'.
        Then: El sistema debe permitir el cambio y actualizar la base de datos correctamente.
        """
        acto_a_editar = self.acto_db_unificado

        acto_a_editar.puestos_disponibles.all().delete()
        
        tipo_original = acto_a_editar.tipo_acto

        nuevo_tipo = TipoActo.objects.exclude(id=tipo_original.id).first()
        self.assertIsNotNone(nuevo_tipo, "Se necesita al menos otro TipoActo en la BD para el test.")

        payload = {
            "tipo_acto_id": nuevo_tipo.id
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()
        self.assertEqual(acto_a_editar.tipo_acto.id, nuevo_tipo.id)
        self.assertNotEqual(acto_a_editar.tipo_acto.id, tipo_original.id)

        if not nuevo_tipo.requiere_papeleta:
            self.assertIsNone(acto_a_editar.modalidad)



    def test_actualizar_otros_campos_manteniendo_mismo_tipo_acto_ok(self):
        """
        Test: Actualizar otros campos manteniendo el mismo tipo de acto.

        Given: Un administrador y un acto que ya tiene puestos generados.
        When: Se actualizan campos como 'lugar' o 'descripcion' pero se mantiene 
            el mismo 'tipo_acto_id' (o no se envía en el payload).
        Then: El sistema debe permitir la actualización sin disparar la validación de puestos.
        """
        acto_a_editar = self.acto_db_unificado
        tipo_original = acto_a_editar.tipo_acto

        tipo_puesto_test = TipoPuesto.objects.create(nombre_tipo="Vara de acompañamiento")
        Puesto.objects.create(
            nombre="Vara 1",
            acto=acto_a_editar,
            tipo_puesto=tipo_puesto_test,
            numero_maximo_asignaciones=1
        )

        self.assertTrue(acto_a_editar.puestos_disponibles.exists())

        nuevo_lugar = "Nueva Ubicación Confirmada"
        payload = {
            "lugar": nuevo_lugar,
            "descripcion": "Descripción actualizada tras reunión de oficiales.",
            "tipo_acto_id": tipo_original.id
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()
        self.assertEqual(acto_a_editar.lugar, nuevo_lugar)
        self.assertEqual(acto_a_editar.tipo_acto.id, tipo_original.id)
        self.assertIsInstance(acto_actualizado, Acto)



    def test_cambiar_tipo_acto_cuando_existen_puestos_fail(self):
        """
        Test: Cambiar tipo de acto cuando existen puestos → ValidationError

        Given: Un administrador y un acto que ya tiene puestos generados 
            (ej: "Vara de acompañamiento").
        When: Se intenta cambiar el 'tipo_acto_id' a uno diferente.
        Then: El sistema debe lanzar ValidationError indicando que primero 
            se deben eliminar los puestos existentes.
        """
        acto_a_editar = self.acto_db_unificado

        tipo_p = TipoPuesto.objects.create(nombre_tipo="Insignia de Prueba", es_insignia=True)
        Puesto.objects.create(
            nombre="Simpecado",
            acto=acto_a_editar,
            tipo_puesto=tipo_p,
            numero_maximo_asignaciones=1
        )

        nuevo_tipo = TipoActo.objects.exclude(id=acto_a_editar.tipo_acto.id).first()
        self.assertIsNotNone(nuevo_tipo)

        payload = {
            "tipo_acto_id": nuevo_tipo.id
        }

        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload
            )

        mensaje_error = context.exception.message_dict['tipo_acto'][0]
        self.assertIn("No se puede cambiar el Tipo de Acto porque ya existen puestos generados", mensaje_error)
        self.assertIn("Elimine los puestos primero", mensaje_error)

        acto_a_editar.refresh_from_db()
        self.assertNotEqual(acto_a_editar.tipo_acto.id, nuevo_tipo.id)



    def test_actualizar_tipo_acto_id_inexistente_fail(self):
        """
        Test: Enviar tipo_acto_id inexistente → ValidationError

        Given: Un administrador y un acto existente.
        When: Se intenta actualizar el acto enviando un 'tipo_acto_id' que 
            no corresponde a ningún registro (ej: 999999).
        Then: El sistema debe capturar el DoesNotExist y lanzar ValidationError 
            con un mensaje descriptivo.
        """
        acto_a_editar = self.acto_db_unificado
        id_inexistente = 999999

        self.assertFalse(TipoActo.objects.filter(pk=id_inexistente).exists())

        payload = {
            "tipo_acto_id": id_inexistente
        }

        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload
            )

        mensaje_error = context.exception.message_dict['tipo_acto'][0]
        self.assertEqual(mensaje_error, "El tipo de acto indicado no existe.")

        acto_a_editar.refresh_from_db()
        self.assertNotEqual(acto_a_editar.tipo_acto_id, id_inexistente)



    def test_actualizar_tipo_acto_objeto_invalido_fail(self):
        """
        Test: Enviar tipo_acto objeto inválido (no instancia) → ValidationError

        Given: Un administrador y un acto existente.
        When: Se envía en el payload un valor para 'tipo_acto' que no es 
            una instancia de TipoActo (ej: un simple string) junto a 'tipo_acto_id'.
        Then: El sistema debe detectar que no es un objeto de modelo válido y lanzar ValidationError.
        """
        acto_a_editar = self.acto_db_unificado

        payload_invalido = {
            "tipo_acto": "Soy un string, no un objeto TipoActo",
            "tipo_acto_id": 1
        }

        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload_invalido
            )

        mensaje_error = context.exception.message_dict['tipo_acto'][0]
        self.assertIn("debe ser una instancia de TipoActo", mensaje_error)

        acto_a_editar.refresh_from_db()
        self.assertNotEqual(acto_a_editar.tipo_acto, "Soy un string, no un objeto TipoActo")



    def test_actualizar_tipo_acto_y_id_inconsistentes_fail(self):
        """
        Test: Enviar tipo_acto y tipo_acto_id inconsistentes → ValidationError

        Given: Un administrador y un acto existente.
        When: Se intenta actualizar enviando la instancia del Tipo A 
            pero el ID del Tipo B en el mismo payload.
        Then: El sistema debe detectar la ambigüedad y lanzar ValidationError.
        """
        tipo_a = self.acto_db_unificado.tipo_acto

        tipo_b = TipoActo.objects.exclude(id=tipo_a.id).first()
        self.assertIsNotNone(tipo_b, "Se requiere al menos un segundo tipo de acto en BD.")

        payload_inconsistente = {
            "tipo_acto": tipo_a,
            "tipo_acto_id": tipo_b.id
        }

        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=self.acto_db_unificado.id,
                data_validada=payload_inconsistente
            )

        errores = context.exception.message_dict
        self.assertIn("tipo_acto", errores)
        self.assertIn("tipo_acto_id", errores)
        self.assertIn("Ambigüedad", errores["tipo_acto"][0])

        self.acto_db_unificado.refresh_from_db()
        self.assertEqual(self.acto_db_unificado.tipo_acto.id, tipo_a.id)
        self.assertNotEqual(self.acto_db_unificado.tipo_acto.id, tipo_b.id)



    def test_actualizar_fecha_antes_de_inicio_solicitud_ok(self):
        """
        Test: Actualizar fecha cuando aún no ha comenzado el plazo de solicitud.

        Given: Un administrador y un acto cuyo plazo de solicitud empieza mañana.
        When: Se intenta cambiar la fecha de celebración del acto.
        Then: El sistema debe permitir el cambio y actualizar la base de datos.
        """
        ahora = timezone.now()
        acto_a_editar = self.acto_db_unificado

        fecha_inicio_futura = ahora + timedelta(days=1)
        fecha_acto_original = ahora + timedelta(days=7)
        
        acto_a_editar.inicio_solicitud = fecha_inicio_futura
        acto_a_editar.fecha = fecha_acto_original
        acto_a_editar.save()

        nueva_fecha_propuesta = fecha_acto_original + timedelta(days=1)
        
        payload = {
            "fecha": nueva_fecha_propuesta
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()
        self.assertEqual(acto_a_editar.fecha, nueva_fecha_propuesta)
        self.assertIsInstance(acto_actualizado, Acto)



    def test_actualizar_fecha_en_acto_que_no_requiere_papeleta_ok(self):
        """
        Test: Actualizar fecha en acto que no requiere papeleta.

        Given: Un administrador y un acto de tipo que NO requiere papeleta 
            (ej: 'CABILDO_GENERAL').
        When: Se intenta cambiar la fecha de celebración del acto.
        Then: El sistema debe permitir el cambio siempre, ya que no hay 
            periodo de solicitudes que se vea afectado.
        """
        tipo_sin_papeleta, _ = TipoActo.objects.get_or_create(
            tipo=TipoActo.OpcionesTipo.CABILDO_GENERAL
        )

        tipo_sin_papeleta.requiere_papeleta = False
        tipo_sin_papeleta.save()

        acto_sin_papeleta = Acto.objects.create(
            nombre="Cabildo de Cuentas",
            lugar="Salón de Cabildos",
            fecha=timezone.now() + timedelta(days=5),
            tipo_acto=tipo_sin_papeleta
        )

        nueva_fecha = acto_sin_papeleta.fecha + timedelta(days=2)
        payload = {
            "fecha": nueva_fecha
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_sin_papeleta.id,
            data_validada=payload
        )

        acto_sin_papeleta.refresh_from_db()
        self.assertEqual(acto_sin_papeleta.fecha, nueva_fecha)
        self.assertIsInstance(acto_actualizado, Acto)



    def test_actualizar_fecha_manteniendo_coherencia_con_plazos_ok(self):
        """
        Test: Actualizar fecha manteniendo coherencia con plazos.

        Given: Un administrador y un acto que aún no ha iniciado su periodo de solicitudes.
        When: Se actualiza la fecha del acto y, simultáneamente en el mismo payload, 
            se modifican los plazos de solicitud para mantener la lógica cronológica.
        Then: El sistema valida la coherencia cruzada y guarda todos los cambios con éxito.
        """
        ahora = timezone.now()
        acto_a_editar = self.acto_db_unificado

        acto_a_editar.inicio_solicitud = ahora + timedelta(days=5)
        acto_a_editar.fin_solicitud = ahora + timedelta(days=10)
        acto_a_editar.fecha = ahora + timedelta(days=15)
        acto_a_editar.save()

        nueva_fecha = acto_a_editar.fecha + timedelta(days=30)
        nuevo_inicio = acto_a_editar.inicio_solicitud + timedelta(days=30)
        nuevo_fin = acto_a_editar.fin_solicitud + timedelta(days=30)

        payload = {
            "fecha": nueva_fecha,
            "inicio_solicitud": nuevo_inicio,
            "fin_solicitud": nuevo_fin
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()
        self.assertEqual(acto_a_editar.fecha, nueva_fecha)
        self.assertEqual(acto_a_editar.inicio_solicitud, nuevo_inicio)
        self.assertEqual(acto_a_editar.fin_solicitud, nuevo_fin)
        self.assertIsInstance(acto_actualizado, Acto)



    def test_actualizar_fecha_cuando_ya_comenzo_plazo_solicitud_fail(self):
        """
        Test: Intentar cambiar fecha cuando ya comenzó el plazo de solicitud.

        Given: Un administrador y un acto cuyo 'inicio_solicitud' es una fecha PASADA 
            (el plazo ya está abierto).
        When: Se intenta modificar la 'fecha' de celebración del acto.
        Then: El sistema debe lanzar una ValidationError impidiendo el cambio, 
            incluso si se intenta mover el 'inicio_solicitud' en el mismo payload.
        """
        ahora = timezone.now()
        acto_a_editar = self.acto_db_unificado

        acto_a_editar.inicio_solicitud = ahora - timedelta(hours=1)
        acto_a_editar.fin_solicitud = ahora + timedelta(days=5)
        acto_a_editar.fecha = ahora + timedelta(days=10)
        acto_a_editar.save()

        fecha_nueva = acto_a_editar.fecha + timedelta(days=2)
        inicio_nuevo = ahora + timedelta(days=1)
        
        payload = {
            "fecha": fecha_nueva,
            "inicio_solicitud": inicio_nuevo
        }

        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload
            )

        errores = context.exception.message_dict
        self.assertIn("fecha", errores)
        self.assertIn("No se puede modificar la fecha del acto porque el plazo de solicitud ya ha comenzado", errores["fecha"][0])
        self.assertIn("no se puede esquivar modificando inicio_solicitud", errores["fecha"][0])

        acto_a_editar.refresh_from_db()
        self.assertNotEqual(acto_a_editar.fecha, fecha_nueva)
        self.assertTrue(acto_a_editar.inicio_solicitud < ahora)



    def test_actualizar_fecha_y_modificar_inicio_solicitud_mismo_payload_fail(self):
        """
        Test: Intentar cambiar fecha y modificar inicio_solicitud en el mismo payload.

        Given: Un administrador y un acto donde el plazo de solicitud ya ha comenzado 
            (inicio_solicitud en el pasado).
        When: Se envía un payload que intenta cambiar la 'fecha' del acto y, 
            simultáneamente, mover 'inicio_solicitud' al futuro para intentar 
            saltarse la validación (anti-bypass).
        Then: El sistema debe detectar que el plazo ya estaba abierto originalmente 
            y lanzar ValidationError.
        """
        ahora = timezone.now()
        acto_a_editar = self.acto_db_unificado

        acto_a_editar.inicio_solicitud = ahora - timedelta(hours=2)
        acto_a_editar.fin_solicitud = ahora + timedelta(days=2)
        acto_a_editar.fecha = ahora + timedelta(days=5)
        acto_a_editar.save()

        fecha_nueva = ahora + timedelta(days=10)
        inicio_futuro = ahora + timedelta(days=1)
        
        payload = {
            "fecha": fecha_nueva,
            "inicio_solicitud": inicio_futuro
        }

        with self.assertRaises(DjangoValidationError) as context:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload
            )

        errores = context.exception.message_dict
        self.assertIn("fecha", errores)
        error_msg = errores["fecha"][0]
        self.assertIn("no se puede esquivar modificando inicio_solicitud", error_msg)

        acto_a_editar.refresh_from_db()
        self.assertNotEqual(acto_a_editar.fecha, fecha_nueva)
        self.assertTrue(acto_a_editar.inicio_solicitud < ahora)



    def test_actualizar_acto_a_tipo_que_no_requiere_papeleta_limpia_campos_ok(self):
        """
        Test: Actualizar acto a tipo que no requiere papeleta.

        Given: Un administrador y un acto que originalmente SÍ requería papeleta 
            (con modalidad y plazos definidos).
        When: Se cambia el 'tipo_acto' a uno que NO requiere papeleta.
        Then: El sistema debe actualizar el tipo y, automáticamente, establecer 
            como None la modalidad y todos los campos de inicio/fin de solicitud.
        """
        acto_con_datos = self.acto_db_unificado
        acto_con_datos.modalidad = Acto.ModalidadReparto.UNIFICADO
        acto_con_datos.inicio_solicitud = timezone.now() + timedelta(days=1)
        acto_con_datos.fin_solicitud = timezone.now() + timedelta(days=5)
        acto_con_datos.save()

        tipo_sin_papeleta, _ = TipoActo.objects.get_or_create(
            tipo=TipoActo.OpcionesTipo.CONVIVENCIA
        )
        tipo_sin_papeleta.requiere_papeleta = False
        tipo_sin_papeleta.save()

        payload = {
            "tipo_acto": tipo_sin_papeleta
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_con_datos.id,
            data_validada=payload
        )

        acto_con_datos.refresh_from_db()

        self.assertEqual(acto_con_datos.tipo_acto, tipo_sin_papeleta)

        self.assertIsNone(acto_con_datos.modalidad)
        self.assertIsNone(acto_con_datos.inicio_solicitud)
        self.assertIsNone(acto_con_datos.fin_solicitud)
        self.assertIsNone(acto_con_datos.inicio_solicitud_cirios)
        self.assertIsNone(acto_con_datos.fin_solicitud_cirios)
        
        self.assertIsInstance(acto_actualizado, Acto)



    def test_actualizar_acto_manteniendo_modalidad_none_ok(self):
        """
        Test: Actualizar acto manteniendo modalidad None.

        Given: Un administrador y un acto de tipo que NO requiere papeleta 
            (ej: 'CONVIVENCIA').
        When: Se intenta actualizar el acto enviando una 'modalidad' en el payload 
            (intento de dato inconsistente).
        Then: El sistema debe procesar la actualización pero forzar 'modalidad' 
            a None mediante la normalización automática.
        """
        tipo_sin_papeleta, _ = TipoActo.objects.get_or_create(
            tipo=TipoActo.OpcionesTipo.CONVIVENCIA
        )
        tipo_sin_papeleta.requiere_papeleta = False
        tipo_sin_papeleta.save()

        acto_sin_papeleta = Acto.objects.create(
            nombre="Comida de Hermandad",
            lugar="Casa Hermandad",
            fecha=timezone.now() + timedelta(days=20),
            tipo_acto=tipo_sin_papeleta,
            modalidad=None
        )

        payload = {
            "nombre": "Comida de Hermandad (Actualizado)",
            "modalidad": Acto.ModalidadReparto.UNIFICADO 
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_sin_papeleta.id,
            data_validada=payload
        )

        acto_sin_papeleta.refresh_from_db()

        self.assertEqual(acto_sin_papeleta.nombre, "Comida de Hermandad (Actualizado)")

        self.assertIsNone(acto_sin_papeleta.modalidad)
        
        self.assertIsInstance(acto_actualizado, Acto)



    def test_verificar_modalidad_permanece_none_en_acto_sin_papeleta_ok(self):
        """
        Test: Verificaciones esperadas - modalidad = None.

        Given: Un administrador y un acto cuyo tipo_acto NO requiere papeleta.
        When: Se intenta actualizar el acto enviando una 'modalidad' y fechas de solicitud 
            en el payload (datos incoherentes para este tipo).
        Then: El servicio debe ignorar esos campos y forzar 'modalidad = None' 
            (y el resto de campos de solicitud a None) tras la normalización.
        """
        tipo_sin_papeleta, _ = TipoActo.objects.get_or_create(
            tipo=TipoActo.OpcionesTipo.CONVIVENCIA
        )
        tipo_sin_papeleta.requiere_papeleta = False
        tipo_sin_papeleta.save()

        acto_sin_papeleta = Acto.objects.create(
            nombre="Convivencia de Jóvenes",
            lugar="Casa Hermandad",
            fecha=timezone.now() + timedelta(days=15),
            tipo_acto=tipo_sin_papeleta,
            modalidad=None
        )

        payload = {
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": timezone.now() + timedelta(days=1),
            "fin_solicitud": timezone.now() + timedelta(days=5)
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_sin_papeleta.id,
            data_validada=payload
        )

        acto_sin_papeleta.refresh_from_db()

        self.assertIsNone(acto_sin_papeleta.modalidad)

        self.assertIsNone(acto_sin_papeleta.inicio_solicitud)
        self.assertIsNone(acto_sin_papeleta.fin_solicitud)
        
        self.assertIsInstance(acto_actualizado, Acto)



    def test_verificar_inicio_solicitud_permanece_none_en_acto_sin_papeleta_ok(self):
        """
        Test: Verificaciones esperadas - inicio_solicitud = None.

        Given: Un administrador y un acto cuyo tipo_acto NO requiere papeleta 
            (ej: 'CABILDO_GENERAL').
        When: Se intenta actualizar el acto enviando un 'inicio_solicitud' 
            (y otros plazos) en el payload.
        Then: El servicio debe ignorar esos plazos y establecer 'inicio_solicitud' 
            (y el resto de campos de periodo) a None tras la normalización.
        """
        tipo_sin_papeleta, _ = TipoActo.objects.get_or_create(
            tipo=TipoActo.OpcionesTipo.CABILDO_GENERAL
        )
        tipo_sin_papeleta.requiere_papeleta = False
        tipo_sin_papeleta.save()

        acto_sin_papeleta = Acto.objects.create(
            nombre="Cabildo General Ordinario",
            lugar="Parroquia",
            fecha=timezone.now() + timedelta(days=10),
            tipo_acto=tipo_sin_papeleta
        )

        fecha_intento = timezone.now() + timedelta(days=1)
        payload = {
            "inicio_solicitud": fecha_intento,
            "fin_solicitud": timezone.now() + timedelta(days=5),
            "lugar": "Salón Parroquial"
        }

        actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_sin_papeleta.id,
            data_validada=payload
        )

        acto_sin_papeleta.refresh_from_db()

        self.assertIsNone(acto_sin_papeleta.inicio_solicitud)
        self.assertIsNone(acto_sin_papeleta.fin_solicitud)

        self.assertEqual(acto_sin_papeleta.lugar, "Salón Parroquial")



    def test_verificar_fin_solicitud_permanece_none_en_acto_sin_papeleta_ok(self):
        """
        Test: Verificaciones esperadas - fin_solicitud = None.

        Given: Un administrador y un acto de tipo que NO requiere papeleta 
            (ej: 'CONVIVENCIA').
        When: Se intenta actualizar el acto enviando un 'fin_solicitud' en el payload.
        Then: El servicio debe limpiar el campo y establecer 'fin_solicitud' a None 
            automáticamente tras la normalización.
        """
        tipo_sin_papeleta, _ = TipoActo.objects.get_or_create(
            tipo=TipoActo.OpcionesTipo.CONVIVENCIA
        )
        tipo_sin_papeleta.requiere_papeleta = False
        tipo_sin_papeleta.save()

        acto_sin_papeleta = Acto.objects.create(
            nombre="Convivencia Rociera",
            lugar="Aldea del Rocío",
            fecha=timezone.now() + timedelta(days=20),
            tipo_acto=tipo_sin_papeleta
        )

        fecha_fin_intento = timezone.now() + timedelta(days=10)
        payload = {
            "fin_solicitud": fecha_fin_intento,
            "descripcion": "Nueva descripción de la convivencia"
        }

        actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_sin_papeleta.id,
            data_validada=payload
        )

        acto_sin_papeleta.refresh_from_db()

        self.assertIsNone(acto_sin_papeleta.fin_solicitud)

        self.assertEqual(acto_sin_papeleta.descripcion, "Nueva descripción de la convivencia")
        self.assertIsInstance(acto_sin_papeleta, Acto)



    def test_verificar_inicio_solicitud_cirios_permanece_none_en_modalidad_unificada_ok(self):
        """
        Test: Verificaciones esperadas - inicio_solicitud_cirios = None.

        Given: Un administrador y un acto con modalidad 'UNIFICADO'.
        When: Se intenta actualizar el acto enviando un 'inicio_solicitud_cirios' 
            en el payload (dato incoherente para esta modalidad).
        Then: El servicio debe limpiar el campo y establecer 'inicio_solicitud_cirios' 
            a None automáticamente tras la normalización.
        """
        acto_unificado = self.acto_db_unificado
        acto_unificado.modalidad = Acto.ModalidadReparto.UNIFICADO
        acto_unificado.save()

        fecha_cirios_intento = timezone.now() + timedelta(days=2)
        payload = {
            "inicio_solicitud_cirios": fecha_cirios_intento,
            "lugar": "Catedral de Sevilla"
        }

        actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_unificado.id,
            data_validada=payload
        )

        acto_unificado.refresh_from_db()

        self.assertIsNone(acto_unificado.inicio_solicitud_cirios)

        self.assertEqual(acto_unificado.lugar, "Catedral de Sevilla")
        self.assertEqual(acto_unificado.modalidad, Acto.ModalidadReparto.UNIFICADO)



    def test_verificar_fin_solicitud_cirios_permanece_none_en_modalidad_unificada_ok(self):
        """
        Test: Verificaciones esperadas - fin_solicitud_cirios = None.

        Given: Un administrador y un acto con modalidad 'UNIFICADO'.
        When: Se intenta actualizar el acto enviando un 'fin_solicitud_cirios' 
            en el payload.
        Then: El servicio debe limpiar el campo y establecer 'fin_solicitud_cirios' 
            a None automáticamente tras la normalización.
        """
        acto_unificado = self.acto_db_unificado
        acto_unificado.modalidad = Acto.ModalidadReparto.UNIFICADO
        acto_unificado.save()

        fecha_fin_cirios_intento = timezone.now() + timedelta(days=5)
        payload = {
            "fin_solicitud_cirios": fecha_fin_cirios_intento,
            "descripcion": "Actualizando descripción en modalidad unificada"
        }

        actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_unificado.id,
            data_validada=payload
        )

        acto_unificado.refresh_from_db()

        self.assertIsNone(acto_unificado.fin_solicitud_cirios)

        self.assertEqual(acto_unificado.descripcion, "Actualizando descripción en modalidad unificada")
        self.assertEqual(acto_unificado.modalidad, Acto.ModalidadReparto.UNIFICADO)



    def test_actualizar_modalidad_a_unificado_elimina_fechas_de_cirios_ok(self):
        """
        Test: Actualizar modalidad a UNIFICADO.

        Given: Un administrador y un acto que originalmente es TRADICIONAL 
            (con fechas de solicitud de insignias y cirios cronológicamente válidas).
        When: Se actualiza el acto cambiando la 'modalidad' a UNIFICADO.
        Then: El sistema debe actualizar la modalidad y, automáticamente, establecer 
            como None 'inicio_solicitud_cirios' y 'fin_solicitud_cirios'.
        """
        ahora = timezone.now()
        acto_a_editar = self.acto_db_unificado

        acto_a_editar.modalidad = Acto.ModalidadReparto.TRADICIONAL
        acto_a_editar.inicio_solicitud = ahora + timedelta(days=1)
        acto_a_editar.fin_solicitud = ahora + timedelta(days=3)

        acto_a_editar.inicio_solicitud_cirios = ahora + timedelta(days=4)
        acto_a_editar.fin_solicitud_cirios = ahora + timedelta(days=6)

        acto_a_editar.fecha = ahora + timedelta(days=10)
        
        acto_a_editar.save()

        payload = {
            "modalidad": Acto.ModalidadReparto.UNIFICADO
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.modalidad, Acto.ModalidadReparto.UNIFICADO)

        self.assertIsNone(acto_a_editar.inicio_solicitud_cirios)
        self.assertIsNone(acto_a_editar.fin_solicitud_cirios)

        self.assertIsNotNone(acto_a_editar.inicio_solicitud)
        
        self.assertIsInstance(acto_actualizado, Acto)



    def test_actualizar_modalidad_unificado_manteniendo_fechas_principales_ok(self):
        """
        Test: Actualizar modalidad UNIFICADO manteniendo fechas principales.

        Given: Un administrador y un acto en modalidad TRADICIONAL con todas sus fechas válidas.
        When: Se cambia la modalidad a UNIFICADO pero NO se envían las fechas 
            principales en el payload (se dejan las existentes).
        Then: El sistema debe cambiar la modalidad, limpiar las fechas de cirios, 
            pero mantener intactas la fecha del acto y los plazos generales.
        """
        ahora = timezone.now()
        acto_a_editar = self.acto_db_unificado

        fecha_acto_orig = ahora + timedelta(days=20)

        inicio_orig = ahora + timedelta(days=1)
        fin_orig = ahora + timedelta(days=3)

        inicio_cirios = ahora + timedelta(days=4)
        fin_cirios = ahora + timedelta(days=6)
        
        acto_a_editar.modalidad = Acto.ModalidadReparto.TRADICIONAL
        acto_a_editar.fecha = fecha_acto_orig
        acto_a_editar.inicio_solicitud = inicio_orig
        acto_a_editar.fin_solicitud = fin_orig
        acto_a_editar.inicio_solicitud_cirios = inicio_cirios
        acto_a_editar.fin_solicitud_cirios = fin_cirios
        acto_a_editar.save()

        payload = {
            "modalidad": Acto.ModalidadReparto.UNIFICADO
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()       

        self.assertEqual(acto_a_editar.fecha, fecha_acto_orig)
        self.assertEqual(acto_a_editar.inicio_solicitud, inicio_orig)
        self.assertEqual(acto_a_editar.fin_solicitud, fin_orig)

        self.assertIsNone(acto_a_editar.inicio_solicitud_cirios)
        self.assertIsNone(acto_a_editar.fin_solicitud_cirios)
        
        self.assertEqual(acto_a_editar.modalidad, Acto.ModalidadReparto.UNIFICADO)



    def test_verificar_inicio_solicitud_cirios_permanece_none_en_modalidad_unificada_ok(self):
        """
        Test: Verificaciones esperadas - inicio_solicitud_cirios = None.

        Given: Un administrador y un acto configurado en modalidad 'UNIFICADO'.
        When: Se intenta actualizar el acto enviando un 'inicio_solicitud_cirios' 
            en el payload (dato inconsistente para esta modalidad).
        Then: El servicio debe ignorar ese valor y forzar 'inicio_solicitud_cirios = None' 
            automáticamente tras la normalización.
        """
        acto_unificado = self.acto_db_unificado
        acto_unificado.modalidad = Acto.ModalidadReparto.UNIFICADO
        acto_unificado.inicio_solicitud_cirios = None
        acto_unificado.fin_solicitud_cirios = None
        acto_unificado.save()

        fecha_cirios_intento = timezone.now() + timedelta(days=5)
        payload = {
            "inicio_solicitud_cirios": fecha_cirios_intento,
            "descripcion": "Descripción actualizada en modalidad unificada"
        }

        actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_unificado.id,
            data_validada=payload
        )

        acto_unificado.refresh_from_db()

        self.assertIsNone(acto_unificado.inicio_solicitud_cirios)

        self.assertEqual(acto_unificado.descripcion, "Descripción actualizada en modalidad unificada")
        self.assertEqual(acto_unificado.modalidad, Acto.ModalidadReparto.UNIFICADO)



    def test_verificar_fin_solicitud_cirios_permanece_none_en_modalidad_unificada_ok(self):
        """
        Test: Verificaciones esperadas - fin_solicitud_cirios = None.

        Given: Un administrador y un acto configurado en modalidad 'UNIFICADO'.
        When: Se intenta actualizar el acto enviando un 'fin_solicitud_cirios' 
            en el payload (dato incoherente para esta modalidad).
        Then: El servicio debe ignorar ese valor y forzar 'fin_solicitud_cirios = None' 
            automáticamente tras la normalización.
        """
        acto_unificado = self.acto_db_unificado
        acto_unificado.modalidad = Acto.ModalidadReparto.UNIFICADO
        acto_unificado.inicio_solicitud_cirios = None
        acto_unificado.fin_solicitud_cirios = None
        acto_unificado.save()

        fecha_fin_intento = timezone.now() + timedelta(days=8)
        payload = {
            "fin_solicitud_cirios": fecha_fin_intento,
            "nombre": "Nombre Actualizado Unificado"
        }

        actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_unificado.id,
            data_validada=payload
        )

        acto_unificado.refresh_from_db()

        self.assertIsNone(acto_unificado.fin_solicitud_cirios)

        self.assertEqual(acto_unificado.nombre, "Nombre Actualizado Unificado")
        self.assertEqual(acto_unificado.modalidad, Acto.ModalidadReparto.UNIFICADO)



    def test_actualizar_acto_con_fechas_coherentes_solicitud_ok(self):
        """
        Test: Acto con fechas coherentes de solicitud.

        Given: Un administrador y un acto en modalidad TRADICIONAL.
        When: Se envían fechas que cumplen estrictamente el orden:
            inicio_solicitud < fin_solicitud < inicio_solicitud_cirios < fin_solicitud_cirios < fecha_acto.
        Then: El servicio debe actualizar todos los campos correctamente y superar 
            el full_clean() del modelo sin lanzar excepciones.
        """
        ahora = timezone.now()
        acto_a_editar = self.acto_db_unificado

        inicio_insignias = ahora + timedelta(days=1)
        fin_insignias = ahora + timedelta(days=3)

        inicio_cirios = ahora + timedelta(days=4)
        fin_cirios = ahora + timedelta(days=6)

        fecha_celebracion = ahora + timedelta(days=10)

        payload = {
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": inicio_insignias,
            "fin_solicitud": fin_insignias,
            "inicio_solicitud_cirios": inicio_cirios,
            "fin_solicitud_cirios": fin_cirios,
            "fecha": fecha_celebracion,
            "lugar": "S.I. Catedral de Sevilla"
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.inicio_solicitud, inicio_insignias)
        self.assertEqual(acto_a_editar.fin_solicitud, fin_insignias)
        self.assertEqual(acto_a_editar.inicio_solicitud_cirios, inicio_cirios)
        self.assertEqual(acto_a_editar.fin_solicitud_cirios, fin_cirios)
        self.assertEqual(acto_a_editar.fecha, fecha_celebracion)
        self.assertEqual(acto_a_editar.lugar, "S.I. Catedral de Sevilla")

        self.assertIsInstance(acto_actualizado, Acto)



    def test_actualizar_acto_modalidad_tradicional_fechas_cirios_validas_ok(self):
        """
        Test: Acto con modalidad tradicional y fechas de cirios válidas.

        Given: Un administrador y un acto configurado como TRADICIONAL.
        When: Se envían fechas de cirios que comienzan después de que termine 
            el plazo de insignias (inicio_solicitud_cirios > fin_solicitud).
        Then: El servicio debe actualizar el acto, superar el full_clean() y 
            persistir ambos rangos de fechas correctamente.
        """
        ahora = timezone.now()
        acto_a_editar = self.acto_db_unificado

        inicio_insignias = ahora + timedelta(days=1)
        fin_insignias = ahora + timedelta(days=5)

        inicio_cirios = ahora + timedelta(days=6)
        fin_cirios = ahora + timedelta(days=10)

        fecha_acto = ahora + timedelta(days=15)

        payload = {
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": inicio_insignias,
            "fin_solicitud": fin_insignias,
            "inicio_solicitud_cirios": inicio_cirios,
            "fin_solicitud_cirios": fin_cirios,
            "fecha": fecha_acto,
            "lugar": "Iglesia de San Juan"
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.inicio_solicitud, inicio_insignias)
        self.assertEqual(acto_a_editar.fin_solicitud, fin_insignias)
        self.assertEqual(acto_a_editar.inicio_solicitud_cirios, inicio_cirios)
        self.assertEqual(acto_a_editar.fin_solicitud_cirios, fin_cirios)

        self.assertEqual(acto_a_editar.modalidad, Acto.ModalidadReparto.TRADICIONAL)
        self.assertIsInstance(acto_actualizado, Acto)



    def test_actualizar_acto_inicio_solicitud_posterior_a_fin_error(self):
        """
        Test: Inicio de solicitud posterior al fin.

        Given: Un administrador y un acto existente.
        When: Se intenta actualizar el acto con un 'inicio_solicitud' que es 
            posterior al 'fin_solicitud'.
        Then: El modelo debe lanzar una ValidationError capturada por el servicio, 
            indicando que el fin debe ser posterior al inicio.
        """
        ahora = timezone.now()
        acto_a_editar = self.acto_db_unificado

        payload = {
            "inicio_solicitud": ahora + timedelta(days=5),
            "fin_solicitud": ahora + timedelta(days=1),
            "modalidad": Acto.ModalidadReparto.UNIFICADO
        }

        with self.assertRaises(DjangoValidationError) as cm:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload
            )

        self.assertIn('fin_solicitud', cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict['fin_solicitud'][0], 
            "El fin de solicitud debe ser posterior al inicio."
        )



    def test_actualizar_acto_inicio_solicitud_posterior_a_fecha_acto_error(self):
        """
        Test: Inicio de solicitud posterior a fecha del acto.

        Given: Un administrador y un acto programado para una fecha concreta.
        When: Se intenta actualizar el acto con un 'inicio_solicitud' que es 
            posterior o igual a la 'fecha' de celebración del acto.
        Then: El modelo debe lanzar una ValidationError capturada por el servicio, 
            indicando que el inicio no puede ser posterior a la fecha del acto.
        """
        ahora = timezone.now()
        acto_a_editar = self.acto_db_unificado

        fecha_acto = ahora + timedelta(days=10)
        inicio_invalido = ahora + timedelta(days=15)
        
        payload = {
            "fecha": fecha_acto,
            "inicio_solicitud": inicio_invalido,
            "fin_solicitud": ahora + timedelta(days=16),
            "modalidad": Acto.ModalidadReparto.UNIFICADO
        }

        with self.assertRaises(DjangoValidationError) as cm:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload
            )

        self.assertIn('inicio_solicitud', cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict['inicio_solicitud'][0], 
            "El inicio de solicitud no puede ser igual o posterior a la fecha del acto."
        )



    def test_actualizar_acto_fin_solicitud_posterior_a_fecha_acto_error(self):
        """
        Test: Fin de solicitud posterior a fecha del acto.

        Given: Un administrador y un acto existente.
        When: Se intenta actualizar el acto con un 'fin_solicitud' que es 
            cronológicamente posterior a la 'fecha' del acto.
        Then: El modelo debe lanzar una ValidationError capturada por el servicio, 
            indicando que el fin de solicitud no puede ser posterior al acto.
        """
        ahora = timezone.now()
        acto_a_editar = self.acto_db_unificado

        fecha_celebracion = ahora + timedelta(days=10)
        fin_invalido = ahora + timedelta(days=11)
        
        payload = {
            "fecha": fecha_celebracion,
            "inicio_solicitud": ahora + timedelta(days=1),
            "fin_solicitud": fin_invalido,
            "modalidad": Acto.ModalidadReparto.UNIFICADO
        }

        with self.assertRaises(DjangoValidationError) as cm:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload
            )

        self.assertIn('fin_solicitud', cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict['fin_solicitud'][0], 
            "El fin de solicitud no puede ser posterior a la fecha del acto."
        )



    def test_actualizar_acto_modalidad_tradicional_sin_fechas_cirios_error(self):
        """
        Test: Modalidad tradicional sin fechas de cirios.

        Given: Un administrador y un acto existente.
        When: Se cambia la modalidad a TRADICIONAL pero NO se envían las fechas 
            obligatorias de 'inicio_solicitud_cirios' o 'fin_solicitud_cirios'.
        Then: El modelo debe lanzar una ValidationError capturada por el servicio, 
            indicando que estas fechas son obligatorias para esta modalidad.
        """
        ahora = timezone.now()
        acto_a_editar = self.acto_db_unificado

        payload = {
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": ahora + timedelta(days=1),
            "fin_solicitud": ahora + timedelta(days=3),
            "fecha": ahora + timedelta(days=10)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload
            )

        self.assertIn('inicio_solicitud_cirios', cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict['inicio_solicitud_cirios'][0], 
            "El inicio de cirios es obligatorio en modalidad tradicional."
        )



    def test_actualizar_solo_nombre_acto_ok(self):
        """
        Test: Actualizaciones parciales válidas - Actualizar solo nombre.

        Given: Un administrador y un acto ya existente en la base de datos con una configuración completa.
        When: Se llama al servicio enviando únicamente el campo 'nombre' en el payload.
        Then: El servicio debe actualizar el nombre, mantener el resto de campos 
            sin cambios y superar las validaciones del modelo.
        """
        acto_a_editar = self.acto_db_unificado
        nombre_original = acto_a_editar.nombre
        lugar_original = acto_a_editar.lugar
        modalidad_original = acto_a_editar.modalidad
        fecha_original = acto_a_editar.fecha

        nuevo_nombre = "Solemne Quinario Actualizado"
        payload = {
            "nombre": nuevo_nombre
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.nombre, nuevo_nombre)

        self.assertEqual(acto_a_editar.lugar, lugar_original)
        self.assertEqual(acto_a_editar.modalidad, modalidad_original)
        self.assertEqual(acto_a_editar.fecha, fecha_original)

        self.assertIsNotNone(acto_a_editar.tipo_acto)
        
        self.assertIsInstance(acto_actualizado, Acto)



    def test_actualizar_solo_descripcion_acto_ok(self):
        """
        Test: Actualizaciones parciales válidas - Actualizar solo descripción.

        Given: Un administrador y un acto existente con descripción previa.
        When: Se envía un payload que solo contiene el campo 'descripcion'.
        Then: El servicio debe actualizar la descripción, mantener intactos 
            el nombre, fechas, lugar y modalidad, y persistir el cambio.
        """
        acto_a_editar = self.acto_db_unificado
        nombre_pre = acto_a_editar.nombre
        fecha_pre = acto_a_editar.fecha
        modalidad_pre = acto_a_editar.modalidad

        nueva_desc = "Nueva descripción detallada para el acto de la Hermandad."
        payload = {
            "descripcion": nueva_desc
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.descripcion, nueva_desc)

        self.assertEqual(acto_a_editar.nombre, nombre_pre)
        self.assertEqual(acto_a_editar.fecha, fecha_pre)
        self.assertEqual(acto_a_editar.modalidad, modalidad_pre)
        
        self.assertIsInstance(acto_actualizado, Acto)



    def test_actualizar_solo_lugar_acto_ok(self):
        """
        Test: Actualizaciones parciales válidas - Actualizar solo lugar.

        Given: Un administrador y un acto existente en la base de datos.
        When: Se llama al servicio enviando únicamente el campo 'lugar' en el payload.
        Then: El servicio debe actualizar el lugar de celebración, mantener el resto 
            de campos (nombre, fechas, modalidad) intactos y persistir el cambio.
        """
        acto_a_editar = self.acto_db_unificado
        nombre_esperado = acto_a_editar.nombre
        fecha_esperada = acto_a_editar.fecha
        modalidad_esperada = acto_a_editar.modalidad

        nuevo_lugar = "Casa Hermandad - Salón de Actos"
        payload = {
            "lugar": nuevo_lugar
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.lugar, nuevo_lugar)

        self.assertEqual(acto_a_editar.nombre, nombre_esperado)
        self.assertEqual(acto_a_editar.fecha, fecha_esperada)
        self.assertEqual(acto_a_editar.modalidad, modalidad_esperada)
        
        self.assertIsInstance(acto_actualizado, Acto)



    def test_actualizar_solo_modalidad_de_tradicional_a_unificado_ok(self):
        """
        Test: Actualizaciones parciales válidas - Actualizar solo modalidad.

        Given: Un administrador y un acto configurado como TRADICIONAL 
            con sus correspondientes fechas de cirios pobladas.
        When: Se envía un payload que solo contiene 'modalidad': UNIFICADO.
        Then: El servicio debe actualizar la modalidad y, por efecto colateral 
            de la normalización, poner a None 'inicio_solicitud_cirios' 
            y 'fin_solicitud_cirios'.
        """
        ahora = timezone.now()
        acto_a_editar = self.acto_db_unificado

        acto_a_editar.modalidad = Acto.ModalidadReparto.TRADICIONAL
        acto_a_editar.inicio_solicitud = ahora + timedelta(days=1)
        acto_a_editar.fin_solicitud = ahora + timedelta(days=2)
        acto_a_editar.inicio_solicitud_cirios = ahora + timedelta(days=3)
        acto_a_editar.fin_solicitud_cirios = ahora + timedelta(days=4)
        acto_a_editar.fecha = ahora + timedelta(days=10)
        acto_a_editar.save()

        payload = {
            "modalidad": Acto.ModalidadReparto.UNIFICADO
        }

        actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.modalidad, Acto.ModalidadReparto.UNIFICADO)

        self.assertIsNone(acto_a_editar.inicio_solicitud_cirios)
        self.assertIsNone(acto_a_editar.fin_solicitud_cirios)

        self.assertIsNotNone(acto_a_editar.inicio_solicitud)
        self.assertEqual(acto_a_editar.fecha.day, (ahora + timedelta(days=10)).day)



    def test_actualizar_solo_fechas_solicitud_insignias_ok(self):
        """
        Test: Actualizaciones parciales válidas - Actualizar solo fechas de solicitud.

        Given: Un administrador y un acto existente.
        When: Se envía un payload que solo contiene 'inicio_solicitud' y 'fin_solicitud'.
        Then: El servicio debe actualizar ambos campos, mantener el resto (nombre, 
            lugar, modalidad) intactos y superar la validación del modelo.
        """
        ahora = timezone.now()
        acto_a_editar = self.acto_db_unificado

        nombre_pre = acto_a_editar.nombre
        modalidad_pre = acto_a_editar.modalidad

        nueva_fecha_inicio = ahora + timedelta(days=2)
        nueva_fecha_fin = ahora + timedelta(days=4)
        
        payload = {
            "inicio_solicitud": nueva_fecha_inicio,
            "fin_solicitud": nueva_fecha_fin
        }

        actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.inicio_solicitud, nueva_fecha_inicio)
        self.assertEqual(acto_a_editar.fin_solicitud, nueva_fecha_fin)

        self.assertEqual(acto_a_editar.nombre, nombre_pre)
        self.assertEqual(acto_a_editar.modalidad, modalidad_pre)

        self.assertIsNone(acto_a_editar.inicio_solicitud_cirios)
        self.assertIsNone(acto_a_editar.fin_solicitud_cirios)



    def test_actualizar_solo_tipo_acto_id_ok(self):
        """
        Test: Actualizaciones parciales válidas - Actualizar solo tipo_acto_id.

        Given: Un administrador, un acto existente y un nuevo Tipo de Acto 
            registrado en el sistema.
        When: Se envía un payload que solo contiene el campo 'tipo_acto_id'.
        Then: El servicio debe actualizar la relación del acto con el nuevo tipo, 
            manteniendo intactos el resto de atributos (fechas, lugar, modalidad).
        """
        nuevo_tipo = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.VIA_CRUCIS, 
            requiere_papeleta=True
        )
        acto_a_editar = self.acto_db_unificado

        nombre_pre = acto_a_editar.nombre
        fecha_pre = acto_a_editar.fecha
        modalidad_pre = acto_a_editar.modalidad
        tipo_original_id = acto_a_editar.tipo_acto_id

        payload = {
            "tipo_acto_id": nuevo_tipo.id
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.tipo_acto_id, nuevo_tipo.id)
        self.assertEqual(acto_a_editar.tipo_acto.tipo, TipoActo.OpcionesTipo.VIA_CRUCIS)

        self.assertNotEqual(acto_a_editar.tipo_acto_id, tipo_original_id)

        self.assertEqual(acto_a_editar.nombre, nombre_pre)
        self.assertEqual(acto_a_editar.fecha, fecha_pre)
        self.assertEqual(acto_a_editar.modalidad, modalidad_pre)
        
        self.assertIsInstance(acto_actualizado, Acto)



    def test_actualizar_nombre_fecha_y_lugar_simultaneamente_ok(self):
        """
        Test: Actualización múltiple válida - Actualizar nombre, fecha y lugar simultáneamente.

        Given: Un administrador y un acto existente.
        When: Se envía un payload con cambios en 'nombre', 'fecha' y 'lugar' 
            al mismo tiempo.
        Then: El servicio debe aplicar los tres cambios, mantener el resto de 
            campos (modalidad, plazos) intactos y persistir la información.
        """
        ahora = timezone.now()
        acto_a_editar = self.acto_db_unificado

        modalidad_pre = acto_a_editar.modalidad
        inicio_solicitud_pre = acto_a_editar.inicio_solicitud

        nuevo_nombre = "Traslado de Ida Extraordinario"
        nueva_fecha = ahora + timedelta(days=20)
        nuevo_lugar = "Convento de Santa Isabel"
        
        payload = {
            "nombre": nuevo_nombre,
            "fecha": nueva_fecha,
            "lugar": nuevo_lugar
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.nombre, nuevo_nombre)
        self.assertEqual(acto_a_editar.fecha, nueva_fecha)
        self.assertEqual(acto_a_editar.lugar, nuevo_lugar)

        self.assertEqual(acto_a_editar.modalidad, modalidad_pre)
        self.assertEqual(acto_a_editar.inicio_solicitud, inicio_solicitud_pre)
        
        self.assertIsInstance(acto_actualizado, Acto)



    def test_actualizar_modalidad_y_fechas_coherentes_ok(self):
        """
        Test: Actualizar modalidad y fechas coherentes.

        Given: Un administrador y un acto configurado inicialmente como UNIFICADO.
        When: Se actualiza la modalidad a TRADICIONAL enviando simultáneamente 
            un cronograma válido (insignias < cirios).
        Then: El servicio debe aplicar el cambio de modalidad y persistir 
            los dos rangos de fechas correctamente sin errores de validación.
        """
        ahora = timezone.now()
        acto_a_editar = self.acto_db_unificado

        nuevo_inicio_insignias = ahora + timedelta(days=1)
        nuevo_fin_insignias = ahora + timedelta(days=3)

        nuevo_inicio_cirios = ahora + timedelta(days=4)
        nuevo_fin_cirios = ahora + timedelta(days=6)

        payload = {
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": nuevo_inicio_insignias,
            "fin_solicitud": nuevo_fin_insignias,
            "inicio_solicitud_cirios": nuevo_inicio_cirios,
            "fin_solicitud_cirios": nuevo_fin_cirios
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()
        
        self.assertEqual(acto_a_editar.modalidad, Acto.ModalidadReparto.TRADICIONAL)

        self.assertEqual(acto_a_editar.inicio_solicitud, nuevo_inicio_insignias)
        self.assertEqual(acto_a_editar.fin_solicitud, nuevo_fin_insignias)
        self.assertEqual(acto_a_editar.inicio_solicitud_cirios, nuevo_inicio_cirios)
        self.assertEqual(acto_a_editar.fin_solicitud_cirios, nuevo_fin_cirios)
        
        self.assertIsInstance(acto_actualizado, Acto)



    def test_actualizar_tipo_acto_y_fechas_validas_ok(self):
        """
        Test: Actualizar tipo de acto y fechas válidas.

        Given: Un administrador, un acto existente y un nuevo Tipo de Acto 
            que requiere papeleta.
        When: Se envía un payload cambiando el 'tipo_acto_id' y reajustando 
            todas las fechas de solicitud ('inicio_solicitud', 'fin_solicitud').
        Then: El servicio debe actualizar la relación de clave foránea y los 
            campos de fecha, superando la validación del modelo.
        """
        ahora = timezone.now()

        nuevo_tipo = self.tipo_con_papeleta_alt 
        acto_a_editar = self.acto_db_unificado

        nueva_fecha_acto = ahora + timedelta(days=30)
        nuevo_inicio = ahora + timedelta(days=5)
        nuevo_fin = ahora + timedelta(days=15)
        
        payload = {
            "tipo_acto_id": nuevo_tipo.id,
            "fecha": nueva_fecha_acto,
            "inicio_solicitud": nuevo_inicio,
            "fin_solicitud": nuevo_fin,
            "modalidad": Acto.ModalidadReparto.UNIFICADO
        }

        acto_actualizado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.tipo_acto_id, nuevo_tipo.id)
        self.assertEqual(acto_a_editar.tipo_acto.tipo, TipoActo.OpcionesTipo.CABILDO_GENERAL)

        self.assertEqual(acto_a_editar.fecha, nueva_fecha_acto)
        self.assertEqual(acto_a_editar.inicio_solicitud, nuevo_inicio)
        self.assertEqual(acto_a_editar.fin_solicitud, nuevo_fin)
        
        self.assertIsInstance(acto_actualizado, Acto)



    def test_actualizacion_valida_persiste_cambios_ok(self):
        """
        Test: Actualización válida persiste cambios correctamente.

        Given: Un administrador y un acto existente ("Convivencia febrero").
        When: Se actualizan campos básicos (nombre, lugar, descripción) y 
            la fecha del evento a una nueva posición válida.
        Then: Los cambios deben quedar persistidos en la base de datos tras 
            refrescar la instancia.
        """
        acto_a_editar = self.acto_db_no_papeleta
        nueva_fecha = self.ahora + timedelta(days=45)
        
        payload = {
            "nombre": "Convivencia Post-Cabildo",
            "lugar": "Salón Parroquial Nuevo",
            "descripcion": "Nueva descripción actualizada para el test de persistencia.",
            "fecha": nueva_fecha,
        }

        acto_resultado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.nombre, "Convivencia Post-Cabildo")
        self.assertEqual(acto_a_editar.lugar, "Salón Parroquial Nuevo")
        self.assertEqual(acto_a_editar.descripcion, "Nueva descripción actualizada para el test de persistencia.")
        self.assertEqual(acto_a_editar.fecha, nueva_fecha)

        self.assertEqual(acto_resultado.pk, acto_a_editar.pk)
        self.assertEqual(acto_resultado.nombre, acto_a_editar.nombre)



    def test_fallo_full_clean_no_persiste_cambios_negativo(self):
        """
        Test: Si falla full_clean, no se guarda ningún cambio.

        Given: Un administrador y un acto existente ("Cabildo General 2026").
        When: Se intenta actualizar el nombre (válido) pero se introduce 
            una fecha de fin_solicitud posterior a la del acto (inválido).
        Then: El servicio debe lanzar una ValidationError y, al refrescar 
            desde la BD, el nombre original debe permanecer intacto.
        """
        acto_a_editar = self.acto_db_unificado
        nombre_original = acto_a_editar.nombre
        fecha_acto = acto_a_editar.fecha

        payload = {
            "nombre": "NOMBRE QUE NO DEBE PERSISTIR",
            "fin_solicitud": fecha_acto + timedelta(hours=1)
        }

        with self.assertRaises(DjangoValidationError) as cm:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload
            )

        self.assertIn('fin_solicitud', cm.exception.message_dict)

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.nombre, nombre_original)
        self.assertNotEqual(acto_a_editar.nombre, "NOMBRE QUE NO DEBE PERSISTIR")



    def test_fallo_validacion_duplicidad_acto_permanece_sin_cambios_negativo(self):
        """
        Test: Si falla validación de duplicidad, acto permanece sin cambios.

        Given: Un administrador y dos actos existentes ("A" y "B") en la misma fecha.
        When: Se intenta renombrar el acto "A" para que se llame exactamente 
            como el acto "B" ("Acto existente mismo día").
        Then: El servicio debe lanzar una ValidationError por duplicidad y el 
            acto "A" debe mantener su nombre original en la base de datos.
        """
        acto_a_editar = self.acto_db_unificado 
        nombre_original = acto_a_editar.nombre

        acto_conflicto = self.acto_db_otro_mismo_dia
        nombre_conflictivo = acto_conflicto.nombre
        fecha_conflicto = acto_conflicto.fecha

        payload = {
            "nombre": nombre_conflictivo,
            "fecha": fecha_conflicto
        }

        with self.assertRaises(DjangoValidationError) as cm:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload
            )

        self.assertTrue(
            any("ya existe" in str(v).lower() for v in cm.exception.messages) or 
            'nombre' in cm.exception.message_dict
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.nombre, nombre_original)
        self.assertNotEqual(acto_a_editar.nombre, nombre_conflictivo)



    def test_actualizar_con_campos_identicos_ok(self):
        """
        Test: Actualizar con campos idénticos al valor actual (no cambia nada).

        Given: Un administrador y un acto existente ("Cabildo General 2026").
        When: Se envía un payload con los mismos valores que ya tiene el 
            acto en la base de datos (nombre, lugar, fecha, etc.).
        Then: El servicio debe completarse con éxito, devolviendo el objeto 
            intacto y sin lanzar excepciones de validación o duplicidad.
        """
        acto_original = self.acto_db_unificado

        payload = {
            "nombre": acto_original.nombre,
            "lugar": acto_original.lugar,
            "descripcion": acto_original.descripcion,
            "fecha": acto_original.fecha,
            "tipo_acto_id": acto_original.tipo_acto.id,
            "modalidad": acto_original.modalidad,
            "inicio_solicitud": acto_original.inicio_solicitud,
            "fin_solicitud": acto_original.fin_solicitud,
        }

        acto_resultado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_original.id,
            data_validada=payload
        )

        acto_original.refresh_from_db()
        
        self.assertEqual(acto_resultado.pk, acto_original.pk)
        self.assertEqual(acto_resultado.nombre, "Cabildo General 2026")
        self.assertEqual(acto_resultado.lugar, "Salón de actos")

        self.assertEqual(acto_resultado.fecha, acto_original.fecha)



    def test_actualizar_acto_descripcion_vacia_ok(self):
        """
        Test: Actualizar acto con descripción vacía ("").

        Given: Un administrador y un acto existente que tiene una descripción previa.
        When: Se envía un payload con la 'descripcion' como una cadena vacía.
        Then: El servicio debe actualizar el campo en la base de datos, 
            permitiendo que el acto quede sin descripción.
        """
        acto_a_editar = self.acto_db_unificado
        self.assertIsNotNone(acto_a_editar.descripcion)

        payload = {
            "descripcion": ""
        }

        acto_resultado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.descripcion, "")
        self.assertEqual(acto_resultado.descripcion, "")

        self.assertEqual(acto_a_editar.nombre, "Cabildo General 2026")



    def test_actualizar_acto_descripcion_none_ok(self):
        """
        Test: Actualizar acto con descripcion=None.

        Given: Un administrador y un acto existente ("Cabildo General 2026") 
            que tiene una descripción previa.
        When: Se envía un payload con el campo 'descripcion' explícitamente como None.
        Then: El servicio debe actualizar el registro en la base de datos, 
            dejando el campo descripción como NULL (None en Python).
        """
        acto_a_editar = self.acto_db_unificado
        self.assertIsNotNone(acto_a_editar.descripcion)

        payload = {
            "descripcion": None
        }

        acto_resultado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()
        
        self.assertIsNone(acto_a_editar.descripcion)
        self.assertIsNone(acto_resultado.descripcion)

        self.assertEqual(acto_a_editar.nombre, "Cabildo General 2026")



    def test_actualizar_nombre_vacio_negativo(self):
        """
        Test: Actualizar nombre con string vacío → ValidationError del modelo.

        Given: Un administrador y un acto existente ("Cabildo General 2026").
        When: Se intenta actualizar el 'nombre' enviando una cadena vacía o 
            compuesta solo por espacios ("   ").
        Then: El servicio debe ejecutar el clean() del modelo, lanzar una 
            ValidationError y no persistir el cambio en la BD.
        """
        acto_a_editar = self.acto_db_unificado
        nombre_original = acto_a_editar.nombre

        payload = {
            "nombre": "   "
        }

        with self.assertRaises(DjangoValidationError) as cm:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload
            )

        self.assertIn('nombre', cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict['nombre'][0], 
            "El nombre del acto no puede estar vacío."
        )

        acto_a_editar.refresh_from_db()
        self.assertEqual(acto_a_editar.nombre, nombre_original)



    def test_actualizar_lugar_vacio_negativo(self):
        """
        Test: Actualizar lugar con string vacío → ValidationError del modelo.

        Given: Un administrador y un acto existente ("Cabildo General 2026").
        When: Se intenta actualizar el 'lugar' enviando una cadena vacía o 
            compuesta solo por espacios ("   ").
        Then: El servicio debe ejecutar el clean() del modelo, lanzar una 
            ValidationError y no persistir el cambio en la BD.
        """
        acto_a_editar = self.acto_db_unificado
        lugar_original = acto_a_editar.lugar

        payload = {
            "lugar": "   "
        }

        with self.assertRaises(DjangoValidationError) as cm:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload
            )

        self.assertIn('lugar', cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict['lugar'][0], 
            "El lugar de celebración no puede estar vacío."
        )

        acto_a_editar.refresh_from_db()
        self.assertEqual(acto_a_editar.lugar, lugar_original)



    def test_actualizar_fecha_formato_invalido_negativo(self):
        """
        Test: Actualizar fechas con valores inválidos (string no fecha).

        Given: Un administrador y un acto existente ("Cabildo General 2026").
        When: Se intenta actualizar la 'fecha' enviando un string que no 
            sigue un formato de fecha válido ("esto-no-es-una-fecha").
        Then: El sistema debe lanzar una excepción (ValidationError, TypeError o AttributeError)
            dependiendo de dónde se intercepte el dato crudo, 
            y el acto debe mantener su fecha original.
        """
        acto_a_editar = self.acto_db_unificado
        fecha_original = acto_a_editar.fecha

        payload = {
            "fecha": "esto-no-es-una-fecha"
        }

        with self.assertRaises((DjangoValidationError, TypeError, ValueError, AttributeError)):
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload
            )

        acto_a_editar.refresh_from_db()
        self.assertEqual(acto_a_editar.fecha, fecha_original)



    def test_actualizar_fecha_none_no_permitido_negativo(self):
        """
        Test: Actualizar acto con fecha None si el modelo no lo permite.

        Given: Un administrador y un acto existente ("Cabildo General 2026").
        When: Se intenta actualizar la 'fecha' enviando un valor None.
        Then: El sistema debe lanzar una ValidationError indicando que el 
            campo es obligatorio y el acto debe mantener su fecha original.
        """
        acto_a_editar = self.acto_db_unificado
        fecha_original = acto_a_editar.fecha

        payload = {
            "fecha": None
        }

        with self.assertRaises(DjangoValidationError) as cm:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload
            )

        self.assertIn('fecha', cm.exception.message_dict)

        acto_a_editar.refresh_from_db()
        self.assertEqual(acto_a_editar.fecha, fecha_original)
        self.assertIsNotNone(acto_a_editar.fecha)



    def test_cambio_modalidad_tradicional_fechas_validas_ok(self):
        """
        Test: Cambio de modalidad TRADICIONAL con todas las fechas válidas.

        Given: Un administrador y un acto existente ("Convivencia febrero") 
            que no requería papeleta.
        When: Se cambia el tipo de acto a uno que sí requiere papeleta ("ESTACION_PENITENCIA") 
            y se establece la modalidad "TRADICIONAL" con una secuencia cronológica 
            correcta de sus 4 fechas de solicitud.
        Then: El acto debe actualizarse correctamente, reflejando la nueva 
            modalidad y todas las fechas de solicitud en la base de datos.
        """
        acto_a_editar = self.acto_db_no_papeleta

        fecha_acto = self.ahora + timedelta(days=60)

        insignias_inicio = self.ahora + timedelta(days=10)
        insignias_fin    = self.ahora + timedelta(days=15)
        cirios_inicio    = self.ahora + timedelta(days=16)
        cirios_fin       = self.ahora + timedelta(days=20)

        payload = {
            "tipo_acto_id": self.tipo_con_papeleta.id, 
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "fecha": fecha_acto,
            "inicio_solicitud": insignias_inicio,
            "fin_solicitud": insignias_fin,
            "inicio_solicitud_cirios": cirios_inicio,
            "fin_solicitud_cirios": cirios_fin,
        }

        acto_resultado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.modalidad, Acto.ModalidadReparto.TRADICIONAL)
        self.assertEqual(acto_a_editar.tipo_acto.requiere_papeleta, True)

        self.assertEqual(acto_a_editar.inicio_solicitud, insignias_inicio)
        self.assertEqual(acto_a_editar.fin_solicitud, insignias_fin)
        self.assertEqual(acto_a_editar.inicio_solicitud_cirios, cirios_inicio)
        self.assertEqual(acto_a_editar.fin_solicitud_cirios, cirios_fin)

        self.assertTrue(acto_a_editar.fin_solicitud < acto_a_editar.inicio_solicitud_cirios)
        self.assertTrue(acto_a_editar.fin_solicitud_cirios < acto_a_editar.fecha)



    def test_cambio_modalidad_unificado_fechas_validas_ok(self):
        """
        Test: Cambio de modalidad UNIFICADO con fechas correctas.

        Given: Un administrador y un acto existente ("Convivencia febrero") 
            que no requería papeleta.
        When: Se cambia el tipo de acto a uno con papeleta ("ESTACION_PENITENCIA") 
            y se establece modalidad "UNIFICADO" con fechas de solicitud 
            coherentes (inicio < fin < fecha_acto).
        Then: El acto debe actualizarse, la modalidad debe ser UNIFICADO y 
            las fechas de cirios deben permanecer como None.
        """
        acto_a_editar = self.acto_db_no_papeleta

        fecha_acto = self.ahora + timedelta(days=30)
        solicitud_inicio = self.ahora + timedelta(days=5)
        solicitud_fin    = self.ahora + timedelta(days=15)

        payload = {
            "tipo_acto_id": self.tipo_con_papeleta.id, 
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "fecha": fecha_acto,
            "inicio_solicitud": solicitud_inicio,
            "fin_solicitud": solicitud_fin,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None
        }

        acto_resultado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.modalidad, Acto.ModalidadReparto.UNIFICADO)
        self.assertEqual(acto_a_editar.inicio_solicitud, solicitud_inicio)
        self.assertEqual(acto_a_editar.fin_solicitud, solicitud_fin)

        self.assertIsNone(acto_a_editar.inicio_solicitud_cirios)
        self.assertIsNone(acto_a_editar.fin_solicitud_cirios)

        self.assertTrue(acto_a_editar.fin_solicitud < acto_a_editar.fecha)



    def test_cambio_modalidad_tradicional_sin_fechas_cirios_error(self):
        """
        Test: Cambiar a TRADICIONAL sin definir fechas de cirios → ValidationError.

        Given: Un administrador y un acto existente ("Convivencia febrero") 
            que no requería papeleta.
        When: Se intenta cambiar a modalidad "TRADICIONAL" y a un tipo de acto 
            con papeleta, pero se envían las fechas de cirios como None.
        Then: El servicio debe lanzar un ValidationError indicando que las fechas 
            de inicio y fin de cirios son obligatorias para esta modalidad.
        """
        acto_a_editar = self.acto_db_no_papeleta

        payload = {
            "tipo_acto_id": self.tipo_con_papeleta.id, 
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "fecha": self.ahora + timedelta(days=30),
            "inicio_solicitud": self.ahora + timedelta(days=5),
            "fin_solicitud": self.ahora + timedelta(days=10),
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None
        }

        with self.assertRaises(DjangoValidationError) as cm:
            actualizar_acto_service(
                usuario_solicitante=self.admin,
                acto_id=acto_a_editar.id,
                data_validada=payload
            )

        self.assertIn("inicio_solicitud_cirios", cm.exception.message_dict)
        self.assertIn("fin_solicitud_cirios", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["inicio_solicitud_cirios"][0],
            "El inicio de cirios es obligatorio en modalidad tradicional."
        )



    def test_cambio_modalidad_unificado_limpieza_automatica_ok(self):
        """
        Test: Cambiar a UNIFICADO manteniendo fechas de cirios -> limpieza automática.

        Given: Un administrador y un acto existente ("Convivencia febrero").
        When: Se intenta cambiar a modalidad "UNIFICADO" enviando por error 
            fechas de la segunda fase (cirios).
        Then: El servicio no debe fallar, sino aplicar la normalización, 
            guardar la modalidad UNIFICADO y dejar las fechas de cirios en None.
        """
        acto_a_editar = self.acto_db_no_papeleta

        payload = {
            "tipo_acto_id": self.tipo_con_papeleta.id, 
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "fecha": self.ahora + timedelta(days=30),
            "inicio_solicitud": self.ahora + timedelta(days=5),
            "fin_solicitud": self.ahora + timedelta(days=10),
            "inicio_solicitud_cirios": self.ahora + timedelta(days=11),
            "fin_solicitud_cirios": self.ahora + timedelta(days=15)
        }

        acto_resultado = actualizar_acto_service(
            usuario_solicitante=self.admin,
            acto_id=acto_a_editar.id,
            data_validada=payload
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.modalidad, Acto.ModalidadReparto.UNIFICADO)

        self.assertIsNone(acto_a_editar.inicio_solicitud_cirios)
        self.assertIsNone(acto_a_editar.fin_solicitud_cirios)

        self.assertIsNone(acto_resultado.inicio_solicitud_cirios)
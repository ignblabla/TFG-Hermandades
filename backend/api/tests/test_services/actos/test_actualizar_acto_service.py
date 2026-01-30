from django.http import QueryDict
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from unittest.mock import patch
import datetime
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError

from ....services import _normalizar_payload_acto, actualizar_acto_service
from ....models import Acto, Hermano, TipoActo, TipoPuesto, Puesto
from api.tests.factories import HermanoFactory


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

        # Un segundo tipo con papeleta para testear "cambio de tipo" (bloqueo si hay puestos)
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
            descripcion="Para test de bloqueo de cambio de fecha",
            fecha=self.ahora + timedelta(days=10),
            tipo_acto=self.tipo_con_papeleta,
            modalidad=Acto.ModalidadReparto.UNIFICADO,
            inicio_solicitud=self.ahora - timedelta(days=1),  # ya empezó
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
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,  # el normalizador lo debería limpiar
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



    def test_usuario_no_admin_no_puede_actualizar_acto_permission_denied(self):
        """
        Test: Usuario no admin

        Given: usuario_solicitante.esAdmin=False
        When: llama al service con cualquier payload válido
        Then: PermissionDenied
        """
        payload_valido = {"descripcion": "Cambio permitido solo para admin"}

        with self.assertRaises(PermissionDenied) as ctx:
            actualizar_acto_service(self.hermano, self.acto_db_unificado.id, payload_valido)

        self.assertIn("No tienes permisos para editar actos", str(ctx.exception))



    def test_acto_no_existe_lanza_validation_error(self):
        """
        Test: Acto no existe

        Given: acto_id inexistente
        When: se llama al service
        Then: ValidationError({'detail': 'El acto solicitado no existe.'})
        """
        acto_id_inexistente = 999999
        payload_valido = {"descripcion": "Intento de actualización"}

        with self.assertRaises(DRFValidationError) as ctx:
            actualizar_acto_service(self.admin, acto_id_inexistente, payload_valido)

        exc = ctx.exception
        self.assertIn("detail", exc.detail)
        self.assertEqual(str(exc.detail["detail"]), "El acto solicitado no existe.")



    def _get_non_field_error_msg(self, exc):
        nfe = exc.detail.get("non_field_errors")
        if isinstance(nfe, (list, tuple)):
            return str(nfe[0])
        return str(nfe)

    def test_payload_string_invalido_lanza_validation_error(self):
        """
        Test: Formato inválido (ni dict ni QueryDict) - string

        Given: data_validada="hola"
        When: llama al service
        Then: ValidationError con non_field_errors: "Formato de datos inválido..."
        """
        with self.assertRaises(DRFValidationError) as ctx:
            actualizar_acto_service(self.admin, self.acto_db_unificado.id, "hola")

        msg = self._get_non_field_error_msg(ctx.exception)
        self.assertIn("Formato de datos inválido para actualizar el acto.", msg)



    def test_payload_none_invalido_lanza_validation_error(self):
        """
        Test: Formato inválido (ni dict ni QueryDict) - None

        Given: data_validada=None
        When: llama al service
        Then: ValidationError con non_field_errors: "Formato de datos inválido..."
        """
        with self.assertRaises(DRFValidationError) as ctx:
            actualizar_acto_service(self.admin, self.acto_db_unificado.id, None)

        msg = self._get_non_field_error_msg(ctx.exception)
        self.assertIn("Formato de datos inválido para actualizar el acto.", msg)



    def test_payload_con_valor_lista_lanza_validation_error(self):
        """
        Test: Valor como lista (anti-QueryDict raro / multi-value)

        Given: data_validada={"nombre": ["X"]}
        When: llama al service
        Then: ValidationError con "nombre": "No se permiten múltiples valores..."
        """
        payload_invalido = {
            "nombre": ["X"]
        }

        with self.assertRaises(DRFValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_unificado.id,
                payload_invalido
            )

        exc = ctx.exception

        self.assertIn("nombre", exc.detail)
        self.assertIn(
            "No se permiten múltiples valores",
            str(exc.detail["nombre"])
        )



    def test_payload_con_valor_tuple_lanza_validation_error(self):
        """
        Test: Valor como tuple (anti-QueryDict raro / multi-value)

        Given: data_validada={"nombre": ("X",)}
        When: llama al service
        Then: ValidationError con "nombre": "No se permiten múltiples valores..."
        """
        payload_invalido = {
            "nombre": ("X",)
        }

        with self.assertRaises(DRFValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_unificado.id,
                payload_invalido
            )

        exc = ctx.exception

        self.assertIn("nombre", exc.detail)
        self.assertIn(
            "No se permiten múltiples valores",
            str(exc.detail["nombre"])
        )



    def test_payload_con_clave_desconocida_lanza_validation_error(self):
        """
        Test: Claves desconocidas (lista blanca estricta)

        Given: payload incluye "foo": "bar"
        When: llama al service
        Then: ValidationError con non_field_errors indicando campos no permitidos
        """
        payload_invalido = {
            "foo": "bar"
        }

        with self.assertRaises(DRFValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_unificado.id,
                payload_invalido
            )

        exc = ctx.exception
        msg = self._get_non_field_error_msg(exc)

        self.assertIn("Payload inválido", msg)
        self.assertIn("campos no permitidos", msg)
        self.assertIn("foo", msg)



    def test_tipo_acto_y_tipo_acto_id_no_coinciden_lanza_validation_error(self):
        """
        Test: Vienen ambos y no coinciden

        Given: tipo_acto=<TipoActo id=1>, tipo_acto_id=2
        When: llama al service
        Then: ValidationError con keys tipo_acto y tipo_acto_id
        """
        payload_invalido = {
            "tipo_acto": self.tipo_con_papeleta,
            "tipo_acto_id": self.tipo_con_papeleta_alt.id
        }

        with self.assertRaises(DRFValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_unificado.id,
                payload_invalido
            )

        exc = ctx.exception

        self.assertIn("tipo_acto", exc.detail)
        self.assertIn("tipo_acto_id", exc.detail)

        self.assertIn(
            "Ambigüedad",
            str(exc.detail["tipo_acto"])
        )
        self.assertIn(
            "Ambigüedad",
            str(exc.detail["tipo_acto_id"])
        )



    def test_tipo_acto_no_instancia_y_tipo_acto_id_lanza_validation_error(self):
        """
        Test: tipo_acto viene pero no es instancia y además viene tipo_acto_id

        Given: tipo_acto=1 y tipo_acto_id=1
        When: llama al service
        Then: ValidationError({"tipo_acto": "tipo_acto debe ser una instancia..."})
        """
        payload_invalido = {
            "tipo_acto": 1,
            "tipo_acto_id": 1
        }

        with self.assertRaises(DRFValidationError) as ctx:
            actualizar_acto_service(self.admin, self.acto_db_unificado.id, payload_invalido)

        exc = ctx.exception
        self.assertIn("tipo_acto", exc.detail)
        self.assertIn(
            "tipo_acto debe ser una instancia de TipoActo",
            str(exc.detail["tipo_acto"])
        )



    def test_tipo_acto_id_inexistente_lanza_validation_error(self):
        """
        Test: tipo_acto_id no existe

        Given: tipo_acto_id=999
        When: llama al service
        Then: ValidationError({"tipo_acto": "El tipo de acto indicado no existe."})
        """
        payload_invalido = {
            "tipo_acto_id": 999
        }

        with self.assertRaises(DRFValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_unificado.id,
                payload_invalido
            )

        exc = ctx.exception
        self.assertIn("tipo_acto", exc.detail)
        self.assertEqual(
            str(exc.detail["tipo_acto"]),
            "El tipo de acto indicado no existe."
        )



    def test_existe_otro_acto_con_mismo_nombre_y_misma_fecha_lanza_validation_error(self):
        """
        Test: Existe otro acto con mismo nombre y misma fecha (día)

        Given:
            - Acto A (a actualizar)
            - Acto B ya existe con nombre="X" y fecha__date=YYYY-MM-DD
        When:
            - se actualiza A con nombre="X" y fecha en ese mismo día
        Then:
            - ValidationError con mensaje plano:
                "Ya existe otro acto llamado 'X' en esa fecha."
        """
        payload_invalido = {
            "nombre": self.acto_db_otro_mismo_dia.nombre,
            "fecha": self.acto_db_otro_mismo_dia.fecha,
        }

        with self.assertRaises(DRFValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_unificado.id,
                payload_invalido
            )

        exc = ctx.exception

        msg = str(exc.detail)

        self.assertIn("Ya existe otro acto llamado", msg)
        self.assertIn(self.acto_db_otro_mismo_dia.nombre, msg)
        self.assertIn("en esa fecha", msg)



    def test_existe_otro_acto_con_mismo_nombre_y_mismo_dia_lanza_validation_error(self):
        """
        Test: Existe otro acto con mismo nombre y mismo día (distinto PK) -> debe fallar

        Given:
            - Acto A (a actualizar)
            - Acto B (PK distinto) ya existe con nombre="X" y fecha en el mismo día
        When:
            - actualizo A con nombre="X" y fecha en ese mismo día
        Then:
            - ValidationError: "Ya existe otro acto llamado 'X' en esa fecha."
        """
        acto_a = self.acto_db_unificado
        acto_b = self.acto_db_otro_mismo_dia

        self.assertNotEqual(acto_a.id, acto_b.id)

        payload_invalido = {
            "nombre": acto_b.nombre,
            "fecha": acto_b.fecha,
        }

        with self.assertRaises(DRFValidationError) as ctx:
            actualizar_acto_service(self.admin, acto_a.id, payload_invalido)

        msg = str(ctx.exception.detail)
        self.assertIn("Ya existe otro acto llamado", msg)
        self.assertIn(acto_b.nombre, msg)
        self.assertIn("en esa fecha", msg)



    def test_cambiar_tipo_acto_con_puestos_lanza_validation_error(self):
        """
        Test: Cambiar tipo_acto cuando ya hay puestos

        Given:
            - acto tiene puestos_disponibles.exists() == True
        When:
            - payload cambia tipo_acto / tipo_acto_id
        Then:
            - ValidationError({"tipo_acto": "No se puede cambiar..."})
        """
        self.assertTrue(self.acto_db_tradicional.puestos_disponibles.exists())

        payload_invalido = {
            "tipo_acto_id": self.tipo_con_papeleta_alt.id
        }

        with self.assertRaises(DRFValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_tradicional.id,
                payload_invalido
            )

        exc = ctx.exception
        self.assertIn("tipo_acto", exc.detail)
        self.assertIn(
            "No se puede cambiar el Tipo de Acto",
            str(exc.detail["tipo_acto"])
        )



    def test_cambiar_fecha_con_plazo_ya_iniciado_lanza_validation_error(self):
        """
        Test: Cambiar fecha cuando now >= acto.inicio_solicitud

        Given:
            - acto.inicio_solicitud = now - 1h
        When:
            - payload cambia fecha
        Then:
            - ValidationError en "fecha" con mensaje indicando que el plazo ya ha comenzado
        """
        nueva_fecha = self.acto_con_plazo_iniciado.fecha + timedelta(days=1)

        payload_invalido = {
            "fecha": nueva_fecha
        }

        with self.assertRaises(DRFValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_con_plazo_iniciado.id,
                payload_invalido
            )

        exc = ctx.exception

        self.assertIn("fecha", exc.detail)
        msg = str(exc.detail["fecha"])

        self.assertIn("plazo de solicitud ya ha comenzado", msg)



    def test_cambiar_fecha_e_intentar_mover_inicio_solicitud_al_futuro_lanza_validation_error_con_sufijo_anti_bypass(self):
        """
        Test: Cambiar fecha + intentar mover inicio_solicitud al futuro (anti-bypass)

        Given: acto.inicio_solicitud = now - 1h
        When: payload incluye fecha=nueva y inicio_solicitud=now+10d
        Then: ValidationError en "fecha" y que el mensaje incluya el sufijo anti-bypass
        """
        self.assertIsNotNone(self.acto_con_plazo_iniciado.inicio_solicitud)
        self.assertLessEqual(self.acto_con_plazo_iniciado.inicio_solicitud, self.ahora)

        payload_invalido = {
            "fecha": self.acto_con_plazo_iniciado.fecha + timedelta(days=1),
            "inicio_solicitud": self.ahora + timedelta(days=10),
        }

        with self.assertRaises(DRFValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_con_plazo_iniciado.id,
                payload_invalido
            )

        exc = ctx.exception

        self.assertIn("fecha", exc.detail)

        msg = str(exc.detail["fecha"])
        self.assertIn("plazo de solicitud ya ha comenzado", msg)
        self.assertIn("no se puede esquivar modificando inicio_solicitud", msg)



    def test_cambiar_fecha_en_acto_sin_papeleta_no_se_bloquea_por_validar_cambio_fecha(self):
        """
        Test: Cambiar fecha en acto que NO requiere papeleta

        Given: acto.tipo_acto.requiere_papeleta = False
        When: payload cambia fecha
        Then: NO falla por _validar_cambio_fecha (actualiza correctamente)
        """
        acto = self.acto_db_no_papeleta
        nueva_fecha = acto.fecha + timedelta(days=1)

        acto_actualizado = actualizar_acto_service(
            self.admin,
            acto.id,
            {"fecha": nueva_fecha}
        )

        self.assertEqual(acto_actualizado.id, acto.id)
        self.assertEqual(acto_actualizado.fecha, nueva_fecha)

        self.assertIsNone(acto_actualizado.modalidad)
        self.assertIsNone(acto_actualizado.inicio_solicitud)
        self.assertIsNone(acto_actualizado.fin_solicitud)
        self.assertIsNone(acto_actualizado.inicio_solicitud_cirios)
        self.assertIsNone(acto_actualizado.fin_solicitud_cirios)



    def test_nombre_solo_espacios_lanza_validation_error(self):
        """
        Test: Nombre vacío o solo espacios

        When: payload {"nombre": " "}
        Then: ValidationError con "nombre"
        """
        payload_invalido = {"nombre": "   "}

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(self.admin, self.acto_db_unificado.id, payload_invalido)

        exc = ctx.exception
        self.assertIn("nombre", exc.message_dict)
        self.assertIn("no puede estar vacío", exc.message_dict["nombre"][0])



    def test_requiere_papeleta_y_modalidad_nula_lanza_validation_error(self):
        """
        Test: Requiere papeleta pero falta modalidad (UPDATE)

        Given: acto con tipo_con_papeleta (requiere_papeleta=True)
        When: payload {"modalidad": None}
        Then: ValidationError con "modalidad": "La modalidad es obligatoria..."
        """
        self.assertTrue(self.acto_db_unificado.tipo_acto.requiere_papeleta)

        payload_invalido = {"modalidad": None}

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(self.admin, self.acto_db_unificado.id, payload_invalido)

        self.assertIn("modalidad", ctx.exception.message_dict)
        self.assertIn(
            "La modalidad es obligatoria para actos con papeleta.",
            ctx.exception.message_dict["modalidad"]
        )



    def test_admin_actualiza_acto_con_papeleta_sin_inicio_solicitud_falla(self):
        """
        Test: Falta inicio_solicitud (UPDATE)

        Given: acto.tipo_acto.requiere_papeleta = True.
        When: payload setea inicio_solicitud=None.
        Then: ValidationError con error en 'inicio_solicitud'.
        """
        self.assertTrue(self.acto_db_unificado.tipo_acto.requiere_papeleta)

        payload_invalido = {
            "inicio_solicitud": None
        }

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(self.admin, self.acto_db_unificado.id, payload_invalido)

        self.assertIn("inicio_solicitud", ctx.exception.message_dict)
        self.assertIn(
            "El inicio de solicitud es obligatorio.",
            ctx.exception.message_dict["inicio_solicitud"]
        )



    def test_admin_actualiza_acto_con_papeleta_sin_fin_solicitud_falla(self):
        """
        Test: Requiere papeleta pero falta fin_solicitud (UPDATE)

        Given: acto.tipo_acto.requiere_papeleta = True
        When: payload setea fin_solicitud=None
        Then: ValidationError con error en 'fin_solicitud'
        """
        self.assertTrue(self.acto_db_unificado.tipo_acto.requiere_papeleta)

        payload_invalido = {
            "fin_solicitud": None
        }

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_unificado.id,
                payload_invalido
            )

        self.assertIn("fin_solicitud", ctx.exception.message_dict)
        self.assertIn(
            "El fin de solicitud es obligatorio.",
            ctx.exception.message_dict["fin_solicitud"]
        )



    def test_admin_actualiza_acto_inicio_solicitud_mayor_o_igual_que_fin_solicitud_falla(self):
        """
        Test: inicio_solicitud >= fin_solicitud (UPDATE)

        Given: acto requiere papeleta y tiene modalidad válida
        When: payload pone inicio_solicitud == fin_solicitud (o inicio > fin)
        Then: ValidationError en 'fin_solicitud'
        """
        self.assertTrue(self.acto_db_unificado.tipo_acto.requiere_papeleta)

        payload_invalido = {
            "inicio_solicitud": self.inicio_insignias,
            "fin_solicitud": self.inicio_insignias,
        }

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_unificado.id,
                payload_invalido
            )

        self.assertIn("fin_solicitud", ctx.exception.message_dict)
        self.assertIn(
            "posterior al inicio",
            ctx.exception.message_dict["fin_solicitud"][0]
        )


    def test_admin_actualiza_acto_inicio_solicitud_mayor_que_fin_solicitud_falla(self):
        """
        Test: inicio_solicitud > fin_solicitud (UPDATE)

        Given: acto requiere papeleta y tiene modalidad válida
        When: payload pone inicio_solicitud > fin_solicitud
        Then: ValidationError en 'fin_solicitud'
        """
        payload_invalido = {
            "inicio_solicitud": self.fin_insignias + timedelta(hours=1),
            "fin_solicitud": self.fin_insignias,
        }

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_unificado.id,
                payload_invalido
            )

        self.assertIn("fin_solicitud", ctx.exception.message_dict)
        self.assertIn(
            "posterior al inicio",
            ctx.exception.message_dict["fin_solicitud"][0]
        )



    def test_admin_actualiza_acto_inicio_solicitud_igual_o_posterior_a_fecha_acto_falla(self):
        """
        Test: inicio_solicitud >= fecha del acto (UPDATE)

        Given: acto requiere papeleta y tiene modalidad válida
        When: payload pone inicio_solicitud igual o posterior a la fecha del acto
        Then: ValidationError en 'inicio_solicitud'
        """
        self.assertTrue(self.acto_db_unificado.tipo_acto.requiere_papeleta)

        payload_invalido = {
            "inicio_solicitud": self.acto_db_unificado.fecha,
        }

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_unificado.id,
                payload_invalido
            )

        self.assertIn("inicio_solicitud", ctx.exception.message_dict)
        self.assertIn(
            "no puede ser igual o posterior a la fecha del acto",
            ctx.exception.message_dict["inicio_solicitud"][0]
        )


    def test_admin_actualiza_acto_inicio_solicitud_posterior_a_fecha_acto_falla(self):
        """
        Test: inicio_solicitud > fecha del acto (UPDATE)

        Given: acto requiere papeleta y tiene modalidad válida
        When: payload pone inicio_solicitud posterior a la fecha del acto
        Then: ValidationError en 'inicio_solicitud'
        """
        payload_invalido = {
            "inicio_solicitud": self.acto_db_unificado.fecha + timedelta(hours=1),
        }

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_unificado.id,
                payload_invalido
            )

        self.assertIn("inicio_solicitud", ctx.exception.message_dict)
        self.assertIn(
            "no puede ser igual o posterior a la fecha del acto",
            ctx.exception.message_dict["inicio_solicitud"][0]
        )



    def test_admin_actualiza_acto_fin_solicitud_posterior_a_fecha_acto_falla(self):
        """
        Test: fin_solicitud > fecha del acto (UPDATE)

        Given: acto requiere papeleta y tiene modalidad válida
        When: payload pone fin_solicitud posterior a la fecha del acto
        Then: ValidationError en 'fin_solicitud'
        """
        self.assertTrue(self.acto_db_unificado.tipo_acto.requiere_papeleta)

        payload_invalido = {
            "fin_solicitud": self.acto_db_unificado.fecha + timedelta(hours=1),
        }

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_unificado.id,
                payload_invalido
            )

        self.assertIn("fin_solicitud", ctx.exception.message_dict)
        self.assertIn(
            "no puede ser posterior a la fecha del acto",
            ctx.exception.message_dict["fin_solicitud"][0]
        )



    def test_admin_actualiza_acto_tradicional_sin_inicio_solicitud_cirios_falla(self):
        """
        Test: Modalidad TRADICIONAL sin inicio_solicitud_cirios (UPDATE)

        Given: acto requiere papeleta
        When: payload {"modalidad": TRADICIONAL, "inicio_solicitud_cirios": None}
        Then: ValidationError en 'inicio_solicitud_cirios'
        """
        self.assertTrue(self.acto_db_unificado.tipo_acto.requiere_papeleta)

        payload_invalido = {
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud_cirios": None,
        }

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_unificado.id,
                payload_invalido
            )

        self.assertIn("inicio_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn(
            "El inicio de cirios es obligatorio en modalidad tradicional.",
            ctx.exception.message_dict["inicio_solicitud_cirios"]
        )


    def test_admin_actualiza_acto_tradicional_sin_fin_solicitud_cirios_falla(self):
        """
        Test: Modalidad TRADICIONAL sin fin_solicitud_cirios (UPDATE)

        Given: acto requiere papeleta
        When: payload {"modalidad": TRADICIONAL, "fin_solicitud_cirios": None}
        Then: ValidationError en 'fin_solicitud_cirios'
        """
        payload_invalido = {
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "fin_solicitud_cirios": None,
        }

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_unificado.id,
                payload_invalido
            )

        self.assertIn("fin_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn(
            "El fin de cirios es obligatorio en modalidad tradicional.",
            ctx.exception.message_dict["fin_solicitud_cirios"]
        )



    def test_admin_actualiza_acto_tradicional_inicio_cirios_mayor_o_igual_fin_cirios_falla(self):
        """
        Test: TRADICIONAL con inicio_solicitud_cirios >= fin_solicitud_cirios (UPDATE)

        Given: acto requiere papeleta y modalidad TRADICIONAL
        When: inicio_solicitud_cirios >= fin_solicitud_cirios
        Then: ValidationError en 'fin_solicitud_cirios'
        """
        self.assertTrue(self.acto_db_tradicional.tipo_acto.requiere_papeleta)
        self.assertEqual(self.acto_db_tradicional.modalidad, Acto.ModalidadReparto.TRADICIONAL)

        payload_invalido = {
            "inicio_solicitud_cirios": self.inicio_cirios,
            "fin_solicitud_cirios": self.inicio_cirios,
        }

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_tradicional.id,
                payload_invalido
            )

        self.assertIn("fin_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn(
            "posterior al inicio",
            ctx.exception.message_dict["fin_solicitud_cirios"][0]
        )


    def test_admin_actualiza_acto_tradicional_inicio_cirios_mayor_fin_cirios_falla(self):
        """
        Test: TRADICIONAL con inicio_solicitud_cirios > fin_solicitud_cirios (UPDATE)

        Given: acto requiere papeleta y modalidad TRADICIONAL
        When: inicio_solicitud_cirios > fin_solicitud_cirios
        Then: ValidationError en 'fin_solicitud_cirios'
        """
        payload_invalido = {
            "inicio_solicitud_cirios": self.fin_cirios + timedelta(hours=1),
            "fin_solicitud_cirios": self.fin_cirios,
        }

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_tradicional.id,
                payload_invalido
            )

        self.assertIn("fin_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn(
            "posterior al inicio",
            ctx.exception.message_dict["fin_solicitud_cirios"][0]
        )



    def test_admin_actualiza_acto_tradicional_inicio_cirios_igual_o_posterior_a_fecha_acto_falla(self):
        """
        Test: TRADICIONAL con inicio_solicitud_cirios >= fecha del acto (UPDATE)

        Given: acto requiere papeleta y modalidad TRADICIONAL
        When: inicio_solicitud_cirios == fecha del acto (o posterior)
        Then: ValidationError en 'inicio_solicitud_cirios'
        """
        self.assertTrue(self.acto_db_tradicional.tipo_acto.requiere_papeleta)
        self.assertEqual(self.acto_db_tradicional.modalidad, Acto.ModalidadReparto.TRADICIONAL)

        payload_invalido = {
            "inicio_solicitud_cirios": self.acto_db_tradicional.fecha,
        }

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_tradicional.id,
                payload_invalido
            )

        self.assertIn("inicio_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn(
            "no puede ser igual o posterior a la fecha del acto",
            ctx.exception.message_dict["inicio_solicitud_cirios"][0]
        )


    def test_admin_actualiza_acto_tradicional_inicio_cirios_posterior_a_fecha_acto_falla(self):
        """
        Test: TRADICIONAL con inicio_solicitud_cirios > fecha del acto (UPDATE)

        Given: acto requiere papeleta y modalidad TRADICIONAL
        When: inicio_solicitud_cirios posterior a la fecha del acto
        Then: ValidationError en 'inicio_solicitud_cirios'
        """
        payload_invalido = {
            "inicio_solicitud_cirios": self.acto_db_tradicional.fecha + timedelta(hours=1),
        }

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_tradicional.id,
                payload_invalido
            )

        self.assertIn("inicio_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn(
            "no puede ser igual o posterior a la fecha del acto",
            ctx.exception.message_dict["inicio_solicitud_cirios"][0]
        )



    def test_admin_actualiza_acto_tradicional_fin_cirios_posterior_a_fecha_acto_falla(self):
        """
        Test: TRADICIONAL con fin_solicitud_cirios > fecha del acto (UPDATE)

        Given: acto requiere papeleta y modalidad TRADICIONAL
        When: fin_solicitud_cirios posterior a la fecha del acto
        Then: ValidationError en 'fin_solicitud_cirios'
        """
        self.assertTrue(self.acto_db_tradicional.tipo_acto.requiere_papeleta)
        self.assertEqual(self.acto_db_tradicional.modalidad, Acto.ModalidadReparto.TRADICIONAL)

        payload_invalido = {
            "fin_solicitud_cirios": self.acto_db_tradicional.fecha + timedelta(hours=1),
        }

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(
                self.admin,
                self.acto_db_tradicional.id,
                payload_invalido
            )

        self.assertIn("fin_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn(
            "no puede ser posterior a la fecha del acto",
            ctx.exception.message_dict["fin_solicitud_cirios"][0]
        )



    def test_admin_actualiza_acto_tradicional_fases_mal_ordenadas_fin_insignias_mayor_o_igual_inicio_cirios_falla(self):
        """
        Test: TRADICIONAL: fases mal ordenadas (UPDATE)

        Given: fin_solicitud >= inicio_solicitud_cirios (cirios empieza antes o igual que termina insignias)
        When: payload deja fin_solicitud >= inicio_solicitud_cirios
        Then: ValidationError en 'inicio_solicitud_cirios'
            ("El período de cirios debe comenzar después de finalizar el de insignias.")
        """
        self.assertTrue(self.acto_db_tradicional.tipo_acto.requiere_papeleta)
        self.assertEqual(self.acto_db_tradicional.modalidad, Acto.ModalidadReparto.TRADICIONAL)

        payload_invalido = {
            "fin_solicitud": self.inicio_cirios,
            "inicio_solicitud_cirios": self.inicio_cirios,
            "fin_solicitud_cirios": self.fin_cirios,
        }

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(self.admin, self.acto_db_tradicional.id, payload_invalido)

        self.assertIn("inicio_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn(
            "El período de cirios debe comenzar después de finalizar el de insignias.",
            ctx.exception.message_dict["inicio_solicitud_cirios"][0]
        )


    def test_admin_actualiza_acto_tradicional_fases_mal_ordenadas_fin_insignias_mayor_inicio_cirios_falla(self):
        """
        Test: TRADICIONAL: fases mal ordenadas (UPDATE) - fin_insignias > inicio_cirios

        Given: fin_solicitud > inicio_solicitud_cirios
        Then: ValidationError en 'inicio_solicitud_cirios'
        """
        payload_invalido = {
            "fin_solicitud": self.inicio_cirios + timedelta(hours=1),
            "inicio_solicitud_cirios": self.inicio_cirios,
            "fin_solicitud_cirios": self.fin_cirios,
        }

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(self.admin, self.acto_db_tradicional.id, payload_invalido)

        self.assertIn("inicio_solicitud_cirios", ctx.exception.message_dict)
        self.assertIn(
            "El período de cirios debe comenzar después de finalizar el de insignias.",
            ctx.exception.message_dict["inicio_solicitud_cirios"][0]
        )



    def test_admin_actualiza_acto_unificado_con_fechas_cirios_y_service_limpia(self):
        """
        Test: UNIFICADO pero vienen fechas de cirios (UPDATE)

        Given: payload incluye modalidad=UNIFICADO y fechas de cirios
        When: se llama al service
        Then: NO lanza excepción y el service limpia inicio_solicitud_cirios/fin_solicitud_cirios
        """
        payload = {
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud_cirios": self.ahora + timedelta(days=1),
            "fin_solicitud_cirios": self.ahora + timedelta(days=2),
        }

        acto_actualizado = actualizar_acto_service(self.admin, self.acto_db_unificado.id, payload)

        self.assertEqual(acto_actualizado.modalidad, Acto.ModalidadReparto.UNIFICADO)
        self.assertIsNone(acto_actualizado.inicio_solicitud_cirios)
        self.assertIsNone(acto_actualizado.fin_solicitud_cirios)



    def test_admin_cambia_a_tipo_sin_papeleta_y_service_limpia_modalidad_y_plazos(self):
        """
        Test: Cambiar a tipo_acto que NO requiere papeleta pero mandas modalidad o fechas (UPDATE)

        Given: acto actual requiere papeleta
        When: payload incluye tipo_acto_id (sin papeleta) + modalidad + fechas
        Then: no lanza excepción y el acto queda normalizado (modalidad y plazos a None)
        """
        self.assertTrue(self.acto_db_unificado.tipo_acto.requiere_papeleta)

        payload = {
            "tipo_acto_id": self.tipo_no_papeleta.id,
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
            "inicio_solicitud": self.inicio_insignias,
            "fin_solicitud": self.fin_insignias,
            "inicio_solicitud_cirios": self.inicio_cirios,
            "fin_solicitud_cirios": self.fin_cirios,
        }

        acto_actualizado = actualizar_acto_service(self.admin, self.acto_db_unificado.id, payload)

        self.assertEqual(acto_actualizado.tipo_acto_id, self.tipo_no_papeleta.id)

        self.assertIsNone(acto_actualizado.modalidad)
        self.assertIsNone(acto_actualizado.inicio_solicitud)
        self.assertIsNone(acto_actualizado.fin_solicitud)
        self.assertIsNone(acto_actualizado.inicio_solicitud_cirios)
        self.assertIsNone(acto_actualizado.fin_solicitud_cirios)



    def test_admin_actualiza_solo_descripcion_y_el_resto_permanece_igual(self):
        """
        Test: Actualizar solo descripcion

        When: payload {"descripcion": "Nueva"}
        Then: el acto se actualiza y el resto de campos permanece igual
        """
        acto_original = self.acto_db_unificado

        payload = {
            "descripcion": "Nueva descripción del acto"
        }

        acto_actualizado = actualizar_acto_service(
            self.admin,
            acto_original.id,
            payload
        )

        self.assertEqual(acto_actualizado.descripcion, "Nueva descripción del acto")

        self.assertEqual(acto_actualizado.nombre, acto_original.nombre)
        self.assertEqual(acto_actualizado.fecha, acto_original.fecha)
        self.assertEqual(acto_actualizado.tipo_acto_id, acto_original.tipo_acto_id)
        self.assertEqual(acto_actualizado.modalidad, acto_original.modalidad)
        self.assertEqual(acto_actualizado.inicio_solicitud, acto_original.inicio_solicitud)
        self.assertEqual(acto_actualizado.fin_solicitud, acto_original.fin_solicitud)
        self.assertEqual(acto_actualizado.inicio_solicitud_cirios, acto_original.inicio_solicitud_cirios)
        self.assertEqual(acto_actualizado.fin_solicitud_cirios, acto_original.fin_solicitud_cirios)



    def test_admin_actualiza_nombre_sin_colision_de_unicidad(self):
        """
        Test: Actualizar nombre manteniendo unicidad

        When: payload {"nombre": "Nombre nuevo"} sin colisión (mismo día)
        Then: actualización correcta
        """
        acto_original = self.acto_db_unificado
        nombre_nuevo = "Nombre nuevo sin colisión"

        self.assertFalse(
            Acto.objects.filter(
                nombre=nombre_nuevo,
                fecha__date=acto_original.fecha.date()
            ).exclude(pk=acto_original.id).exists()
        )

        payload = {
            "nombre": nombre_nuevo
        }

        acto_actualizado = actualizar_acto_service(
            self.admin,
            acto_original.id,
            payload
        )

        self.assertEqual(acto_actualizado.nombre, nombre_nuevo)

        self.assertEqual(acto_actualizado.fecha, acto_original.fecha)
        self.assertEqual(acto_actualizado.tipo_acto_id, acto_original.tipo_acto_id)
        self.assertEqual(acto_actualizado.modalidad, acto_original.modalidad)
        self.assertEqual(acto_actualizado.inicio_solicitud, acto_original.inicio_solicitud)
        self.assertEqual(acto_actualizado.fin_solicitud, acto_original.fin_solicitud)
        self.assertEqual(acto_actualizado.inicio_solicitud_cirios, acto_original.inicio_solicitud_cirios)
        self.assertEqual(acto_actualizado.fin_solicitud_cirios, acto_original.fin_solicitud_cirios)



    def test_admin_actualiza_fecha_cuando_plazo_aun_no_ha_empezado_ok(self):
        """
        Test: Actualizar fecha cuando aún NO ha empezado el plazo

        Given: acto.inicio_solicitud = now + 2d
        When: payload cambia fecha a más adelante (coherente con plazos)
        Then: actualización correcta
        """
        acto_original = self.acto_db_unificado

        self.assertGreater(acto_original.inicio_solicitud, self.ahora)

        nueva_fecha = acto_original.fecha + timedelta(days=5)

        payload = {
            "fecha": nueva_fecha
        }

        acto_actualizado = actualizar_acto_service(
            self.admin,
            acto_original.id,
            payload
        )

        self.assertEqual(acto_actualizado.fecha, nueva_fecha)

        self.assertEqual(acto_actualizado.nombre, acto_original.nombre)
        self.assertEqual(acto_actualizado.tipo_acto_id, acto_original.tipo_acto_id)
        self.assertEqual(acto_actualizado.modalidad, acto_original.modalidad)
        self.assertEqual(acto_actualizado.inicio_solicitud, acto_original.inicio_solicitud)
        self.assertEqual(acto_actualizado.fin_solicitud, acto_original.fin_solicitud)
        self.assertEqual(acto_actualizado.inicio_solicitud_cirios, acto_original.inicio_solicitud_cirios)
        self.assertEqual(acto_actualizado.fin_solicitud_cirios, acto_original.fin_solicitud_cirios)



    def test_admin_actualiza_solo_fin_solicitud_manteniendo_coherencia_ok(self):
        """
        Test: Actualizar solo fin_solicitud (manteniendo coherencia)

        When: fin_solicitud se mueve pero sigue siendo > inicio_solicitud
            y <= fecha del acto
        Then: actualización correcta
        """
        acto_original = self.acto_db_unificado

        self.assertTrue(acto_original.tipo_acto.requiere_papeleta)
        self.assertLess(acto_original.inicio_solicitud, acto_original.fin_solicitud)
        self.assertLessEqual(acto_original.fin_solicitud, acto_original.fecha)

        nueva_fin = acto_original.fin_solicitud + timedelta(hours=12)
        self.assertGreater(nueva_fin, acto_original.inicio_solicitud)
        self.assertLessEqual(nueva_fin, acto_original.fecha)

        payload = {
            "fin_solicitud": nueva_fin
        }

        acto_actualizado = actualizar_acto_service(
            self.admin,
            acto_original.id,
            payload
        )

        self.assertEqual(acto_actualizado.fin_solicitud, nueva_fin)

        self.assertEqual(acto_actualizado.inicio_solicitud, acto_original.inicio_solicitud)
        self.assertEqual(acto_actualizado.fecha, acto_original.fecha)
        self.assertEqual(acto_actualizado.nombre, acto_original.nombre)
        self.assertEqual(acto_actualizado.tipo_acto_id, acto_original.tipo_acto_id)
        self.assertEqual(acto_actualizado.modalidad, acto_original.modalidad)
        self.assertEqual(acto_actualizado.inicio_solicitud_cirios, acto_original.inicio_solicitud_cirios)
        self.assertEqual(acto_actualizado.fin_solicitud_cirios, acto_original.fin_solicitud_cirios)



    def test_admin_cambia_de_tradicional_a_unificado_y_service_limpia_fechas_cirios(self):
        """
        Test: Cambiar de TRADICIONAL a UNIFICADO y enviar cirios (se limpian)

        Given: acto TRADICIONAL válido
        When: payload {"modalidad": UNIFICADO, "inicio_solicitud_cirios": X, "fin_solicitud_cirios": Y}
        Then: OK y en BD inicio_solicitud_cirios is None y fin_solicitud_cirios is None
        """
        acto_original = self.acto_db_tradicional

        self.assertEqual(acto_original.modalidad, Acto.ModalidadReparto.TRADICIONAL)
        self.assertIsNotNone(acto_original.inicio_solicitud_cirios)
        self.assertIsNotNone(acto_original.fin_solicitud_cirios)

        payload = {
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud_cirios": self.ahora + timedelta(days=1),
            "fin_solicitud_cirios": self.ahora + timedelta(days=2),
        }

        acto_actualizado = actualizar_acto_service(self.admin, acto_original.id, payload)

        self.assertEqual(acto_actualizado.modalidad, Acto.ModalidadReparto.UNIFICADO)

        self.assertIsNone(acto_actualizado.inicio_solicitud_cirios)
        self.assertIsNone(acto_actualizado.fin_solicitud_cirios)

        acto_refrescado = Acto.objects.get(pk=acto_original.id)
        self.assertIsNone(acto_refrescado.inicio_solicitud_cirios)
        self.assertIsNone(acto_refrescado.fin_solicitud_cirios)



    def test_admin_cambia_de_tradicional_a_unificado_sin_tocar_cirios_y_service_limpia(self):
        """
        Test: Cambiar de TRADICIONAL a UNIFICADO sin tocar cirios

        Given: acto TRADICIONAL válido (con fechas de cirios en BD)
        When: payload {"modalidad": UNIFICADO} (no se envían campos de cirios)
        Then: OK y en BD inicio_solicitud_cirios y fin_solicitud_cirios quedan a None
            por normalización del service
        """
        acto_original = self.acto_db_tradicional

        self.assertEqual(acto_original.modalidad, Acto.ModalidadReparto.TRADICIONAL)
        self.assertIsNotNone(acto_original.inicio_solicitud_cirios)
        self.assertIsNotNone(acto_original.fin_solicitud_cirios)

        payload = {
            "modalidad": Acto.ModalidadReparto.UNIFICADO
        }

        acto_actualizado = actualizar_acto_service(
            self.admin,
            acto_original.id,
            payload
        )

        self.assertEqual(acto_actualizado.modalidad, Acto.ModalidadReparto.UNIFICADO)

        self.assertIsNone(acto_actualizado.inicio_solicitud_cirios)
        self.assertIsNone(acto_actualizado.fin_solicitud_cirios)

        acto_refrescado = Acto.objects.get(pk=acto_original.id)
        self.assertIsNone(acto_refrescado.inicio_solicitud_cirios)
        self.assertIsNone(acto_refrescado.fin_solicitud_cirios)



    def test_admin_cambia_a_tipo_sin_papeleta_y_service_limpia_modalidad_y_todos_los_plazos(self):
        """
        Test: Cambiar a tipo_acto que NO requiere papeleta (limpia todo)

        Given: acto con papeleta (tiene modalidad y fechas) y NO tiene puestos
        When: payload {"tipo_acto_id": tipo_sin_papeleta}
        Then: OK y en BD:
            - modalidad is None
            - inicio_solicitud/fin_solicitud is None
            - inicio_solicitud_cirios/fin_solicitud_cirios is None
        """
        acto_original = self.acto_db_unificado

        self.assertTrue(acto_original.tipo_acto.requiere_papeleta)
        self.assertFalse(acto_original.puestos_disponibles.exists())

        self.assertIsNotNone(acto_original.modalidad)
        self.assertIsNotNone(acto_original.inicio_solicitud)
        self.assertIsNotNone(acto_original.fin_solicitud)

        payload = {"tipo_acto_id": self.tipo_no_papeleta.id}

        acto_actualizado = actualizar_acto_service(self.admin, acto_original.id, payload)

        self.assertEqual(acto_actualizado.tipo_acto_id, self.tipo_no_papeleta.id)

        self.assertIsNone(acto_actualizado.modalidad)
        self.assertIsNone(acto_actualizado.inicio_solicitud)
        self.assertIsNone(acto_actualizado.fin_solicitud)
        self.assertIsNone(acto_actualizado.inicio_solicitud_cirios)
        self.assertIsNone(acto_actualizado.fin_solicitud_cirios)

        acto_refrescado = Acto.objects.get(pk=acto_original.id)
        self.assertIsNone(acto_refrescado.modalidad)
        self.assertIsNone(acto_refrescado.inicio_solicitud)
        self.assertIsNone(acto_refrescado.fin_solicitud)
        self.assertIsNone(acto_refrescado.inicio_solicitud_cirios)
        self.assertIsNone(acto_refrescado.fin_solicitud_cirios)



    def test_admin_cambia_de_sin_papeleta_a_con_papeleta_y_mantiene_estado_valido_ok(self):
        """
        Test: Cambiar a tipo_acto que requiere papeleta (manteniendo todo válido)

        Given: acto sin papeleta con fecha X
        When: payload setea tipo_con_papeleta + modalidad + plazos válidos
        Then: OK
        """
        acto_original = self.acto_db_no_papeleta

        self.assertFalse(acto_original.tipo_acto.requiere_papeleta)
        self.assertIsNone(acto_original.modalidad)
        self.assertIsNone(acto_original.inicio_solicitud)
        self.assertIsNone(acto_original.fin_solicitud)
        self.assertIsNone(acto_original.inicio_solicitud_cirios)
        self.assertIsNone(acto_original.fin_solicitud_cirios)

        payload = {
            "tipo_acto_id": self.tipo_con_papeleta.id,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.inicio_insignias,
            "fin_solicitud": self.fin_insignias,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        }

        acto_actualizado = actualizar_acto_service(
            self.admin,
            acto_original.id,
            payload
        )

        self.assertEqual(acto_actualizado.tipo_acto_id, self.tipo_con_papeleta.id)
        self.assertTrue(acto_actualizado.tipo_acto.requiere_papeleta)

        self.assertEqual(acto_actualizado.modalidad, Acto.ModalidadReparto.UNIFICADO)
        self.assertEqual(acto_actualizado.inicio_solicitud, self.inicio_insignias)
        self.assertEqual(acto_actualizado.fin_solicitud, self.fin_insignias)
        self.assertIsNone(acto_actualizado.inicio_solicitud_cirios)
        self.assertIsNone(acto_actualizado.fin_solicitud_cirios)

        acto_refrescado = Acto.objects.get(pk=acto_original.id)
        self.assertEqual(acto_refrescado.tipo_acto_id, self.tipo_con_papeleta.id)
        self.assertEqual(acto_refrescado.modalidad, Acto.ModalidadReparto.UNIFICADO)
        self.assertEqual(acto_refrescado.inicio_solicitud, self.inicio_insignias)
        self.assertEqual(acto_refrescado.fin_solicitud, self.fin_insignias)
        self.assertIsNone(acto_refrescado.inicio_solicitud_cirios)
        self.assertIsNone(acto_refrescado.fin_solicitud_cirios)



    def test_admin_actualiza_acto_usando_solo_tipo_acto_id_ok(self):
        """
        Test: Actualizar usando solo tipo_acto_id

        When: payload {"tipo_acto_id": tipo_con_papeleta.id, ... plazos válidos ...}
        Then: OK y acto.tipo_acto_id correcto
        """
        acto_original = self.acto_db_no_papeleta

        payload = {
            "tipo_acto_id": self.tipo_con_papeleta.id,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.inicio_insignias,
            "fin_solicitud": self.fin_insignias,
        }

        acto_actualizado = actualizar_acto_service(
            self.admin,
            acto_original.id,
            payload
        )

        self.assertEqual(acto_actualizado.tipo_acto_id, self.tipo_con_papeleta.id)
        self.assertTrue(acto_actualizado.tipo_acto.requiere_papeleta)

        self.assertEqual(acto_actualizado.modalidad, Acto.ModalidadReparto.UNIFICADO)
        self.assertEqual(acto_actualizado.inicio_solicitud, self.inicio_insignias)
        self.assertEqual(acto_actualizado.fin_solicitud, self.fin_insignias)
        self.assertIsNone(acto_actualizado.inicio_solicitud_cirios)
        self.assertIsNone(acto_actualizado.fin_solicitud_cirios)



    def test_admin_actualiza_acto_enviando_tipo_acto_y_tipo_acto_id_coherentes_ok(self):
        """
        Test: Enviar tipo_acto y tipo_acto_id coherentes

        When: payload incluye tipo_acto (instancia) y tipo_acto_id y coinciden
        Then: OK
        """
        acto_original = self.acto_db_no_papeleta

        payload = {
            "tipo_acto": self.tipo_con_papeleta,
            "tipo_acto_id": self.tipo_con_papeleta.id,
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.inicio_insignias,
            "fin_solicitud": self.fin_insignias,
        }

        acto_actualizado = actualizar_acto_service(
            self.admin,
            acto_original.id,
            payload
        )

        self.assertEqual(acto_actualizado.tipo_acto_id, self.tipo_con_papeleta.id)
        self.assertEqual(acto_actualizado.tipo_acto, self.tipo_con_papeleta)
        self.assertEqual(acto_actualizado.modalidad, Acto.ModalidadReparto.UNIFICADO)
        self.assertEqual(acto_actualizado.inicio_solicitud, self.inicio_insignias)
        self.assertEqual(acto_actualizado.fin_solicitud, self.fin_insignias)
        self.assertIsNone(acto_actualizado.inicio_solicitud_cirios)
        self.assertIsNone(acto_actualizado.fin_solicitud_cirios)



    def test_admin_actualiza_acto_con_payload_vacio_no_cambia_nada(self):
        """
        Test: Payload vacío {}

        Decide: no debe lanzar y no debe modificar ningún campo.
        """
        acto_original = self.acto_db_unificado

        payload = {}

        acto_actualizado = actualizar_acto_service(
            self.admin,
            acto_original.id,
            payload
        )

        self.assertIsNotNone(acto_actualizado)
        self.assertEqual(acto_actualizado.id, acto_original.id)

        self.assertEqual(acto_actualizado.nombre, acto_original.nombre)
        self.assertEqual(acto_actualizado.descripcion, acto_original.descripcion)
        self.assertEqual(acto_actualizado.fecha, acto_original.fecha)
        self.assertEqual(acto_actualizado.tipo_acto_id, acto_original.tipo_acto_id)
        self.assertEqual(acto_actualizado.modalidad, acto_original.modalidad)
        self.assertEqual(acto_actualizado.inicio_solicitud, acto_original.inicio_solicitud)
        self.assertEqual(acto_actualizado.fin_solicitud, acto_original.fin_solicitud)
        self.assertEqual(acto_actualizado.inicio_solicitud_cirios, acto_original.inicio_solicitud_cirios)
        self.assertEqual(acto_actualizado.fin_solicitud_cirios, acto_original.fin_solicitud_cirios)



    def test_admin_actualiza_fecha_sin_tocar_plazos_y_queda_incoherente_falla_por_clean(self):
        """
        Test: Cambio de fecha sin tocar plazos pero que queda incoherente

        Example: mueves fecha a antes de fin_solicitud
        Then: falla por clean() (prueba que full_clean() está actuando)
        """
        acto_original = self.acto_db_unificado

        self.assertLessEqual(acto_original.fin_solicitud, acto_original.fecha)

        nueva_fecha_invalida = acto_original.fin_solicitud - timedelta(hours=1)
        self.assertLess(nueva_fecha_invalida, acto_original.fin_solicitud)

        payload_invalido = {
            "fecha": nueva_fecha_invalida
        }

        with self.assertRaises(DjangoValidationError) as ctx:
            actualizar_acto_service(self.admin, acto_original.id, payload_invalido)

        self.assertIn("fin_solicitud", ctx.exception.message_dict)
        self.assertIn(
            "no puede ser posterior a la fecha del acto",
            ctx.exception.message_dict["fin_solicitud"][0]
        )



    def test_admin_actualiza_acto_sin_papeleta_intentando_setear_modalidad_y_service_limpia(self):
        """
        Test: Actualizar acto con tipo_sin_papeleta intentando setear modalidad

        Given: acto NO requiere papeleta
        When: payload intenta setear modalidad
        Then: OK, el service normaliza y deja modalidad=None (y plazos a None),
            y pasa full_clean() sin errores.
        """
        acto_original = self.acto_db_no_papeleta

        self.assertFalse(acto_original.tipo_acto.requiere_papeleta)
        self.assertIsNone(acto_original.modalidad)

        payload = {
            "modalidad": Acto.ModalidadReparto.TRADICIONAL,
        }

        acto_actualizado = actualizar_acto_service(
            self.admin,
            acto_original.id,
            payload
        )

        self.assertIsNone(acto_actualizado.modalidad)
        self.assertIsNone(acto_actualizado.inicio_solicitud)
        self.assertIsNone(acto_actualizado.fin_solicitud)
        self.assertIsNone(acto_actualizado.inicio_solicitud_cirios)
        self.assertIsNone(acto_actualizado.fin_solicitud_cirios)

        acto_refrescado = Acto.objects.get(pk=acto_original.id)
        self.assertIsNone(acto_refrescado.modalidad)
        self.assertIsNone(acto_refrescado.inicio_solicitud)
        self.assertIsNone(acto_refrescado.fin_solicitud)
        self.assertIsNone(acto_refrescado.inicio_solicitud_cirios)
        self.assertIsNone(acto_refrescado.fin_solicitud_cirios)



    def test_normalizar_payload_acepta_querydict(self):
        """
        Test: _normalizar_payload_acto acepta QueryDict y lo convierte a dict plano
        """
        qd = QueryDict("nombre=Acto%20prueba&descripcion=Desc")

        data = _normalizar_payload_acto(qd)

        self.assertIsInstance(data, dict)
        self.assertEqual(data["nombre"], "Acto prueba")
        self.assertEqual(data["descripcion"], "Desc")



    def test_normalizar_payload_querydict_multivalue_falla(self):
        """
        Test: QueryDict con múltiples valores por clave debe fallar
        """
        qd = QueryDict("nombre=A&nombre=B")

        with self.assertRaises(DRFValidationError) as ctx:
            _normalizar_payload_acto(qd)

        self.assertIn("nombre", ctx.exception.detail)
        self.assertIn(
            "No se permiten múltiples valores",
            str(ctx.exception.detail["nombre"])
        )



    def test_normalizar_payload_acepta_querydict_simple(self):
        """
        Test: QueryDict con un solo valor por clave pasa y se aplana a dict
        """
        qd = QueryDict("nombre=Acto%20prueba&descripcion=Desc")

        data = _normalizar_payload_acto(qd)

        self.assertEqual(data["nombre"], "Acto prueba")
        self.assertEqual(data["descripcion"], "Desc")
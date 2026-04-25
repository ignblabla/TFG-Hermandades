from django.http import Http404, QueryDict
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.exceptions import ValidationError as DRFValidationError
from unittest.mock import patch
import datetime
from django.db import DatabaseError, transaction
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from api.servicios.acto.acto_service import update_acto_service


from ....models import Acto, Hermano, TipoActo, TipoPuesto, Puesto


class ActualizarActoServiceTest(TestCase):

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

        self.tipo_con_papeleta_alt = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.CABILDO_GENERAL,
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

        self.acto_db_no_papeleta = Acto.objects.create(**self.acto_no_papeleta_ok)

        self.acto_db_tradicional = Acto.objects.create(**self.acto_tradicional_ok)

        self.acto_db_unificado = Acto.objects.create(**self.acto_unificado_ok)

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



    def test_update_acto_service_admin_success(self):
        """
        #     Test: Usuario admin puede actualizar un acto

        #     Given: Un usuario con esAdmin = True y un Acto existente en la base de datos.
        #     When: Se llama al servicio update_acto_service con cambios válidos en el payload.
        #     Then: El sistema actualiza los campos correspondientes en la base de datos
        #           y devuelve la instancia del acto con los nuevos valores.
        """
        usuario_ejecutor = self.admin
        acto_a_editar = self.acto_db_unificado
        
        data_cambios = {
            "nombre": "Cabildo General Actualizado",
            "lugar": "Nuevo Salón de Actos",
            "descripcion": "Descripción modificada por el administrador"
        }

        acto_actualizado = update_acto_service(
            usuario=usuario_ejecutor,
            acto_id=acto_a_editar.id,
            data_validada=data_cambios
        )

        self.assertEqual(acto_actualizado.nombre, "Cabildo General Actualizado")
        self.assertEqual(acto_actualizado.lugar, "Nuevo Salón de Actos")

        acto_a_editar.refresh_from_db()
        self.assertEqual(acto_a_editar.nombre, "Cabildo General Actualizado")
        self.assertEqual(acto_a_editar.descripcion, "Descripción modificada por el administrador")

        self.assertEqual(acto_a_editar.modalidad, Acto.ModalidadReparto.UNIFICADO)



    def test_update_acto_service_actualizacion_parcial(self):
        """
        #     Test: Actualización parcial de campos

        #     Given: Un Acto existente y un payload de data_validada que contiene 
        #           únicamente un campo (ej: nombre).
        #     When: Se ejecuta el servicio update_acto_service().
        #     Then: Solo el campo enviado en el diccionario cambia en la base de datos, 
        #           mientras que el resto de atributos del acto permanecen intactos.
        """
        usuario_ejecutor = self.admin
        acto_a_editar = self.acto_db_no_papeleta

        lugar_original = acto_a_editar.lugar
        fecha_original = acto_a_editar.fecha
        tipo_original = acto_a_editar.tipo_acto

        data_cambios = {
            "nombre": "Nombre Editado Únicamente"
        }

        update_acto_service(
            usuario=usuario_ejecutor,
            acto_id=acto_a_editar.id,
            data_validada=data_cambios
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.nombre, "Nombre Editado Únicamente")

        self.assertEqual(
            acto_a_editar.lugar, 
            lugar_original, 
            "El campo 'lugar' cambió y no venía en el payload."
        )
        self.assertEqual(
            acto_a_editar.fecha, 
            fecha_original, 
            "El campo 'fecha' cambió y no venía en el payload."
        )
        self.assertEqual(
            acto_a_editar.tipo_acto, 
            tipo_original, 
            "El campo 'tipo_acto' cambió y no venía en el payload."
        )



    def test_update_acto_service_mismo_tipo_con_puestos_permitido(self):
        """
        #     Test: No se cambia el tipo → permitido aunque haya puestos

        #     Given: Un acto (self.acto_db_tradicional) que ya tiene puestos asociados 
        #           en la base de datos (puesto_en_acto_tradicional).
        #     When: Se actualizan otros campos (ej: lugar) pero el tipo_acto enviado 
        #           es el mismo que ya tenía el registro.
        #     Then: La operación se realiza correctamente sin lanzar ValidationError, 
        #           permitiendo la edición del resto de la información.
        """
        usuario_ejecutor = self.admin
        acto_con_puestos = self.acto_db_tradicional

        self.assertTrue(acto_con_puestos.puestos_disponibles.exists())

        data_cambios = {
            "lugar": "Ubicación Actualizada con Puestos",
            "tipo_acto": acto_con_puestos.tipo_acto
        }

        try:
            acto_actualizado = update_acto_service(
                usuario=usuario_ejecutor,
                acto_id=acto_con_puestos.id,
                data_validada=data_cambios
            )
        except DjangoValidationError:
            self.fail("update_acto_service lanzó ValidationError al enviar el mismo tipo_acto.")

        # Then
        acto_con_puestos.refresh_from_db()
        self.assertEqual(acto_con_puestos.lugar, "Ubicación Actualizada con Puestos")
        self.assertEqual(acto_con_puestos.tipo_acto, self.tipo_con_papeleta)



    def test_update_acto_service_cambio_tipo_sin_puestos_permitido(self):
        """
        #     Test: Cambio de tipo permitido sin puestos asignados

        #     Given: Un Acto existente (self.acto_db_unificado) que no tiene ningún
        #           puesto asociado en la base de datos.
        #     When: Se intenta cambiar su tipo_acto por uno diferente que no requiere papeleta.
        #     Then: El servicio permite la actualización si se limpian los campos 
        #           incompatibles, cumpliendo con las validaciones del modelo.
        """
        usuario_ejecutor = self.admin
        acto_sin_puestos = self.acto_db_unificado
        nuevo_tipo = self.tipo_no_papeleta

        self.assertFalse(acto_sin_puestos.puestos_disponibles.exists())
        self.assertNotEqual(acto_sin_puestos.tipo_acto, nuevo_tipo)

        data_cambios = {
            "tipo_acto": nuevo_tipo,
            "nombre": "Acto Reclasificado",
            "modalidad": None,
            "inicio_solicitud": None,
            "fin_solicitud": None,
            "inicio_solicitud_cirios": None,
            "fin_solicitud_cirios": None,
        }

        acto_actualizado = update_acto_service(
            usuario=usuario_ejecutor,
            acto_id=acto_sin_puestos.id,
            data_validada=data_cambios
        )

        acto_sin_puestos.refresh_from_db()
        self.assertEqual(
            acto_sin_puestos.tipo_acto, 
            nuevo_tipo, 
            "El tipo de acto debería haberse actualizado correctamente."
        )
        self.assertIsNone(acto_sin_puestos.modalidad)
        self.assertEqual(acto_sin_puestos.nombre, "Acto Reclasificado")



    def test_update_acto_service_multiples_cambios_simultaneos(self):
        """
        #     Test: Se aplican múltiples cambios a la vez

        #     Given: Un Acto existente (sin papeleta) y un diccionario data_validada con 
        #           múltiples campos, incluyendo el cambio a un tipo que requiere papeleta.
        #     When: Se ejecuta el servicio update_acto_service().
        #     Then: Todos los campos enviados se reflejan correctamente, cumpliendo 
        #           con los requisitos de integridad del nuevo tipo de acto.
        """
        usuario_ejecutor = self.admin
        acto_a_editar = self.acto_db_no_papeleta
        
        nueva_fecha = self.ahora + timedelta(days=60)
        nuevo_tipo = self.tipo_con_papeleta_alt

        data_cambios = {
            "nombre": "Nombre Totalmente Nuevo",
            "lugar": "Sede Central Reformada",
            "fecha": nueva_fecha,
            "tipo_acto": nuevo_tipo,
            "descripcion": "Cambio masivo de datos para test de integridad.",
            "modalidad": Acto.ModalidadReparto.UNIFICADO,
            "inicio_solicitud": self.ahora + timedelta(days=10),
            "fin_solicitud": self.ahora + timedelta(days=15),
        }

        update_acto_service(
            usuario=usuario_ejecutor,
            acto_id=acto_a_editar.id,
            data_validada=data_cambios
        )

        acto_a_editar.refresh_from_db()

        self.assertEqual(acto_a_editar.nombre, data_cambios["nombre"])
        self.assertEqual(acto_a_editar.lugar, data_cambios["lugar"])
        self.assertEqual(acto_a_editar.fecha, data_cambios["fecha"])
        self.assertEqual(acto_a_editar.tipo_acto, nuevo_tipo)
        self.assertEqual(acto_a_editar.modalidad, data_cambios["modalidad"])
        self.assertEqual(acto_a_editar.descripcion, data_cambios["descripcion"])



    from unittest.mock import patch

    def test_update_acto_service_llama_a_save_una_vez(self):
        """
        #     Test: Se llama a save() una vez

        #     Given: Un usuario administrador y un acto existente.
        #     When: Se llama al servicio update_acto_service() con datos válidos.
        #     Then: El método .save() de la instancia se ejecuta exactamente una vez,
        #           garantizando que la persistencia es atómica y eficiente.
        """
        usuario_ejecutor = self.admin
        acto_id = self.acto_db_no_papeleta.id
        data_validada = {"nombre": "Nombre para test de save"}

        with patch("api.models.Acto.save") as mock_save:
            # When
            update_acto_service(
                usuario=usuario_ejecutor,
                acto_id=acto_id,
                data_validada=data_validada
            )

            self.assertEqual(
                mock_save.call_count, 
                1, 
                f"Se esperaba 1 llamada a .save(), pero se detectaron {mock_save.call_count}."
            )



    def test_update_acto_service_devuelve_objeto_actualizado(self):
        """
        #     Test: Devuelve el objeto actualizado

        #     Given: Un Acto existente y un usuario administrador.
        #     When: Se ejecuta el servicio update_acto_service().
        #     Then: El objeto retornado por la función no es una instancia vieja,
        #           sino que ya contiene los cambios persistidos en sus atributos.
        """
        usuario_ejecutor = self.admin
        acto_a_editar = self.acto_db_no_papeleta
        nuevo_nombre = "Nombre Retornado Test"
        
        data_cambios = {
            "nombre": nuevo_nombre,
            "lugar": "Lugar Retornado Test"
        }

        acto_retornado = update_acto_service(
            usuario=usuario_ejecutor,
            acto_id=acto_a_editar.id,
            data_validada=data_cambios
        )

        self.assertEqual(
            acto_retornado.nombre, 
            nuevo_nombre, 
            "El objeto retornado no muestra el nombre actualizado."
        )
        self.assertEqual(
            acto_retornado.lugar, 
            "Lugar Retornado Test", 
            "El objeto retornado no muestra el lugar actualizado."
        )

        self.assertEqual(
            acto_retornado.id, 
            acto_a_editar.id, 
            "El servicio devolvió un objeto con un ID diferente al original."
        )

        acto_retornado.refresh_from_db()
        self.assertEqual(acto_retornado.nombre, nuevo_nombre)



    def test_update_acto_service_soporta_valores_none(self):
        """
        #     Test: Soporta valores None si el modelo lo permite

        #     Given: Un Acto con campos opcionales ya rellenos (ej: descripción).
        #     When: Se envía un valor None para esos campos en data_validada.
        #     Then: El servicio actualiza correctamente el registro en la base de datos
        #           estableciendo el valor como nulo (None).
        """
        usuario_ejecutor = self.admin
        acto_a_editar = self.acto_db_unificado

        self.assertIsNotNone(acto_a_editar.descripcion)
        
        data_cambios = {
            "descripcion": None
        }

        update_acto_service(
            usuario=usuario_ejecutor,
            acto_id=acto_a_editar.id,
            data_validada=data_cambios
        )

        acto_a_editar.refresh_from_db()

        self.assertIsNone(
            acto_a_editar.descripcion,
            "El servicio no actualizó el campo opcional a None."
        )

        self.assertEqual(
            acto_a_editar.nombre, 
            "Cabildo General 2026",
            "Un campo no relacionado fue modificado accidentalmente."
        )



    @patch("api.servicios.acto.acto_service.get_object_or_404")
    @patch("api.models.Acto.save")
    def test_update_acto_service_no_admin_lanza_error_y_no_consulta(self, mock_save, mock_get):
        """
        #     Test: Usuario no admin → error de permisos

        #     Given: Un usuario con esAdmin = False (self.hermano).
        #     When: Se intenta llamar al servicio update_acto_service().
        #     Then: Se lanza una excepción PermissionDenied.
        #     And: Se garantiza que no se llega a consultar el acto (get_object_or_404)
        #          ni a ejecutar el guardado (.save()).
        """
        usuario_no_admin = self.hermano
        acto_id = self.acto_db_unificado.id
        data_cambios = {"nombre": "Intento de modificación no autorizada"}

        with self.assertRaises(PermissionDenied) as cm:
            update_acto_service(
                usuario=usuario_no_admin,
                acto_id=acto_id,
                data_validada=data_cambios
            )
        
        self.assertEqual(str(cm.exception), "No tienes permisos para editar actos.")

        mock_get.assert_not_called()

        mock_save.assert_not_called()

        self.acto_db_unificado.refresh_from_db()
        self.assertNotEqual(self.acto_db_unificado.nombre, "Intento de modificación no autorizada")



    def test_update_acto_service_usuario_sin_esadmin_lanza_error(self):
        """
        #     Test: Usuario sin atributo esAdmin

        #     Given: Un objeto de usuario (o entidad) que no tiene definido 
        #           el atributo 'esAdmin'.
        #     When: Se intenta ejecutar el servicio update_acto_service().
        #     Then: Se lanza PermissionDenied porque getattr(..., False) 
        #           asume el valor restrictivo por defecto.
        """
        class UsuarioIncompleto:
            pass
            
        usuario_sin_atributo = UsuarioIncompleto()
        acto_id = self.acto_db_no_papeleta.id
        data_cambios = {"nombre": "Cambio no autorizado"}

        with self.assertRaises(PermissionDenied) as cm:
            update_acto_service(
                usuario=usuario_sin_atributo,
                acto_id=acto_id,
                data_validada=data_cambios
            )
            
        self.assertEqual(str(cm.exception), "No tienes permisos para editar actos.")

        self.acto_db_no_papeleta.refresh_from_db()
        self.assertNotEqual(self.acto_db_no_papeleta.nombre, "Cambio no autorizado")



    def test_update_acto_service_usuario_nulo_lanza_error(self):
        """
        #     Test: usuario = None

        #     Given: Un valor de usuario igual a None.
        #     When: Se intenta llamar a update_acto_service().
        #     Then: Se lanza PermissionDenied, ya que getattr(None, 'esAdmin', False)
        #           no encontrará el atributo y devolverá el valor por defecto False.
        """
        usuario_nulo = None
        acto_id = self.acto_db_no_papeleta.id
        data_cambios = {"nombre": "Intento con usuario nulo"}

        with self.assertRaises(PermissionDenied) as cm:
            update_acto_service(
                usuario=usuario_nulo,
                acto_id=acto_id,
                data_validada=data_cambios
            )
            
        self.assertEqual(str(cm.exception), "No tienes permisos para editar actos.")

        self.acto_db_no_papeleta.refresh_from_db()
        self.assertNotEqual(self.acto_db_no_papeleta.nombre, "Intento con usuario nulo")



    def test_update_acto_service_acto_inexistente_lanza_404(self):
        """
        #     Test: Acto no existe

        #     Given: Un usuario administrador y un acto_id que no existe en la BD (9999).
        #     When: Se intenta llamar al servicio update_acto_service().
        #     Then: Se lanza una excepción Http404, disparada por la función 
        #           get_object_or_404 al no encontrar el registro.
        """
        usuario_ejecutor = self.admin
        id_falso = 9999
        data_cambios = {"nombre": "Nombre irrelevante"}

        self.assertFalse(Acto.objects.filter(id=id_falso).exists())

        with self.assertRaises(Http404):
            update_acto_service(
                usuario=usuario_ejecutor,
                acto_id=id_falso,
                data_validada=data_cambios
            )



    def test_update_acto_service_cambio_tipo_con_puestos_prohibido(self):
        """
        #     Test: Intentar cambiar tipo con puestos asignados

        #     Given: Un acto (self.acto_db_tradicional) que ya tiene puestos asignados 
        #           en la base de datos (puesto_en_acto_tradicional).
        #     When: Se intenta cambiar el campo 'tipo_acto' por uno diferente.
        #     Then: El servicio lanza un ValidationError con un mensaje específico, 
        #           evitando que los puestos queden en un estado inconsistente.
        """
        usuario_ejecutor = self.admin
        acto_con_puestos = self.acto_db_tradicional
        nuevo_tipo = self.tipo_con_papeleta_alt

        self.assertTrue(acto_con_puestos.puestos_disponibles.exists())
        self.assertNotEqual(acto_con_puestos.tipo_acto, nuevo_tipo)
        
        data_cambios = {
            "tipo_acto": nuevo_tipo,
            "nombre": "Intento de cambio de tipo"
        }

        with self.assertRaises(DjangoValidationError) as cm:
            update_acto_service(
                usuario=usuario_ejecutor,
                acto_id=acto_con_puestos.id,
                data_validada=data_cambios
            )

        self.assertIn("tipo_acto", cm.exception.message_dict)
        self.assertEqual(
            cm.exception.message_dict["tipo_acto"][0],
            "No se puede cambiar el tipo de acto porque ya tiene puestos asignados."
        )

        acto_con_puestos.refresh_from_db()
        self.assertNotEqual(acto_con_puestos.tipo_acto, nuevo_tipo)
        self.assertEqual(acto_con_puestos.tipo_acto, self.tipo_con_papeleta)



    @patch("api.models.Acto.save")
    def test_update_acto_service_no_guarda_si_falla_validacion_tipo(self, mock_save):
        """
        #     Test: No debe guardar si falla la validación del tipo

        #     Given: Un acto con puestos asignados y un intento de cambiar su tipo_acto.
        #     When: Se ejecuta el servicio update_acto_service().
        #     Then: Se lanza un ValidationError y se garantiza que el método .save()
        #           NUNCA es llamado, evitando cualquier escritura en BD.
        """
        usuario_ejecutor = self.admin
        acto_con_puestos = self.acto_db_tradicional
        nuevo_tipo = self.tipo_con_papeleta_alt

        self.assertTrue(acto_con_puestos.puestos_disponibles.exists())
        
        data_cambios = {
            "tipo_acto": nuevo_tipo,
            "nombre": "Nombre que nunca debería guardarse"
        }

        with self.assertRaises(DjangoValidationError):
            update_acto_service(
                usuario=usuario_ejecutor,
                acto_id=acto_con_puestos.id,
                data_validada=data_cambios
            )

        mock_save.assert_not_called()

        acto_con_puestos.refresh_from_db()
        self.assertNotEqual(
            acto_con_puestos.nombre, 
            "Nombre que nunca debería guardarse",
            "El nombre se actualizó en la BD a pesar de que la validación falló."
        )



    def test_update_acto_service_falla_save_y_no_se_captura(self):
        """
        #     Test: Error en save() (validación del modelo)

        #     Given: Datos que pasan la lógica del servicio pero fallan en el 
        #           save/clean del modelo.
        #     When: Se ejecuta update_acto_service().
        #     Then: Se lanza un ValidationError y se verifica que el servicio
        #           no captura la excepción, dejándola escalar.
        """
        usuario_ejecutor = self.admin
        acto_id = self.acto_db_no_papeleta.id
        data_cambios = {"nombre": "Nombre Inválido por Modelo"}

        with patch("api.models.Acto.save") as mock_save:
            mock_save.side_effect = DjangoValidationError({"nombre": "Error de integridad del modelo."})

            with self.assertRaises(DjangoValidationError) as cm:
                update_acto_service(
                    usuario=usuario_ejecutor,
                    acto_id=acto_id,
                    data_validada=data_cambios
                )

            self.assertIn("nombre", cm.exception.message_dict)
            self.assertEqual(
                cm.exception.message_dict["nombre"][0],
                "Error de integridad del modelo."
            )

            mock_save.assert_called_once()



    def test_update_acto_service_data_validada_vacio(self):
        """
        #     Test: data_validada vacío

        #     Given: Un diccionario data_validada sin ninguna clave ({}).
        #     When: Se llama al servicio update_acto_service().
        #     Then: El servicio no debe fallar, el acto no cambia sus valores 
        #           pero se ejecuta el método save() (comportamiento actual).
        """
        usuario_ejecutor = self.admin
        acto_a_editar = self.acto_db_no_papeleta

        nombre_original = acto_a_editar.nombre
        data_vacia = {}

        with patch("api.models.Acto.save") as mock_save:
            acto_retornado = update_acto_service(
                usuario=usuario_ejecutor,
                acto_id=acto_a_editar.id,
                data_validada=data_vacia
            )

            self.assertEqual(acto_retornado.id, acto_a_editar.id)

            self.assertEqual(acto_retornado.nombre, nombre_original)

            self.assertEqual(
                mock_save.call_count, 
                1, 
                "El servicio debería haber ejecutado save() incluso con datos vacíos."
            )



    def test_update_acto_service_campo_inexistente_no_persiste(self):
        """
        #     Test: Campo inexistente en data_validada

        #     Given: Una clave en data_validada que NO es un atributo del modelo ('campo_inventado').
        #     When: Se llama al servicio update_acto_service().
        #     Then: setattr añade el atributo al objeto en memoria (runtime), 
        #           pero Django lo ignora en el .save() y no se persiste en la BD.
        #
        #     Nota: Esto confirma que el servicio no valida la existencia de los campos.
        """
        usuario_ejecutor = self.admin
        acto_a_editar = self.acto_db_no_papeleta
        data_con_basura = {
            "nombre": "Nombre Válido",
            "campo_inventado": "Soy un infiltrado"
        }

        acto_retornado = update_acto_service(
            usuario=usuario_ejecutor,
            acto_id=acto_a_editar.id,
            data_validada=data_con_basura
        )

        self.assertTrue(hasattr(acto_retornado, "campo_inventado"))
        self.assertEqual(acto_retornado.campo_inventado, "Soy un infiltrado")

        acto_a_editar.refresh_from_db()
        self.assertEqual(acto_a_editar.nombre, "Nombre Válido")

        with self.assertRaises(AttributeError):
            print(acto_a_editar.campo_inventado)



    def test_update_acto_service_no_modifica_atributos_no_incluidos(self):
        """
        #     Test: No debe modificar atributos no incluidos

        #     Given: Un Acto con valores iniciales definidos y un payload que solo 
        #           contiene un campo (ej: lugar).
        #     When: Se ejecuta el servicio update_acto_service().
        #     Then: Solo el campo 'lugar' se actualiza en la base de datos, mientras 
        #           que el 'nombre' y otros atributos NO incluidos en data_validada 
        #           permanecen idénticos a su estado original.
        """
        usuario_ejecutor = self.admin
        acto = self.acto_db_no_papeleta

        nombre_original = acto.nombre
        fecha_original = acto.fecha
        descripcion_original = acto.descripcion

        data_cambios = {
            "lugar": "Ubicación Modificada Específicamente"
        }

        update_acto_service(
            usuario=usuario_ejecutor,
            acto_id=acto.id,
            data_validada=data_cambios
        )

        acto.refresh_from_db()

        self.assertEqual(acto.lugar, "Ubicación Modificada Específicamente")

        self.assertEqual(
            acto.nombre, 
            nombre_original, 
            "El campo 'nombre' se modificó sin estar en el payload."
        )
        self.assertEqual(
            acto.fecha, 
            fecha_original, 
            "La 'fecha' se modificó sin estar en el payload."
        )
        self.assertEqual(
            acto.descripcion, 
            descripcion_original, 
            "La 'descripcion' se modificó sin estar en el payload."
        )



    @patch("api.models.Acto.save")
    def test_update_acto_service_atomicidad_rollback(self, mock_save):
        """
        #     Test: Atomicidad: rollback en caso de error

        #     Given: Un usuario administrador y un Acto con valores conocidos.
        #     When: El servicio actualiza atributos en memoria, pero el método .save() 
        #           lanza una excepción (simulando un fallo de integridad o de BD).
        #     Then: La transacción debe revertirse, asegurando que los valores en la 
        #           base de datos permanecen como estaban antes de la llamada.
        """
        usuario_ejecutor = self.admin
        acto = self.acto_db_no_papeleta
        nombre_original = acto.nombre
        lugar_original = acto.lugar

        data_cambios = {
            "nombre": "Nombre Transaccional",
            "lugar": "Lugar Transaccional"
        }

        mock_save.side_effect = DjangoValidationError("Fallo forzado para probar rollback")

        with self.assertRaises(DjangoValidationError):
            update_acto_service(
                usuario=usuario_ejecutor,
                acto_id=acto.id,
                data_validada=data_cambios
            )

        acto.refresh_from_db()

        self.assertEqual(
            acto.nombre, 
            nombre_original, 
            "El rollback falló: el nombre se persistió a pesar del error."
        )
        self.assertEqual(
            acto.lugar, 
            lugar_original, 
            "El rollback falló: el lugar se persistió a pesar del error."
        )
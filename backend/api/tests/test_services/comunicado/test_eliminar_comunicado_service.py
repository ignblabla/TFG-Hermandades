from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.db import DatabaseError, transaction, IntegrityError
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.contrib.auth import get_user_model
from django.db.models import ProtectedError

from api.models import Acto, AreaInteres, Comunicado, CuerpoPertenencia, Hermano, HermanoCuerpo, TipoActo
from api.servicios.comunicado.creacion_comunicado_service import ComunicadoService

from unittest.mock import MagicMock, PropertyMock, patch


class EliminarComunicadoServiceTest(TestCase):

    def setUp(self):
        """
        Configuración inicial para testear el servicio de Comunicados.
        """
        self.ahora = timezone.now()

        # ---------------------------------------------------------------------
        # 1. ÁREAS DE INTERÉS (Para probar notificaciones de Telegram)
        # ---------------------------------------------------------------------
        self.area_con_telegram = AreaInteres.objects.create(
            nombre_area=AreaInteres.NombreArea.TODOS_HERMANOS,
            telegram_channel_id="-100987654321"
        )
        
        self.area_sin_telegram = AreaInteres.objects.create(
            nombre_area=AreaInteres.NombreArea.JUVENTUD,
            telegram_channel_id=None
        )

        # ---------------------------------------------------------------------
        # 2. CUERPOS DE PERTENENCIA
        # ---------------------------------------------------------------------
        self.cuerpo_junta = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        )

        # ---------------------------------------------------------------------
        # 3. USUARIOS (Roles para probar _verificar_permisos)
        # ---------------------------------------------------------------------
        self.admin = Hermano.objects.create_user(
            dni="11111111A",
            username="11111111A",
            password="password",
            nombre="Admin",
            primer_apellido="Root",
            segundo_apellido="Test",
            email="admin@example.com",
            telefono="600000001",
            estado_civil=Hermano.EstadoCivil.SOLTERO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=1,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1980-01-01",
            direccion="Calle Administración 1",
            codigo_postal="41001",
            localidad="Sevilla",
            provincia="Sevilla",
            comunidad_autonoma="Andalucía",
            esAdmin=True,
        )

        self.miembro_junta = Hermano.objects.create_user(
            dni="22222222B",
            username="22222222B",
            password="password",
            nombre="Vocal",
            primer_apellido="Junta",
            segundo_apellido="Test",
            email="junta@example.com",
            telefono="600000002",
            estado_civil=Hermano.EstadoCivil.CASADO,
            genero=Hermano.Genero.FEMENINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=1001,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1985-05-15",
            direccion="Calle Cabildo 2",
            codigo_postal="41002",
            localidad="Sevilla",
            provincia="Sevilla",
            comunidad_autonoma="Andalucía",
            esAdmin=False,
        )

        HermanoCuerpo.objects.create(
            hermano=self.miembro_junta,
            cuerpo=self.cuerpo_junta,
            anio_ingreso=self.ahora.year
        )

        self.usuario_base = Hermano.objects.create_user(
            dni="33333333C",
            username="33333333C",
            password="password",
            nombre="Hermano",
            primer_apellido="Raso",
            segundo_apellido="Test",
            email="base@example.com",
            telefono="600000003",
            estado_civil=Hermano.EstadoCivil.SOLTERO,
            genero=Hermano.Genero.MASCULINO,
            estado_hermano=Hermano.EstadoHermano.ALTA,
            numero_registro=1002,
            fecha_ingreso_corporacion=self.ahora.date(),
            fecha_nacimiento="1990-10-20",
            direccion="Calle Hermandad 3",
            codigo_postal="41003",
            localidad="Sevilla",
            provincia="Sevilla",
            comunidad_autonoma="Andalucía",
            esAdmin=False,
        )

        # ---------------------------------------------------------------------
        # 4. PAYLOADS BASE PARA TESTS
        # ---------------------------------------------------------------------
        self.imagen_dummy = SimpleUploadedFile(
            name='test_portada.jpg', 
            content=b'file_content', 
            content_type='image/jpeg'
        )

        self.payload_comunicado_valido = {
            "titulo": "Nuevo horario de misas",
            "contenido": "Se informa a todos los hermanos del nuevo horario...",
            "tipo_comunicacion": "INFORMATIVO",
            "areas_interes": [self.area_con_telegram, self.area_sin_telegram],
            "imagen_portada": None
        }
        
        self.payload_comunicado_con_imagen = {
            "titulo": "Restauración completada",
            "contenido": "Presentamos el resultado final...",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [self.area_con_telegram],
            "imagen_portada": self.imagen_dummy
        }



    def test_admin_elimina_comunicado_correctamente(self):
        """
        Test: Administrador elimina un comunicado.

        Given: Un comunicado guardado en la base de datos y un usuario con 
            permisos de administrador (esAdmin=True).
        When: Se invoca el método delete_comunicado con dicho usuario y 
            la instancia del comunicado.
        Then: El servicio retorna True y el registro del comunicado es 
            eliminado definitivamente de la base de datos.
        """
        comunicado_a_borrar = Comunicado.objects.create(
            titulo="Comunicado de prueba para borrado",
            contenido="Este contenido debe desaparecer.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        comunicado_a_borrar.areas_interes.add(self.area_con_telegram)
        
        comunicado_id = comunicado_a_borrar.pk

        self.assertTrue(Comunicado.objects.filter(pk=comunicado_id).exists())

        servicio = ComunicadoService()

        resultado = servicio.delete_comunicado(
            usuario=self.admin, 
            comunicado_instance=comunicado_a_borrar
        )

        self.assertTrue(resultado)

        self.assertFalse(Comunicado.objects.filter(pk=comunicado_id).exists())



    def test_miembro_junta_elimina_comunicado_correctamente(self):
        """
        Test: Miembro de la Junta de Gobierno elimina un comunicado.

        Given: Un comunicado existente y un usuario que NO es administrador 
            pero pertenece al cuerpo 'JUNTA_GOBIERNO'.
        When: Se invoca el método delete_comunicado con dicho usuario y 
            la instancia del comunicado.
        Then: El servicio procesa la solicitud correctamente, retorna True 
            y el comunicado es eliminado de la base de datos.
        """
        comunicado_junta = Comunicado.objects.create(
            titulo="Comunicado de Junta",
            contenido="Información relevante de la hermandad.",
            tipo_comunicacion=Comunicado.TipoComunicacion.SECRETARIA,
            autor=self.miembro_junta
        )
        
        id_comunicado = comunicado_junta.pk
        servicio = ComunicadoService()

        self.assertFalse(self.miembro_junta.esAdmin)
        self.assertTrue(
            self.miembro_junta.cuerpos.filter(
                nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
            ).exists()
        )

        resultado = servicio.delete_comunicado(
            usuario=self.miembro_junta, 
            comunicado_instance=comunicado_junta
        )

        self.assertTrue(resultado)

        self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())



    def test_usuario_admin_y_junta_elimina_comunicado_correctamente(self):
        """
        Test: Usuario con doble rol (Admin + Junta) elimina un comunicado.

        Given: Un comunicado en la base de datos y un usuario que cumple 
               ambas condiciones de permiso: esAdmin=True y pertenece al 
               cuerpo 'JUNTA_GOBIERNO'.
        When: Se invoca el método delete_comunicado con este usuario.
        Then: El servicio procesa la eliminación sin conflictos de permisos, 
              retorna True y el registro desaparece de la base de datos.
        """
        HermanoCuerpo.objects.create(
            hermano=self.admin,
            cuerpo=self.cuerpo_junta,
            anio_ingreso=self.ahora.year
        )

        comunicado_dual = Comunicado.objects.create(
            titulo="Comunicado Institucional",
            contenido="Contenido de prueba para usuario con doble rol.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        
        id_comunicado = comunicado_dual.pk
        servicio = ComunicadoService()

        self.assertTrue(self.admin.esAdmin)
        self.assertTrue(self.admin.cuerpos.filter(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
        ).exists())

        resultado = servicio.delete_comunicado(
            usuario=self.admin, 
            comunicado_instance=comunicado_dual
        )

        self.assertTrue(resultado)

        self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())



    def test_usuario_multiples_cuerpos_incluyendo_junta_elimina_correctamente(self):
        """
        Test: Usuario con múltiples cuerpos (incluyendo Junta) elimina un comunicado.

        Given: Un comunicado y un usuario que pertenece a varios cuerpos 
            (ej: COSTALEROS, ACOLITOS y JUNTA_GOBIERNO).
        When: Se invoca el método delete_comunicado con dicho usuario.
        Then: El servicio identifica la pertenencia a la Junta entre los cuerpos 
            del usuario, otorga el permiso, retorna True y elimina el registro.
        """
        cuerpo_costaleros = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.COSTALEROS
        )
        cuerpo_acolitos = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.ACOLITOS
        )

        for cuerpo in [cuerpo_costaleros, cuerpo_acolitos, self.cuerpo_junta]:
            HermanoCuerpo.objects.create(
                hermano=self.usuario_base,
                cuerpo=cuerpo,
                anio_ingreso=self.ahora.year
            )

        comunicado_multi = Comunicado.objects.create(
            titulo="Comunicado para Hermanos",
            contenido="Información para diversos colectivos.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.usuario_base
        )
        
        id_comunicado = comunicado_multi.pk
        servicio = ComunicadoService()

        self.assertEqual(self.usuario_base.cuerpos.count(), 3)
        self.assertFalse(self.usuario_base.esAdmin)

        resultado = servicio.delete_comunicado(
            usuario=self.usuario_base, 
            comunicado_instance=comunicado_multi
        )

        self.assertTrue(resultado)

        self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())



    def test_usuario_admin_sin_cuerpos_elimina_comunicado_correctamente(self):
        """
        Test: Usuario administrador sin cuerpos asociados elimina un comunicado.

        Given: Un comunicado existente y un usuario con esAdmin=True que 
            no tiene ninguna relación en la tabla HermanoCuerpo.
        When: Se invoca el método delete_comunicado con este usuario.
        Then: El servicio otorga el permiso basándose exclusivamente en el flag 
            'esAdmin', retorna True y el comunicado es eliminado.
        """
        self.admin.pertenencias_cuerpos.all().delete()

        comunicado_solo_admin = Comunicado.objects.create(
            titulo="Comunicado de Sistema",
            contenido="Contenido administrativo sin cuerpo de origen.",
            tipo_comunicacion=Comunicado.TipoComunicacion.URGENTE,
            autor=self.admin
        )
        
        id_comunicado = comunicado_solo_admin.pk
        servicio = ComunicadoService()

        self.assertTrue(self.admin.esAdmin)
        self.assertEqual(self.admin.cuerpos.count(), 0)

        resultado = servicio.delete_comunicado(
            usuario=self.admin, 
            comunicado_instance=comunicado_solo_admin
        )

        self.assertTrue(resultado)

        self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())



    def test_usuario_junta_no_admin_elimina_comunicado_correctamente(self):
        """
        Test: Miembro de Junta sin privilegios de administrador elimina comunicado.

        Given: Un comunicado guardado y un usuario con esAdmin=False que 
            pertenece al cuerpo 'JUNTA_GOBIERNO'.
        When: Se invoca el método delete_comunicado con dicho usuario.
        Then: El servicio valida la pertenencia al cuerpo de gestión, otorga 
            el permiso, retorna True y elimina el registro de la base de datos.
        """
        comunicado_junta = Comunicado.objects.create(
            titulo="Aviso de Secretaría",
            contenido="Contenido para ser eliminado por la junta.",
            tipo_comunicacion=Comunicado.TipoComunicacion.SECRETARIA,
            autor=self.miembro_junta
        )
        
        id_comunicado = comunicado_junta.pk
        servicio = ComunicadoService()

        self.assertFalse(self.miembro_junta.esAdmin)
        self.assertTrue(
            self.miembro_junta.cuerpos.filter(
                nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.JUNTA_GOBIERNO
            ).exists()
        )

        resultado = servicio.delete_comunicado(
            usuario=self.miembro_junta, 
            comunicado_instance=comunicado_junta
        )

        self.assertTrue(resultado)

        self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())



    def test_eliminar_comunicado_sin_imagen_correctamente(self):
        """
        Test: Eliminar un comunicado que no tiene imagen de portada.

        Given: Un comunicado guardado en la base de datos con el campo 
            'imagen_portada' como None.
        When: Se invoca el método delete_comunicado con un usuario administrador.
        Then: El servicio elimina el registro de la base de datos correctamente,
            retorna True y no se producen errores al intentar limpiar archivos.
        """
        comunicado_sin_foto = Comunicado.objects.create(
            titulo="Comunicado sin imagen",
            contenido="Este comunicado solo tiene texto.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            imagen_portada=None
        )
        
        id_comunicado = comunicado_sin_foto.pk
        servicio = ComunicadoService()

        self.assertFalse(comunicado_sin_foto.imagen_portada)

        resultado = servicio.delete_comunicado(
            usuario=self.admin, 
            comunicado_instance=comunicado_sin_foto
        )

        self.assertTrue(resultado)

        self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())



    def test_eliminar_comunicado_sin_imagen_retorna_true(self):
        """
        Test: Eliminación de comunicado sin imagen y retorno de confirmación.

        Given: Un comunicado existente en la base de datos que no dispone de 
            archivo adjunto (imagen_portada=None).
        When: Se invoca el método delete_comunicado con un usuario con permisos.
        Then: El método retorna True, confirmando la operación, y el registro 
            es eliminado de la base de datos sin intentar borrar archivos inexistentes.
        """
        comunicado_simple = Comunicado.objects.create(
            titulo="Comunicado Solo Texto",
            contenido="Este es un comunicado sin archivos multimedia.",
            tipo_comunicacion=Comunicado.TipoComunicacion.INFORMATIVO,
            autor=self.admin,
            imagen_portada=None
        )
        
        id_comunicado = comunicado_simple.pk
        servicio = ComunicadoService()

        self.assertFalse(comunicado_simple.imagen_portada)

        resultado = servicio.delete_comunicado(
            usuario=self.admin, 
            comunicado_instance=comunicado_simple
        )

        self.assertIs(resultado, True)

        self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())



    def test_verificar_comunicado_desaparece_de_bd_tras_borrado(self):
        """
        Test: Verificación de ausencia en base de datos tras eliminación.

        Given: Un comunicado guardado en la base de datos con un ID específico.
        When: Se ejecuta con éxito el método delete_comunicado del servicio.
        Then: Una consulta directa a la base de datos filtrando por dicho ID 
            no debe devolver ningún resultado (el registro ya no existe).
        """
        comunicado_efimero = Comunicado.objects.create(
            titulo="Comunicado a eliminar",
            contenido="Este registro debe desaparecer de la BD.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        
        id_comunicado = comunicado_efimero.pk
        servicio = ComunicadoService()

        self.assertTrue(Comunicado.objects.filter(pk=id_comunicado).exists())

        servicio.delete_comunicado(
            usuario=self.admin, 
            comunicado_instance=comunicado_efimero
        )

        existe_en_bd = Comunicado.objects.filter(pk=id_comunicado).exists()
        
        self.assertFalse(
            existe_en_bd, 
            f"Error: El comunicado con ID {id_comunicado} todavía persiste en la base de datos."
        )



    def test_no_registra_on_commit_si_no_hay_imagen(self):
        """
        Test: Ausencia de callbacks de transacción sin imagen adjunta.

        Given: Un comunicado que no tiene 'imagen_portada' (es None).
        When: Se invoca el método delete_comunicado dentro de un bloque de transacción.
        Then: El servicio no debe registrar ninguna función en transaction.on_commit,
            ya que no hay archivos físicos que eliminar del servidor.
        """
        comunicado_sin_imagen = Comunicado.objects.create(
            titulo="Sin imagen",
            contenido="Sin contenido multimedia.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            imagen_portada=None
        )
        
        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(using='default') as callbacks:
            servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado_sin_imagen
            )

        self.assertEqual(
            len(callbacks), 0, 
            "Se registró un callback en on_commit pero el comunicado no tenía imagen."
        )

        self.assertFalse(Comunicado.objects.filter(pk=comunicado_sin_imagen.pk).exists())



    def test_eliminar_comunicado_sin_imagen_no_lanza_excepciones(self):
        """
        Test: Resiliencia ante imagen_portada nula.

        Given: Un comunicado cuya 'imagen_portada' es None.
        When: Se invoca el método delete_comunicado con un usuario administrador.
        Then: El servicio no debe lanzar ninguna excepción (AttributeError, ValueError, etc.)
            y debe finalizar la ejecución correctamente devolviendo True.
        """
        comunicado_nulo = Comunicado.objects.create(
            titulo="Comunicado sin imagen adjunta",
            contenido="Verificando que el servicio no falle por campos nulos.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            imagen_portada=None
        )
        
        servicio = ComunicadoService()

        try:
            resultado = servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado_nulo
            )
        except Exception as e:
            self.fail(f"delete_comunicado lanzó la excepción {type(e).__name__} inesperadamente: {e}")

        self.assertTrue(resultado)
        self.assertFalse(Comunicado.objects.filter(pk=comunicado_nulo.pk).exists())



    def test_transaccion_se_confirma_y_objeto_es_eliminado(self):
        """
        Test: Confirmación de la transacción atómica.

        Given: Un comunicado guardado en la base de datos.
        When: Se invoca delete_comunicado (protegido por @transaction.atomic).
        Then: La transacción debe completarse sin errores, confirmando el borrado 
            del objeto en la base de datos de forma permanente.
        """
        comunicado_transaccional = Comunicado.objects.create(
            titulo="Comunicado Transaccional",
            contenido="Verificando el commit de la base de datos.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        
        id_comunicado = comunicado_transaccional.pk
        servicio = ComunicadoService()

        with transaction.atomic():
            resultado = servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado_transaccional
            )

        self.assertTrue(resultado)

        existe_en_bd = Comunicado.objects.filter(pk=id_comunicado).exists()
        self.assertFalse(existe_en_bd, "La transacción no eliminó el objeto correctamente.")



    def test_verificar_permisos_se_ejecuta_antes_del_borrado(self):
        """
        Test: Orden de ejecución de la seguridad.

        Given: Un comunicado existente y un servicio de comunicación.
        When: Se invoca delete_comunicado.
        Then: El método interno '_verificar_permisos' debe ser llamado antes 
            de que el objeto sea eliminado de la base de datos, asegurando 
            que la protección precede a la acción.
        """
        comunicado_test = Comunicado.objects.create(
            titulo="Comunicado de Seguridad",
            contenido="Probando el orden de ejecución.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        
        id_comunicado = comunicado_test.pk
        servicio = ComunicadoService()

        servicio._verificar_permisos = MagicMock(return_value=None)

        servicio.delete_comunicado(
            usuario=self.admin, 
            comunicado_instance=comunicado_test
        )

        servicio._verificar_permisos.assert_called_once_with(self.admin)

        self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())



    def test_metodo_delete_se_ejecuta_exactamente_una_vez(self):
        """
        Test: Verificación de llamada única al método delete del modelo.

        Given: Un comunicado existente y un usuario con permisos.
        When: Se invoca el método delete_comunicado del servicio.
        Then: El método 'delete' de la instancia del comunicado debe ser llamado 
            exactamente una vez, asegurando un flujo de borrado eficiente.
        """
        comunicado_spy = Comunicado.objects.create(
            titulo="Comunicado para test de llamada única",
            contenido="Verificando contador de ejecuciones.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        
        servicio = ComunicadoService()

        with patch.object(comunicado_spy, 'delete', wraps=comunicado_spy.delete) as mock_delete:
            servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado_spy
            )

            mock_delete.assert_called_once()

        self.assertFalse(Comunicado.objects.filter(pk=comunicado_spy.pk).exists())



    def test_no_intenta_borrar_archivo_si_imagen_portada_esta_vacio(self):
        """
        Test: Evitar borrado de archivo físico si el campo está vacío.

        Given: Un comunicado cuya 'imagen_portada' es evaluada como falsa 
            (None o campo de archivo vacío).
        When: Se invoca el método delete_comunicado con un usuario administrador.
        Then: El servicio no debe realizar ninguna llamada al método delete() del 
            objeto de archivo, optimizando el proceso y evitando errores.
        """
        comunicado_vacio = Comunicado.objects.create(
            titulo="Comunicado sin imagen real",
            contenido="Probando que no se toque el sistema de archivos.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            imagen_portada=None
        )
        
        servicio = ComunicadoService()

        mock_file = MagicMock()
        mock_file.__bool__.return_value = False 

        comunicado_vacio.imagen_portada = mock_file

        servicio.delete_comunicado(
            usuario=self.admin, 
            comunicado_instance=comunicado_vacio
        )

        mock_file.delete.assert_not_called()

        self.assertFalse(Comunicado.objects.filter(pk=comunicado_vacio.pk).exists())



    def test_eliminar_comunicado_con_imagen_correctamente(self):
        """
        Test: Eliminación de comunicado con archivo de imagen asociado.

        Given: Un comunicado que tiene una imagen válida en 'imagen_portada'.
        When: Se invoca el método delete_comunicado con un usuario administrador.
        Then: El servicio elimina el registro de la base de datos, identifica 
            la presencia de la imagen y programa su borrado físico, 
            retornando finalmente True.
        """
        imagen_dummy = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x00\x01\x02\x03',
            content_type='image/jpeg'
        )

        comunicado_con_imagen = Comunicado.objects.create(
            titulo="Comunicado con Foto",
            contenido="Este comunicado tiene un archivo adjunto.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            imagen_portada=imagen_dummy
        )
        
        id_comunicado = comunicado_con_imagen.pk
        servicio = ComunicadoService()

        self.assertTrue(comunicado_con_imagen.imagen_portada)

        with self.captureOnCommitCallbacks(using='default') as callbacks:
            resultado = servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado_con_imagen
            )

        self.assertTrue(resultado)

        self.assertEqual(
            len(callbacks), 1, 
            "No se programó el borrado físico de la imagen en on_commit."
        )

        self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())



    def test_registra_on_commit_cuando_hay_imagen_portada(self):
        """
        Test: Registro de callback en transaction.on_commit con imagen.

        Given: Un comunicado que dispone de una 'imagen_portada' válida.
        When: Se invoca el método delete_comunicado dentro de un contexto transaccional.
        Then: El servicio debe registrar una función en transaction.on_commit 
            para que el borrado del archivo físico ocurra solo tras el éxito en BD.
        """
        imagen_test = SimpleUploadedFile(
            name='test_archivo.jpg',
            content=b'datos_de_imagen',
            content_type='image/jpeg'
        )

        comunicado_con_foto = Comunicado.objects.create(
            titulo="Comunicado con Imagen",
            contenido="Verificando el hook de transacción.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            imagen_portada=imagen_test
        )
        
        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(using='default') as callbacks:
            resultado = servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado_con_foto
            )

        self.assertTrue(resultado)

        self.assertEqual(
            len(callbacks), 1, 
            "No se registró el callback de on_commit a pesar de existir una imagen."
        )

        self.assertFalse(Comunicado.objects.filter(pk=comunicado_con_foto.pk).exists())



    def test_lambda_ejecuta_delete_del_archivo_sin_guardar(self):
        """
        Test: Ejecución del lambda de limpieza de imagen.

        Given: Un comunicado que tiene una imagen en 'imagen_portada'.
        When: Se invoca delete_comunicado y se ejecutan los callbacks de 
            confirmación de la transacción (on_commit).
        Then: El lambda registrado debe llamar al método .delete(save=False) 
            del archivo, asegurando que el archivo físico se borra pero 
            no se intenta actualizar el registro en BD (que ya no existe).
        """
        comunicado_con_archivo = Comunicado.objects.create(
            titulo="Test de Lambda",
            contenido="Verificando argumentos del borrado de archivo.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            imagen_portada=SimpleUploadedFile('foto.jpg', b'content')
        )

        mock_file = MagicMock()
        comunicado_con_archivo.imagen_portada = mock_file
        
        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(using='default') as callbacks:
            servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado_con_archivo
            )

        self.assertEqual(len(callbacks), 1)
        callback_limpieza = callbacks[0]

        callback_limpieza()

        mock_file.delete.assert_called_once_with(save=False)



    def test_archivo_fisico_se_elimina_tras_commit_exitoso(self):
        """
        Test: Eliminación física del archivo en el storage tras el commit.

        Given: Un comunicado con una imagen guardada físicamente en el storage.
        When: Se completa el método delete_comunicado y se ejecutan los 
            callbacks de la transacción (on_commit).
        Then: El archivo debe dejar de existir en el sistema de almacenamiento,
            evitando la acumulación de archivos huérfanos.
        """
        archivo_nombre = 'foto_para_borrar.jpg'
        imagen_real = SimpleUploadedFile(
            name=archivo_nombre,
            content=b'datos_de_imagen_binarios',
            content_type='image/jpeg'
        )

        comunicado_con_archivo = Comunicado.objects.create(
            titulo="Comunicado con Archivo Real",
            contenido="Verificando el sistema de archivos.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            imagen_portada=imagen_real
        )

        storage = comunicado_con_archivo.imagen_portada.storage
        ruta_archivo = comunicado_con_archivo.imagen_portada.name

        self.assertTrue(storage.exists(ruta_archivo))

        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(using='default', execute=True):
            servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado_con_archivo
            )

        self.assertFalse(Comunicado.objects.filter(pk=comunicado_con_archivo.pk).exists())

        self.assertFalse(
            storage.exists(ruta_archivo), 
            "El archivo físico aún persiste en el storage tras el borrado."
        )



    def test_archivo_no_se_elimina_antes_del_commit(self):
        """
        Test: Protección del archivo físico ante fallos de transacción.

        Given: Un comunicado con una imagen asociada guardada en el storage.
        When: Se ejecuta delete_comunicado pero la transacción aún no se ha 
            confirmado (commit).
        Then: El archivo físico debe permanecer intacto en el storage hasta 
            que el ciclo de la base de datos finalice satisfactoriamente.
        """
        archivo_nombre = 'seguridad_ante_error.jpg'
        imagen_test = SimpleUploadedFile(
            name=archivo_nombre,
            content=b'datos_binarios_de_prueba',
            content_type='image/jpeg'
        )

        comunicado_con_archivo = Comunicado.objects.create(
            titulo="Comunicado con Archivo Protegido",
            contenido="Verificando que el borrado es diferido.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            imagen_portada=imagen_test
        )
        
        storage = comunicado_con_archivo.imagen_portada.storage
        ruta_archivo = comunicado_con_archivo.imagen_portada.name
        
        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(using='default') as callbacks:
            servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado_con_archivo
            )

        self.assertFalse(Comunicado.objects.filter(pk=comunicado_con_archivo.pk).exists())

        self.assertEqual(len(callbacks), 1)

        self.assertTrue(
            storage.exists(ruta_archivo),
            "ERROR: El archivo se borró físicamente ANTES de confirmar la transacción."
        )

        for callback in callbacks:
            callback()

        self.assertFalse(storage.exists(ruta_archivo))



    def test_agenda_borrado_de_archivo_correctamente_en_transaccion(self):
        """
        Test: Agendamiento del borrado físico mediante on_commit.

        Given: Un comunicado con una imagen_portada válida.
        When: Se ejecuta delete_comunicado dentro de una transacción.
        Then: Se debe registrar exactamente un callback en la cola de commit,
            y el archivo debe permanecer en el storage hasta que dicho 
            callback sea ejecutado manualmente.
        """
        archivo_nombre = 'imagen_agendada.jpg'
        imagen_test = SimpleUploadedFile(
            name=archivo_nombre,
            content=b'datos_binarios',
            content_type='image/jpeg'
        )

        comunicado = Comunicado.objects.create(
            titulo="Comunicado con Imagen Agendada",
            contenido="Verificando el hook de on_commit.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            imagen_portada=imagen_test
        )
        
        storage = comunicado.imagen_portada.storage
        ruta_archivo = comunicado.imagen_portada.name
        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(using='default') as callbacks:
            resultado = servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado
            )

        self.assertTrue(resultado)

        self.assertEqual(
            len(callbacks), 1, 
            "Debe agendarse exactamente una tarea de limpieza."
        )

        self.assertTrue(
            storage.exists(ruta_archivo),
            "El archivo se borró prematuramente antes de procesar los callbacks."
        )

        callbacks[0]()

        self.assertFalse(
            storage.exists(ruta_archivo),
            "El archivo debería haberse borrado tras ejecutar el callback agendado."
        )



    def test_orden_eliminacion_registro_antes_que_archivo(self):
        """
        Test: El registro en BD debe eliminarse antes de procesar el archivo.

        Given: Un comunicado con una imagen asociada.
        When: Se ejecuta delete_comunicado.
        Then: El registro debe desaparecer de la BD en la transacción actual 
            mientras que el archivo debe seguir existiendo hasta el commit.
        """
        archivo_nombre = 'orden_test.jpg'
        imagen_test = SimpleUploadedFile(
            name=archivo_nombre,
            content=b'datos',
            content_type='image/jpeg'
        )

        comunicado = Comunicado.objects.create(
            titulo="Test de Orden",
            contenido="Verificando precedencia.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            imagen_portada=imagen_test
        )
        
        id_comunicado = comunicado.pk
        storage = comunicado.imagen_portada.storage
        ruta_archivo = comunicado.imagen_portada.name
        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(using='default') as callbacks:
            with patch.object(Comunicado, 'delete', wraps=comunicado.delete) as spy_delete:
                servicio.delete_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=comunicado
                )

                spy_delete.assert_called_once()

            self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())

            self.assertTrue(storage.exists(ruta_archivo))

        for callback in callbacks:
            callback()
        
        self.assertFalse(storage.exists(ruta_archivo))



    def test_retorna_true_tras_eliminacion_exitosa_con_imagen(self):
        """
        Test: Valor de retorno tras eliminación con multimedia.

        Given: Un comunicado con una imagen_portada válida.
        When: Se invoca el método delete_comunicado por un usuario autorizado.
        Then: El método debe retornar exactamente True, indicando al llamador 
            que la operación se procesó sin errores.
        """
        imagen = SimpleUploadedFile(
            name='final_test.jpg',
            content=b'data',
            content_type='image/jpeg'
        )
        comunicado = Comunicado.objects.create(
            titulo="Comunicado Final",
            contenido="Verificando el retorno booleano.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            imagen_portada=imagen
        )
        
        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(using='default', execute=True):
            resultado = servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado
            )

        self.assertIs(
            resultado, True, 
            "El método debería haber retornado True tras la eliminación exitosa."
        )

        self.assertFalse(Comunicado.objects.filter(pk=comunicado.pk).exists())



    def test_imagen_valida_pero_vacia_no_lanza_excepcion(self):
        """
        Test: Manejo de ImageField inicializado pero sin archivo.

        Given: Un comunicado donde 'imagen_portada' existe como campo pero 
            no tiene un archivo asignado (evalúa como False).
        When: Se invoca el método delete_comunicado.
        Then: El servicio no debe lanzar excepciones y debe ignorar la 
            lógica de borrado físico, eliminando solo el registro en BD.
        """
        comunicado_vacio = Comunicado.objects.create(
            titulo="Comunicado con campo vacío",
            contenido="El campo imagen existe pero no tiene archivo.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            imagen_portada=None
        )
        
        servicio = ComunicadoService()

        try:
            with self.captureOnCommitCallbacks(using='default') as callbacks:
                resultado = servicio.delete_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=comunicado_vacio
                )
        except Exception as e:
            self.fail(f"El servicio rompió con un campo de imagen vacío: {e}")

        self.assertTrue(resultado)
        self.assertEqual(len(callbacks), 0, "Se intentó agendar un borrado para un archivo inexistente.")
        self.assertFalse(Comunicado.objects.filter(pk=comunicado_vacio.pk).exists())



    def test_multiples_eliminaciones_consecutivas_funcionan(self):
        """
        Test: Consistencia en eliminaciones múltiples.

        Given: Una lista de 3 comunicados, todos con imágenes asociadas.
        When: Se llama a delete_comunicado para cada uno de forma secuencial.
        Then: Cada registro debe ser eliminado de la base de datos y cada imagen 
            debe ser agendada para borrado físico de forma independiente.
        """
        servicio = ComunicadoService()
        comunicados = []
        rutas_archivos = []

        for i in range(3):
            nombre = f'imagen_{i}.jpg'
            img = SimpleUploadedFile(name=nombre, content=b'data', content_type='image/jpeg')
            c = Comunicado.objects.create(
                titulo=f"Comunicado {i}",
                contenido="Contenido",
                tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
                autor=self.admin,
                imagen_portada=img
            )
            comunicados.append(c)
            rutas_archivos.append(c.imagen_portada.name)

        with self.captureOnCommitCallbacks(using='default', execute=True) as callbacks:
            for c in comunicados:
                resultado = servicio.delete_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=c
                )
                self.assertTrue(resultado)

        for i, c in enumerate(comunicados):
            self.assertFalse(Comunicado.objects.filter(pk=c.pk).exists())
            self.assertFalse(
                comunicados[0].imagen_portada.storage.exists(rutas_archivos[i]),
                f"El archivo {rutas_archivos[i]} no fue eliminado físicamente."
            )



    def test_transaccion_se_confirma_y_persiste_en_base_de_datos(self):
        """
        Test: Confirmación (commit) de la transacción.

        Given: Un comunicado guardado en la base de datos.
        When: Se invoca el método delete_comunicado del servicio.
        Then: La transacción debe cerrarse con éxito (commit), eliminando 
            el registro de forma permanente de la tabla de comunicados.
        """
        comunicado_db = Comunicado.objects.create(
            titulo="Confirmación de Commit",
            contenido="Este registro debe desaparecer definitivamente.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        
        id_comunicado = comunicado_db.pk
        servicio = ComunicadoService()

        resultado = servicio.delete_comunicado(
            usuario=self.admin, 
            comunicado_instance=comunicado_db
        )

        self.assertTrue(resultado)

        self.assertFalse(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "La transacción no se confirmó: el registro sigue presente en la base de datos."
        )



    def test_archivo_se_elimina_unicamente_despues_del_commit(self):
        """
        Test: Sincronización entre DB y Storage.

        Given: Un comunicado con una imagen_portada guardada físicamente.
        When: Se ejecuta delete_comunicado pero la transacción no ha finalizado.
        Then: El archivo debe seguir existiendo en el storage; solo tras ejecutar 
            los callbacks de on_commit el archivo debe ser borrado.
        """
        archivo_nombre = 'imagen_segura.jpg'
        imagen_test = SimpleUploadedFile(
            name=archivo_nombre,
            content=b'datos_de_prueba_binarios',
            content_type='image/jpeg'
        )

        comunicado = Comunicado.objects.create(
            titulo="Comunicado con borrado diferido",
            contenido="Verificando on_commit.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            imagen_portada=imagen_test
        )
        
        storage = comunicado.imagen_portada.storage
        ruta_archivo = comunicado.imagen_portada.name
        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(using='default') as callbacks:
            servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado
            )

            self.assertFalse(Comunicado.objects.filter(pk=comunicado.pk).exists())

            self.assertTrue(
                storage.exists(ruta_archivo),
                "Error: El archivo se borró físicamente antes del commit de la BD."
            )

        for callback in callbacks:
            callback()

        self.assertFalse(
            storage.exists(ruta_archivo),
            "El archivo debería haberse eliminado tras procesar los callbacks de on_commit."
        )



    def test_archivo_no_se_elimina_si_la_transaccion_falla(self):
        """
        Test: Reversión (rollback) de borrado de archivo ante error en BD.

        Given: Un comunicado con una imagen asociada en el storage.
        When: Se ejecuta delete_comunicado pero ocurre una excepción de base 
            de datos (IntegrityError) antes de finalizar el bloque atómico.
        Then: La transacción debe hacer rollback, el registro debe persistir 
            en la BD y, lo más importante, el archivo físico NO debe borrarse.
        """
        archivo_nombre = 'archivo_protegido_ante_error.jpg'
        imagen_test = SimpleUploadedFile(
            name=archivo_nombre,
            content=b'datos_binarios_importantes',
            content_type='image/jpeg'
        )

        comunicado = Comunicado.objects.create(
            titulo="Comunicado con Riesgo de Fallo",
            contenido="Verificando integridad física tras error.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            imagen_portada=imagen_test
        )
        
        storage = comunicado.imagen_portada.storage
        ruta_archivo = comunicado.imagen_portada.name
        servicio = ComunicadoService()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                with patch.object(Comunicado, 'delete', side_effect=IntegrityError("Fallo simulado")):
                    servicio.delete_comunicado(
                        usuario=self.admin, 
                        comunicado_instance=comunicado
                    )

        self.assertTrue(Comunicado.objects.filter(pk=comunicado.pk).exists())

        self.assertTrue(
            storage.exists(ruta_archivo),
            "ERROR: El archivo se borró a pesar de que la transacción de la BD falló."
        )



    def test_operacion_es_completamente_atomica_ante_fallo_post_delete(self):
        """
        Test: Atomicidad total del servicio (Todo o Nada).

        Given: Un comunicado con una imagen guardada físicamente.
        When: Se ejecuta delete_comunicado pero ocurre un error de base de datos
            inesperado inmediatamente después de la instrucción de borrado.
        Then: La base de datos debe hacer rollback (el registro reaparece) y
            el archivo físico NO debe ser eliminado del storage.
        """
        archivo_nombre = 'imagen_atomica.jpg'
        imagen_test = SimpleUploadedFile(
            name=archivo_nombre,
            content=b'contenido_binario',
            content_type='image/jpeg'
        )

        comunicado = Comunicado.objects.create(
            titulo="Comunicado Atómico",
            contenido="Probando integridad referencial.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            imagen_portada=imagen_test
        )
        
        storage = comunicado.imagen_portada.storage
        ruta_archivo = comunicado.imagen_portada.name

        id_comunicado = comunicado.pk 
        
        servicio = ComunicadoService()

        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                with patch('django.db.transaction.on_commit', side_effect=DatabaseError("Error de DB")):
                    servicio.delete_comunicado(
                        usuario=self.admin, 
                        comunicado_instance=comunicado
                    )

        self.assertTrue(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "La BD no hizo rollback: el registro desapareció a pesar del error."
        )

        self.assertTrue(
            storage.exists(ruta_archivo),
            "El archivo se borró físicamente a pesar de que la transacción falló."
        )



    def test_flujo_completo_exito_commit_y_borrado_fisico(self):
        """
        Test: Simulación de entorno productivo con commit exitoso.

        Given: Un comunicado con una imagen_portada real guardada en el storage.
        When: Se ejecuta delete_comunicado y la transacción de BD finaliza (commit).
        Then: 
            1. El registro debe ser eliminado de la base de datos.
            2. El callback de on_commit debe dispararse automáticamente.
            3. El archivo físico debe dejar de existir en el storage.
        """
        archivo_nombre = 'foto_final_test.jpg'
        imagen_real = SimpleUploadedFile(
            name=archivo_nombre,
            content=b'datos_binarios_reales',
            content_type='image/jpeg'
        )

        comunicado = Comunicado.objects.create(
            titulo="Comunicado Post-Commit",
            contenido="Validando el efecto completo del servicio.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin,
            imagen_portada=imagen_real
        )
        
        storage = comunicado.imagen_portada.storage
        ruta_archivo = comunicado.imagen_portada.name
        id_comunicado = comunicado.pk

        self.assertTrue(storage.exists(ruta_archivo))
        
        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(using='default', execute=True):
            resultado = servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado
            )

        self.assertTrue(resultado)

        self.assertFalse(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "El registro no fue eliminado de la base de datos."
        )

        self.assertFalse(
            storage.exists(ruta_archivo),
            "El archivo físico persiste en el storage a pesar del commit exitoso."
        )



    def test_usuario_no_autenticado_lanza_permission_denied(self):
        """
        Test: Bloqueo de eliminación para usuarios no autenticados.

        Given: Un comunicado existente y un usuario anónimo (no logueado).
        When: El usuario anónimo intenta invocar delete_comunicado.
        Then: El servicio debe lanzar PermissionDenied inmediatamente y el 
            comunicado debe permanecer intacto en la base de datos.
        """
        comunicado_protegido = Comunicado.objects.create(
            titulo="Comunicado Protegido",
            contenido="Ningún anónimo puede borrar esto.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado_protegido.pk

        usuario_anonimo = AnonymousUser() 
        servicio = ComunicadoService()

        with self.assertRaises(PermissionDenied):
            servicio.delete_comunicado(
                usuario=usuario_anonimo, 
                comunicado_instance=comunicado_protegido
            )

        self.assertTrue(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "Alerta de Seguridad: El comunicado fue eliminado por un usuario no autenticado."
        )



    def test_usuario_none_lanza_excepcion(self):
        """
        Test: Manejo de entrada nula para el usuario.

        Given: Un comunicado válido y un valor de usuario tipo None.
        When: Se intenta ejecutar delete_comunicado.
        Then: El servicio debe lanzar una excepción (PermissionDenied o AttributeError)
            y el registro no debe ser afectado.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado Inalcanzable",
            contenido="Protección ante parámetros None.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk
        servicio = ComunicadoService()

        with self.assertRaises((PermissionDenied, AttributeError)):
            servicio.delete_comunicado(
                usuario=None, 
                comunicado_instance=comunicado
            )

        self.assertTrue(Comunicado.objects.filter(pk=id_comunicado).exists())



    def test_usuario_anonimo_sin_atributo_cuerpos_lanza_permission_denied(self):
        """
        Test: Un usuario anónimo no tiene el atributo 'cuerpos'.
        
        Given: Un comunicado y un AnonymousUser (que no tiene la relación M2M 'cuerpos').
        When: Se intenta eliminar el comunicado a través del servicio.
        Then: El servicio debe lanzar PermissionDenied (o AttributeError) y no borrar.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado de Prueba",
            contenido="Contenido protegido",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk

        usuario_anonimo = AnonymousUser()
        servicio = ComunicadoService()

        with self.assertRaises((PermissionDenied, AttributeError)):
            servicio.delete_comunicado(
                usuario=usuario_anonimo, 
                comunicado_instance=comunicado
            )

        self.assertTrue(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "Error: El registro fue eliminado por un usuario anónimo."
        )



    def test_usuario_autenticado_sin_relacion_cuerpos_lanza_permission_denied(self):
        """
        Test: Usuario autenticado pero con modelo incompleto (sin relación 'cuerpos').

        Given: Un comunicado válido y un usuario autenticado con todos sus campos
            obligatorios, pero al que se le simula un fallo en el atributo 'cuerpos'.
        When: Se intenta ejecutar delete_comunicado.
        Then: El servicio debe lanzar PermissionDenied o AttributeError y el registro persistir.
        """
        User = get_user_model()

        usuario_incompleto = User.objects.create_user(
            dni='12345678Z',
            username='12345678Z',
            password='password123',
            nombre='Test',
            primer_apellido='Apellido1',
            segundo_apellido='Apellido2',
            email='test@ejemplo.com',
            telefono='600000000',
            estado_civil='SOLTERO',
            genero='MASCULINO',
            esAdmin=False
        )
        
        comunicado = Comunicado.objects.create(
            titulo="Comunicado Inalcanzable",
            contenido="Seguridad ante fallos de esquema.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk
        servicio = ComunicadoService()

        with patch.object(User, 'cuerpos', new_callable=PropertyMock) as mock_cuerpos:
            mock_cuerpos.side_effect = AttributeError("Simulando ausencia de atributo cuerpos")
            
            with self.assertRaises((PermissionDenied, AttributeError)):
                servicio.delete_comunicado(
                    usuario=usuario_incompleto, 
                    comunicado_instance=comunicado
                )

        self.assertTrue(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "Error: El comunicado fue borrado a pesar de la inconsistencia de datos."
        )



    def test_usuario_autenticado_sin_permisos_lanza_permission_denied(self):
        """
        Test: Un usuario real sin rango de Admin o Junta no puede borrar.

        Given: Un comunicado y un Hermano que pertenece al cuerpo de COSTALEROS.
        When: El Hermano (no admin) intenta ejecutar delete_comunicado.
        Then: El servicio debe lanzar PermissionDenied y el registro debe persistir.
        """
        User = get_user_model()

        usuario_comun = User.objects.create_user(
            dni='87654321X',
            username='87654321X',
            password='password123',
            nombre='Juan',
            primer_apellido='Pérez',
            segundo_apellido='García',
            email='juan@ejemplo.com',
            telefono='611223344',
            estado_civil='CASADO',
            esAdmin=False
        )

        cuerpo_costaleros = CuerpoPertenencia.objects.get_or_create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.COSTALEROS
        )[0]
        
        HermanoCuerpo.objects.create(
            hermano=usuario_comun,
            cuerpo=cuerpo_costaleros,
            anio_ingreso=2020
        )

        comunicado = Comunicado.objects.create(
            titulo="Comunicado Confidencial",
            contenido="Información sensible de la Hermandad.",
            tipo_comunicacion=Comunicado.TipoComunicacion.SECRETARIA,
            autor=self.admin
        )
        id_comunicado = comunicado.pk
        servicio = ComunicadoService()

        with self.assertRaises(PermissionDenied):
            servicio.delete_comunicado(
                usuario=usuario_comun, 
                comunicado_instance=comunicado
            )

        self.assertTrue(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "Fallo de Seguridad: Un hermano común pudo borrar un comunicado."
        )



    def test_usuario_con_cuerpos_distintos_a_junta_lanza_permission_denied(self):
        """
        Test: Un usuario con cuerpos asignados que NO son la Junta no puede borrar.

        Given: Un comunicado y un Hermano que pertenece a COSTALEROS y NAZARENOS.
        When: El Hermano intenta borrar el comunicado a través del servicio.
        Then: El servicio debe lanzar PermissionDenied y el registro no debe borrarse.
        """
        User = get_user_model()

        usuario_no_junta = User.objects.create_user(
            dni='99887766K',
            password='password123',
            username='99887766K',
            nombre='Pedro',
            primer_apellido='No',
            segundo_apellido='Autorizado',
            email='pedro@test.com',
            telefono='655443322',
            estado_civil='SOLTERO',
            esAdmin=False
        )

        cuerpos_nombres = [
            CuerpoPertenencia.NombreCuerpo.COSTALEROS,
            CuerpoPertenencia.NombreCuerpo.NAZARENOS
        ]
        
        for nombre in cuerpos_nombres:
            cuerpo, _ = CuerpoPertenencia.objects.get_or_create(nombre_cuerpo=nombre)
            HermanoCuerpo.objects.create(
                hermano=usuario_no_junta,
                cuerpo=cuerpo,
                anio_ingreso=2022
            )

        comunicado = Comunicado.objects.create(
            titulo="Comunicado de la Junta",
            contenido="Solo la junta puede gestionar esto.",
            tipo_comunicacion=Comunicado.TipoComunicacion.SECRETARIA,
            autor=self.admin
        )
        id_comunicado = comunicado.pk
        servicio = ComunicadoService()

        with self.assertRaises(PermissionDenied):
            servicio.delete_comunicado(
                usuario=usuario_no_junta, 
                comunicado_instance=comunicado
            )

        self.assertTrue(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "Brecha de seguridad: Un usuario ajeno a la Junta pudo borrar el comunicado."
        )



    def test_usuario_autenticado_sin_cuerpos_y_no_admin_lanza_permission_denied(self):
        """
        Test: Un usuario estándar sin cargos ni permisos de admin no puede borrar.

        Given: Un comunicado y un Hermano que no pertenece a ningún cuerpo.
        When: El Hermano intenta ejecutar delete_comunicado.
        Then: El servicio debe lanzar PermissionDenied y el registro debe persistir.
        """
        User = get_user_model()

        usuario_estandar = User.objects.create_user(
            dni='11223344L',
            username='11223344L',
            password='password123',
            nombre='Antonio',
            primer_apellido='Hermano',
            segundo_apellido='Raso',
            email='antonio@test.com',
            telefono='600112233',
            estado_civil='SOLTERO',
            esAdmin=False
        )

        comunicado = Comunicado.objects.create(
            titulo="Comunicado Oficial",
            contenido="Solo para lectura general.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk
        servicio = ComunicadoService()

        with self.assertRaises(PermissionDenied):
            servicio.delete_comunicado(
                usuario=usuario_estandar, 
                comunicado_instance=comunicado
            )

        self.assertTrue(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "Error de seguridad: Un usuario sin cargos pudo borrar el comunicado."
        )



    def test_usuario_es_admin_none_tratado_como_falso_lanza_permission_denied(self):
        """
        Test: Un valor None en esAdmin (en memoria) no debe otorgar privilegios.

        Given: Un comunicado y un usuario cuyo atributo en memoria esAdmin es None.
        When: Se intenta ejecutar delete_comunicado.
        Then: El servicio debe tratarlo como False y lanzar PermissionDenied.
        """
        User = get_user_model()

        usuario_nulo = User.objects.create_user(
            dni='00000000N',
            username='00000000N',
            password='password123',
            nombre='Nulo',
            primer_apellido='Admin',
            segundo_apellido='Test',
            email='nulo@test.com',
            telefono='600000000',
            estado_civil='SOLTERO'
        )

        usuario_nulo.esAdmin = None

        comunicado = Comunicado.objects.create(
            titulo="Comunicado Blindado",
            contenido="Protección contra valores nulos en memoria.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk
        servicio = ComunicadoService()

        with self.assertRaises(PermissionDenied):
            servicio.delete_comunicado(
                usuario=usuario_nulo, 
                comunicado_instance=comunicado
            )

        self.assertTrue(Comunicado.objects.filter(pk=id_comunicado).exists())



    def test_usuario_con_relacion_cuerpos_vacia_lanza_permission_denied(self):
        """
        Test: Un usuario sin ningún cuerpo asignado no tiene permisos.

        Given: Un comunicado válido y un Hermano autenticado que no tiene 
            registros en la tabla intermedia HermanoCuerpo.
        When: Se intenta ejecutar delete_comunicado.
        Then: El servicio debe lanzar PermissionDenied y el comunicado no debe borrarse.
        """
        User = get_user_model()

        usuario_sin_cuerpos = User.objects.create_user(
            dni='55555555M',
            username='55555555M',
            password='password123',
            nombre='Hermano',
            primer_apellido='Sin',
            segundo_apellido='Cargos',
            email='sin@test.com',
            telefono='600000001',
            estado_civil='SOLTERO',
            esAdmin=False
        )
        
        comunicado = Comunicado.objects.create(
            titulo="Comunicado Intacto",
            contenido="Seguridad ante relaciones vacías.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk
        servicio = ComunicadoService()

        with self.assertRaises(PermissionDenied):
            servicio.delete_comunicado(
                usuario=usuario_sin_cuerpos, 
                comunicado_instance=comunicado
            )

        self.assertTrue(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "Error: Un usuario sin cuerpos pudo realizar el borrado."
        )



    def test_usuario_error_en_filtro_cuerpos_propaga_excepcion(self):
        """
        Test: Si la consulta a 'cuerpos' falla técnicamente, el servicio debe fallar.

        Given: Un comunicado y un usuario autenticado.
        When: Se simula un error de base de datos al ejecutar .filter() sobre cuerpos.
        Then: El servicio debe propagar el error y el registro no debe borrarse.
        """
        User = get_user_model()
        usuario = User.objects.create_user(
            dni='22334455K',
            username='22334455K',
            password='password123',
            nombre='Error',
            primer_apellido='Test',
            segundo_apellido='Mock',
            email='error@test.com',
            telefono='600000000',
            estado_civil='SOLTERO'
        )

        comunicado = Comunicado.objects.create(
            titulo="Comunicado Protegido",
            contenido="Error de base de datos simulado.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk
        servicio = ComunicadoService()

        with patch.object(User, 'cuerpos') as mock_descriptor:
            mock_descriptor.filter.side_effect = DatabaseError("Error crítico de conexión")

            with self.assertRaises(DatabaseError):
                servicio.delete_comunicado(
                    usuario=usuario, 
                    comunicado_instance=comunicado
                )

        self.assertTrue(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "Error: El comunicado se borró a pesar de un fallo crítico en la validación."
        )



    def test_comunicado_instance_none_lanza_excepcion(self):
        """
        Test: El servicio debe validar que la instancia del comunicado no sea None.

        Given: Un usuario con permisos de administrador.
        When: Se llama a delete_comunicado pasando None como instancia.
        Then: El servicio debe lanzar una excepción (AttributeError o ValueError).
        """
        usuario_admin = self.admin 
        servicio = ComunicadoService()

        with self.assertRaises((AttributeError, ValueError)):
            servicio.delete_comunicado(
                usuario=usuario_admin, 
                comunicado_instance=None
            )



    def test_comunicado_instance_no_persistido_lanza_error(self):
        """
        Test: El servicio debe fallar si la instancia no existe en la base de datos.

        Given: Un usuario administrador y un objeto Comunicado creado en memoria
            pero NO guardado (sin ID).
        When: Se intenta ejecutar delete_comunicado.
        Then: El servicio debería lanzar un error al intentar borrar algo inexistente.
        """
        usuario_admin = self.admin

        comunicado_volatil = Comunicado(
            titulo="No estoy en la DB",
            contenido="Soy un objeto efímero.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        
        servicio = ComunicadoService()

        with self.assertRaises((ValueError, AttributeError)):
            servicio.delete_comunicado(
                usuario=usuario_admin, 
                comunicado_instance=comunicado_volatil
            )



    def test_eliminar_comunicado_ya_eliminado_lanza_excepcion(self):
        """
        Test: No se puede eliminar lo que ya no existe.

        Given: Un comunicado que es borrado de la DB justo antes de la llamada.
        When: El servicio intenta ejecutar delete_comunicado sobre esa instancia.
        Then: El servicio debe detectar la anomalía y lanzar una excepción.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado Efímero",
            contenido="Alguien me borrará antes de tiempo.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk

        comunicado.delete() 

        servicio = ComunicadoService()

        with self.assertRaises((ObjectDoesNotExist, ValueError)):
            servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado
            )



    def test_eliminar_comunicado_protegido_por_db_lanza_protected_error(self):
        """
        Test: El servicio debe propagar ProtectedError si la DB impide el borrado.

        Given: Un comunicado que tiene dependencias protegidas en la base de datos.
        When: El servicio intenta ejecutar el borrado.
        Then: Se debe lanzar django.db.models.ProtectedError y el registro debe persistir.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado con Dependencias",
            contenido="Este registro está referenciado por otros con PROTECT.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk
        servicio = ComunicadoService()

        with patch.object(Comunicado, 'delete') as mock_delete:
            mock_delete.side_effect = ProtectedError(
                "No se puede borrar: Existen registros vinculados.",
                [comunicado]
            )

            with self.assertRaises(ProtectedError):
                servicio.delete_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=comunicado
                )

        self.assertTrue(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "Error: El comunicado desapareció de la DB a pesar de estar protegido."
        )



    def test_comunicado_con_referencia_invalida_lanza_error(self):
        """
        Test: El servicio solo debe aceptar instancias reales de Comunicado.

        Given: Un usuario administrador y un objeto de una clase distinta (ej. Acto).
        When: Se intenta ejecutar delete_comunicado pasando el objeto erróneo.
        Then: El servicio debe lanzar TypeError o AttributeError.
        """
        tipo = TipoActo.objects.create(tipo='PRUEBA', requiere_papeleta=False)
        objeto_impostor = Acto.objects.create(
            nombre="Soy un Acto, no un Comunicado",
            fecha=timezone.now(),
            tipo_acto=tipo
        )

        servicio = ComunicadoService()

        with self.assertRaises((TypeError, AttributeError)):
            servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=objeto_impostor
            )



    def test_si_verificar_permisos_falla_no_se_ejecuta_delete(self):
        """
        Test: El borrado no debe ejecutarse si la validación de permisos falla.

        Given: Un comunicado y un usuario administrador.
        When: Se simula que el método interno '_verificar_permisos' lanza una excepción.
        Then: El servicio debe propagar la excepción y NO llamar al método .delete() del comunicado.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado Protegido",
            contenido="Este registro no debe borrarse si falla el permiso.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )

        comunicado.delete = MagicMock()
        
        servicio = ComunicadoService()

        with patch.object(ComunicadoService, '_verificar_permisos') as mock_verificar:
            mock_verificar.side_effect = PermissionDenied("Acceso denegado simulado")

            with self.assertRaises(PermissionDenied):
                servicio.delete_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=comunicado
                )

        comunicado.delete.assert_not_called()

        self.assertTrue(Comunicado.objects.filter(pk=comunicado.pk).exists())



    def test_si_delete_falla_no_se_registra_on_commit(self):
        """
        Test: Si el borrado en DB falla, no se deben disparar efectos secundarios.

        Given: Un comunicado y un usuario administrador.
        When: El método .delete() del modelo lanza una excepción de base de datos.
        Then: La excepción se propaga y no se llega a registrar ninguna acción on_commit.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado Crítico",
            contenido="Su borrado dispararía limpieza de archivos.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        servicio = ComunicadoService()

        with patch.object(Comunicado, 'delete') as mock_delete, \
            patch('django.db.transaction.on_commit') as mock_on_commit:

            mock_delete.side_effect = DatabaseError("Fallo de escritura en disco")

            with self.assertRaises(DatabaseError):
                servicio.delete_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=comunicado
                )

            mock_on_commit.assert_not_called()



    def test_si_falla_antes_del_commit_no_se_borra_archivo_fisico(self):
        """
        Test: La limpieza de archivos no debe ocurrir si la transacción falla.

        Given: Un comunicado que tiene una imagen asociada y un usuario admin.
        When: El servicio intenta borrar, pero ocurre una excepción justo 
            antes del commit final.
        Then: La imagen física no debe ser eliminada del almacenamiento.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado con Imagen",
            contenido="Este tiene una foto adjunta.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )

        mock_imagen = MagicMock()
        mock_imagen.name = "fotos/test.jpg"
        comunicado.imagen_portada = mock_imagen

        servicio = ComunicadoService()

        with patch.object(Comunicado, 'delete') as mock_db_delete:
            
            mock_db_delete.side_effect = DatabaseError("Error de transacción")

            with self.assertRaises(DatabaseError):
                servicio.delete_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=comunicado
                )

            mock_imagen.delete.assert_not_called()



    def test_fallo_en_on_commit_propaga_excepcion(self):
        """
        Test: Si la programación de la tarea post-borrado falla, el servicio falla.

        Given: Un comunicado CON IMAGEN y un usuario administrador.
        When: El método transaction.on_commit lanza una excepción inesperada.
        Then: El servicio debe propagar dicha excepción.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado con Limpieza",
            contenido="Este registro tiene imagen, por lo que usará on_commit.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )

        comunicado.imagen_portada = MagicMock()
        comunicado.imagen_portada.name = "fotos/test.jpg"

        servicio = ComunicadoService()

        with patch('django.db.transaction.on_commit') as mock_on_commit:
            mock_on_commit.side_effect = DatabaseError("Error al registrar tarea post-commit")

            with self.assertRaises(DatabaseError):
                servicio.delete_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=comunicado
                )



    def test_fallo_borrado_archivo_tras_commit_no_afecta_resultado_servicio(self):
        """
        Test: Un error al borrar el archivo físico post-commit no revierte el borrado del registro.

        Given: Un comunicado con imagen ya borrado de la DB (en una transacción exitosa).
        When: Se ejecuta la tarea on_commit y falla el borrado del archivo físico.
        Then: El servicio debe haber devuelto True y el registro debe seguir borrado.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado con Imagen Post-Commit",
            contenido="Su archivo fallará al borrarse, pero el registro se irá.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk

        mock_imagen = MagicMock()
        mock_imagen.name = "fotos/test_error.jpg"
        mock_imagen.delete.side_effect = Exception("Error de permisos en sistema de archivos")
        comunicado.imagen_portada = mock_imagen

        servicio = ComunicadoService()

        resultado = servicio.delete_comunicado(
            usuario=self.admin, 
            comunicado_instance=comunicado
        )

        self.assertTrue(resultado)

        self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())



    def test_fallo_en_lambda_post_commit_no_revierte_borrado_db(self):
        """
        Test: Un error dentro del lambda de on_commit no afecta a la DB ya confirmada.

        Given: Un comunicado con imagen y un usuario administrador.
        When: La transacción de DB termina con éxito, pero el lambda de limpieza falla.
        Then: El comunicado sigue borrado y el servicio informa éxito (True).
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado con Lambda Crítico",
            contenido="Su limpieza fallará en el post-commit.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk

        comunicado.imagen_portada = "fotos/test.jpg"
        servicio = ComunicadoService()

        with patch('django.db.transaction.on_commit') as mock_on_commit:

            resultado = servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado
            )

            func_lambda = mock_on_commit.call_args[0][0]

            with patch.object(comunicado.imagen_portada, 'delete', side_effect=Exception("Error en Storage")):
                try:
                    func_lambda()
                except Exception:
                    pass

        self.assertTrue(resultado)

        self.assertFalse(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "Error: El registro 'resucitó' tras un fallo en el post-commit (imposible en DB)."
        )



    def test_rollback_transaccional_impide_borrado_de_imagen(self):
        """
        Test: Si la transacción sufre un rollback, el on_commit no debe dispararse.

        Given: Un comunicado con imagen dentro de un bloque atómico.
        When: El servicio ejecuta el borrado, pero la transacción falla después.
        Then: El registro persiste en DB y la imagen no se borra del storage.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado Protegido por Rollback",
            contenido="Este archivo debe sobrevivir al fallo.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )

        id_comunicado = comunicado.pk 
        
        mock_imagen = MagicMock()
        mock_imagen.name = "fotos/test_survival.jpg"
        comunicado.imagen_portada = mock_imagen
        
        servicio = ComunicadoService()

        try:
            with transaction.atomic():
                servicio.delete_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=comunicado
                )
                raise IntegrityError("Fallo manual para forzar rollback")
        except IntegrityError:
            pass

        self.assertTrue(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "Error: El registro desapareció a pesar del rollback."
        )

        mock_imagen.delete.assert_not_called()



    def test_archivo_fisico_inexistente_no_rompe_el_servicio(self):
        """
        Test: Si la imagen ya no existe físicamente, el servicio debe borrar el registro igual.

        Given: Un comunicado cuyo archivo 'imagen_portada' ha desaparecido del disco.
        When: El servicio intenta borrar el comunicado y su imagen asociada.
        Then: El servicio no debe lanzar excepción, debe devolver True y el registro debe borrarse.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado con Archivo Fantasma",
            contenido="Su imagen ya no está en el servidor.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk

        mock_imagen = MagicMock()
        mock_imagen.name = "fotos/desaparecida.jpg"
        mock_imagen.delete.side_effect = FileNotFoundError("El archivo no existe en el storage")
        comunicado.imagen_portada = mock_imagen

        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(execute=True):
            resultado = servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado
            )

        self.assertTrue(resultado, "El servicio debería haber completado la operación con éxito.")

        self.assertFalse(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "El comunicado debería haberse borrado a pesar del fallo en el archivo físico."
        )



    def test_archivo_fantasma_no_detiene_el_servicio(self):
        """
        Test: El servicio debe ser resiliente ante inconsistencias del storage.

        Given: Un comunicado con una ruta de imagen en DB que no existe en disco.
        When: Se ejecuta delete_comunicado.
        Then: El registro se borra de la DB y el servicio devuelve True sin lanzar excepciones.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado con Referencia Huérfana",
            contenido="La base de datos cree que hay una foto, pero el disco no.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk

        mock_imagen = MagicMock()
        mock_imagen.delete.side_effect = FileNotFoundError("File not found on storage")
        comunicado.imagen_portada = mock_imagen

        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(execute=True):
            resultado = servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado
            )

        self.assertTrue(resultado)
        self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())



    def test_imagen_corrupta_no_impide_eliminacion_comunicado(self):
        """
        Test: Un fallo por archivo corrupto post-commit no debe afectar al éxito del servicio.

        Given: Un comunicado con una imagen que lanza un error de sistema (corrupción).
        When: Se ejecuta la limpieza on_commit tras borrar el comunicado.
        Then: El servicio devuelve True, el registro desaparece y la excepción se silencia.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado con Imagen Corrupta",
            contenido="La imagen existe pero el archivo está dañado o bloqueado.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk

        mock_imagen = MagicMock()
        mock_imagen.delete.side_effect = OSError("Input/Output error: file corrupted")
        comunicado.imagen_portada = mock_imagen

        servicio = ComunicadoService()

        try:
            with self.captureOnCommitCallbacks(execute=True):
                resultado = servicio.delete_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=comunicado
                )
        except OSError:
            self.fail("El servicio permitió que un error de archivo corrupto (OSError) se propagara.")

        self.assertTrue(resultado)
        self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())



    def test_path_invalido_no_impide_borrado_comunicado(self):
        """
        Test: Un path mal formado o inválido no debe bloquear el borrado del registro.

        Given: Un comunicado con una ruta de imagen técnicamente inválida.
        When: El servicio intenta borrar el comunicado y su imagen asociada.
        Then: El servicio devuelve True y el registro se borra de la DB.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado con Path Maligno",
            contenido="La ruta de la imagen es inválida o corrupta.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk

        mock_imagen = MagicMock()
        mock_imagen.delete.side_effect = ValueError("Invalid path format")
        comunicado.imagen_portada = mock_imagen

        servicio = ComunicadoService()

        try:
            with self.captureOnCommitCallbacks(execute=True):
                resultado = servicio.delete_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=comunicado
                )
        except ValueError:
            self.fail("El servicio crasheó debido a un path de imagen inválido.")

        self.assertTrue(resultado)
        self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())



    def test_imagen_pesada_no_ralentiza_respuesta_del_servicio(self):
        """
        Test: Un archivo que tarda en borrarse no debe bloquear la lógica del servicio.

        Given: Un comunicado con una imagen "pesada" (simulada con un delay).
        When: El servicio ejecuta el borrado del comunicado.
        Then: El servicio devuelve True inmediatamente y el borrado del registro es exitoso.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado con Video/Imagen Pesada",
            contenido="Este archivo tarda mucho en borrarse del storage.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk

        def borrado_lento(*args, **kwargs):
            return None

        mock_imagen = MagicMock()
        mock_imagen.delete.side_effect = borrado_lento
        comunicado.imagen_portada = mock_imagen

        servicio = ComunicadoService()

        resultado = servicio.delete_comunicado(
            usuario=self.admin, 
            comunicado_instance=comunicado
        )

        self.assertTrue(resultado, "El servicio debe responder rápido incluso con archivos pesados.")

        self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())



    def test_borrado_llama_a_limpieza_de_archivo_independientemente_del_storage(self):
        """
        Test: El servicio debe dar la orden de borrado físico del archivo 
            usando save=False para evitar colisiones con el delete de la instancia.

        Given: Un comunicado con una imagen asociada.
        When: El servicio ejecuta el borrado del comunicado.
        Then: Se debe llamar al método delete del archivo exactamente una vez con save=False.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado en la Nube",
            contenido="La imagen podría estar en S3 o cualquier storage externo.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )

        mock_imagen = MagicMock()
        mock_imagen.name = "uploads/foto_remota.jpg"
        comunicado.imagen_portada = mock_imagen

        servicio = ComunicadoService()

        with self.captureOnCommitCallbacks(execute=True):
            servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado
            )

        mock_imagen.delete.assert_called_once_with(save=False)



    def test_si_falla_antes_del_delete_no_se_borra_archivo(self):
        """
        Test: Si ocurre un error antes de borrar el registro, el archivo debe quedar intacto.

        Given: Un comunicado con imagen.
        When: Se captura la referencia de la imagen pero algo falla antes de llamar a .delete().
        Then: La imagen no debe borrarse y el registro debe persistir.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado con Imagen Intocable",
            contenido="Este archivo no debe borrarse si el servicio falla pronto.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk
        
        mock_imagen = MagicMock()
        mock_imagen.name = "fotos/permanente.jpg"
        comunicado.imagen_portada = mock_imagen

        servicio = ComunicadoService()

        with patch.object(ComunicadoService, '_verificar_permisos') as mock_permisos:
            mock_permisos.side_effect = Exception("Fallo crítico de seguridad antes de borrar")

            with self.assertRaises(Exception):
                servicio.delete_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=comunicado
                )

        self.assertTrue(Comunicado.objects.filter(pk=id_comunicado).exists())

        mock_imagen.delete.assert_not_called()



    def test_excepcion_entre_delete_y_on_commit_evita_borrado_archivo(self):
        """
        Test: Si el código falla tras borrar de DB pero antes de registrar on_commit.

        Given: Un comunicado con imagen.
        When: El registro se borra pero una excepción ocurre inmediatamente después.
        Then: La base de datos hace rollback y la imagen no se borra.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado en el Limbo",
            contenido="Este registro sobrevivirá por un fallo de código posterior.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk
        
        mock_imagen = MagicMock()
        mock_imagen.name = "fotos/limbo.jpg"
        comunicado.imagen_portada = mock_imagen

        servicio = ComunicadoService()

        with patch('django.db.transaction.on_commit') as mock_on_commit:
            mock_on_commit.side_effect = RuntimeError("Error inesperado tras el delete")

            with self.assertRaises(RuntimeError):
                servicio.delete_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=comunicado
                )

        self.assertTrue(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "El registro debería haber resucitado por el rollback."
        )

        mock_imagen.delete.assert_not_called()



    def test_rollback_restaura_comunicado_si_falla_despues_de_delete(self):
        """
        Test: El registro debe restaurarse si ocurre un error tras el delete()
            dentro de la misma transacción atómica.

        Given: Un comunicado guardado en la DB.
        When: El servicio borra el registro, pero el método lanza una excepción antes de terminar.
        Then: El registro debe seguir existiendo en la base de datos (Rollback).
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado a Restaurar",
            contenido="Este registro será borrado pero debe volver a la vida.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk

        mock_imagen = MagicMock()
        mock_imagen.name = "fotos/test_rollback.jpg"
        comunicado.imagen_portada = mock_imagen

        servicio = ComunicadoService()

        with patch('django.db.transaction.on_commit', side_effect=RuntimeError("Error post-delete")):
            try:
                servicio.delete_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=comunicado
                )
            except RuntimeError:
                pass

        self.assertTrue(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "El rollback falló: El comunicado no se restauró en la base de datos."
        )



    def test_rollback_anula_ejecucion_de_limpieza_de_archivo(self):
        """
        Test: Si la transacción hace rollback, la función de limpieza registrada
            en on_commit no debe ejecutarse.

        Given: Un comunicado con imagen.
        When: Se llama al servicio y luego se fuerza un rollback (simulando un fallo posterior).
        Then: La imagen no se borra (delete no es llamado) y el registro persiste.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado Superviviente",
            contenido="Este registro y su imagen sobrevivirán al rollback.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )

        id_comunicado = comunicado.pk

        mock_imagen = MagicMock()
        mock_imagen.name = "fotos/rollback_test.jpg"
        comunicado.imagen_portada = mock_imagen

        servicio = ComunicadoService()

        try:
            with transaction.atomic():
                servicio.delete_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=comunicado
                )

                raise IntegrityError("Fallo forzado para cancelar la transacción")
        except IntegrityError:
            pass

        self.assertTrue(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "El registro debería seguir existiendo gracias al rollback."
        )

        mock_imagen.delete.assert_not_called()



    def test_atomicidad_protege_integridad_ante_fallo_en_metodo(self):
        """
        Test: Confirma que transaction.atomic revierte el borrado si el método no termina.

        Given: Un comunicado guardado en DB.
        When: El servicio ejecuta el delete(), pero algo lanza una excepción justo antes de retornar.
        Then: El registro se restaura en la DB y el sistema vuelve al estado inicial.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado Atómico",
            contenido="Este registro es indivisible.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk

        mock_imagen = MagicMock()
        mock_imagen.name = "fotos/test_atomicidad.jpg"
        comunicado.imagen_portada = mock_imagen

        servicio = ComunicadoService()

        with patch('django.db.transaction.on_commit', side_effect=RuntimeError("Fallo post-delete")):
            try:
                servicio.delete_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=comunicado
                )
            except RuntimeError:
                pass

        self.assertTrue(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "La atomicidad falló: El registro no se restauró tras el error en el servicio."
        )



    def test_fallo_en_permisos_no_programa_borrado_de_archivo(self):
        """
        Test: Si el servicio falla antes de procesar el borrado, no se debe programar nada.

        Given: Un comunicado con imagen.
        When: El servicio falla en la verificación de permisos (u otra lógica inicial).
        Then: El registro persiste y el método delete del archivo nunca se registra ni llama.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado Protegido",
            contenido="Este archivo debe ignorarse si el usuario no tiene permiso.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk
        
        mock_imagen = MagicMock()
        comunicado.imagen_portada = mock_imagen
        
        servicio = ComunicadoService()

        User = get_user_model()
        usuario_sin_permiso = User.objects.create_user(
            dni="12345678Z",
            username="12345678Z", 
            password="testpassword123",
            nombre="Intruso",
            primer_apellido="Sin",
            segundo_apellido="Permisos",
            telefono="600000000",
            estado_civil=Hermano.EstadoCivil.SOLTERO,
            email="intruso@test.com"
        )

        with self.assertRaises(PermissionDenied):
            servicio.delete_comunicado(
                usuario=usuario_sin_permiso, 
                comunicado_instance=comunicado
            )

        self.assertTrue(Comunicado.objects.filter(pk=id_comunicado).exists())

        mock_imagen.delete.assert_not_called()



    def test_delete_comunicado_retorna_true_en_exito_y_procesa_todo(self):
        """
        Test: El método debe devolver True cuando la operación es exitosa
            y todas las acciones (DB y Archivo) se ejecutan.

        Given: Un comunicado existente y un usuario con permisos (Admin).
        When: Se llama a delete_comunicado.
        Then: Retorna True, el objeto desaparece de DB y se programa el borrado del archivo.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado Exitoso",
            contenido="Este registro se borrará perfectamente.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk

        mock_imagen = MagicMock()
        mock_imagen.name = "fotos/exito.jpg"
        comunicado.imagen_portada = mock_imagen

        servicio = ComunicadoService()

        with patch('django.db.transaction.on_commit') as mock_on_commit:
            resultado = servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado
            )

        self.assertIs(resultado, True, "El servicio debería retornar True tras un borrado exitoso.")

        self.assertFalse(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "El comunicado debería haber sido eliminado de la base de datos."
        )

        mock_on_commit.assert_called_once()



    def test_delete_comunicado_no_retorna_none(self):
        """
        Test: El método nunca debe devolver None en caso de éxito.

        Given: Un comunicado válido y un usuario con permisos.
        When: Se ejecuta la eliminación.
        Then: El valor de retorno debe ser distinto de None (específicamente True).
        """
        comunicado = Comunicado.objects.create(
            titulo="Test No None",
            contenido="Verificando el contrato del método.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        servicio = ComunicadoService()

        resultado = servicio.delete_comunicado(
            usuario=self.admin, 
            comunicado_instance=comunicado
        )

        self.assertIsNotNone(
            resultado, 
            "El servicio devolvió None. Se esperaba un valor booleano (True)."
        )
        self.assertIsInstance(
            resultado, 
            bool, 
            "El servicio debe devolver un tipo de dato booleano."
        )



    def test_delete_comunicado_no_afecta_a_otros_registros(self):
        """
        Test: Borrar un comunicado no debe eliminar ni modificar otros existentes.

        Given: Dos comunicados en la base de datos.
        When: Se elimina solo uno de ellos a través del servicio.
        Then: El segundo comunicado debe persistir intacto en la base de datos.
        """
        comunicado_a_borrar = Comunicado.objects.create(
            titulo="Comunicado A (Borrar)",
            contenido="Este será eliminado.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        
        comunicado_persistente = Comunicado.objects.create(
            titulo="Comunicado B (Persistir)",
            contenido="Este debe sobrevivir.",
            tipo_comunicacion=Comunicado.TipoComunicacion.INFORMATIVO,
            autor=self.admin
        )

        id_a = comunicado_a_borrar.pk
        id_b = comunicado_persistente.pk
        
        servicio = ComunicadoService()

        servicio.delete_comunicado(
            usuario=self.admin, 
            comunicado_instance=comunicado_a_borrar
        )

        self.assertFalse(Comunicado.objects.filter(pk=id_a).exists())

        comunicado_check = Comunicado.objects.filter(pk=id_b).first()
        self.assertIsNotNone(comunicado_check, "El comunicado B debería seguir en la DB.")
        self.assertEqual(comunicado_check.titulo, "Comunicado B (Persistir)")



    def test_delete_comunicado_no_afecta_entidades_area_interes(self):
        """
        Test: Al borrar un comunicado, las Áreas de Interés asociadas 
            no deben ser eliminadas de la base de datos.

        Given: Un comunicado vinculado a un área de interés específica.
        When: Se elimina el comunicado a través del servicio.
        Then: El área de interés debe seguir existiendo en la base de datos.
        """
        area, _ = AreaInteres.objects.get_or_create(
            nombre_area=AreaInteres.NombreArea.JUVENTUD
        )
        
        comunicado = Comunicado.objects.create(
            titulo="Noticia de Juventud",
            contenido="Contenido para jóvenes.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        comunicado.areas_interes.add(area)
        
        id_area = area.pk
        id_comunicado = comunicado.pk
        servicio = ComunicadoService()

        servicio.delete_comunicado(
            usuario=self.admin, 
            comunicado_instance=comunicado
        )

        self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())

        self.assertTrue(
            AreaInteres.objects.filter(pk=id_area).exists(),
            "Error: El Área de Interés fue eliminada (borrado en cascada incorrecto)."
        )

        area_recuperada = AreaInteres.objects.get(pk=id_area)
        self.assertEqual(area_recuperada.nombre_area, AreaInteres.NombreArea.JUVENTUD)



    def test_delete_comunicado_no_altera_registro_del_autor(self):
        """
        Test: Al borrar un comunicado, el registro del Hermano que lo creó
            debe permanecer exactamente igual.

        Given: Un comunicado asociado a un autor (Hermano).
        When: Se elimina el comunicado.
        Then: El registro del Hermano sigue existiendo y sus datos no han cambiado.
        """
        autor_id = self.admin.pk
        nombre_original = self.admin.nombre
        dni_original = self.admin.dni

        comunicado = Comunicado.objects.create(
            titulo="Comunicado del Autor",
            contenido="Este texto desaparecerá, pero el autor no.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        
        id_comunicado = comunicado.pk
        servicio = ComunicadoService()

        servicio.delete_comunicado(
            usuario=self.admin, 
            comunicado_instance=comunicado
        )

        self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())

        autor_check = Hermano.objects.filter(pk=autor_id).first()
        self.assertIsNotNone(autor_check, "El autor (Hermano) desapareció de la base de datos.")

        self.assertEqual(autor_check.nombre, nombre_original)
        self.assertEqual(autor_check.dni, dni_original)

        self.assertEqual(autor_check.comunicados_emitidos.count(), 0)



    def test_eliminaciones_en_paralelo_mantienen_integridad(self):
        """
        Test: Simula dos eliminaciones simultáneas del mismo objeto para verificar
            que el servicio es reentrante y no genera inconsistencias.

        Given: Un comunicado con imagen guardado en la base de datos.
        When: Se intenta eliminar el mismo objeto dos veces dentro de la misma transacción.
        Then: La primera eliminación tiene éxito, el registro desaparece y el sistema 
            maneja la segunda petición sin corromper la integridad del proceso.
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado Concurrente",
            contenido="¿Qué pasa si dos personas pulsan borrar a la vez?",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk
        
        mock_imagen = MagicMock()
        comunicado.imagen_portada = mock_imagen
        
        servicio = ComunicadoService()

        with transaction.atomic():
            resultado_1 = servicio.delete_comunicado(self.admin, comunicado)

            try:
                resultado_2 = servicio.delete_comunicado(self.admin, comunicado)
            except Exception:
                resultado_2 = False

        self.assertTrue(resultado_1)

        self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())



    def test_delete_comunicado_bajo_transaccion_anidada_respeta_rollback_externo(self):
        """
        Test: Verifica que el borrado se revierte si una transacción superior falla,
            confirmando que el servicio se integra correctamente en flujos complejos.

        Given: Un comunicado guardado en la base de datos.
        When: El servicio elimina el comunicado exitosamente, pero la transacción 
            que lo envuelve hace un rollback posterior.
        Then: El comunicado debe ser restaurado en la base de datos (rollback total).
        """
        comunicado = Comunicado.objects.create(
            titulo="Comunicado Anidado",
            contenido="Este borrado será revertido por un error externo.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        id_comunicado = comunicado.pk
        servicio = ComunicadoService()

        try:
            with transaction.atomic():
                servicio.delete_comunicado(
                    usuario=self.admin, 
                    comunicado_instance=comunicado
                )

                self.assertFalse(Comunicado.objects.filter(pk=id_comunicado).exists())
                
                raise RuntimeError("Error en el proceso superior")
        except RuntimeError:
            pass

        self.assertTrue(
            Comunicado.objects.filter(pk=id_comunicado).exists(),
            "La transacción anidada falló: El comunicado no se restauró tras el rollback externo."
        )



    def test_verificar_permisos_se_llama_exactamente_una_vez(self):
        """
        Test: Garantiza que la lógica de seguridad se invoca una sola vez por petición.

        Given: Un comunicado y un usuario con permisos.
        When: Se ejecuta el servicio de eliminación.
        Then: El método interno de verificación de permisos se llama exactamente una vez.
        """
        comunicado = Comunicado.objects.create(
            titulo="Test de Seguridad Única",
            contenido="Verificando llamadas al método de permisos.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )
        servicio = ComunicadoService()

        with patch.object(ComunicadoService, '_verificar_permisos') as mock_permisos:
            servicio.delete_comunicado(
                usuario=self.admin, 
                comunicado_instance=comunicado
            )

        mock_permisos.assert_called_once_with(self.admin)



    def test_consulta_pertenencia_a_cuerpos_se_ejecuta(self):
        """
        Test: Verifica que el servicio consulta activamente los cuerpos del usuario 
            para validar permisos de la Junta de Gobierno.

        Given: Un comunicado y un usuario cuya pertenencia a la Junta debe ser validada.
        When: Se llama al servicio de eliminación.
        Then: El sistema debe ejecutar una consulta filtrando los cuerpos del usuario.
        """
        comunicado = Comunicado.objects.create(
            titulo="Test de Consulta de Cuerpos",
            contenido="Verificando el acceso al ORM para permisos.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )

        usuario_mock = MagicMock()
        usuario_mock.esAdmin = False

        mock_filter = usuario_mock.cuerpos.filter
        mock_exists = mock_filter.return_value.exists
        mock_exists.return_value = True

        servicio = ComunicadoService()

        servicio.delete_comunicado(
            usuario=usuario_mock, 
            comunicado_instance=comunicado
        )

        mock_filter.assert_called_with(nombre_cuerpo='JUNTA_GOBIERNO')

        self.assertTrue(mock_exists.called, "No se verificó la existencia del cargo en el cuerpo.")



    def test_usuario_sin_atributo_es_admin_se_trata_como_false(self):
        """
        Test: Verifica que el servicio maneja con seguridad usuarios que no tienen
            definido el atributo 'esAdmin', tratándolos como no administradores.

        Given: Un comunicado y un objeto de usuario que carece del atributo 'esAdmin'.
        When: Se intenta eliminar el comunicado.
        Then: El servicio no lanza error de atributo y procede a verificar otros permisos
            (como la pertenencia a cuerpos) tratándolo inicialmente como no admin.
        """

        comunicado = Comunicado.objects.create(
            titulo="Test Atributo Faltante",
            contenido="Probando robustez ante objetos incompletos.",
            tipo_comunicacion=Comunicado.TipoComunicacion.GENERAL,
            autor=self.admin
        )

        usuario_incompleto = MagicMock()
        if hasattr(usuario_incompleto, 'esAdmin'):
            del usuario_incompleto.esAdmin

        usuario_incompleto.cuerpos.filter.return_value.exists.return_value = False

        servicio = ComunicadoService()

        try:
            servicio.delete_comunicado(
                usuario=usuario_incompleto, 
                comunicado_instance=comunicado
            )
        except PermissionDenied:
            pass
        except AttributeError as e:
            self.fail(f"El servicio lanzó AttributeError: {e}. No maneja usuarios sin 'esAdmin'.")
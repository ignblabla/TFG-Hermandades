from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.exceptions import PermissionDenied, ValidationError
from unittest.mock import patch
import datetime
from django.db import transaction

from ....services import actualizar_acto_service
from ....models import Acto, TipoActo, TipoPuesto, Puesto
from api.tests.factories import HermanoFactory


class ActualizarActoServiceTest(TestCase):

    def setUp(self):
        """
        Configuración inicial común para las pruebas de actualización.
        Creamos usuarios, un tipo de acto y un ACTO YA EXISTENTE para intentar modificarlo.
        """
        self.usuario_no_admin = HermanoFactory(esAdmin=False)
        self.usuario_admin = HermanoFactory(esAdmin=True)

        self.tipo_acto = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.ESTACION_PENITENCIA,
            requiere_papeleta=True
        )

        self.fecha_original = timezone.now() + timedelta(days=30)
        self.nombre_original = "Acto Original"
        
        self.acto_existente = Acto.objects.create(
            nombre=self.nombre_original,
            fecha=self.fecha_original,
            tipo_acto=self.tipo_acto,
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            descripcion="Descripción original",
            inicio_solicitud=self.fecha_original - timedelta(days=20),
            fin_solicitud=self.fecha_original - timedelta(days=10),
            inicio_solicitud_cirios=self.fecha_original - timedelta(days=9),
            fin_solicitud_cirios=self.fecha_original - timedelta(days=5),
        )



    def test_actualizar_acto_usuario_no_admin(self):
        """
        TC-01: Usuario No Administrador
        [Negativo] Verifica que un usuario sin privilegios de administrador (esAdmin=False)
        NO pueda actualizar un acto existente.
        
        Resultado Esperado: Excepción PermissionDenied.
        """
        data_actualizacion = {
            'nombre': 'Intento de Hackeo de Nombre',
            'descripcion': 'El usuario no admin intenta cambiar esto',
            'fecha': self.fecha_original,
            'tipo_acto': self.tipo_acto
        }

        with self.assertRaises(PermissionDenied) as contexto:
            actualizar_acto_service(
                self.usuario_no_admin, 
                self.acto_existente.id, 
                data_actualizacion
            )

        self.assertIn(
            "No tienes permisos", 
            str(contexto.exception.detail)
        )

        self.acto_existente.refresh_from_db()
        
        self.assertEqual(
            self.acto_existente.nombre, 
            self.nombre_original,
            "El nombre del acto no debería haber cambiado."
        )
        self.assertEqual(
            self.acto_existente.descripcion, 
            "Descripción original",
            "La descripción no debería haber cambiado."
        )



    def test_actualizar_acto_inexistente(self):
        """
        TC-02: Acto Inexistente
        [Negativo] Verifica que el sistema lance ValidationError si el ID no existe.
        
        Nota: Debemos usar un usuario ADMIN, porque el servicio comprueba permisos 
        ANTES de buscar el objeto en la base de datos.
        """
        id_inexistente = 9999
        
        data_dummy = {
            'nombre': 'Intento Actualización',
            'fecha': timezone.now()
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(self.usuario_admin, id_inexistente, data_dummy)

        self.assertIn(
            "El acto solicitado no existe",
            str(contexto.exception.detail)
        )



    def test_actualizar_acto_acceso_correcto_happy_path(self):
        """
        TC-03: Acceso Correcto (Happy Path)
        [Positivo] Verifica que un usuario administrador pueda actualizar exitosamente
        los datos básicos de un acto existente.
        
        Condiciones:
        - Usuario es Admin.
        - El ID existe.
        - Los datos son válidos y no generan conflictos.
        - El plazo de solicitud NO ha comenzado (para evitar bloqueo de edición de fecha).
        """
        nuevo_nombre = "Nombre Actualizado Correctamente"
        nueva_descripcion = "Esta descripción ha sido modificada por el test"
        
        nueva_fecha = self.fecha_original + timedelta(hours=2)

        data_valida = {
            'nombre': nuevo_nombre,
            'descripcion': nueva_descripcion,
            'fecha': nueva_fecha,
            'tipo_acto': self.tipo_acto,
            'modalidad': self.acto_existente.modalidad,
            'inicio_solicitud': self.acto_existente.inicio_solicitud,
            'fin_solicitud': self.acto_existente.fin_solicitud,
            'inicio_solicitud_cirios': self.acto_existente.inicio_solicitud_cirios,
            'fin_solicitud_cirios': self.acto_existente.fin_solicitud_cirios,
        }

        acto_actualizado = actualizar_acto_service(
            self.usuario_admin, 
            self.acto_existente.id, 
            data_valida
        )

        self.assertIsNotNone(acto_actualizado)
        self.assertEqual(acto_actualizado.id, self.acto_existente.id)

        self.assertEqual(acto_actualizado.nombre, nuevo_nombre)
        self.assertEqual(acto_actualizado.descripcion, nueva_descripcion)
        self.assertEqual(acto_actualizado.fecha, nueva_fecha)

        self.acto_existente.refresh_from_db()
        self.assertEqual(self.acto_existente.nombre, nuevo_nombre)
        self.assertEqual(self.acto_existente.descripcion, nueva_descripcion)



    def test_actualizar_acto_colision_nombre_fecha_otro_acto(self):
        """
        TC-04: Colisión de Nombre y Fecha (Otro Acto)
        [Negativo] Verifica que falle si se intenta actualizar un acto (Acto A)
        para que tenga el mismo nombre y fecha que OTRO acto ya existente (Acto B).
        
        La validación del servicio busca duplicados excluyendo el propio ID del acto editado.
        """
        fecha_conflicto = timezone.now() + timedelta(days=60)
        nombre_conflicto = "Misa de Hermandad"

        Acto.objects.create(
            nombre=nombre_conflicto,
            fecha=fecha_conflicto,
            tipo_acto=self.tipo_acto,
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            descripcion="Acto B existente",
            inicio_solicitud=fecha_conflicto - timedelta(days=10),
            fin_solicitud=fecha_conflicto - timedelta(days=5),
        )

        data_colision = {
            'nombre': nombre_conflicto,
            'fecha': fecha_conflicto,
            'tipo_acto': self.tipo_acto,
            
            'inicio_solicitud': fecha_conflicto - timedelta(days=20),
            'fin_solicitud': fecha_conflicto - timedelta(days=15),
            'inicio_solicitud_cirios': fecha_conflicto - timedelta(days=14),
            'fin_solicitud_cirios': fecha_conflicto - timedelta(days=10),
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                self.usuario_admin, 
                self.acto_existente.id, 
                data_colision
            )

        self.assertIn(
            f"Ya existe otro acto llamado '{nombre_conflicto}' en esa fecha.",
            str(contexto.exception.detail)
        )



    def test_actualizar_acto_falso_positivo_colision_mismo_acto(self):
        """
        TC-05: Falso Positivo de Colisión (Mismo Acto)
        [Positivo] Verifica que NO salte el error de duplicado si se actualiza
        el mismo acto manteniendo su nombre y fecha original.
        
        El sistema debe ser lo suficientemente inteligente para excluir el propio ID 
        del acto en la búsqueda de duplicados (exclude(pk=acto.id)).
        """
        nombre_mismo = self.nombre_original
        fecha_misma = self.fecha_original
        
        nueva_descripcion = "Actualización de descripción manteniendo identidad"

        data_misma_identidad = {
            'nombre': nombre_mismo,
            'fecha': fecha_misma,
            'descripcion': nueva_descripcion,
            'tipo_acto': self.tipo_acto,

            'inicio_solicitud': self.acto_existente.inicio_solicitud,
            'fin_solicitud': self.acto_existente.fin_solicitud,
            'inicio_solicitud_cirios': self.acto_existente.inicio_solicitud_cirios,
            'fin_solicitud_cirios': self.acto_existente.fin_solicitud_cirios,
        }

        acto_actualizado = actualizar_acto_service(
            self.usuario_admin, 
            self.acto_existente.id, 
            data_misma_identidad
        )

        self.assertIsNotNone(acto_actualizado)
        
        self.assertEqual(acto_actualizado.descripcion, nueva_descripcion)
        
        self.assertEqual(acto_actualizado.nombre, self.nombre_original)



    def test_actualizar_acto_cambio_tipo_con_puestos_existentes(self):
        """
        TC-06: Cambio de Tipo con Puestos Existentes
        [Negativo] Verifica que no se pueda cambiar el 'tipo_acto' si el acto
        ya tiene objetos 'Puesto' vinculados.
        """
        nuevo_tipo = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.QUINARIO,
            requiere_papeleta=False
        )


        tipo_puesto_dummy = TipoPuesto.objects.create(
            nombre_tipo="Vara de Presidencia",
            es_insignia=True
        )

        Puesto.objects.create(
            acto=self.acto_existente, 
            nombre="Vara de Presidencia",
            tipo_puesto=tipo_puesto_dummy 
        )

        data_cambio_tipo = {
            'nombre': self.acto_existente.nombre,
            'fecha': self.acto_existente.fecha,
            'tipo_acto': nuevo_tipo, 
            'modalidad': self.acto_existente.modalidad,
            'inicio_solicitud': self.acto_existente.inicio_solicitud,
            'fin_solicitud': self.acto_existente.fin_solicitud,
            'inicio_solicitud_cirios': self.acto_existente.inicio_solicitud_cirios,
            'fin_solicitud_cirios': self.acto_existente.fin_solicitud_cirios,
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                self.usuario_admin, 
                self.acto_existente.id, 
                data_cambio_tipo
            )

        detalle_error = contexto.exception.detail
        
        self.assertIn('tipo_acto', detalle_error)
        
        self.assertIn(
            "No se puede cambiar el Tipo de Acto porque ya existen puestos generados",
            str(detalle_error['tipo_acto'])
        )



    def test_actualizar_acto_cambio_tipo_limpio(self):
        """
        TC-07: Cambio de Tipo Limpio
        [Positivo] Verifica que SE PUEDA cambiar el 'tipo_acto' si el acto
        NO tiene objetos 'Puesto' vinculados.
        
        Escenario:
        - Acto original: Estación de Penitencia (sin puestos creados).
        - Nuevo tipo: Quinario.
        - Resultado: El tipo se actualiza correctamente.
        """
        nuevo_tipo = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.QUINARIO,
            requiere_papeleta=True
        )

        self.assertEqual(self.acto_existente.puestos_disponibles.count(), 0)

        data_cambio = {
            'nombre': self.acto_existente.nombre,
            'fecha': self.acto_existente.fecha,
            'tipo_acto': nuevo_tipo,
            'modalidad': self.acto_existente.modalidad,
            'inicio_solicitud': self.acto_existente.inicio_solicitud,
            'fin_solicitud': self.acto_existente.fin_solicitud,
            'inicio_solicitud_cirios': self.acto_existente.inicio_solicitud_cirios,
            'fin_solicitud_cirios': self.acto_existente.fin_solicitud_cirios,
        }

        acto_actualizado = actualizar_acto_service(
            self.usuario_admin,
            self.acto_existente.id,
            data_cambio
        )

        self.assertIsNotNone(acto_actualizado)
        
        self.assertEqual(acto_actualizado.tipo_acto, nuevo_tipo)
        
        self.acto_existente.refresh_from_db()
        self.assertEqual(self.acto_existente.tipo_acto, nuevo_tipo)



    def test_actualizar_acto_cambio_fecha_permitido_antes_plazo(self):
        """
        TC-08: Cambio permitido (Antes del plazo)
        [Positivo] Verifica que SE PERMITA modificar la fecha del acto si el día actual (now)
        es ANTERIOR al inicio del plazo de solicitud.
        
        Escenario Simulado:
        - Now (Simulado): 28/02
        - Inicio Solicitud: 01/03 (Futuro)
        - Acción: Cambiar fecha del acto al 25/03.
        """
        now_simulado = datetime.datetime(2024, 2, 28, 12, 0, tzinfo=datetime.timezone.utc)
        
        inicio_solicitud_futuro = datetime.datetime(2024, 3, 1, 10, 0, tzinfo=datetime.timezone.utc)
        
        self.acto_existente.inicio_solicitud = inicio_solicitud_futuro
        self.acto_existente.fecha = datetime.datetime(2024, 3, 30, 20, 0, tzinfo=datetime.timezone.utc)
        self.acto_existente.save()

        nueva_fecha_acto = datetime.datetime(2024, 3, 25, 20, 0, tzinfo=datetime.timezone.utc)

        data_cambio_fecha = {
            'nombre': self.acto_existente.nombre,
            'fecha': nueva_fecha_acto,
            'tipo_acto': self.tipo_acto,
            'inicio_solicitud': inicio_solicitud_futuro,
            'fin_solicitud': inicio_solicitud_futuro + timedelta(days=5),
            'inicio_solicitud_cirios': inicio_solicitud_futuro + timedelta(days=6),
            'fin_solicitud_cirios': inicio_solicitud_futuro + timedelta(days=10),
        }

        with patch('django.utils.timezone.now', return_value=now_simulado):
            acto_actualizado = actualizar_acto_service(
                self.usuario_admin,
                self.acto_existente.id,
                data_cambio_fecha
            )

        self.assertIsNotNone(acto_actualizado)
        
        self.assertEqual(acto_actualizado.fecha, nueva_fecha_acto)



    def test_actualizar_acto_cambio_bloqueado_plazo_iniciado(self):
        """
        TC-09: Cambio bloqueado (Plazo iniciado)
        [Negativo] Verifica que falle si se intenta cambiar la fecha del acto
        cuando el día actual (now) es POSTERIOR al inicio del plazo de solicitud.
        
        Escenario Simulado:
        - Inicio Solicitud: 01/03
        - Now (Simulado): 02/03 (El plazo ya ha empezado hace 1 día)
        - Acción: Intentar cambiar la fecha del acto.
        """
        inicio_solicitud_pasado = datetime.datetime(2024, 3, 1, 10, 0, tzinfo=datetime.timezone.utc)
        
        now_simulado = datetime.datetime(2024, 3, 2, 12, 0, tzinfo=datetime.timezone.utc)
        
        self.acto_existente.inicio_solicitud = inicio_solicitud_pasado
        self.acto_existente.fecha = datetime.datetime(2024, 3, 30, 20, 0, tzinfo=datetime.timezone.utc)
        self.acto_existente.save()

        nueva_fecha_acto = datetime.datetime(2024, 3, 25, 20, 0, tzinfo=datetime.timezone.utc)

        data_cambio_prohibido = {
            'nombre': self.acto_existente.nombre,
            'fecha': nueva_fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': self.acto_existente.modalidad,
            'inicio_solicitud': inicio_solicitud_pasado,
            'fin_solicitud': inicio_solicitud_pasado + timedelta(days=10),
        }

        with patch('django.utils.timezone.now', return_value=now_simulado):
            with self.assertRaises(ValidationError) as contexto:
                actualizar_acto_service(
                    self.usuario_admin,
                    self.acto_existente.id,
                    data_cambio_prohibido
                )

        detalle_error = contexto.exception.detail
        
        self.assertIn('fecha', detalle_error)
        
        mensaje_esperado = "No se puede modificar la fecha del acto porque el plazo de solicitud ya ha comenzado"
        self.assertIn(mensaje_esperado, str(detalle_error['fecha']))



    def test_actualizar_acto_frontera_critica_exacta(self):
        """
        TC-10: Frontera Crítica (Exacta)
        [Negativo] Verifica que el bloqueo se active EXACTAMENTE en el segundo de inicio.
        
        Escenario:
        - Inicio Solicitud: 01/03/2026 a las 10:00:00.
        - Now (Simulado):   01/03/2026 a las 10:00:00 (Exactamente igual).
        
        Condición a probar: if now >= fecha_limite: ...
        Resultado esperado: ValidationError.
        """
        instante_critico = datetime.datetime(2026, 3, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
        
        self.acto_existente.inicio_solicitud = instante_critico
        self.acto_existente.fecha = instante_critico + timedelta(days=20)
        self.acto_existente.save()

        nueva_fecha_evento = instante_critico + timedelta(days=25)

        data_frontera = {
            'nombre': self.acto_existente.nombre,
            'fecha': nueva_fecha_evento,
            'tipo_acto': self.tipo_acto,
            
            'modalidad': self.acto_existente.modalidad,
            'inicio_solicitud': instante_critico,
            'fin_solicitud': instante_critico + timedelta(days=5),
        }

        with patch('django.utils.timezone.now', return_value=instante_critico):
            with self.assertRaises(ValidationError) as contexto:
                actualizar_acto_service(
                    self.usuario_admin,
                    self.acto_existente.id,
                    data_frontera
                )

        detalle_error = contexto.exception.detail
        
        self.assertIn('fecha', detalle_error)
        
        self.assertIn(
            "No se puede modificar la fecha del acto porque el plazo de solicitud ya ha comenzado",
            str(detalle_error['fecha'])
        )



    def test_actualizar_acto_frontera_segura_limite_inferior(self):
        """
        TC-11: Frontera Segura (Límite inferior)
        [Positivo] Verifica que SE PERMITA el cambio si el momento actual (now)
        es exactamente 1 segundo antes del inicio del plazo.
        
        """
        fecha_limite = datetime.datetime(2026, 3, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
        
        now_seguro = fecha_limite - datetime.timedelta(seconds=1)
        
        self.acto_existente.inicio_solicitud = fecha_limite
        self.acto_existente.fecha = fecha_limite + datetime.timedelta(days=20)
        self.acto_existente.save()

        nueva_fecha_acto = fecha_limite + datetime.timedelta(days=25)
        
        fin_insignias = fecha_limite + datetime.timedelta(days=5)
        
        inicio_cirios = fin_insignias + datetime.timedelta(days=1)
        fin_cirios = inicio_cirios + datetime.timedelta(days=4)

        data_frontera_safe = {
            'nombre': self.acto_existente.nombre,
            'fecha': nueva_fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': self.acto_existente.modalidad,
            'inicio_solicitud': fecha_limite,
            'fin_solicitud': fin_insignias,
            'inicio_solicitud_cirios': inicio_cirios,
            'fin_solicitud_cirios': fin_cirios,
        }

        with patch('django.utils.timezone.now', return_value=now_seguro):
            acto_actualizado = actualizar_acto_service(
                self.usuario_admin,
                self.acto_existente.id,
                data_frontera_safe
            )

        self.assertIsNotNone(acto_actualizado)
        self.assertEqual(acto_actualizado.fecha, nueva_fecha_acto)



    def test_actualizar_acto_parcial_sin_tocar_fecha_plazo_iniciado(self):
        """
        TC-12: Actualización parcial sin tocar fecha
        [Positivo] Verifica que SE PERMITA cambiar campos (ej: Nombre) aunque el plazo 
        ya haya empezado, siempre que la FECHA del acto se mantenga idéntica.
        
        Prueba la línea del servicio: 
            if acto.fecha == nueva_fecha: return
        Esto evita que salte el error de bloqueo por plazo iniciado.
        """
        inicio_solicitud_pasado = datetime.datetime(2024, 3, 1, 10, 0, tzinfo=datetime.timezone.utc)
        
        now_simulado = datetime.datetime(2024, 3, 5, 12, 0, tzinfo=datetime.timezone.utc)
        
        self.acto_existente.inicio_solicitud = inicio_solicitud_pasado
        self.acto_existente.fin_solicitud = inicio_solicitud_pasado + datetime.timedelta(days=5)
        self.acto_existente.inicio_solicitud_cirios = inicio_solicitud_pasado + datetime.timedelta(days=6)
        self.acto_existente.fin_solicitud_cirios = inicio_solicitud_pasado + datetime.timedelta(days=10)
        fecha_original = datetime.datetime(2024, 3, 30, 20, 0, tzinfo=datetime.timezone.utc)
        self.acto_existente.fecha = fecha_original
        self.acto_existente.save()

        nuevo_nombre = "Nombre Corregido Durante el Reparto"

        data_sin_cambio_fecha = {
            'nombre': nuevo_nombre,
            'fecha': fecha_original,
            'tipo_acto': self.tipo_acto,
        }

        with patch('django.utils.timezone.now', return_value=now_simulado):
            acto_actualizado = actualizar_acto_service(
                self.usuario_admin,
                self.acto_existente.id,
                data_sin_cambio_fecha
            )

        self.assertIsNotNone(acto_actualizado)
        
        self.assertEqual(acto_actualizado.nombre, nuevo_nombre)
        
        self.assertEqual(acto_actualizado.fecha, fecha_original)



    def test_actualizar_acto_limpieza_por_tipo_sin_papeleta(self):
        """
        TC-13: Limpieza por Tipo de Acto (Sin Papeleta)
        [Positivo] Verifica que si se cambia el tipo de acto a uno que NO requiere papeleta,
        el sistema fuerce a None todas las fechas de solicitud.
        
        Además, verifica que IGNORE cualquier fecha enviada en el input para esos campos.
        """
        tipo_sin_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.CONVIVENCIA,
            requiere_papeleta=False
        )

        self.assertIsNotNone(self.acto_existente.inicio_solicitud)

        fecha_trampa = timezone.now() + timedelta(days=50)

        data_cambio_tipo = {
            'nombre': self.acto_existente.nombre,
            'fecha': self.acto_existente.fecha,
            'tipo_acto': tipo_sin_papeleta,

            'inicio_solicitud': fecha_trampa,
            'fin_solicitud': fecha_trampa,
            'inicio_solicitud_cirios': fecha_trampa,
            'fin_solicitud_cirios': fecha_trampa,
        }

        acto_actualizado = actualizar_acto_service(
            self.usuario_admin,
            self.acto_existente.id,
            data_cambio_tipo
        )

        self.assertEqual(acto_actualizado.tipo_acto, tipo_sin_papeleta)

        self.assertIsNone(
            acto_actualizado.inicio_solicitud, 
            "El inicio_solicitud debería haberse limpiado a None"
        )
        self.assertIsNone(acto_actualizado.fin_solicitud)
        self.assertIsNone(acto_actualizado.inicio_solicitud_cirios)
        self.assertIsNone(acto_actualizado.fin_solicitud_cirios)

        self.acto_existente.refresh_from_db()
        self.assertIsNone(self.acto_existente.inicio_solicitud)



    def test_actualizar_acto_incoherencia_hibrida_dato_nuevo_vs_viejo(self):
        """
        TC-14: Incoherencia Híbrida (Dato Nuevo vs Dato Viejo)
        [Negativo] Verifica que el sistema valide la coherencia combinando los datos
        que envía el usuario (Nuevos) con los que ya existen en BBDD (Viejos).
        
        Escenario:
        - BBDD (Viejo): Inicio Cirios = Día 10.
        - Input (Nuevo): Fin Insignias = Día 12.
        - Input (Omisión): No se envía Inicio Cirios (se asume el de BBDD).
        
        Conflicto: Fin Insignias (12) > Inicio Cirios (10) -> ERROR en Tradicional.
        """
        base_time = timezone.now()
        
        fin_insignias_original = base_time + timedelta(days=5)
        inicio_cirios_original = base_time + timedelta(days=10)
        
        self.acto_existente.modalidad = Acto.ModalidadReparto.TRADICIONAL
        self.acto_existente.inicio_solicitud = base_time
        self.acto_existente.fin_solicitud = fin_insignias_original
        self.acto_existente.inicio_solicitud_cirios = inicio_cirios_original
        self.acto_existente.fin_solicitud_cirios = base_time + timedelta(days=15)
        self.acto_existente.save()
        nuevo_fin_insignias = base_time + timedelta(days=12)

        data_hibrida = {
            'nombre': self.acto_existente.nombre,
            'fecha': self.acto_existente.fecha,
            'tipo_acto': self.tipo_acto,
            'inicio_solicitud': base_time,
            'fin_solicitud': nuevo_fin_insignias,

        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                self.usuario_admin,
                self.acto_existente.id,
                data_hibrida
            )

        detalle_error = contexto.exception.detail

        self.assertIn('inicio_solicitud_cirios', detalle_error)
        
        mensaje_error = str(detalle_error['inicio_solicitud_cirios'])
        
        self.assertIn("En reparto Tradicional", mensaje_error)
        self.assertIn("no puede comenzar hasta que finalice", mensaje_error)

        fecha_str = nuevo_fin_insignias.strftime('%d/%m/%Y %H:%M')
        self.assertIn(fecha_str, mensaje_error)



    def test_actualizar_acto_validacion_contra_nueva_fecha_adelantada(self):
        """
        TC-15: Validación contra Nueva Fecha de Acto
        [Negativo] Verifica que falle si se adelanta la fecha del acto (ej: del día 20 al 04)
        haciendo que los plazos existentes en BBDD queden incoherentes.
        """
        base_time = timezone.now()
        
        inicio_solicitud = base_time + timedelta(days=1)
        fin_insignias_existente = base_time + timedelta(days=5) 
        
        self.acto_existente.fecha = base_time + timedelta(days=20)
        self.acto_existente.inicio_solicitud = inicio_solicitud
        self.acto_existente.fin_solicitud = fin_insignias_existente
        
        self.acto_existente.inicio_solicitud_cirios = base_time + timedelta(days=6)
        self.acto_existente.fin_solicitud_cirios = base_time + timedelta(days=10)
        
        self.acto_existente.save()

        nueva_fecha_adelantada = base_time + timedelta(days=4)

        data_fecha_adelantada = {
            'nombre': self.acto_existente.nombre,
            'fecha': nueva_fecha_adelantada, 
            'tipo_acto': self.tipo_acto,
        }

        from django.core.exceptions import ValidationError as DjangoValidationError
        from rest_framework.exceptions import ValidationError as DRFValidationError

        with self.assertRaises((DjangoValidationError, DRFValidationError)) as contexto:
            actualizar_acto_service(
                self.usuario_admin,
                self.acto_existente.id,
                data_fecha_adelantada
            )
        e = contexto.exception
        detalle_error = {}

        if hasattr(e, 'detail'):
            detalle_error = e.detail
        elif hasattr(e, 'message_dict'):
            detalle_error = e.message_dict
        elif hasattr(e, 'messages'):
            detalle_error = {'non_field_errors': e.messages}
        else:
            self.fail(f"Tipo de excepción no reconocido o sin detalles: {type(e)}")

        self.assertIn('fin_solicitud', detalle_error)
        
        mensaje_error = str(detalle_error['fin_solicitud'])
        
        self.assertIn("debe ser anterior al acto", mensaje_error)



    def test_actualizar_acto_frontera_cirios_vs_insignias_solapamiento(self):
        """
        TC-16: Frontera Cirios vs Insignias (Solapamiento)
        [Negativo] Verifica que en modalidad TRADICIONAL falle si el inicio de cirios
        se solapa con el fin de insignias (ej: 09:59 vs 10:00).
        
        Condición a probar: if inicio_cirios <= fin_insignias: Error
        """
        base_time = timezone.now()
        punto_choque = base_time + timedelta(days=5)

        fin_insignias_limite = punto_choque
        inicio_cirios_solapado = punto_choque - timedelta(minutes=1)

        self.acto_existente.modalidad = Acto.ModalidadReparto.TRADICIONAL
        self.acto_existente.save()

        data_solapamiento = {
            'nombre': self.acto_existente.nombre,
            'fecha': self.acto_existente.fecha,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': punto_choque - timedelta(days=2),
            'fin_solicitud': fin_insignias_limite,
            'inicio_solicitud_cirios': inicio_cirios_solapado,
            'fin_solicitud_cirios': punto_choque + timedelta(days=2),
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                self.usuario_admin,
                self.acto_existente.id,
                data_solapamiento
            )

        detalle_error = contexto.exception.detail

        self.assertIn('inicio_solicitud_cirios', detalle_error)
        
        mensaje_error = str(detalle_error['inicio_solicitud_cirios'])
        
        self.assertIn("En reparto Tradicional", mensaje_error)
        self.assertIn("no puede comenzar hasta que finalice", mensaje_error)
        
        fecha_str = fin_insignias_limite.strftime('%d/%m/%Y %H:%M')
        self.assertIn(fecha_str, mensaje_error)



    def test_actualizar_acto_frontera_cirios_vs_insignias_igualdad(self):
        """
        TC-17: Frontera Cirios vs Insignias (Igualdad/Toque)
        [Negativo] Verifica que en modalidad TRADICIONAL falle si el inicio de cirios
        coincide EXACTAMENTE con el fin de insignias.
        
        Escenario:
            - Fin Insignias: 10:00:00
            - Inicio Cirios: 10:00:00
        
        La validación 'inicio_cirios <= fin_insignias' debe bloquear este caso,
        exigiendo que sea estrictamente posterior.
        """
        base_time = timezone.now()
        punto_contacto = base_time + timedelta(days=5)

        self.acto_existente.modalidad = Acto.ModalidadReparto.TRADICIONAL
        self.acto_existente.save()

        data_igualdad = {
            'nombre': self.acto_existente.nombre,
            'fecha': self.acto_existente.fecha,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': punto_contacto - timedelta(days=2),
            'fin_solicitud': punto_contacto,
            
            'inicio_solicitud_cirios': punto_contacto,
            'fin_solicitud_cirios': punto_contacto + timedelta(days=2),
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                self.usuario_admin,
                self.acto_existente.id,
                data_igualdad
            )

        detalle_error = contexto.exception.detail

        self.assertIn('inicio_solicitud_cirios', detalle_error)
        
        mensaje_error = str(detalle_error['inicio_solicitud_cirios'])
        
        self.assertIn("En reparto Tradicional", mensaje_error)
        self.assertIn("no puede comenzar hasta que finalice", mensaje_error)
        
        fecha_str = punto_contacto.strftime('%d/%m/%Y %H:%M')
        self.assertIn(fecha_str, mensaje_error)



    def test_actualizar_acto_frontera_cirios_vs_insignias_consecutivo_valido(self):
        """
        TC-18: Frontera Cirios vs Insignias (Consecutivo Válido)
        [Positivo] Verifica que en modalidad TRADICIONAL se permita el cambio si
        el inicio de cirios es estrictamente posterior al fin de insignias.
        
        Escenario:
            - Fin Insignias: 10:00:00
            - Inicio Cirios: 10:01:00
        
        Resultado esperado: Éxito.
        """
        base_time = timezone.now()

        fin_insignias = base_time + timedelta(days=5)
        inicio_cirios = fin_insignias + timedelta(minutes=1)

        self.acto_existente.modalidad = Acto.ModalidadReparto.TRADICIONAL
        self.acto_existente.save()

        data_consecutivo = {
            'nombre': self.acto_existente.nombre,
            'fecha': self.acto_existente.fecha + timedelta(days=10),
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            
            'inicio_solicitud': fin_insignias - timedelta(days=2),
            'fin_solicitud': fin_insignias,
            
            'inicio_solicitud_cirios': inicio_cirios, 
            'fin_solicitud_cirios': inicio_cirios + timedelta(days=2),
        }

        acto_actualizado = actualizar_acto_service(
            self.usuario_admin,
            self.acto_existente.id,
            data_consecutivo
        )

        self.assertIsNotNone(acto_actualizado)
        self.assertEqual(acto_actualizado.fin_solicitud, fin_insignias)
        self.assertEqual(acto_actualizado.inicio_solicitud_cirios, inicio_cirios)
        
        self.acto_existente.refresh_from_db()
        self.assertEqual(self.acto_existente.inicio_solicitud_cirios, inicio_cirios)



    def test_actualizar_acto_rollback_por_error_inesperado(self):
        """
        TC-19: Rollback por Error Inesperado
        [Integridad] Verifica que si ocurre una excepción tras el guardado del objeto
        pero dentro del bloque atómico, los cambios no se persistan en la BD.
        """
        nombre_original = self.acto_existente.nombre
        fecha_original = self.acto_existente.fecha
        
        data_nueva = {
            'nombre': "Nombre que no debe guardarse",
            'fecha': fecha_original + timedelta(days=1),
            'tipo_acto': self.tipo_acto,
        }
        
        with patch('api.models.Acto.save', side_effect=Exception("Error de base de datos inesperado")):
            with self.assertRaises(Exception) as contexto:
                actualizar_acto_service(
                    self.usuario_admin,
                    self.acto_existente.id,
                    data_nueva
                )
            
            self.assertEqual(str(contexto.exception), "Error de base de datos inesperado")

        self.acto_existente.refresh_from_db()
        
        self.assertEqual(self.acto_existente.nombre, nombre_original)
        self.assertEqual(self.acto_existente.fecha, fecha_original)
        self.assertNotEqual(self.acto_existente.nombre, "Nombre que no debe guardarse")



    def test_actualizar_acto_error_inicio_insignias_posterior_a_cirios(self):
        """
        TC-20: Orden de Apertura (Insignias vs Cirios)
        [Negativo] Verifica que falle si el plazo de insignias comienza el mismo día 
        o después que el de cirios.
        
        Lógica probada: if inicio_insignias >= inicio_cirios: Error
        """
        base_time = timezone.now()

        inicio_cirios = base_time + timedelta(days=5)
        inicio_insignias_tardio = base_time + timedelta(days=6)

        self.acto_existente.modalidad = Acto.ModalidadReparto.TRADICIONAL
        self.acto_existente.save()

        data_orden_incorrecto = {
            'nombre': self.acto_existente.nombre,
            'fecha': self.acto_existente.fecha + timedelta(days=20),
            'tipo_acto': self.tipo_acto,
            'inicio_solicitud': inicio_insignias_tardio, 
            'fin_solicitud': inicio_insignias_tardio + timedelta(days=5),
            
            'inicio_solicitud_cirios': inicio_cirios,
            'fin_solicitud_cirios': inicio_cirios + timedelta(days=10),
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                self.usuario_admin,
                self.acto_existente.id,
                data_orden_incorrecto
            )

        detalle_error = contexto.exception.detail

        self.assertIn('inicio_solicitud', detalle_error)
        
        mensaje_error = str(detalle_error['inicio_solicitud'])
        self.assertIn("El reparto de insignias debe comenzar antes que el de cirios", mensaje_error)



    def test_actualizar_acto_error_fin_cirios_anterior_a_inicio(self):
        """
        TC-21: Coherencia interna de Cirios (Fin <= Inicio)
        [Negativo] Verifica que falle si la fecha de fin de cirios es anterior 
        o igual a la de inicio.
        
        Lógica probada: if inicio_cirios >= fin_cirios: Error
        """
        base_time = timezone.now()

        inicio_cirios = base_time + timedelta(days=10)
        fin_cirios_invalido = base_time + timedelta(days=9)

        inicio_insignias = base_time + timedelta(days=1)
        fin_insignias = base_time + timedelta(days=5)

        data_cirios_incoherente = {
            'nombre': self.acto_existente.nombre,
            'fecha': base_time + timedelta(days=20),
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            
            'inicio_solicitud': inicio_insignias,
            'fin_solicitud': fin_insignias,
            
            'inicio_solicitud_cirios': inicio_cirios,
            'fin_solicitud_cirios': fin_cirios_invalido,
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                self.usuario_admin,
                self.acto_existente.id,
                data_cirios_incoherente
            )

        detalle_error = contexto.exception.detail

        self.assertIn('fin_solicitud_cirios', detalle_error)
        
        mensaje_error = str(detalle_error['fin_solicitud_cirios'])
        self.assertIn("La fecha fin de cirios debe ser posterior a su fecha de inicio", mensaje_error)



    def test_actualizar_acto_error_fin_insignias_anterior_a_inicio(self):
        """
        TC-22: Coherencia interna de Insignias (Fin <= Inicio)
        [Negativo] Verifica que falle si la fecha de fin de insignias es anterior 
        o igual a la de inicio.
        
        Lógica probada: if inicio_insignias >= fin_insignias: Error
        """
        base_time = timezone.now()

        inicio_insignias = base_time + timedelta(days=5)
        fin_insignias_invalido = base_time + timedelta(days=4)

        data_insignias_incoherente = {
            'nombre': self.acto_existente.nombre,
            'fecha': base_time + timedelta(days=20),
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.UNIFICADO,
            
            'inicio_solicitud': inicio_insignias,
            'fin_solicitud': fin_insignias_invalido,
            
            'inicio_solicitud_cirios': inicio_insignias + timedelta(days=1),
            'fin_solicitud_cirios': inicio_insignias + timedelta(days=5),
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                self.usuario_admin,
                self.acto_existente.id,
                data_insignias_incoherente
            )

        detalle_error = contexto.exception.detail

        self.assertIn('fin_solicitud', detalle_error)
        
        mensaje_error = str(detalle_error['fin_solicitud'])
        self.assertIn("La fecha fin de insignias debe ser posterior a su fecha de inicio", mensaje_error)



    def test_actualizar_acto_error_inicio_insignias_posterior_al_acto(self):
        """
        TC-23: Inicio de Insignias vs Fecha del Acto
        [Negativo] Verifica que falle si el plazo de insignias comienza el mismo día 
        o después de la celebración del acto.
        
        Lógica probada: if inicio_insignias >= fecha_acto: Error
        """
        base_time = timezone.now()

        fecha_acto = base_time + timedelta(days=10)
        inicio_insignias_tardio = base_time + timedelta(days=10)

        data_inicio_post_acto = {
            'nombre': self.acto_existente.nombre,
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.UNIFICADO,

            'inicio_solicitud': inicio_insignias_tardio,
            'fin_solicitud': inicio_insignias_tardio + timedelta(days=2),
        }

        with self.assertRaises(ValidationError) as contexto:
            actualizar_acto_service(
                self.usuario_admin,
                self.acto_existente.id,
                data_inicio_post_acto
            )

        detalle_error = contexto.exception.detail

        self.assertIn('inicio_solicitud', detalle_error)
        
        mensaje_error = str(detalle_error['inicio_solicitud'])
        
        self.assertIn("El inicio de insignias debe ser anterior al acto", mensaje_error)
        
        fecha_str = fecha_acto.strftime('%d/%m/%Y %H:%M')
        self.assertIn(fecha_str, mensaje_error)
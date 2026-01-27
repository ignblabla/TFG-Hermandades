from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from rest_framework.exceptions import PermissionDenied, ValidationError

from ....models import Acto, TipoActo
from ....services import crear_acto_service
from api.tests.factories import HermanoFactory

User = get_user_model()

class CrearActoServiceTest(TestCase):

    def setUp(self):
        """
        Configuración inicial común para todos los tests de esta clase.
        """
        self.usuario_no_admin = HermanoFactory(esAdmin=False)

        self.usuario_admin = HermanoFactory(esAdmin=True)

        self.tipo_acto = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.ESTACION_PENITENCIA,
            requiere_papeleta=True
        )

    def test_crear_acto_usuario_sin_permisos_admin(self):
        """
        [Negativo] Verifica que un usuario sin 'esAdmin=True' no pueda crear un acto
        y que se lance la excepción PermissionDenied.
        """
        
        fecha_acto = timezone.now() + timedelta(days=30)
        
        data_validada = {
            'nombre': 'Estación de Penitencia 2025',
            'descripcion': 'Salida procesional',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': fecha_acto - timedelta(days=20),
            'fin_solicitud': fecha_acto - timedelta(days=10),
            'inicio_solicitud_cirios': fecha_acto - timedelta(days=9),
            'fin_solicitud_cirios': fecha_acto - timedelta(days=5),
        }

        with self.assertRaises(PermissionDenied) as contexto:
            crear_acto_service(self.usuario_no_admin, data_validada)
        
        self.assertEqual(
            str(contexto.exception), 
            "No tienes permisos para crear actos. Se requiere ser Administrador."
        )

        self.assertEqual(Acto.objects.count(), 0, "No se debería haber persistido ningún Acto en la BBDD")



    def test_crear_acto_duplicado_mismo_nombre_y_dia(self):
        """
        [Negativo] Verifica que el servicio lance ValidationError (DRF) si intentamos
        crear un acto con el mismo nombre en el mismo día.
        """
        nombre_comun = "Función Principal"
        fecha_base = timezone.now() + timedelta(days=60)

        Acto.objects.create(
            nombre=nombre_comun,
            fecha=fecha_base,
            tipo_acto=self.tipo_acto,
            descripcion="Acto original"
        )

        fecha_intento = fecha_base + timedelta(hours=5)

        data_duplicada = {
            'nombre': nombre_comun,
            'fecha': fecha_intento,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': None,
            'fin_solicitud': None,
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_duplicada)

        error_detail = contexto.exception.detail[0]
        
        self.assertIn(
            f"Ya existe el acto '{nombre_comun}' en esa fecha.",
            str(error_detail)
        )

        self.assertEqual(Acto.objects.count(), 1)



    def test_crear_acto_mismo_nombre_dia_diferente(self):
        """
        [Positivo] Verifica que SÍ se permita crear un acto con el mismo nombre
        que uno existente, siempre que sea en una fecha (día) diferente.
        Ejemplo: 'Cabildo General' puede repetirse varios días distintos.
        """
        nombre_comun = "Cabildo General Ordinario"
        
        fecha_existente = timezone.now() + timedelta(days=10)
        
        Acto.objects.create(
            nombre=nombre_comun,
            fecha=fecha_existente,
            tipo_acto=self.tipo_acto,
            descripcion="Primer cabildo"
        )

        fecha_nueva = timezone.now() + timedelta(days=50)

        data_valida = {
            'nombre': nombre_comun,
            'fecha': fecha_nueva,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'descripcion': "Segundo cabildo (mismo nombre, otra fecha)",
            'inicio_solicitud': fecha_nueva - timedelta(days=20),
            'fin_solicitud': fecha_nueva - timedelta(days=15),
            'inicio_solicitud_cirios': fecha_nueva - timedelta(days=14),
            'fin_solicitud_cirios': fecha_nueva - timedelta(days=5),
        }

        nuevo_acto = crear_acto_service(self.usuario_admin, data_valida)

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.nombre, nombre_comun)
        self.assertEqual(nuevo_acto.fecha, fecha_nueva)

        self.assertEqual(Acto.objects.count(), 2)



    def test_crear_acto_sin_papeleta_limpia_fechas(self):
        """
        [Positivo] Verifica que si tipo_acto.requiere_papeleta = False, 
        las fechas de solicitud se guarden como None aunque se envíen datos.
        """
        tipo_sin_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.QUINARIO,
            requiere_papeleta=False
        )

        fecha_acto = timezone.now() + timedelta(days=20)

        data = {
            'nombre': 'Primer día de Quinario en honor a Nuestro Padre Jesús en Su Soberano Poder ante Caifás',
            'descripcion': 'Quinario 2026',
            'fecha': fecha_acto,
            'tipo_acto': tipo_sin_papeleta,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': fecha_acto - timedelta(days=5),
            'fin_solicitud': fecha_acto - timedelta(days=1),
            'inicio_solicitud_cirios': fecha_acto - timedelta(days=5),
            'fin_solicitud_cirios': fecha_acto - timedelta(days=1),
        }

        nuevo_acto = crear_acto_service(self.usuario_admin, data)

        self.assertIsNotNone(nuevo_acto.id)
        
        self.assertIsNone(nuevo_acto.inicio_solicitud, "Inicio solicitud insignia debe ser None")
        self.assertIsNone(nuevo_acto.fin_solicitud, "Fin solicitud insignia debe ser None")
        self.assertIsNone(nuevo_acto.inicio_solicitud_cirios, "Inicio solicitud cirio debe ser None")
        self.assertIsNone(nuevo_acto.fin_solicitud_cirios, "Fin solicitud cirio debe ser None")



    def test_crear_acto_fecha_limite_un_segundo_antes(self):
        """
        [Positivo] Límite Justo Antes: Verifica que sea posible fijar el fin de la solicitud
        exactamente 1 segundo antes de la fecha y hora del acto.
        """
        fecha_acto = timezone.now() + timedelta(days=5)
        
        un_segundo_antes = fecha_acto - timedelta(seconds=1)

        data_limite = {
            'nombre': 'Acto Límite Temporal',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,

            'inicio_solicitud': fecha_acto - timedelta(hours=5),
            'fin_solicitud': fecha_acto - timedelta(hours=4),
            'inicio_solicitud_cirios': fecha_acto - timedelta(hours=3),
            'fin_solicitud_cirios': un_segundo_antes,
        }

        nuevo_acto = crear_acto_service(self.usuario_admin, data_limite)

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.fin_solicitud_cirios, un_segundo_antes)



    def test_crear_acto_fecha_limite_colision_exacta(self):
        """
        [Negativo] Límite Exacto (Colisión):
        Verifica que falle si la fecha de fin de solicitud es EXACTAMENTE
        igual a la fecha del acto. La lógica exige que sea estrictamente anterior (<).
        """
        fecha_acto = timezone.now() + timedelta(days=5)

        data_colision = {
            'nombre': 'Acto Colisión Límite',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': fecha_acto - timedelta(hours=10),
            'fin_solicitud': fecha_acto - timedelta(hours=8),
            'inicio_solicitud_cirios': fecha_acto - timedelta(hours=6),
            'fin_solicitud_cirios': fecha_acto,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_colision)

        detalle_error = contexto.exception.detail
        
        self.assertIn('fin_solicitud_cirios', detalle_error)

        mensaje_error = str(detalle_error['fin_solicitud_cirios'])
        
        self.assertIn(
            "debe finalizar antes de la fecha del acto", 
            mensaje_error
        )
        
        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_fecha_limite_superado_un_segundo_despues(self):
        """
        [Negativo] Límite Superado:
        Verifica que falle si la fecha de fin de solicitud supera por 1 segundo
        a la fecha del acto.
        """
        fecha_acto = timezone.now() + timedelta(days=5)
        
        un_segundo_despues = fecha_acto + timedelta(seconds=1)

        data_exceso = {
            'nombre': 'Acto Exceso Límite',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': fecha_acto - timedelta(hours=10),
            'fin_solicitud': fecha_acto - timedelta(hours=8),
            'inicio_solicitud_cirios': fecha_acto - timedelta(hours=6),
            'fin_solicitud_cirios': un_segundo_despues,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_exceso)

        detalle_error = contexto.exception.detail
        
        self.assertIn('fin_solicitud_cirios', detalle_error)
        
        self.assertIn(
            "debe finalizar antes de la fecha del acto", 
            str(detalle_error['fin_solicitud_cirios'])
        )
        
        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_inicio_solicitud_posterior_al_acto(self):
        """
        [Negativo] Inicio de solicitud posterior al acto:
        Verifica que falle si la fecha de inicio de solicitud de insignias
        es posterior a la fecha del acto.
        """
        fecha_acto = timezone.now() + timedelta(days=5)
        
        inicio_posterior = fecha_acto + timedelta(minutes=1)

        data_invalida = {
            'nombre': 'Acto con Fechas Futuras',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': inicio_posterior,
            'fin_solicitud': inicio_posterior + timedelta(days=1),
            'inicio_solicitud_cirios': inicio_posterior + timedelta(days=2),
            'fin_solicitud_cirios': inicio_posterior + timedelta(days=3),
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        detalle_error = contexto.exception.detail
        
        self.assertIn('inicio_solicitud', detalle_error)
        
        self.assertIn(
            "debe ser anterior a la fecha del acto", 
            str(detalle_error['inicio_solicitud'])
        )
        
        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_intervalo_minimo_valido(self):
        """
        [Positivo] Intervalo Mínimo Válido:
        Verifica que el servicio acepte un intervalo de solicitud donde 
        el fin es exactamente 1 segundo posterior al inicio (inicio < fin).
        """
        fecha_acto = timezone.now() + timedelta(days=20)

        inicio_solicitud = fecha_acto - timedelta(days=10)
        
        fin_solicitud = inicio_solicitud + timedelta(seconds=1)

        data = {
            'nombre': 'Acto Intervalo Mínimo',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': inicio_solicitud,
            'fin_solicitud': fin_solicitud,
            'inicio_solicitud_cirios': fin_solicitud + timedelta(minutes=1),
            'fin_solicitud_cirios': fin_solicitud + timedelta(hours=1),
        }

        nuevo_acto = crear_acto_service(self.usuario_admin, data)

        self.assertIsNotNone(nuevo_acto.id)
        
        diferencia = nuevo_acto.fin_solicitud - nuevo_acto.inicio_solicitud
        self.assertEqual(diferencia, timedelta(seconds=1))



    def test_crear_acto_intervalo_tiempo_cero_iguales(self):
        """
        [Negativo] Intervalo de Tiempo Cero (Iguales):
        Verifica que falle si la fecha de inicio es IGUAL a la fecha de fin.
        La lógica de negocio exige estrictamente que inicio < fin.
        """
        fecha_acto = timezone.now() + timedelta(days=20)
        
        fecha_inicio = fecha_acto - timedelta(days=10)

        fecha_fin = fecha_inicio

        data_invalida = {
            'nombre': 'Acto Intervalo Cero',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': fecha_inicio,
            'fin_solicitud': fecha_fin,
            'inicio_solicitud_cirios': fecha_fin + timedelta(hours=1),
            'fin_solicitud_cirios': fecha_fin + timedelta(hours=5),
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        detalle_error = contexto.exception.detail

        self.assertIn('fin_solicitud', detalle_error)

        self.assertIn(
            "debe ser posterior al inicio", 
            str(detalle_error['fin_solicitud'])
        )
        
        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_intervalo_invertido(self):
        """
        [Negativo] Intervalo Invertido:
        Verifica que falle si la fecha de inicio es posterior a la de fin.
        Ejemplo: Inicio 10:00:01 > Fin 10:00:00.
        """
        fecha_acto = timezone.now() + timedelta(days=20)

        fecha_inicio = fecha_acto - timedelta(days=10)

        fecha_fin = fecha_inicio - timedelta(seconds=1)

        data_invalida = {
            'nombre': 'Acto Intervalo Invertido',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            
            'inicio_solicitud': fecha_inicio,
            'fin_solicitud': fecha_fin,
            'inicio_solicitud_cirios': fecha_inicio + timedelta(days=1),
            'fin_solicitud_cirios': fecha_inicio + timedelta(days=2),
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        detalle_error = contexto.exception.detail
        
        self.assertIn('fin_solicitud', detalle_error)

        self.assertIn(
            "debe ser posterior al inicio", 
            str(detalle_error['fin_solicitud'])
        )
        
        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_tradicional_secuencia_correcta_con_holgura(self):
        """
        [Positivo] Secuencia Correcta (Con holgura):
        Verifica que en modalidad TRADICIONAL se permita crear el acto si
        existe un espacio de tiempo entre el Fin de Insignias y el Inicio de Cirios.
        
        Escenario:
        - Fin Insignias: T - 10 días (10:00 aprox)
        - Inicio Cirios: T - 10 días + 2 horas (12:00 aprox)
        - Gap: 2 horas.
        """
        fecha_acto = timezone.now() + timedelta(days=30)

        fin_insignias = fecha_acto - timedelta(days=10)
        
        inicio_cirios = fin_insignias + timedelta(hours=2)

        data_tradicional = {
            'nombre': 'Acto Tradicional Correcto',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': fin_insignias - timedelta(hours=4),
            'fin_solicitud': fin_insignias,
            'inicio_solicitud_cirios': inicio_cirios,
            'fin_solicitud_cirios': inicio_cirios + timedelta(hours=4),
        }

        nuevo_acto = crear_acto_service(self.usuario_admin, data_tradicional)

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.modalidad, Acto.ModalidadReparto.TRADICIONAL)
        
        self.assertGreater(nuevo_acto.inicio_solicitud_cirios, nuevo_acto.fin_solicitud)



    def test_crear_acto_tradicional_limite_secuencia_contiguos(self):
        """
        [Positivo] Límite de Secuencia (Contiguos):
        Verifica que en modalidad TRADICIONAL se permita la creación si
        el inicio de cirios es exactamente 1 segundo posterior al fin de insignias.
        
        Input: Fin Insignias (T), Inicio Cirios (T + 1s).
        Resultado: Éxito.
        """
        fecha_acto = timezone.now() + timedelta(days=20)

        fin_insignias = fecha_acto - timedelta(days=10)

        inicio_cirios = fin_insignias + timedelta(seconds=1)

        data_contigua = {
            'nombre': 'Acto Secuencia Contigua',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': fin_insignias - timedelta(hours=5),
            'fin_solicitud': fin_insignias,
            'inicio_solicitud_cirios': inicio_cirios,
            'fin_solicitud_cirios': inicio_cirios + timedelta(hours=5),
        }

        nuevo_acto = crear_acto_service(self.usuario_admin, data_contigua)

        self.assertIsNotNone(nuevo_acto.id)

        diferencia = nuevo_acto.inicio_solicitud_cirios - nuevo_acto.fin_solicitud
        self.assertEqual(diferencia, timedelta(seconds=1))



    def test_crear_acto_tradicional_limite_contacto_mismo_instante(self):
        """
        [Negativo] Límite de Contacto (Mismo instante):
        Verifica que en modalidad TRADICIONAL falle si el inicio de cirios
        coincide exactamente con el fin de insignias.
        La validación interna usa (inicio_cirios <= fin_insignias), por lo que la igualdad es error.
        """
        fecha_acto = timezone.now() + timedelta(days=20)

        punto_colision = fecha_acto - timedelta(days=10)

        data_colision = {
            'nombre': 'Acto Contacto Exacto',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,
            'inicio_solicitud': punto_colision - timedelta(hours=5),
            'fin_solicitud': punto_colision,
            'inicio_solicitud_cirios': punto_colision,
            'fin_solicitud_cirios': punto_colision + timedelta(hours=5),
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_colision)

        detalle_error = contexto.exception.detail
        
        self.assertIn('inicio_solicitud_cirios', detalle_error)
        self.assertIn(
            "no pueden empezar antes", 
            str(detalle_error['inicio_solicitud_cirios'])
        )
        
        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_tradicional_solapamiento_overlap(self):
        """
        [Negativo] Solapamiento (Overlap):
        Verifica que falle si el inicio de solicitud de cirios es ANTERIOR
        al fin de solicitud de insignias en modalidad TRADICIONAL.
        
        Escenario:
        - Fin Insignias: 10:30
        - Inicio Cirios: 10:00 (Esto provoca el solapamiento de 30 minutos).
        """
        fecha_acto = timezone.now() + timedelta(days=20)

        fin_insignias = fecha_acto - timedelta(days=10)

        inicio_cirios = fin_insignias - timedelta(minutes=30)

        data_overlap = {
            'nombre': 'Acto Solapamiento Tradicional',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,

            'inicio_solicitud': fin_insignias - timedelta(hours=2),
            'fin_solicitud': fin_insignias,

            'inicio_solicitud_cirios': inicio_cirios,
            'fin_solicitud_cirios': inicio_cirios + timedelta(hours=5),
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_overlap)

        detalle_error = contexto.exception.detail

        self.assertIn('inicio_solicitud_cirios', detalle_error)

        self.assertIn(
            "no pueden empezar antes", 
            str(detalle_error['inicio_solicitud_cirios'])
        )
        
        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_tradicional_orden_incorrecto_inicios(self):
        """
        [Negativo] Orden Incorrecto de Inicios:
        Verifica que falle si el inicio de insignias es posterior al inicio de cirios.
        En modalidad TRADICIONAL, las insignias siempre deben abrir el proceso.

        Escenario invertido (Input):
        - Cirios: Empiezan a las 10:00.
        - Insignias: Empiezan a las 12:00.
        Aunque los intervalos no se toquen, la lógica de negocio exige que 
        inicio_insignias < inicio_cirios.
        """
        fecha_acto = timezone.now() + timedelta(days=20)

        base_time = fecha_acto - timedelta(days=10)

        inicio_cirios = base_time

        inicio_insignias = base_time + timedelta(hours=2)

        data_orden_invertido = {
            'nombre': 'Acto Orden Invertido',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,

            'inicio_solicitud': inicio_insignias,
            'fin_solicitud': inicio_insignias + timedelta(hours=1),

            'inicio_solicitud_cirios': inicio_cirios,
            'fin_solicitud_cirios': inicio_cirios + timedelta(hours=1),
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_orden_invertido)

        detalle_error = contexto.exception.detail

        self.assertIn('inicio_solicitud', detalle_error)

        self.assertIn(
            "debe comenzar antes", 
            str(detalle_error['inicio_solicitud'])
        )
        
        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_limpieza_total_sin_papeleta_datos_extra(self):
        """
        [Positivo] Limpieza total:
        Verifica que si requiere_papeleta = False, se limpien TODAS las fechas
        y la modalidad, incluso si se envían datos mezclados (pasados, futuros o inválidos).
        
        Input:
            - requiere_papeleta = False
            - modalidad = TRADICIONAL
            - inicio_solicitud = Fecha válida pasada
            - inicio_cirios = Fecha futura "inválida"
            
        Resultado esperado:
            - Objeto creado.
            - Modalidad es None.
            - Fechas son None.
        """
        tipo_sin_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.QUINARIO,
            requiere_papeleta=False
        )

        fecha_acto = timezone.now() + timedelta(days=30)

        fecha_pasada = timezone.now() - timedelta(days=100)
        fecha_futura = timezone.now() + timedelta(days=365)

        data_sucia = {
            'nombre': 'Acto Limpieza Total',
            'descripcion': 'Prueba de limpieza de campos',
            'fecha': fecha_acto,
            'tipo_acto': tipo_sin_papeleta,

            'modalidad': Acto.ModalidadReparto.TRADICIONAL, 
            'inicio_solicitud': fecha_pasada,
            'inicio_solicitud_cirios': fecha_futura,

            'fin_solicitud': None,
            'fin_solicitud_cirios': None,
        }

        nuevo_acto = crear_acto_service(self.usuario_admin, data_sucia)

        self.assertIsNotNone(nuevo_acto.id)

        self.assertIsNone(nuevo_acto.inicio_solicitud, "Inicio solicitud debe ser None")
        self.assertIsNone(nuevo_acto.inicio_solicitud_cirios, "Inicio cirios debe ser None")

        self.assertIsNone(nuevo_acto.modalidad, "La modalidad debería ser None según el requisito")



    def test_crear_acto_sin_papeleta_ignora_fechas_invalidas_futuras(self):
        """
        [Positivo] Fechas inválidas ignoradas:
        Verifica que si requiere_papeleta = False, el sistema NO lance ValidationError
        aunque se envíe una fecha de solicitud POSTERIOR a la fecha del acto.
        
        Esto demuestra que el sistema limpia (pone a None) los datos antes de validar
        su coherencia cronológica.
        """
        tipo_sin_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.QUINARIO,
            requiere_papeleta=False
        )

        fecha_acto = timezone.now() + timedelta(days=10)

        fecha_posterior_al_acto = fecha_acto + timedelta(days=5)

        data_trampa = {
            'nombre': 'Acto Fechas Ignoradas',
            'fecha': fecha_acto,
            'tipo_acto': tipo_sin_papeleta,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,

            'inicio_solicitud': fecha_posterior_al_acto,

            'fin_solicitud': None,
            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        nuevo_acto = crear_acto_service(self.usuario_admin, data_trampa)

        self.assertIsNotNone(nuevo_acto.id)
        
        self.assertIsNone(nuevo_acto.inicio_solicitud)



    def test_crear_acto_unificado_limpia_fechas_cirios(self):
        """
        [Positivo] Ignorado de Cirios (Limpieza):
        Verifica que si la modalidad es UNIFICADO (y requiere papeleta),
        se guarden las fechas generales (inicio_solicitud) pero se limpien/ignoren
        las fechas específicas de cirios (inicio_solicitud_cirios), incluso si se envían datos válidos.
        """
        fecha_acto = timezone.now() + timedelta(days=30)

        inicio_general = fecha_acto - timedelta(days=20)
        fin_general = fecha_acto - timedelta(days=10)

        inicio_cirios_basura = fecha_acto - timedelta(days=15)
        fin_cirios_basura = fecha_acto - timedelta(days=12)

        data_unificado = {
            'nombre': 'Acto Reparto Unificado',
            'descripcion': 'Reparto express',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,

            'modalidad': Acto.ModalidadReparto.UNIFICADO,

            'inicio_solicitud': inicio_general,
            'fin_solicitud': fin_general,

            'inicio_solicitud_cirios': inicio_cirios_basura,
            'fin_solicitud_cirios': fin_cirios_basura,
        }

        nuevo_acto = crear_acto_service(self.usuario_admin, data_unificado)

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.modalidad, Acto.ModalidadReparto.UNIFICADO)

        self.assertEqual(nuevo_acto.inicio_solicitud, inicio_general)
        self.assertEqual(nuevo_acto.fin_solicitud, fin_general)

        self.assertIsNone(
            nuevo_acto.inicio_solicitud_cirios, 
            "El inicio de solicitud de cirios debería haberse limpiado en modalidad UNIFICADO."
        )
        self.assertIsNone(
            nuevo_acto.fin_solicitud_cirios, 
            "El fin de solicitud de cirios debería haberse limpiado en modalidad UNIFICADO."
        )



    def test_crear_acto_unificado_ignora_fechas_cirios_invalidas_futuras(self):
        """
        [Positivo] Ignorado de Cirios Inválidos (Critical Path):
        Verifica que si la modalidad es UNIFICADA, el sistema limpie las fechas de cirios
        ANTES de validar su coherencia contra la fecha del acto.

        Input:
            - Modalidad: UNIFICADO
            - Inicio Cirios: Fecha posterior al acto (Inválida).

        Explicación:
            Si el sistema validara antes de limpiar, lanzaría ValidationError ("Inicio
            de cirios debe ser anterior al acto"). Al limpiar primero, la fecha tóxica
            desaparece (se vuelve None) y la validación pasa con éxito.
        """
        fecha_acto = timezone.now() + timedelta(days=30)

        inicio_general = fecha_acto - timedelta(days=20)
        fin_general = fecha_acto - timedelta(days=10)

        inicio_cirios_toxico = fecha_acto + timedelta(days=5)

        data_critical = {
            'nombre': 'Acto Unificado Critical Path',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.UNIFICADO,

            'inicio_solicitud': inicio_general,
            'fin_solicitud': fin_general,

            'inicio_solicitud_cirios': inicio_cirios_toxico,
            'fin_solicitud_cirios': inicio_cirios_toxico + timedelta(days=1),
        }

        nuevo_acto = crear_acto_service(self.usuario_admin, data_critical)

        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.modalidad, Acto.ModalidadReparto.UNIFICADO)

        self.assertIsNone(nuevo_acto.inicio_solicitud_cirios)
        self.assertIsNone(nuevo_acto.fin_solicitud_cirios)



    def test_crear_acto_unificado_validacion_general_activa(self):
        """
        [Negativo] Validación General Activa en Modalidad Unificada:
        Verifica que, aunque la modalidad sea UNIFICADA (que limpia datos de cirios),
        las validaciones de las fechas generales sigan activas.
        
        Si el 'inicio_solicitud' (General/Insignias) es posterior al acto, 
        debe fallar igualmente.
        """
        fecha_acto = timezone.now() + timedelta(days=30)
        
        inicio_posterior = fecha_acto + timedelta(days=1)

        data_invalida = {
            'nombre': 'Acto Unificado Error General',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.UNIFICADO,

            'inicio_solicitud': inicio_posterior,
            'fin_solicitud': inicio_posterior + timedelta(days=1),

            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        detalle_error = contexto.exception.detail

        self.assertIn('inicio_solicitud', detalle_error)
        
        self.assertIn(
            "debe ser anterior a la fecha del acto", 
            str(detalle_error['inicio_solicitud'])
        )
        
        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_unificado_coherencia_general_activa(self):
        """
        [Negativo] Coherencia General Activa:
        Verifica que, aunque la modalidad sea UNIFICADA, se mantenga la validación
        de coherencia cronológica básica del intervalo general.
        
        Si el Fin es anterior al Inicio, debe fallar.
        
        Input: 
            - Modalidad: UNIFICADO
            - Inicio: 10:00
            - Fin: 09:00 (ERROR)
        """
        fecha_acto = timezone.now() + timedelta(days=30)

        inicio_solicitud = fecha_acto - timedelta(days=10)
        fin_solicitud = inicio_solicitud - timedelta(hours=1)

        data_invalida = {
            'nombre': 'Acto Unificado Incoherente',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.UNIFICADO,

            'inicio_solicitud': inicio_solicitud,
            'fin_solicitud': fin_solicitud,

            'inicio_solicitud_cirios': None,
            'fin_solicitud_cirios': None,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        detalle_error = contexto.exception.detail

        self.assertIn('fin_solicitud', detalle_error)

        self.assertIn(
            "debe ser posterior al inicio", 
            str(detalle_error['fin_solicitud'])
        )
        
        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_flujo_completo_tradicional_mantiene_fechas(self):
        """
        [Positivo] Flujo completo Tradicional:
        Verifica que en modalidad TRADICIONAL se guarden correctamente AMBOS conjuntos de fechas
        (Insignias y Cirios) siempre que respeten el orden cronológico.

        Input:
            - Insignias: 10:00 - 11:00
            - Cirios:    12:00 - 13:00
        Resultado:
            - Objeto creado.
            - inicio_solicitud (Insignias) se mantiene.
            - inicio_solicitud_cirios (Cirios) se mantiene.
        """
        fecha_acto = timezone.now() + timedelta(days=30)

        base_time = fecha_acto - timedelta(days=10)

        inicio_insignias = base_time
        fin_insignias = base_time + timedelta(hours=1)

        inicio_cirios = base_time + timedelta(hours=2)
        fin_cirios = base_time + timedelta(hours=3)

        data_tradicional = {
            'nombre': 'Acto Tradicional Completo',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto, # Requiere papeleta
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,

            'inicio_solicitud': inicio_insignias,
            'fin_solicitud': fin_insignias,

            'inicio_solicitud_cirios': inicio_cirios,
            'fin_solicitud_cirios': fin_cirios,
        }

        nuevo_acto = crear_acto_service(self.usuario_admin, data_tradicional)


        self.assertIsNotNone(nuevo_acto.id)
        self.assertEqual(nuevo_acto.modalidad, Acto.ModalidadReparto.TRADICIONAL)

        self.assertEqual(nuevo_acto.inicio_solicitud, inicio_insignias)
        self.assertEqual(nuevo_acto.fin_solicitud, fin_insignias)
        
        self.assertEqual(nuevo_acto.inicio_solicitud_cirios, inicio_cirios)
        self.assertEqual(nuevo_acto.fin_solicitud_cirios, fin_cirios)



    def test_crear_acto_tradicional_solapamiento_intervalos_cruzados(self):
        """
        [Negativo] Solapamiento Tradicional:
        Verifica que falle si los intervalos de insignias y cirios se solapan en el tiempo,
        incluso si cada intervalo es coherente por sí mismo.
        
        Escenario:
            - Insignias: 10:00 - 12:00 (Duración 2h, válida)
            - Cirios:    11:00 - 13:00 (Duración 2h, válida)
            
        Conflicto:
            El reparto de cirios empieza (11:00) ANTES de que termine el de insignias (12:00).
        """
        fecha_acto = timezone.now() + timedelta(days=30)

        base_time = fecha_acto - timedelta(days=10)

        inicio_insignias = base_time
        fin_insignias = base_time + timedelta(hours=2)

        inicio_cirios = base_time + timedelta(hours=1)
        fin_cirios = base_time + timedelta(hours=3)

        data_solapada = {
            'nombre': 'Acto Solapamiento Cruzado',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,

            'inicio_solicitud': inicio_insignias,
            'fin_solicitud': fin_insignias,

            'inicio_solicitud_cirios': inicio_cirios,
            'fin_solicitud_cirios': fin_cirios,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_solapada)

        detalle_error = contexto.exception.detail

        self.assertIn('inicio_solicitud_cirios', detalle_error)

        mensaje_error = str(detalle_error['inicio_solicitud_cirios'])
        self.assertIn(
            "no pueden empezar antes", 
            mensaje_error
        )
        
        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_tradicional_cirios_fuera_de_fecha_acto(self):
        """
        [Negativo] Cirios fuera de fecha (Modalidad Tradicional):
        Verifica que si la modalidad es TRADICIONAL, una fecha de inicio de cirios
        posterior al acto provoque un ValidationError.
        
        Contrastar con: test_crear_acto_unificado_ignora_fechas_cirios_invalidas_futuras.
        Aquí NO hay limpieza previa, por lo que la validación debe atrapar el error.
        """
        fecha_acto = timezone.now() + timedelta(days=20)

        fin_insignias = fecha_acto - timedelta(days=10)

        inicio_cirios_futuro = fecha_acto + timedelta(days=1)

        data_invalida = {
            'nombre': 'Acto Tradicional Fuera de Fecha',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,

            'inicio_solicitud': fin_insignias - timedelta(days=1),
            'fin_solicitud': fin_insignias,

            'inicio_solicitud_cirios': inicio_cirios_futuro,
            'fin_solicitud_cirios': inicio_cirios_futuro + timedelta(days=1),
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_invalida)

        detalle_error = contexto.exception.detail

        self.assertIn('inicio_solicitud_cirios', detalle_error)

        self.assertIn(
            "debe ser anterior a la fecha del acto", 
            str(detalle_error['inicio_solicitud_cirios'])
        )
        
        self.assertEqual(Acto.objects.count(), 0)



    def test_crear_acto_cirios_intervalo_incoherente(self):
        """
        [Negativo] Intervalo Cirios Incoherente (Inicio >= Fin):
        Verifica que falle si la fecha de fin de cirios es anterior o igual 
        a su fecha de inicio.
        
        Cubre la condición: 
        if inicio_cirios and fin_cirios and inicio_cirios >= fin_cirios: ...
        """
        fecha_acto = timezone.now() + timedelta(days=30)

        fin_insignias = fecha_acto - timedelta(days=15)

        inicio_cirios = fecha_acto - timedelta(days=5)
        fin_cirios = inicio_cirios - timedelta(hours=1)

        data_incoherente = {
            'nombre': 'Acto Cirios Invertidos',
            'fecha': fecha_acto,
            'tipo_acto': self.tipo_acto,
            'modalidad': Acto.ModalidadReparto.TRADICIONAL,

            'inicio_solicitud': fin_insignias - timedelta(days=2),
            'fin_solicitud': fin_insignias,

            'inicio_solicitud_cirios': inicio_cirios,
            'fin_solicitud_cirios': fin_cirios,
        }

        with self.assertRaises(ValidationError) as contexto:
            crear_acto_service(self.usuario_admin, data_incoherente)

        detalle_error = contexto.exception.detail

        self.assertIn('fin_solicitud_cirios', detalle_error)

        self.assertIn(
            "debe ser posterior al inicio", 
            str(detalle_error['fin_solicitud_cirios'])
        )
        
        self.assertEqual(Acto.objects.count(), 0)
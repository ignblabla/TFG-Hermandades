from django.test import TestCase
from django.utils import timezone
from unittest import mock
from datetime import timedelta
from django.core.exceptions import ValidationError

from api.models import (
    Acto, Hermano, PreferenciaSolicitud, TipoActo, Puesto, TipoPuesto, 
    CuerpoPertenencia, HermanoCuerpo, PapeletaSitio
)

from api.servicios.papeleta_sitio_service import PapeletaSitioService
from api.tests.factories import HermanoFactory


class ProcesarSolicitudInsigniaServiceTest(TestCase):

    def setUp(self):
        """
        Configuración inicial para pruebas de solicitud de INSIGNIAS (Modalidad Tradicional).
        Estrategia:
        1. Crear Cuerpos (necesarios para validación de pertenencia).
        2. Crear Usuario y asignarle cuerpo válido.
        3. Crear Acto en fecha válida para insignias.
        4. Crear Puestos (uno tipo insignia y uno tipo cirio para probar fallos).
        """
        self.ahora = timezone.now()

        self.inicio_insignias = self.ahora - timedelta(days=2)
        self.fin_insignias = self.ahora + timedelta(days=5)

        self.inicio_cirios = self.fin_insignias + timedelta(days=1)
        self.fin_cirios = self.inicio_cirios + timedelta(days=5)

        self.cuerpo_nazarenos = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.NAZARENOS
        )
        self.cuerpo_costaleros = CuerpoPertenencia.objects.create(
            nombre_cuerpo=CuerpoPertenencia.NombreCuerpo.COSTALEROS
        )

        self.hermano_nazareno = HermanoFactory(esAdmin=False)
        HermanoCuerpo.objects.create(
            hermano=self.hermano_nazareno,
            cuerpo=self.cuerpo_nazarenos,
            anio_ingreso=2010
        )

        self.hermano_sin_derecho = HermanoFactory(esAdmin=False)

        self.tipo_acto_ep = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.ESTACION_PENITENCIA,
            requiere_papeleta=True
        )

        self.acto_tradicional = Acto.objects.create(
            nombre="Estación de Penitencia 2025",
            fecha=self.ahora + timedelta(days=40),
            tipo_acto=self.tipo_acto_ep,
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            
            inicio_solicitud=self.inicio_insignias,
            fin_solicitud=self.fin_insignias,
            
            inicio_solicitud_cirios=self.inicio_cirios,
            fin_solicitud_cirios=self.fin_cirios
        )

        self.tipo_puesto_insignia = TipoPuesto.objects.create(
            nombre_tipo="Vara de Acompañamiento",
            es_insignia=True,
            solo_junta_gobierno=False
        )
        
        self.puesto_vara = Puesto.objects.create(
            nombre="Vara Boca Bocina",
            numero_maximo_asignaciones=4,
            acto=self.acto_tradicional,
            tipo_puesto=self.tipo_puesto_insignia
        )

        self.tipo_puesto_cirio = TipoPuesto.objects.create(
            nombre_tipo="Cirio",
            es_insignia=False
        )
        
        self.puesto_cirio = Puesto.objects.create(
            nombre="Cirio Tramo 3",
            numero_maximo_asignaciones=50,
            acto=self.acto_tradicional,
            tipo_puesto=self.tipo_puesto_cirio
        )



    def test_solicitud_estandar_correcta_dos_insignias(self):
        """
        Solicitud estándar correcta: 
        Verificar que un Hermano (Nazareno) puede solicitar con éxito 2 insignias 
        diferentes dentro del plazo establecido para un acto Tradicional.
        Resultado esperado: 1 PapeletaSitio y 2 objetos PreferenciaSolicitud.
        """
        segunda_insignia = Puesto.objects.create(
            nombre="Diputado de Cruz de Guía",
            numero_maximo_asignaciones=2,
            acto=self.acto_tradicional,
            tipo_puesto=self.tipo_puesto_insignia
        )

        preferencias_data = [
            {'puesto_solicitado': self.puesto_vara, 'orden_prioridad': 1},
            {'puesto_solicitado': segunda_insignia, 'orden_prioridad': 2}
        ]

        servicio = PapeletaSitioService() 
        papeleta_resultado = servicio.procesar_solicitud_insignia_tradicional(
            hermano=self.hermano_nazareno,
            acto=self.acto_tradicional,
            preferencias_data=preferencias_data
        )

        self.assertIsNotNone(papeleta_resultado)
        self.assertIsInstance(papeleta_resultado, PapeletaSitio)

        self.assertTrue(PapeletaSitio.objects.filter(id=papeleta_resultado.id).exists())
        self.assertEqual(papeleta_resultado.hermano, self.hermano_nazareno)
        self.assertEqual(papeleta_resultado.acto, self.acto_tradicional)
        self.assertTrue(papeleta_resultado.es_solicitud_insignia)
        self.assertEqual(papeleta_resultado.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)

        preferencias_creadas = PreferenciaSolicitud.objects.filter(papeleta=papeleta_resultado)
        self.assertEqual(preferencias_creadas.count(), 2)

        pref_1 = preferencias_creadas.get(orden_prioridad=1)
        pref_2 = preferencias_creadas.get(orden_prioridad=2)

        self.assertEqual(pref_1.puesto_solicitado, self.puesto_vara)
        self.assertEqual(pref_2.puesto_solicitado, segunda_insignia)



    def test_solicitud_con_una_sola_preferencia(self):
        """
        Solicitud con una sola preferencia: 
        Verificar que se puede crear la solicitud enviando una lista con un único 
        puesto (insignia) y prioridad 1.
        """
        preferencias_data = [
            {'puesto_solicitado': self.puesto_vara, 'orden_prioridad': 1}
        ]

        servicio = PapeletaSitioService()
        papeleta_resultado = servicio.procesar_solicitud_insignia_tradicional(
            hermano=self.hermano_nazareno,
            acto=self.acto_tradicional,
            preferencias_data=preferencias_data
        )

        self.assertIsNotNone(papeleta_resultado.id)
        self.assertTrue(papeleta_resultado.es_solicitud_insignia)

        qs_preferencias = papeleta_resultado.preferencias.all()
        self.assertEqual(qs_preferencias.count(), 1)

        preferencia_unica = qs_preferencias.first()
        self.assertEqual(preferencia_unica.puesto_solicitado, self.puesto_vara)
        self.assertEqual(preferencia_unica.orden_prioridad, 1)



    def test_reintento_tras_anulacion(self):
        """
        Reintento tras anulación: 
        Verificar que un Hermano que tenía una solicitud previa en estado ANULADA 
        puede volver a crear una solicitud nueva con éxito.
        El sistema debe ignorar la papeleta anulada en la validación de unicidad.
        """
        papeleta_anulada = PapeletaSitio.objects.create(
            hermano=self.hermano_nazareno,
            acto=self.acto_tradicional,
            anio=self.acto_tradicional.fecha.year,
            fecha_solicitud=self.ahora - timedelta(hours=5),
            estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA,
            es_solicitud_insignia=True,
            codigo_verificacion="CODIGO_ANTIGUO_ANULADO"
        )

        preferencias_data = [
            {'puesto_solicitado': self.puesto_vara, 'orden_prioridad': 1}
        ]

        servicio = PapeletaSitioService()
        papeleta_nueva = servicio.procesar_solicitud_insignia_tradicional(
            hermano=self.hermano_nazareno,
            acto=self.acto_tradicional,
            preferencias_data=preferencias_data
        )

        self.assertNotEqual(papeleta_nueva.id, papeleta_anulada.id)

        self.assertEqual(papeleta_nueva.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)

        total_papeletas = PapeletaSitio.objects.filter(
            hermano=self.hermano_nazareno, 
            acto=self.acto_tradicional
        ).count()
        self.assertEqual(total_papeletas, 2)

        papeletas_activas = PapeletaSitio.objects.filter(
            hermano=self.hermano_nazareno, 
            acto=self.acto_tradicional
        ).exclude(
            estado_papeleta=PapeletaSitio.EstadoPapeleta.ANULADA
        ).count()
        self.assertEqual(papeletas_activas, 1)



    def test_verificacion_prioridad_tres_preferencias(self):
        """
        Verificación de prioridad: 
        Comprobar que si se envían 3 preferencias, se guardan correctamente 
        los números de orden_prioridad (1, 2, 3) asociados a la papeleta creada.
        """
        insignia_2 = Puesto.objects.create(
            nombre="Bocina de Paso de Cristo",
            numero_maximo_asignaciones=4,
            acto=self.acto_tradicional,
            tipo_puesto=self.tipo_puesto_insignia
        )

        insignia_3 = Puesto.objects.create(
            nombre="Antepresidencia Paso de Cristo",
            numero_maximo_asignaciones=5,
            acto=self.acto_tradicional,
            tipo_puesto=self.tipo_puesto_insignia
        )

        preferencias_data = [
            {'puesto_solicitado': self.puesto_vara, 'orden_prioridad': 1},
            {'puesto_solicitado': insignia_2, 'orden_prioridad': 2},
            {'puesto_solicitado': insignia_3, 'orden_prioridad': 3},
        ]

        servicio = PapeletaSitioService()
        papeleta_resultado = servicio.procesar_solicitud_insignia_tradicional(
            hermano=self.hermano_nazareno,
            acto=self.acto_tradicional,
            preferencias_data=preferencias_data
        )

        qs_preferencias = papeleta_resultado.preferencias.all()
        self.assertEqual(qs_preferencias.count(), 3, "Deberían haberse guardado 3 preferencias")
        
        pref_1 = qs_preferencias.get(orden_prioridad=1)
        self.assertEqual(pref_1.puesto_solicitado, self.puesto_vara, "La prioridad 1 no corresponde a la Vara")

        pref_2 = qs_preferencias.get(orden_prioridad=2)
        self.assertEqual(pref_2.puesto_solicitado, insignia_2, "La prioridad 2 no corresponde a la Bocina")

        pref_3 = qs_preferencias.get(orden_prioridad=3)
        self.assertEqual(pref_3.puesto_solicitado, insignia_3, "La prioridad 3 no corresponde a la Antepresidencia")



    def test_modalidad_incorrecta_acto_unificado(self):
        """
        Modalidad incorrecta: 
        Intentar solicitar insignia cuando el Acto está configurado como UNIFICADO 
        (o cualquier otro que no sea TRADICIONAL).
        Debe lanzar ValidationError.
        """
        self.acto_tradicional.modalidad = Acto.ModalidadReparto.UNIFICADO
        self.acto_tradicional.save()

        preferencias_data = [
            {'puesto_solicitado': self.puesto_vara, 'orden_prioridad': 1}
        ]

        servicio = PapeletaSitioService()

        with self.assertRaises(ValidationError) as context:
            servicio.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_nazareno,
                acto=self.acto_tradicional,
                preferencias_data=preferencias_data
            )

        mensaje_esperado = "Este endpoint es solo para actos de modalidad TRADICIONAL."

        self.assertIn(mensaje_esperado, context.exception.messages)



    def test_error_acto_sin_papeleta(self):
        """
        Acto sin papeleta: 
        Intentar realizar una solicitud para un Acto cuyo TipoActo tiene 
        requiere_papeleta = False.
        Debe lanzar ValidationError indicando que el acto no admite solicitudes.
        """
        tipo_acto_sin_papeleta = TipoActo.objects.create(
            tipo=TipoActo.OpcionesTipo.CONVIVENCIA,
            requiere_papeleta=False
        )

        acto_convivencia = Acto.objects.create(
            nombre="Convivencia de Hermandad",
            fecha=self.ahora + timedelta(days=5),
            tipo_acto=tipo_acto_sin_papeleta,
            modalidad=Acto.ModalidadReparto.TRADICIONAL
        )

        preferencias_data = [
            {'puesto_solicitado': self.puesto_vara, 'orden_prioridad': 1}
        ]

        servicio = PapeletaSitioService()

        with self.assertRaises(ValidationError) as context:
            servicio.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_nazareno,
                acto=acto_convivencia,
                preferencias_data=preferencias_data
            )

        mensaje_esperado = f"El acto 'Convivencia de Hermandad' no admite solicitudes."
        self.assertIn(mensaje_esperado, context.exception.messages)



    def test_error_fechas_no_configuradas(self):
        """
        Fechas no configuradas: 
        Intentar solicitar cuando el Acto tiene inicio_solicitud o fin_solicitud 
        como None (null).
        Debe lanzar ValidationError indicando que el plazo no está configurado.
        """
        acto_sin_fechas = Acto.objects.create(
            nombre="Acto con Fechas Nulas",
            fecha=self.ahora + timedelta(days=60),
            tipo_acto=self.tipo_acto_ep,
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            inicio_solicitud=None,
            fin_solicitud=None
        )

        preferencias_data = [
            {'puesto_solicitado': self.puesto_vara, 'orden_prioridad': 1}
        ]

        servicio = PapeletaSitioService()

        with self.assertRaises(ValidationError) as context:
            servicio.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_nazareno,
                acto=acto_sin_fechas,
                preferencias_data=preferencias_data
            )

        mensaje_esperado = "Plazo de insignias no configurado."
        self.assertIn(mensaje_esperado, context.exception.messages)



    def test_error_solicitud_prematura(self):
        """
        Solicitud prematura: 
        Intentar solicitar insignia un minuto antes de la fecha_inicio_solicitud.
        Debe lanzar ValidationError de "Fuera del plazo de solicitud de insignias."
        """
        ahora_test = timezone.now()

        fecha_apertura = ahora_test + timedelta(minutes=1)
        fecha_cierre = ahora_test + timedelta(days=5)

        acto_futuro = Acto.objects.create(
            nombre="Acto que abre pronto",
            fecha=ahora_test + timedelta(days=30),
            tipo_acto=self.tipo_acto_ep,
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            inicio_solicitud=fecha_apertura,
            fin_solicitud=fecha_cierre
        )

        preferencias_data = [
            {'puesto_solicitado': self.puesto_vara, 'orden_prioridad': 1}
        ]

        servicio = PapeletaSitioService()

        with self.assertRaises(ValidationError) as context:
            servicio.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_nazareno,
                acto=acto_futuro,
                preferencias_data=preferencias_data
            )

        mensaje_esperado = "Fuera del plazo de solicitud de insignias."
        self.assertIn(mensaje_esperado, context.exception.messages)



    def test_error_solicitud_tardia(self):
        """
        Solicitud tardía: 
        Intentar solicitar insignia un minuto después de la fecha_fin_solicitud.
        Debe lanzar ValidationError de "Fuera del plazo de solicitud de insignias."
        """
        ahora_test = timezone.now()

        fecha_apertura = ahora_test - timedelta(days=5)
        fecha_cierre = ahora_test - timedelta(minutes=1)

        acto_pasado = Acto.objects.create(
            nombre="Acto con plazo cerrado",
            fecha=ahora_test + timedelta(days=30),
            tipo_acto=self.tipo_acto_ep,
            modalidad=Acto.ModalidadReparto.TRADICIONAL,
            inicio_solicitud=fecha_apertura,
            fin_solicitud=fecha_cierre
        )

        preferencias_data = [
            {'puesto_solicitado': self.puesto_vara, 'orden_prioridad': 1}
        ]

        servicio = PapeletaSitioService()

        with self.assertRaises(ValidationError) as context:
            servicio.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_nazareno,
                acto=acto_pasado,
                preferencias_data=preferencias_data
            )

        mensaje_esperado = "Fuera del plazo de solicitud de insignias."
        self.assertIn(mensaje_esperado, context.exception.messages)



    def test_edge_case_solicitud_exactamente_en_inicio_plazo(self):
        """
        Edge Case (límite exacto):
        Verificar que la solicitud se ACEPTA exactamente en el instante de inicio_solicitud
        del acto Tradicional (inicio incluido en el rango).

        Con la lógica actual:
            if ahora < inicio_solicitud or ahora > fin_solicitud: raise ...
        entonces ahora == inicio_solicitud debe ser válido (NO lanza error).
        """
        self.ahora = self.inicio_insignias

        self.acto_tradicional.inicio_solicitud = self.inicio_insignias
        self.acto_tradicional.fin_solicitud = self.fin_insignias
        self.acto_tradicional.save()

        preferencias_data = [
            {'puesto_solicitado': self.puesto_vara, 'orden_prioridad': 1}
        ]

        servicio = PapeletaSitioService()
        papeleta_resultado = servicio.procesar_solicitud_insignia_tradicional(
            hermano=self.hermano_nazareno,
            acto=self.acto_tradicional,
            preferencias_data=preferencias_data
        )

        self.assertIsNotNone(papeleta_resultado)
        self.assertIsInstance(papeleta_resultado, PapeletaSitio)

        self.assertTrue(PapeletaSitio.objects.filter(id=papeleta_resultado.id).exists())
        self.assertEqual(papeleta_resultado.hermano, self.hermano_nazareno)
        self.assertEqual(papeleta_resultado.acto, self.acto_tradicional)

        self.assertTrue(papeleta_resultado.es_solicitud_insignia)
        self.assertEqual(papeleta_resultado.estado_papeleta, PapeletaSitio.EstadoPapeleta.SOLICITADA)

        self.assertIsNotNone(papeleta_resultado.fecha_solicitud)
        self.assertGreaterEqual(papeleta_resultado.fecha_solicitud, self.acto_tradicional.inicio_solicitud)

        preferencias_creadas = PreferenciaSolicitud.objects.filter(papeleta=papeleta_resultado)
        self.assertEqual(preferencias_creadas.count(), 1)

        pref_1 = preferencias_creadas.get(orden_prioridad=1)
        self.assertEqual(pref_1.puesto_solicitado, self.puesto_vara)



    def test_error_mezcla_prohibida_insignia_y_cirio_en_preferencias(self):
        """
        Mezcla prohibida (Insignia + Cirio):
        Enviar preferencias que incluyen 1 puesto insignia (Vara) y 1 puesto NO insignia (Cirio).
        Debe lanzar ValidationError porque, en modalidad TRADICIONAL fase 1, todas las preferencias
        deben ser insignias.
        """
        preferencias_data = [
            {'puesto_solicitado': self.puesto_vara, 'orden_prioridad': 1},
            {'puesto_solicitado': self.puesto_cirio, 'orden_prioridad': 2},
        ]

        servicio = PapeletaSitioService()

        with self.assertRaises(ValidationError) as context:
            servicio.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_nazareno,
                acto=self.acto_tradicional,
                preferencias_data=preferencias_data
            )

        mensaje_esperado = (
            f"El puesto '{self.puesto_cirio.nombre}' no es una insignia. "
            f"En plazo tradicional, los cirios se piden aparte."
        )
        self.assertIn(mensaje_esperado, context.exception.messages)

        self.assertEqual(
            PapeletaSitio.objects.filter(hermano=self.hermano_nazareno, acto=self.acto_tradicional).count(),
            0
        )
        self.assertEqual(PreferenciaSolicitud.objects.count(), 0)



    def test_error_solo_cirio_en_plazo_de_insignias(self):
        """
        Solo Cirio en plazo de Insignias:
        Enviar una solicitud donde el único puesto solicitado NO es insignia (Cirio).
        Debe lanzar ValidationError indicando que los cirios se piden aparte.
        """
        preferencias_data = [
            {'puesto_solicitado': self.puesto_cirio, 'orden_prioridad': 1}
        ]

        servicio = PapeletaSitioService()

        with self.assertRaises(ValidationError) as context:
            servicio.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_nazareno,
                acto=self.acto_tradicional,
                preferencias_data=preferencias_data
            )

        mensaje_esperado = (
            f"El puesto '{self.puesto_cirio.nombre}' no es una insignia. "
            f"En plazo tradicional, los cirios se piden aparte."
        )
        self.assertIn(mensaje_esperado, context.exception.messages)

        self.assertEqual(
            PapeletaSitio.objects.filter(hermano=self.hermano_nazareno, acto=self.acto_tradicional).count(),
            0
        )
        self.assertEqual(PreferenciaSolicitud.objects.count(), 0)



    def test_error_cuerpo_no_permitido_costaleros(self):
        """
        Cuerpo no permitido:
        Intentar solicitar papeleta con un Hermano que SOLO pertenece al cuerpo de COSTALEROS.
        Debe lanzar ValidationError indicando que su cuerpo de pertenencia no permite solicitar papeleta.
        """
        HermanoCuerpo.objects.create(
            hermano=self.hermano_sin_derecho,
            cuerpo=self.cuerpo_costaleros,
            anio_ingreso=2015
        )

        preferencias_data = [
            {'puesto_solicitado': self.puesto_vara, 'orden_prioridad': 1}
        ]

        servicio = PapeletaSitioService()

        with self.assertRaises(ValidationError) as context:
            servicio.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_sin_derecho,
                acto=self.acto_tradicional,
                preferencias_data=preferencias_data
            )

        mensaje_esperado = "Tu cuerpo de pertenencia actual no permite solicitar papeleta."
        self.assertIn(mensaje_esperado, context.exception.messages)

        self.assertEqual(
            PapeletaSitio.objects.filter(hermano=self.hermano_sin_derecho, acto=self.acto_tradicional).count(),
            0
        )
        self.assertEqual(PreferenciaSolicitud.objects.count(), 0)



    def test_error_duplicidad_solicitud_unicidad_con_papeleta_activa(self):
        """
        Duplicidad de solicitud (Unicidad):
        Intentar solicitar con un Hermano que ya tiene una papeleta activa (SOLICITADA o EMITIDA)
        para el mismo acto. Debe lanzar ValidationError de "Ya existe una solicitud activa para este acto."
        """

        PapeletaSitio.objects.create(
            hermano=self.hermano_nazareno,
            acto=self.acto_tradicional,
            anio=self.acto_tradicional.fecha.year,
            fecha_solicitud=self.ahora - timedelta(hours=2),
            estado_papeleta=PapeletaSitio.EstadoPapeleta.SOLICITADA,
            es_solicitud_insignia=True,
            codigo_verificacion="CODIGO_ACTIVO"
        )

        preferencias_data = [
            {'puesto_solicitado': self.puesto_vara, 'orden_prioridad': 1}
        ]

        servicio = PapeletaSitioService()

        with self.assertRaises(ValidationError) as context:
            servicio.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_nazareno,
                acto=self.acto_tradicional,
                preferencias_data=preferencias_data
            )

        mensaje_esperado = "Ya existe una solicitud activa para este acto."
        self.assertIn(mensaje_esperado, context.exception.messages)

        total_papeletas = PapeletaSitio.objects.filter(
            hermano=self.hermano_nazareno,
            acto=self.acto_tradicional
        ).count()
        self.assertEqual(total_papeletas, 1)

        self.assertEqual(PreferenciaSolicitud.objects.count(), 0)



    def test_rollback_por_error_al_crear_segunda_preferencia_no_crea_papeleta(self):
        """
        Rollback por error en preferencias:
        Forzar un error al crear la segunda PreferenciaSolicitud (item corrupto / falta clave),
        y verificar que NO queda persistida la PapeletaSitio ni ninguna PreferenciaSolicitud
        gracias a @transaction.atomic.
        """
        preferencias_data = [
            {'puesto_solicitado': self.puesto_vara, 'orden_prioridad': 1},
            {'orden_prioridad': 2}
        ]

        servicio = PapeletaSitioService()

        with self.assertRaises(KeyError):
            servicio.procesar_solicitud_insignia_tradicional(
                hermano=self.hermano_nazareno,
                acto=self.acto_tradicional,
                preferencias_data=preferencias_data
            )

        self.assertEqual(
            PapeletaSitio.objects.filter(hermano=self.hermano_nazareno, acto=self.acto_tradicional).count(),
            0
        )
        self.assertEqual(
            PreferenciaSolicitud.objects.count(),
            0
        )
    


    def test_codigo_verificacion_generado_y_no_nulo(self):
        """
        Validación de UUID (codigo_verificacion):
        Verificar que, tras una solicitud exitosa de insignia en modalidad Tradicional,
        la papeleta generada contiene un codigo_verificacion relleno, no nulo y no vacío.
        """
        preferencias_data = [
            {'puesto_solicitado': self.puesto_vara, 'orden_prioridad': 1}
        ]

        servicio = PapeletaSitioService()
        papeleta_resultado = servicio.procesar_solicitud_insignia_tradicional(
            hermano=self.hermano_nazareno,
            acto=self.acto_tradicional,
            preferencias_data=preferencias_data
        )

        self.assertIsNotNone(papeleta_resultado)
        self.assertIsInstance(papeleta_resultado, PapeletaSitio)

        self.assertIsNotNone(papeleta_resultado.codigo_verificacion, "El código de verificación no debe ser None")
        self.assertNotEqual(papeleta_resultado.codigo_verificacion, "", "El código de verificación no debe estar vacío")

        self.assertEqual(len(papeleta_resultado.codigo_verificacion), 8)
        self.assertTrue(
            papeleta_resultado.codigo_verificacion.isalnum(),
            "El código de verificación debe ser alfanumérico"
        )
        self.assertEqual(
            papeleta_resultado.codigo_verificacion,
            papeleta_resultado.codigo_verificacion.upper(),
            "El código de verificación debe estar en mayúsculas"
        )

        papeleta_bd = PapeletaSitio.objects.get(id=papeleta_resultado.id)
        self.assertEqual(papeleta_bd.codigo_verificacion, papeleta_resultado.codigo_verificacion)

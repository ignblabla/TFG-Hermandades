from django.test import TestCase
from django.utils import timezone
from django.db.models.query import QuerySet

from datetime import timedelta
from api.models import Acto, Hermano, Puesto, TipoActo, TipoPuesto
from api.servicios.acto.acto_service import ActoService


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



    def test_get_todos_los_actos_devuelve_todos(self):
        """
        #     Test: Devuelve todos los actos existentes en la base de datos

        #     Given: Varios actos creados previamente en la base de datos mediante el setUp.
        #     When: Se llama al método ActoService.get_todos_los_actos().
        #     Then: El sistema devuelve un queryset con exactamente el mismo número 
        #           de registros que hay en la base de datos.
        """
        total_actos_en_bd = Acto.objects.count()

        actos_obtenidos = ActoService.get_todos_los_actos()

        self.assertEqual(
            actos_obtenidos.count(), 
            total_actos_en_bd,
            f"Se esperaban {total_actos_en_bd} actos, pero el servicio devolvió {actos_obtenidos.count()}."
        )



    def test_get_todos_los_actos_ordenacion_descendente(self):
        """
        #     Test: Ordenación descendente por fecha

        #     Given: Varios actos con distintas fechas creados en la base de datos.
        #     When: Se obtiene el queryset mediante ActoService.get_todos_los_actos().
        #     Then: El queryset está ordenado de forma que el primer elemento es 
        #           el más reciente (mayor fecha) y el último es el más antiguo (menor fecha).
        """
        actos_obtenidos = list(ActoService.get_todos_los_actos())

        self.assertTrue(len(actos_obtenidos) > 1, "Debe haber más de un acto para comprobar la ordenación.")

        fechas_obtenidas = [acto.fecha for acto in actos_obtenidos]

        fechas_esperadas = sorted(fechas_obtenidas, reverse=True)

        self.assertEqual(
            fechas_obtenidas, 
            fechas_esperadas,
            "El queryset no está ordenado por fecha de forma descendente."
        )

        self.assertEqual(fechas_obtenidas[0], max(fechas_obtenidas), "El primer acto no es el más reciente.")
        self.assertEqual(fechas_obtenidas[-1], min(fechas_obtenidas), "El último acto no es el más antiguo.")



    def test_get_todos_los_actos_fechas_iguales(self):
        """
        #     Test: Orden correcto con fechas iguales

        #     Given: Varios actos creados en la base de datos con exactamente la misma fecha.
        #     When: Se ejecuta el servicio ActoService.get_todos_los_actos().
        #     Then: El servicio no rompe y devuelve todos los registros (comprobando que 
        #           los actos con la misma fecha están incluidos en el resultado).
        """
        fecha_comun = self.ahora + timedelta(days=60)
        
        Acto.objects.create(
            nombre="Acto simultáneo 1", 
            lugar="Capilla", 
            fecha=fecha_comun, 
            tipo_acto=self.tipo_no_papeleta
        )
        Acto.objects.create(
            nombre="Acto simultáneo 2", 
            lugar="Casa Hermandad", 
            fecha=fecha_comun, 
            tipo_acto=self.tipo_no_papeleta
        )
        Acto.objects.create(
            nombre="Acto simultáneo 3", 
            lugar="Parroquia", 
            fecha=fecha_comun, 
            tipo_acto=self.tipo_no_papeleta
        )

        total_esperado_bd = Acto.objects.count()

        actos_obtenidos = list(ActoService.get_todos_los_actos())

        self.assertEqual(
            len(actos_obtenidos), 
            total_esperado_bd,
            "El servicio no devolvió el número total de actos esperado al haber fechas duplicadas."
        )

        actos_misma_fecha = [acto for acto in actos_obtenidos if acto.fecha == fecha_comun]
        self.assertEqual(
            len(actos_misma_fecha), 
            3, 
            "Faltan actos en el queryset entre los que comparten la misma fecha."
        )



    def test_get_todos_los_actos_devuelve_queryset_lazy(self):
        """
        #     Test: Queryset evaluable (lazy)

        #     Given: La base de datos inicializada con varios actos.
        #     When: Se llama al método ActoService.get_todos_los_actos().
        #     Then: El método devuelve un objeto QuerySet (no una lista ya evaluada),
        #           lo que permite la evaluación diferida (lazy) y el encadenamiento 
        #           de operaciones (chaining como .filter() o .count()).
        """
        actos_obtenidos = ActoService.get_todos_los_actos()

        self.assertIsInstance(
            actos_obtenidos, 
            QuerySet, 
            "El servicio debe devolver un QuerySet (lazy), no una lista u otro tipo de dato."
        )

        try:
            actos_filtrados = actos_obtenidos.filter(tipo_acto=self.tipo_no_papeleta)
            cantidad = actos_filtrados.count()

            self.assertEqual(
                cantidad, 
                1, 
                "El chaining del QuerySet no devolvió el resultado esperado."
            )
        except AttributeError as e:
            self.fail(f"El objeto devuelto no permite chaining de QuerySet. Error: {e}")



    def test_get_todos_los_actos_compatible_con_paginacion(self):
        """
        #     Test: Compatible con paginación

        #     Given: Un número considerable de registros en la base de datos (mínimo 6 del setUp).
        #     When: Se aplica un slicing ([:3]) al QuerySet devuelto por el servicio.
        #     Then: El sistema devuelve correctamente los primeros 3 elementos manteniendo 
        #           el orden descendente por fecha, simulando una primera página.
        """
        limite_paginacion = 3

        queryset = ActoService.get_todos_los_actos()
        pagina_1 = queryset[:limite_paginacion]

        self.assertEqual(
            len(pagina_1), 
            limite_paginacion, 
            "El slicing no devolvió la cantidad de registros esperada."
        )

        lista_completa = list(queryset)
        self.assertEqual(
            list(pagina_1), 
            lista_completa[:limite_paginacion], 
            "El slicing no mantuvo el orden consistente necesario para la paginación."
        )



    def test_get_todos_los_actos_bd_vacia(self):
        """
        #     Test: Funciona con base de datos vacía

        #     Given: Una base de datos sin registros de la entidad Acto (eliminando los previos).
        #     When: Se ejecuta el servicio ActoService.get_todos_los_actos().
        #     Then: El sistema devuelve un QuerySet vacío, sin lanzar excepciones ni devolver None.
        """
        Acto.objects.all().delete()

        actos_obtenidos = ActoService.get_todos_los_actos()

        self.assertIsNotNone(
            actos_obtenidos, 
            "El servicio devolvió None en lugar de un QuerySet vacío."
        )

        self.assertEqual(
            actos_obtenidos.count(), 
            0, 
            "El QuerySet debería estar vacío."
        )

        try:
            for acto in actos_obtenidos:
                pass
        except Exception as e:
            self.fail(f"El QuerySet vacío lanzado una excepción al ser iterado: {e}")



    def test_get_todos_los_actos_incluye_todos_los_tipos(self):
        """
        #     Test: Incluye todos los tipos de actos

        #     Given: Actos asociados a distintos tipo_acto (con papeleta, sin papeleta, etc.)
        #            creados previamente en la base de datos.
        #     When: Se llama al método ActoService.get_todos_los_actos().
        #     Then: El servicio devuelve todos los registros sin filtrar por tipo,
        #           asegurando que la colección resultante contiene actos de todas las categorías.
        """
        Acto.objects.create(
            nombre="Acto alternativo",
            lugar="Capilla",
            fecha=self.ahora + timedelta(days=40),
            tipo_acto=self.tipo_con_papeleta_alt,
            modalidad=Acto.ModalidadReparto.UNIFICADO,
            inicio_solicitud=self.ahora + timedelta(days=31),
            fin_solicitud=self.ahora + timedelta(days=35)
        )

        tipos_en_bd = TipoActo.objects.count()
        total_actos_en_bd = Acto.objects.count()

        actos_obtenidos = ActoService.get_todos_los_actos()

        self.assertEqual(
            actos_obtenidos.count(), 
            total_actos_en_bd,
            "El servicio ha filtrado registros y no ha devuelto todos los tipos de actos."
        )

        tipos_en_queryset = actos_obtenidos.values_list('tipo_acto', flat=True).distinct().count()
        
        self.assertEqual(
            tipos_en_queryset, 
            tipos_en_bd,
            f"Se esperaban actos de {tipos_en_bd} tipos diferentes, pero solo se encontraron {tipos_en_queryset}."
        )



    def test_get_todos_los_actos_ignora_orden_insercion(self):
        """
        #     Test: No debe devolver resultados desordenados (ignora orden inserción)

        #     Given: Varios actos insertados en la base de datos en un orden cronológico 
        #           aleatorio (primero uno futuro, luego uno pasado, luego uno intermedio).
        #     When: Se llama al método ActoService.get_todos_los_actos().
        #     Then: El sistema ignora el orden en que fueron creados los registros y los
        #           devuelve estrictamente ordenados por el campo 'fecha' de forma descendente.
        """
        Acto.objects.all().delete()

        fecha_intermedia = self.ahora + timedelta(days=10)
        Acto.objects.create(nombre="Intermedio", lugar="L", fecha=fecha_intermedia, tipo_acto=self.tipo_no_papeleta)

        fecha_futura = self.ahora + timedelta(days=20)
        Acto.objects.create(nombre="Futuro", lugar="L", fecha=fecha_futura, tipo_acto=self.tipo_no_papeleta)

        fecha_pasada = self.ahora + timedelta(days=1)
        Acto.objects.create(nombre="Pasado", lugar="L", fecha=fecha_pasada, tipo_acto=self.tipo_no_papeleta)

        actos_obtenidos = list(ActoService.get_todos_los_actos())
        
        self.assertEqual(actos_obtenidos[0].nombre, "Futuro")
        self.assertEqual(actos_obtenidos[1].nombre, "Intermedio")
        self.assertEqual(actos_obtenidos[2].nombre, "Pasado")

        for i in range(len(actos_obtenidos) - 1):
            self.assertGreater(
                actos_obtenidos[i].fecha, 
                actos_obtenidos[i+1].fecha,
                "El orden descendente falló: un acto posterior tiene una fecha menor que el siguiente."
            )



    def test_get_todos_los_actos_sin_filtros_implicitos(self):
        """
        #     Test: No debe aplicar filtros implícitos

        #     Given: Actos con distintas características creados en BD (futuros, 
        #            pasados, con papeleta, sin papeleta).
        #     When: Se ejecuta el método ActoService.get_todos_los_actos().
        #     Then: El servicio no excluye ninguno por lógica oculta (no hay filtros), 
        #           devolviendo la totalidad de los registros.
        """
        acto_pasado = Acto.objects.create(
            nombre="Acto del año pasado",
            lugar="Capilla",
            fecha=self.ahora - timedelta(days=365),
            tipo_acto=self.tipo_no_papeleta
        )
        
        total_esperado_bd = Acto.objects.count()

        actos_obtenidos = ActoService.get_todos_los_actos()

        self.assertEqual(
            actos_obtenidos.count(),
            total_esperado_bd,
            "El servicio está aplicando algún filtro implícito y no devuelve la totalidad de registros."
        )

        self.assertIn(
            acto_pasado,
            list(actos_obtenidos),
            "El acto con fecha pasada fue filtrado inesperadamente."
        )



    def test_get_todos_los_actos_no_devuelve_lista(self):
        """
        #     Test: No debe devolver lista en lugar de queryset

        #     Given: El estado actual de la base de datos (independientemente de si 
        #            tiene actos o no).
        #     When: Se realiza una llamada al servicio ActoService.get_todos_los_actos().
        #     Then: El objeto devuelto es estrictamente de la clase QuerySet de Django, 
        #           asegurando que no se ha evaluado prematuramente como una lista (list).
        """
        actos_obtenidos = ActoService.get_todos_los_actos()

        self.assertNotIsInstance(
            actos_obtenidos, 
            list,
            "Error: El servicio evaluó la consulta prematuramente y devolvió una lista (list)."
        )

        self.assertIsInstance(
            actos_obtenidos, 
            QuerySet,
            f"Se esperaba un QuerySet, pero se recibió un tipo: {type(actos_obtenidos).__name__}."
        )



    def test_get_todos_los_actos_no_modifica_datos(self):
        """
        #     Test: No debe modificar datos (solo lectura)

        #     Given: El estado inicial de la base de datos con los actos creados.
        #     When: Se llama al método ActoService.get_todos_los_actos() múltiples veces.
        #     Then: Ningún registro de la base de datos sufre modificaciones ni 
        #           se altera el conteo total, garantizando que es una operación segura.
        """
        total_inicial = Acto.objects.count()

        estado_inicial = list(Acto.objects.values_list('id', 'nombre', 'fecha'))

        for _ in range(5):
            list(ActoService.get_todos_los_actos())

        total_final = Acto.objects.count()
        self.assertEqual(
            total_final, 
            total_inicial,
            "El número de actos cambió tras ejecutar el servicio de consulta."
        )

        estado_final = list(Acto.objects.values_list('id', 'nombre', 'fecha'))

        self.assertListEqual(
            sorted(estado_inicial),
            sorted(estado_final),
            "Los datos de los registros han sido modificados tras una operación de solo lectura."
        )



    def test_get_todos_los_actos_sin_consultas_innecesarias(self):
        """
        #     Test: No debe ejecutar consultas adicionales innecesarias

        #     Given: Varios actos creados y almacenados en la base de datos (setUp).
        #     When: Se llama al servicio ActoService.get_todos_los_actos() y se 
        #           itera sobre sus resultados.
        #     Then: Se ejecuta exactamente 1 consulta a la base de datos, sin 
        #           consultas adicionales inesperadas (sin efectos secundarios).
        """
        total_esperado = Acto.objects.count()

        with self.assertNumQueries(1):
            actos_obtenidos = ActoService.get_todos_los_actos()

            nombres = [acto.nombre for acto in actos_obtenidos]

        self.assertEqual(
            len(nombres), 
            total_esperado,
            "El número de elementos iterados no coincide con la base de datos."
        )
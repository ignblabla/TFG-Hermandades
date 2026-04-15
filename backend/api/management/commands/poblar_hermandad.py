import random

from ...models import Acto, Comunicado, CuerpoPertenencia, Cuota, DatosBancarios, Hermano, AreaInteres, PapeletaSitio, PreferenciaSolicitud, Puesto, TipoActo, TipoPuesto, Tramo
from datetime import date, datetime
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import make_aware
import os
from django.conf import settings
from django.core.files import File
import random
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = 'Puebla la base de datos con hermanos de prueba y áreas de interés'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando el poblado de datos...")

        with transaction.atomic():

            # =========================================================================
            # LIMPIEZA PREVIA DE TABLAS
            # =========================================================================
            self.stdout.write("Limpiando tablas y reiniciando contadores autoincrementales...")

            PreferenciaSolicitud.objects.all().delete()
            PapeletaSitio.objects.all().delete()
            Puesto.objects.all().delete()
            Acto.objects.all().delete()
            TipoActo.objects.all().delete()
            TipoPuesto.objects.all().delete()
            AreaInteres.objects.all().delete()
            CuerpoPertenencia.objects.all().delete()
            Comunicado.objects.all().delete()
            Cuota.objects.all().delete()
            Hermano.objects.all().delete()

            modelos_a_reiniciar = [
                PreferenciaSolicitud, PapeletaSitio, Puesto, Acto, TipoActo, 
                TipoPuesto, AreaInteres, CuerpoPertenencia, Comunicado, Cuota, Hermano
            ]

            with connection.cursor() as cursor:
                for modelo in modelos_a_reiniciar:
                    try:
                        cursor.execute(f"ALTER TABLE {modelo._meta.db_table} AUTO_INCREMENT = 1;")
                    except Exception as e:
                        pass
            
            self.stdout.write(self.style.SUCCESS("Tablas limpias y contadores a 0."))

            # =========================================================================
            # POBLADO DE TIPOS DE PUESTO
            # =========================================================================
            self.stdout.write("Iniciando el poblado de Tipos de Puesto...")
            
            tipos_puesto_data = [
                {"id": 1, "nombre_tipo": "CIRIO_APAGADO", "solo_junta_gobierno": False, "es_insignia": True},
                {"id": 2, "nombre_tipo": "MANIGUETA", "solo_junta_gobierno": False, "es_insignia": True},
                {"id": 3, "nombre_tipo": "VARA_ANTEPRESIDENCIA", "solo_junta_gobierno": False, "es_insignia": True},
                {"id": 4, "nombre_tipo": "VARA_PRESIDENCIA", "solo_junta_gobierno": True, "es_insignia": True},
                {"id": 5, "nombre_tipo": "CIRIO", "solo_junta_gobierno": False, "es_insignia": False},
                {"id": 6, "nombre_tipo": "VARA_TRAMO", "solo_junta_gobierno": False, "es_insignia": True},
                {"id": 7, "nombre_tipo": "INSIGNIA", "solo_junta_gobierno": False, "es_insignia": True},
                {"id": 8, "nombre_tipo": "BOCINA", "solo_junta_gobierno": False, "es_insignia": True},
                {"id": 9, "nombre_tipo": "FAROL", "solo_junta_gobierno": False, "es_insignia": True},
                {"id": 10, "nombre_tipo": "PENITENTE", "solo_junta_gobierno": False, "es_insignia": False},
                {"id": 11, "nombre_tipo": "DIPUTADO_BANDA", "solo_junta_gobierno": False, "es_insignia": True},
                {"id": 12, "nombre_tipo": "CRUZ_GUIA", "solo_junta_gobierno": False, "es_insignia": True},
            ]

            tipos_puesto_a_crear = [TipoPuesto(**data) for data in tipos_puesto_data]
            TipoPuesto.objects.bulk_create(tipos_puesto_a_crear)
            
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(tipos_puesto_a_crear)} tipos de puesto.'))

            # =========================================================================
            # POBLADO DE TIPOS DE ACTO
            # =========================================================================
            self.stdout.write("Iniciando el poblado de Tipos de Acto...")
            
            tipos_acto_data = [
                {"id": 1, "tipo": "ESTACION_PENITENCIA", "requiere_papeleta": True},
                {"id": 2, "tipo": "CABILDO_GENERAL", "requiere_papeleta": False},
                {"id": 3, "tipo": "CABILDO_EXTRAORDINARIO", "requiere_papeleta": False},
                {"id": 4, "tipo": "VIA_CRUCIS", "requiere_papeleta": True},
                {"id": 5, "tipo": "QUINARIO", "requiere_papeleta": False},
                {"id": 6, "tipo": "TRIDUO", "requiere_papeleta": False},
                {"id": 7, "tipo": "ROSARIO_AURORA", "requiere_papeleta": True},
                {"id": 8, "tipo": "CONVIVENCIA", "requiere_papeleta": False},
                {"id": 9, "tipo": "PROCESION_EUCARISTICA", "requiere_papeleta": False},
                {"id": 10, "tipo": "PROCESION_EXTRAORDINARIA", "requiere_papeleta": True},
                {"id": 11, "tipo": "MISA_HERMANDAD", "requiere_papeleta": False},
            ]

            tipos_acto_a_crear = [TipoActo(**data) for data in tipos_acto_data]
            TipoActo.objects.bulk_create(tipos_acto_a_crear)
            
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(tipos_acto_a_crear)} tipos de acto.'))

            # =========================================================================
            # POBLADO DE ÁREAS DE INTERÉS
            # =========================================================================
            self.stdout.write("Iniciando el poblado de Áreas de Interés...")
            
            areas_data = [
                {"id": 1,"nombre_area": "CARIDAD", "telegram_channel_id": "-1003771492735", "telegram_invite_link": "https://t.me/+6COuAR98wTg4ZTg0"},
                {"id": 2,"nombre_area": "CULTOS_FORMACION", "telegram_channel_id": "-1003810636379", "telegram_invite_link": "https://t.me/+y6RU6E-56GlwZjk0"},
                {"id": 3,"nombre_area": "JUVENTUD", "telegram_channel_id": "-1003712795257", "telegram_invite_link": "https://t.me/+YLUtzvpqJ0UwNzdk"},
                {"id": 4,"nombre_area": "PATRIMONIO", "telegram_channel_id": "-1003845246574", "telegram_invite_link": "https://t.me/+0pt8qkh_swYwZjY0"},
                {"id": 5,"nombre_area": "PRIOSTIA", "telegram_channel_id": "-1003827691615", "telegram_invite_link": "https://t.me/+kBu6wbNcxyU4MTFk"},
                {"id": 6,"nombre_area": "DIPUTACION_MAYOR_GOBIERNO", "telegram_channel_id": "-1003752302067", "telegram_invite_link": "https://t.me/+RSbb2civhvsyYjk8"},
                {"id": 7,"nombre_area": "COSTALEROS", "telegram_channel_id": "-1003754745133", "telegram_invite_link": "https://t.me/+W-HAa5nMjLNINTc0"},
                {"id": 8,"nombre_area": "ACOLITOS", "telegram_channel_id": "-1003681055153", "telegram_invite_link": "https://t.me/+sVPhJF3zi3wyNjI0"},
                {"id": 9,"nombre_area": "TODOS_HERMANOS", "telegram_channel_id": "-1003835565597", "telegram_invite_link": "https://t.me/+gs2wua73Y003N2M0"},
            ]

            areas_a_crear = [AreaInteres(**data) for data in areas_data]
            AreaInteres.objects.bulk_create(areas_a_crear)
            
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(areas_a_crear)} áreas de interés.'))

            # =========================================================================
            # POBLADO DE CUERPOS DE PERTENENCIA
            # =========================================================================
            self.stdout.write("Iniciando el poblado de Cuerpos de Pertenencia...")
            
            cuerpos_data = [
                {"id": 1, "nombre_cuerpo": "COSTALEROS"},
                {"id": 2, "nombre_cuerpo": "NAZARENOS"},
                {"id": 3, "nombre_cuerpo": "DIPUTADOS"},
                {"id": 4, "nombre_cuerpo": "BRAZALETES"},
                {"id": 5, "nombre_cuerpo": "ACOLITOS"},
                {"id": 6, "nombre_cuerpo": "CAPATACES"},
                {"id": 7, "nombre_cuerpo": "SANITARIOS"},
                {"id": 8, "nombre_cuerpo": "PRIOSTIA"},
                {"id": 9, "nombre_cuerpo": "CARIDAD_ACCION_SOCIAL"},
                {"id": 10, "nombre_cuerpo": "JUVENTUD"},
                {"id": 11, "nombre_cuerpo": "JUNTA_GOBIERNO"},
            ]

            cuerpos_a_crear = [CuerpoPertenencia(**data) for data in cuerpos_data]
            CuerpoPertenencia.objects.bulk_create(cuerpos_a_crear)
            
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(cuerpos_a_crear)} cuerpos de pertenencia.'))

            # =========================================================================
            # POBLADO DE HERMANOS
            # =========================================================================
            self.stdout.write("Iniciando el poblado de Hermanos...")

            if not Hermano.objects.filter(dni="11111111A").exists():
                Hermano.objects.create_user(id=1, nombre="Rafael", primer_apellido="Blanquero", segundo_apellido="Bravo",
                    dni="11111111A", username="11111111A", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="rblanquero@us.es", telefono="646172201", estado_civil="CASADO",
                    fecha_nacimiento="1966-01-06",genero="MASCULINO",
                    direccion="Calle Pensamiento, 50", localidad="Mairena del Aljarafe", codigo_postal = "41927",
                    provincia="Sevilla",comunidad_autonoma="Andalucía",
                    fecha_bautismo="1966-01-30", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Gonzalo",
                    estado_hermano = "ALTA", numero_registro="1", fecha_ingreso_corporacion="1973-03-01")

            if not Hermano.objects.filter(dni="11111111B").exists():
                Hermano.objects.create_user(id=2, nombre="Francisco", primer_apellido="Barrio", segundo_apellido="Muñoz",
                    dni="11111111B", username="11111111B", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="pacobarrio@gmail.com", telefono="649146786", estado_civil="CASADO",
                    fecha_nacimiento="1968-05-07",genero="MASCULINO",
                    direccion="Calle Cristo del Soberano Poder, 16", localidad="Sevilla", codigo_postal = "41010",
                    provincia="Sevilla",comunidad_autonoma="Andalucía",
                    fecha_bautismo="1968-10-25", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Gonzalo",
                    estado_hermano = "ALTA", numero_registro="2", fecha_ingreso_corporacion="1973-03-02")


            def generar_dni():
                letras = "TRWAGMYFPDXBNJZSQVHLCKE"
                numero = random.randint(30000000, 99999999)
                letra = letras[numero % 23]
                return f"{numero}{letra}"

            def generar_fecha_aleatoria(inicio, fin):
                dias_diferencia = (fin - inicio).days
                dias_aleatorios = random.randint(0, dias_diferencia)
                return inicio + timedelta(days=dias_aleatorios)

            def crear_hermanos_ordenados_bulk(cantidad, inicio_registro, fecha_ingreso_inicio, fecha_ingreso_fin):
                nombres_masculinos = ["Antonio", "Manuel", "José", "Francisco", "David", "Juan", "Javier", "Daniel", "Carlos", "Alejandro", "Rafael", "Miguel"]
                nombres_femeninos = ["María", "Carmen", "Ana", "Isabel", "Laura", "Marta", "Cristina", "Lucía", "Rosario", "Rocío", "Elena", "Paula"]
                apellidos = ["García", "Martínez", "López", "Sánchez", "Pérez", "Gómez", "Martín", "Jiménez", "Ruiz", "Hernández", "Díaz", "Moreno", "Álvarez", "Muñoz", "Blanco", "Navarro"]

                vias = [
                    "Calle Pureza", "Calle Betis", "Calle San Jacinto", "Calle Castilla", 
                    "Calle Alfarería", "Calle Rodrigo de Triana", "Calle Esperanza de Triana", 
                    "Calle Pagés del Corro", "Plaza del Altozano", "Calle Sierpes", 
                    "Avenida de la Constitución", "Calle Tetuán", "Plaza Nueva"
                ]

                parroquias = [
                    "Real Parroquia de Señora Santa Ana", "Parroquia de San Gonzalo", 
                    "Parroquia de San Jacinto", "Parroquia de Nuestra Señora de la O", 
                    "Parroquia del Sagrario", "Parroquia de San Lorenzo", 
                    "Parroquia de San Bernardo", "Parroquia de Omnium Sanctorum",
                    "Basílica de la Macarena", "Basílica del Gran Poder"
                ]
                
                estados_civiles = ["SOLTERO", "SEPARADO", "CASADO", "VIUDO"]

                fecha_nacimiento_inicio = date(1920, 1, 1)
                
                password_hasheada = make_password("1234")
                
                datos_temporales = []
                dnis_usados = set(["11111111A", "11111111B"])

                while len(datos_temporales) < cantidad:
                    dni = generar_dni()
                    if dni in dnis_usados:
                        continue
                    dnis_usados.add(dni)

                    genero = random.choice(["MASCULINO", "FEMENINO"])
                    nombre = random.choice(nombres_masculinos) if genero == "MASCULINO" else random.choice(nombres_femeninos)
                    apellido1 = random.choice(apellidos)
                    apellido2 = random.choice(apellidos)

                    fecha_ingreso = generar_fecha_aleatoria(fecha_ingreso_inicio, fecha_ingreso_fin)

                    fecha_bautismo_fin_posible = fecha_ingreso - timedelta(days=30)

                    fecha_nacimiento_fin_posible = fecha_bautismo_fin_posible - timedelta(days=30)

                    if fecha_nacimiento_fin_posible < fecha_nacimiento_inicio:
                        fecha_nac_inicio_ajustada = fecha_nacimiento_fin_posible - timedelta(days=365*20)
                    else:
                        fecha_nac_inicio_ajustada = fecha_nacimiento_inicio

                    fecha_nac = generar_fecha_aleatoria(fecha_nac_inicio_ajustada, fecha_nacimiento_fin_posible)

                    fecha_bau = generar_fecha_aleatoria(fecha_nac + timedelta(days=1), fecha_ingreso - timedelta(days=1))
                    
                    email = f"{nombre[:1].lower()}{apellido1.lower()}{random.randint(100,999)}@ejemplo.com"
                    telefono = f"6{random.randint(0, 9)}{random.randint(1000000, 9999999)}"
                    direccion = f"{random.choice(vias)}, {random.randint(1, 150)}"
                    
                    datos_temporales.append({
                        "nombre": nombre,
                        "primer_apellido": apellido1,
                        "segundo_apellido": apellido2,
                        "dni": dni,
                        "username": dni,
                        "password": password_hasheada,
                        "is_superuser": False,
                        "is_staff": True,
                        "is_active": True,
                        "esAdmin": False,
                        "email": email,
                        "telefono": telefono,
                        "estado_civil": random.choice(estados_civiles),
                        "fecha_nacimiento": fecha_nac,
                        "genero": genero,
                        "direccion": direccion,
                        "localidad": "Sevilla",
                        "codigo_postal": "41010",
                        "provincia": "Sevilla",
                        "comunidad_autonoma": "Andalucía",
                        "fecha_bautismo": fecha_bau,
                        "lugar_bautismo": "Sevilla",
                        "parroquia_bautismo": random.choice(parroquias),
                        "estado_hermano": "ALTA",
                        "fecha_ingreso_corporacion": fecha_ingreso
                    })

                datos_temporales.sort(key=lambda x: x["fecha_ingreso_corporacion"])

                hermanos_a_crear = []
                numero_registro_actual = inicio_registro

                for datos in datos_temporales:
                    datos["numero_registro"] = str(numero_registro_actual)
                    hermanos_a_crear.append(Hermano(**datos))
                    numero_registro_actual += 1

                Hermano.objects.bulk_create(hermanos_a_crear)
                print(f"Se han creado {len(hermanos_a_crear)} hermanos en Sevilla/Triana correctamente, ordenados por fecha de ingreso.")
                return numero_registro_actual

            sig_registro = crear_hermanos_ordenados_bulk(
                cantidad=100, 
                inicio_registro=3, 
                fecha_ingreso_inicio=date(1973, 3, 3), 
                fecha_ingreso_fin=date(1973, 12, 31)
            )

            sig_registro = crear_hermanos_ordenados_bulk(
                cantidad=500, 
                inicio_registro=sig_registro, 
                fecha_ingreso_inicio=date(1974, 1, 1), 
                fecha_ingreso_fin=date(2000, 1, 1)
            )

            sig_registro = crear_hermanos_ordenados_bulk(
                cantidad=750, 
                inicio_registro=sig_registro, 
                fecha_ingreso_inicio=date(2000, 2, 1), 
                fecha_ingreso_fin=date(2005, 12, 27)
            )

            if not Hermano.objects.filter(dni="53962686V").exists():
                Hermano.objects.create_user(id=1353, nombre="Ignacio", primer_apellido="Blanquero", segundo_apellido="Blanco",
                    dni="53962686V", username="53962686V", password="1234", is_superuser=True, is_staff=True, is_active=True,
                    esAdmin=True, email="ignblabla@us.es", telefono="644169492", estado_civil="SOLTERO",
                    fecha_nacimiento="2003-01-24",genero="MASCULINO",
                    direccion="Calle Pensamiento, 50", localidad="Mairena del Aljarafe", codigo_postal = "41927",
                    provincia="Sevilla",comunidad_autonoma="Andalucía",
                    fecha_bautismo="2003-04-26", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Gonzalo",
                    estado_hermano = "ALTA", numero_registro="1353", fecha_ingreso_corporacion="2006-03-01")
                
            sig_registro += 1

            sig_registro = crear_hermanos_ordenados_bulk(
                cantidad=3500, 
                inicio_registro=sig_registro, 
                fecha_ingreso_inicio=date(2006, 3, 2), 
                fecha_ingreso_fin=date(2025, 12, 27)
            )

            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Todos los lotes de hermanos creados correctamente.'))


        # =========================================================================
        # POBLADO DE CUOTAS
        # =========================================================================
        self.stdout.write("Iniciando el poblado masivo de Cuotas...")
        
        Cuota.objects.all().delete()

        with connection.cursor() as cursor:
            try:
                cursor.execute(f"ALTER TABLE {Cuota._meta.db_table} AUTO_INCREMENT = 1;")
            except Exception:
                pass

        hermanos_a_poblar = Hermano.objects.all()

        cuotas_a_crear = []
        anio_actual = 2026

        for hermano in hermanos_a_poblar:
            anio_ingreso = hermano.fecha_ingreso_corporacion.year if hermano.fecha_ingreso_corporacion else 1974
            anio_inicio_cuotas = max(1974, anio_ingreso)

            for anio in range(anio_inicio_cuotas, anio_actual + 1):
                cuota = Cuota(
                    hermano=hermano,
                    anio=anio,
                    tipo="ORDINARIA",
                    descripcion=f"Cuota Ordinaria {anio}",
                    importe=45.00,
                    estado="PAGADA",
                    metodo_pago="DOMICILIACION",
                    fecha_emision=f"{anio}-05-15",
                    fecha_pago=f"{anio}-06-15"
                )
                cuotas_a_crear.append(cuota)

        Cuota.objects.bulk_create(cuotas_a_crear)
        
        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han generado {len(cuotas_a_crear)} cuotas anuales masivamente.'))


        # =========================================================================
        # POBLADO DE ACTO: ESTACIÓN DE PENITENCIA 2026 (ID=1)
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Acto: Estación de Penitencia 2026...")

        now = timezone.now()

        Acto.objects.filter(id=1).delete()

        descripcion_acto = (
            "La Estación de Penitencia a la Santa Iglesia Catedral es el acto central y culminante "
            "de la vida de nuestra Hermandad de San Gonzalo. En este año 2026, nos preparamos para vivir "
            "nuevamente este encuentro íntimo con nuestro Señor en su Soberano Poder ante Caifás y nuestra "
            "Madre y Señora de la Salud. Este solemne acto público de fe es la manifestación más genuina de nuestro "
            "compromiso cristiano, donde cada nazareno, costalero, acólito y hermano se convierte en un "
            "testimonio vivo del Evangelio por las calles de nuestro barrio de Triana y de toda Sevilla. "
            "Durante nuestro caminar, la túnica blanca se transforma en nuestra piel, igualándonos a todos "
            "bajo la cruz de Cristo. La cofradía no es solo un cortejo estético, es una auténtica comunidad en "
            "movimiento que reza, que acompaña y que sostiene a los Sagrados Titulares en su discurrir. "
            "Se invita a todos los hermanos a participar con recogimiento, orden y profundo sentido de "
            "pertenencia, haciendo de cada paso una oración y de cada cirio encendido una luz de esperanza "
            "para aquellos que más lo necesitan en estos tiempos. Que esta nueva Estación de Penitencia renueve "
            "nuestra vocación de servicio, fortaleciendo firmemente los lazos de fraternidad que nos unen "
            "como corporación cristiana y acercándonos aún más a la misericordia infinita de Dios, viviendo la "
            "caridad, la esperanza y la inquebrantable devoción en cada instante de nuestra procesión."
        )

        acto_ep = Acto(
            id=1,
            nombre="Estación de Penitencia 2026",
            lugar="Parroquia de San Gonzalo",
            descripcion=descripcion_acto,
            fecha=(now + timedelta(days=30)).replace(hour=15, minute=0, second=0, microsecond=0),
            modalidad="TRADICIONAL",
            tipo_acto_id=1,
            inicio_solicitud=now - timedelta(days=10),
            fin_solicitud=now - timedelta(days=1),
            inicio_solicitud_cirios=now + timedelta(days=16),
            fin_solicitud_cirios=now + timedelta(days=24),
            fecha_ejecucion_reparto=None,
        )

        ruta_imagen = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'EstacionPenitencia2025.jpg')
        
        if os.path.exists(ruta_imagen):
            with open(ruta_imagen, 'rb') as f:
                acto_ep.imagen_portada.save('EstacionPenitencia2025.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Acto 1.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen}'))

        acto_ep.save()
        
        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Acto Estación de Penitencia 2026 con ID 1.'))


        # =========================================================================
        # POBLADO DE PUESTOS DEL ACTO 1
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Puestos para el Acto 1...")

        puestos_data = [
            {"id": 1, "nombre": "Bocina Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 8, "cortejo_cristo": True},
            {"id": 2, "nombre": "Cruz de Guía", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 12, "cortejo_cristo": True},
            {"id": 3, "nombre": "Farol Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 9, "cortejo_cristo": True},
            {"id": 4, "nombre": "Senatus (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 5, "nombre": "Varas Senatus (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 6, "nombre": "Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 7, "nombre": "Varas Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 8, "nombre": "Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 9, "nombre": "Varas Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 10, "nombre": "Banderín Sacramental (tramo 5)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 11, "nombre": "Varas Banderín Sacramental (tramo 5)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 12, "nombre": "Guión del Cincuentenario (tramo 6)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 13, "nombre": "Varas Guión del Cincuentenario (tramo 6)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 14, "nombre": "Banderín de la Juventud (tramo 7)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 15, "nombre": "Varas Banderín de la Juventud (tramo 7)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 16, "nombre": "Bandera Cruz de Jerusalén (tramo 8)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 17, "nombre": "Varas Bandera Cruz de Jerusalén (tramo 8)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 18, "nombre": "Guión de la Caridad (tramo 9)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 19, "nombre": "Varas Guión de la Caridad (tramo 9)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 20, "nombre": "Guión Sacramental (tramo 10)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 21, "nombre": "Varas Guión Sacramental (tramo 10)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 22, "nombre": "Estandarte Sacramental (tramo 11)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 23, "nombre": "Varas Estandarte Sacramental (tramo 11)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 24, "nombre": "Cirio Grande Cristo", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 25, "nombre": "Cirio Mediano Cristo", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 26, "nombre": "Cirio Pequeño Cristo", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 5, "cortejo_cristo": True},
        ]

        puestos_virgen_data = [
            {"id": 27, "nombre": "Cirios apagados cruces (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 1, "cortejo_cristo": False},
            {"id": 28, "nombre": "Bocinas (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 8, "cortejo_cristo": False},
            {"id": 29, "nombre": "Simpecado (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 30, "nombre": "Faroles Simpecado (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 9, "cortejo_cristo": False},
            {"id": 31, "nombre": "Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 32, "nombre": "Varas Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 33, "nombre": "Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 34, "nombre": "Varas Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 35, "nombre": "Bandera Concepcionista (tramo 5)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 36, "nombre": "Varas Bandera Concepcionista (tramo 5)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 37, "nombre": "Bandera Realeza de María (tramo 6)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 38, "nombre": "Varas Bandera Realeza de María (tramo 6)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 39, "nombre": "Guión de la Coronación (tramo 7)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 40, "nombre": "Varas Guión de la Coronación (tramo 7)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 41, "nombre": "Libro de Reglas (tramo 8)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 42, "nombre": "Varas Libro de Reglas (tramo 8)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 43, "nombre": "Estandarte (tramo 9)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 44, "nombre": "Varas Estandarte (tramo 9)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 45, "nombre": "Cirio Grande Virgen", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 46, "nombre": "Cirio Mediano Virgen", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 47, "nombre": "Cirio Pequeño Virgen", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 5, "cortejo_cristo": False},
        ]

        puestos_data.extend(puestos_virgen_data)

        puestos_a_crear = [Puesto(**data) for data in puestos_data]
        Puesto.objects.bulk_create(puestos_a_crear)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(puestos_a_crear)} puestos para el Acto 1 en total.'))



        # =========================================================================
        # POBLADO DE PAPELETAS DE SITIO: ACTO ID=1
        # =========================================================================
        self.stdout.write("Iniciando el poblado masivo de Papeletas de Sitio para el Acto 1...")

        PapeletaSitio.objects.filter(acto_id=1).delete()

        papeletas_data = []
        codigos_usados = set()

        segundos_min = 86400
        segundos_max = 864000

        todos_hermanos_ids = list(Hermano.objects.values_list('id', flat=True))

        hermanos_para_papeleta = []
        id_objetivo = 1

        if id_objetivo in todos_hermanos_ids:
            hermanos_para_papeleta.append(id_objetivo)
            todos_hermanos_ids.remove(id_objetivo)
            self.stdout.write(self.style.SUCCESS(f'Forzando solicitud para el Hermano ID {id_objetivo} en el Acto 1.'))

        cantidad_restante = min(375 - len(hermanos_para_papeleta), len(todos_hermanos_ids))
        hermanos_para_papeleta.extend(random.sample(todos_hermanos_ids, cantidad_restante))

        for id_papeleta, hermano_id in enumerate(hermanos_para_papeleta, start=1):

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados:
                    codigos_usados.add(codigo)
                    break

            segundos_aleatorios = random.randint(segundos_min, segundos_max)
            fecha_aleatoria = now - timedelta(seconds=segundos_aleatorios)

            papeletas_data.append(
                {
                    "id": id_papeleta,
                    "estado_papeleta": "SOLICITADA",
                    "fecha_solicitud": fecha_aleatoria,
                    "fecha_emision": None, 
                    "codigo_verificacion": codigo,
                    "anio": 2026,
                    "numero_papeleta": None,
                    "es_solicitud_insignia": True,
                    "acto_id": 1,
                    "hermano_id": hermano_id,
                    "puesto_id": None,
                    "tramo_id": None,
                    "vinculado_a_id": None,
                    "lado": None,
                    "orden_en_tramo": None,
                }
            )

        papeletas_a_crear = [PapeletaSitio(**data) for data in papeletas_data]
        PapeletaSitio.objects.bulk_create(papeletas_a_crear)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_a_crear)} papeletas de sitio para el Acto 1.'))


        # =========================================================================
        # POBLADO DE PREFERENCIAS DE SOLICITUD: ACTO ID=1
        # =========================================================================
        self.stdout.write("Iniciando el poblado masivo de Preferencias de Solicitud para el Acto 1...")

        PreferenciaSolicitud.objects.all().delete()

        puestos_excluidos = {24, 25, 26, 45, 46, 47}
        puestos_disponibles_ids = [pid for pid in range(1, 42) if pid not in puestos_excluidos]

        preferencias_data = []
        id_preferencia = 1

        for papeleta in papeletas_data:
            num_preferencias = random.randint(4, 7)
            puestos_elegidos = random.sample(puestos_disponibles_ids, num_preferencias)

            for orden, puesto_id in enumerate(puestos_elegidos, start=1):
                preferencias_data.append(
                    {
                        "id": id_preferencia,
                        "orden_prioridad": orden,
                        "papeleta_id": papeleta["id"],
                        "puesto_solicitado_id": puesto_id
                    }
                )
                id_preferencia += 1

        preferencias_a_crear = [PreferenciaSolicitud(**data) for data in preferencias_data]
        PreferenciaSolicitud.objects.bulk_create(preferencias_a_crear)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(preferencias_a_crear)} preferencias de solicitud.'))



        # =========================================================================
        # POBLADO DE ACTO: ESTACIÓN DE PENITENCIA 2027 (ID=2)
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Acto: Estación de Penitencia 2027...")

        now = timezone.now()

        Acto.objects.filter(id=2).delete()

        descripcion_acto = (
                "La Estación de Penitencia a la Santa Iglesia Catedral es el acto central y culminante "
                "de la vida de nuestra Hermandad de San Gonzalo. En este año 2027, nos preparamos para vivir "
                "nuevamente este encuentro íntimo con nuestro Señor en su Soberano Poder ante Caifás y nuestra "
                "Madre y Señora de la Salud. Este solemne acto público de fe es la manifestación más genuina de nuestro "
                "compromiso cristiano, donde cada nazareno, costalero, acólito y hermano se convierte en un "
                "testimonio vivo del Evangelio por las calles de nuestro barrio de Triana y de toda Sevilla. "
                "Durante nuestro caminar, la túnica blanca se transforma en nuestra piel, igualándonos a todos "
                "bajo la cruz de Cristo. La cofradía no es solo un cortejo estético, es una auténtica comunidad en "
                "movimiento que reza, que acompaña y que sostiene a los Sagrados Titulares en su discurrir. "
                "Se invita a todos los hermanos a participar con recogimiento, orden y profundo sentido de "
                "pertenencia, haciendo de cada paso una oración y de cada cirio encendido una luz de esperanza "
                "para aquellos que más lo necesitan en estos tiempos. Que esta nueva Estación de Penitencia renueve "
                "nuestra vocación de servicio, fortaleciendo firmemente los lazos de fraternidad que nos unen "
                "como corporación cristiana y acercándonos aún más a la misericordia infinita de Dios, viviendo la "
                "caridad, la esperanza y la inquebrantable devoción en cada instante de nuestra procesión."
            )

        acto_ep27 = Acto(
                id=2,
                nombre="Estación de Penitencia 2027",
                lugar="Parroquia de San Gonzalo",
                descripcion=descripcion_acto,
                fecha=(now + timedelta(days=365)).replace(hour=15, minute=0, second=0, microsecond=0),
                modalidad="TRADICIONAL",
                tipo_acto_id=1,
                inicio_solicitud=now - timedelta(days=20),
                fin_solicitud=now - timedelta(days=10),
                inicio_solicitud_cirios=now - timedelta(days=8),
                fin_solicitud_cirios=now - timedelta(days=1),
                fecha_ejecucion_reparto = (now - timedelta(days=9))
            )

        ruta_imagen = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'EstacionPenitencia2025.jpg')

        if os.path.exists(ruta_imagen):
            with open(ruta_imagen, 'rb') as f:
                acto_ep27.imagen_portada.save('EstacionPenitencia2025.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Acto 2.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen}'))

        acto_ep27.save()
        
        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Acto Estación de Penitencia 2027 con ID 2.'))


        # =========================================================================
        # POBLADO DE PUESTOS DEL ACTO 2
        # =========================================================================

        self.stdout.write("Iniciando el poblado de Puestos para el Acto 2...")

        puestos_data_ep27 = [
            {"id": 48, "nombre": "Bocina Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 8, "cortejo_cristo": True},
            {"id": 49, "nombre": "Cruz de Guía", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 12, "cortejo_cristo": True},
            {"id": 50, "nombre": "Farol Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 9, "cortejo_cristo": True},
            {"id": 51, "nombre": "Senatus (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 52, "nombre": "Varas Senatus (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 53, "nombre": "Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 54, "nombre": "Varas Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 55, "nombre": "Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 56, "nombre": "Varas Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 57, "nombre": "Banderín Sacramental (tramo 5)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 58, "nombre": "Varas Banderín Sacramental (tramo 5)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 59, "nombre": "Guión del Cincuentenario (tramo 6)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 60, "nombre": "Varas Guión del Cincuentenario (tramo 6)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 61, "nombre": "Banderín de la Juventud (tramo 7)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 62, "nombre": "Varas Banderín de la Juventud (tramo 7)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 63, "nombre": "Bandera Cruz de Jerusalén (tramo 8)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 64, "nombre": "Varas Bandera Cruz de Jerusalén (tramo 8)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 65, "nombre": "Guión de la Caridad (tramo 9)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 66, "nombre": "Varas Guión de la Caridad (tramo 9)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 67, "nombre": "Guión Sacramental (tramo 10)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 68, "nombre": "Varas Guión Sacramental (tramo 10)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 69, "nombre": "Estandarte Sacramental (tramo 11)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 70, "nombre": "Varas Estandarte Sacramental (tramo 11)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 71, "nombre": "Cirio Grande Cristo", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 72, "nombre": "Cirio Mediano Cristo", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 73, "nombre": "Cirio Pequeño Cristo", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 5, "cortejo_cristo": True},
        ]


        puestos_virgen_data_ep27 = [
            {"id": 74, "nombre": "Cirios apagados cruces (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 1, "cortejo_cristo": False},
            {"id": 75, "nombre": "Bocinas (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 8, "cortejo_cristo": False},
            {"id": 76, "nombre": "Simpecado (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 77, "nombre": "Faroles Simpecado (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 9, "cortejo_cristo": False},
            {"id": 78, "nombre": "Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 79, "nombre": "Varas Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 80, "nombre": "Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 81, "nombre": "Varas Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 82, "nombre": "Bandera Concepcionista (tramo 5)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 83, "nombre": "Varas Bandera Concepcionista (tramo 5)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 84, "nombre": "Bandera Realeza de María (tramo 6)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 85, "nombre": "Varas Bandera Realeza de María (tramo 6)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 86, "nombre": "Guión de la Coronación (tramo 7)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 87, "nombre": "Varas Guión de la Coronación (tramo 7)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 88, "nombre": "Libro de Reglas (tramo 8)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 89, "nombre": "Varas Libro de Reglas (tramo 8)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 90, "nombre": "Estandarte (tramo 9)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 91, "nombre": "Varas Estandarte (tramo 9)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 92, "nombre": "Cirio Grande Virgen", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 93, "nombre": "Cirio Mediano Virgen", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 94, "nombre": "Cirio Pequeño Virgen", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 5, "cortejo_cristo": False},
        ]

        puestos_data_ep27.extend(puestos_virgen_data_ep27)

        puestos_a_crear = [Puesto(**data) for data in puestos_data_ep27]
        Puesto.objects.bulk_create(puestos_a_crear)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(puestos_a_crear)} puestos para el Acto 2 en total.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS DE SITIO: ACTO ID=2 (EMITIDAS CON ANTIGÜEDAD)
        # =========================================================================
        self.stdout.write("Iniciando el poblado masivo de Papeletas y Preferencias para el Acto 2 (Asignación por antigüedad)...")

        PapeletaSitio.objects.filter(acto_id=2).delete()
        papeletas_acto2_ids = PapeletaSitio.objects.filter(acto_id=2).values_list('id', flat=True)
        PreferenciaSolicitud.objects.filter(papeleta_id__in=papeletas_acto2_ids).delete()

        puestos_objetivo = {
            48: 4, 49: 1, 50: 4, 51: 1, 52: 4, 53: 1, 54: 4, 55: 1, 
            56: 4, 57: 1, 58:4, 59: 1, 60: 4, 61: 1, 62: 4, 63: 1, 64: 4, 65: 1, 66: 4, 67: 1, 68: 4, 69: 1, 70: 4,
            74: 4, 75: 4, 76: 1, 77: 4, 78: 1, 79: 4, 80: 1, 81: 4,
            82: 1, 83: 4, 84: 1, 85: 4, 86: 1, 87: 4, 88: 1, 89: 4, 90: 1, 91: 4
        }

        puestos_disponibles_para_preferencia = list(puestos_objetivo.keys())

        cantidad_participantes = 300 
        
        todos_hermanos = list(Hermano.objects.all().order_by('id')) 
        hermanos_seleccionados_objetos = random.sample(todos_hermanos, min(cantidad_participantes, len(todos_hermanos)))
        hermanos_seleccionados_objetos.sort(key=lambda h: h.id)

        papeletas_data_acto2 = []
        preferencias_data_acto2 = []
        codigos_usados_acto2 = set()

        fecha_emision = now - timedelta(days=9)
        dias_solicitud_min = 11
        dias_solicitud_max = 19

        ultimo_id_papeleta = PapeletaSitio.objects.order_by('-id').first()
        id_papeleta_actual = (ultimo_id_papeleta.id + 1) if ultimo_id_papeleta else 1
        
        ultimo_id_preferencia = PreferenciaSolicitud.objects.order_by('-id').first()
        id_preferencia_actual = (ultimo_id_preferencia.id + 1) if ultimo_id_preferencia else 1

        numero_papeleta_secuencial = 1

        for hermano in hermanos_seleccionados_objetos:

            num_preferencias = random.randint(4, 7)
            puestos_elegidos = random.sample(puestos_disponibles_para_preferencia, num_preferencias)
            
            preferencias_hermano = []
            for orden, puesto_id in enumerate(puestos_elegidos, start=1):
                preferencias_hermano.append(puesto_id)
                preferencias_data_acto2.append(
                    {
                        "id": id_preferencia_actual,
                        "orden_prioridad": orden,
                        "papeleta_id": id_papeleta_actual,
                        "puesto_solicitado_id": puesto_id
                    }
                )
                id_preferencia_actual += 1

            puesto_asignado = None
            estado_papeleta = "NO_ASIGNADA"
            numero_asignado = None

            for pref_puesto_id in preferencias_hermano:
                if puestos_objetivo[pref_puesto_id] > 0:
                    puesto_asignado = pref_puesto_id
                    puestos_objetivo[pref_puesto_id] -= 1
                    estado_papeleta = "EMITIDA"
                    numero_asignado = numero_papeleta_secuencial
                    numero_papeleta_secuencial += 1
                    break

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto2:
                    codigos_usados_acto2.add(codigo)
                    break

            dias_aleatorios = random.randint(dias_solicitud_min, dias_solicitud_max)
            fecha_solicitud = now - timedelta(days=dias_aleatorios)

            papeletas_data_acto2.append(
                {
                    "id": id_papeleta_actual,
                    "estado_papeleta": estado_papeleta,
                    "fecha_solicitud": fecha_solicitud,
                    "fecha_emision": fecha_emision if estado_papeleta == "EMITIDA" else None, 
                    "codigo_verificacion": codigo,
                    "anio": 2027,
                    "numero_papeleta": numero_asignado,
                    "es_solicitud_insignia": True,
                    "acto_id": 2, 
                    "hermano_id": hermano.id,
                    "puesto_id": puesto_asignado,
                    "tramo_id": None,
                    "vinculado_a_id": None,
                    "lado": None,
                    "orden_en_tramo": None,
                }
            )
            
            id_papeleta_actual += 1

        papeletas_a_crear_acto2 = [PapeletaSitio(**data) for data in papeletas_data_acto2]
        PapeletaSitio.objects.bulk_create(papeletas_a_crear_acto2)
        
        preferencias_a_crear_acto2 = [PreferenciaSolicitud(**data) for data in preferencias_data_acto2]
        PreferenciaSolicitud.objects.bulk_create(preferencias_a_crear_acto2)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_a_crear_acto2)} papeletas y {len(preferencias_a_crear_acto2)} preferencias para el Acto 2, respetando la antigüedad y el estado de asignación.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS: ACTO ID=2 (CIRIOS - SOLICITADAS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Papeletas de Sitio para Cirios (Acto 2)...")

        papeletas_cirios_data = []
        puestos_cirios = [71, 72, 73, 92, 93, 94]
        cantidad_cirios = 2300

        dias_solicitud_min_cirio = 2
        dias_solicitud_max_cirio = 7

        hermanos_con_papeleta_emitida = PapeletaSitio.objects.filter(
            acto_id=2, 
            estado_papeleta="EMITIDA"
        ).values_list('hermano_id', flat=True)

        hermanos_disponibles = list(Hermano.objects.exclude(id__in=hermanos_con_papeleta_emitida).values_list('id', flat=True))

        hermanos_seleccionados_cirios = []
        id_objetivo = 1

        if id_objetivo in hermanos_disponibles:
            hermanos_seleccionados_cirios.append(id_objetivo)
            hermanos_disponibles.remove(id_objetivo)
            self.stdout.write(self.style.SUCCESS(f'Añadida solicitud de cirio obligatoria para el Hermano ID {id_objetivo}.'))

        cantidad_restante = min(cantidad_cirios - len(hermanos_seleccionados_cirios), len(hermanos_disponibles))
        hermanos_seleccionados_cirios.extend(random.sample(hermanos_disponibles, cantidad_restante))

        for hermano_id in hermanos_seleccionados_cirios:
            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto2:
                    codigos_usados_acto2.add(codigo)
                    break

            dias_aleatorios = random.randint(dias_solicitud_min_cirio, dias_solicitud_max_cirio)
            fecha_solicitud = now - timedelta(days=dias_aleatorios)

            puesto_solicitado = random.choice(puestos_cirios)

            papeletas_cirios_data.append(
                {
                    "id": id_papeleta_actual,
                    "estado_papeleta": "SOLICITADA",
                    "fecha_solicitud": fecha_solicitud,
                    "fecha_emision": None,
                    "codigo_verificacion": codigo,
                    "anio": 2027,
                    "numero_papeleta": None,
                    "es_solicitud_insignia": False,
                    "acto_id": 2, 
                    "hermano_id": hermano_id,
                    "puesto_id": puesto_solicitado,
                    "tramo_id": None,
                    "vinculado_a_id": None,
                    "lado": None,
                    "orden_en_tramo": None,
                }
            )
            id_papeleta_actual += 1

        papeletas_a_crear_cirios = [PapeletaSitio(**data) for data in papeletas_cirios_data]
        PapeletaSitio.objects.bulk_create(papeletas_a_crear_cirios)
        
        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_a_crear_cirios)} papeletas de CIRIOS (SOLICITADAS) para el Acto 2.'))


        # =========================================================================
        # POBLADO DE TRAMOS DEL ACTO 2
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Tramos para el Acto 2...")

        aforo_tramo = 250 

        tramos_data_ep27 = [
            {"nombre": "Cruz de Guía", "numero_orden": 1, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Senatus", "numero_orden": 2, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Bandera Morada", "numero_orden": 3, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Bandera Pontificia", "numero_orden": 4, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Banderín Sacramental", "numero_orden": 5, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Guión del Cincuentenario", "numero_orden": 6, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Banderín de la Juventud", "numero_orden": 7, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Bandera Cruz de Jerusalén", "numero_orden": 8, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Guión de la Caridad", "numero_orden": 9, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Guión Sacramental", "numero_orden": 10, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Estandarte Sacramental", "numero_orden": 11, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},

            # --- TRAMOS DE VIRGEN ---
            {"nombre": "Cruces y Bocinas", "numero_orden": 1, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Simpecado", "numero_orden": 2, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Bandera Blanca y Celeste", "numero_orden": 3, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Bandera Asuncionista", "numero_orden": 4, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Bandera Concepcionista", "numero_orden": 5, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Bandera Realeza de María", "numero_orden": 6, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Guión de la Coronación", "numero_orden": 7, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Libro de Reglas", "numero_orden": 8, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
            {"nombre": "Estandarte", "numero_orden": 9, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo, "acto_id": 2},
        ]

        tramos_a_crear_ep27 = [Tramo(**data) for data in tramos_data_ep27]
        Tramo.objects.bulk_create(tramos_a_crear_ep27)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(tramos_a_crear_ep27)} tramos para el Acto 2 en total.'))



        # =========================================================================
        # POBLADO DE ACTO: ESTACIÓN DE PENITENCIA 1996 (ID=3)
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Acto: Estación de Penitencia 1996...")

        fecha_1996 = datetime(1996, 4, 1, 15, 0, 0, tzinfo=timezone.get_current_timezone())

        Acto.objects.filter(id=3).delete()

        descripcion_acto = (
                "La Estación de Penitencia a la Santa Iglesia Catedral es el acto central y culminante "
                "de la vida de nuestra Hermandad de San Gonzalo. En este año 1996, nos preparamos para vivir "
                "nuevamente este encuentro íntimo con nuestro Señor en su Soberano Poder ante Caifás y nuestra "
                "Madre y Señora de la Salud. Este solemne acto público de fe es la manifestación más genuina de nuestro "
                "compromiso cristiano, donde cada nazareno, costalero, acólito y hermano se convierte en un "
                "testimonio vivo del Evangelio por las calles de nuestro barrio de Triana y de toda Sevilla. "
                "Durante nuestro caminar, la túnica blanca se transforma en nuestra piel, igualándonos a todos "
                "bajo la cruz de Cristo. La cofradía no es solo un cortejo estético, es una auténtica comunidad en "
                "movimiento que reza, que acompaña y que sostiene a los Sagrados Titulares en su discurrir. "
                "Se invita a todos los hermanos a participar con recogimiento, orden y profundo sentido de "
                "pertenencia, haciendo de cada paso una oración y de cada cirio encendido una luz de esperanza "
                "para aquellos que más lo necesitan en estos tiempos. Que esta nueva Estación de Penitencia renueve "
                "nuestra vocación de servicio, fortaleciendo firmemente los lazos de fraternidad que nos unen "
                "como corporación cristiana y acercándonos aún más a la misericordia infinita de Dios, viviendo la "
                "caridad, la esperanza y la inquebrantable devoción en cada instante de nuestra procesión."
            )

        acto_ep96 = Acto(
            id=3,
            nombre="Estación de Penitencia 1996",
            lugar="Parroquia de San Gonzalo",
            descripcion=descripcion_acto,
            fecha=fecha_1996,
            modalidad="TRADICIONAL",
            tipo_acto_id=1,
            inicio_solicitud=fecha_1996 - timedelta(days=60),
            fin_solicitud=fecha_1996 - timedelta(days=35),
            fecha_ejecucion_reparto= fecha_1996 - timedelta(days=34),
            inicio_solicitud_cirios = fecha_1996 - timedelta(days=33),
            fin_solicitud_cirios= fecha_1996 - timedelta(days=15),
            fecha_ejecucion_cirios = fecha_1996 - timedelta(days=14),
        )

        ruta_imagen = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'EstacionPenitencia1996.jpg')
        
        if os.path.exists(ruta_imagen):
            with open(ruta_imagen, 'rb') as f:
                acto_ep96.imagen_portada.save('EstacionPenitencia1996.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Acto 3.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen}'))

        acto_ep96.save()
        
        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Acto Estación de Penitencia 1996 con ID 3.'))



        # =========================================================================
        # POBLADO DE PUESTOS DEL ACTO 3
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Puestos para el Acto 3...")

        puestos_data_ep96 = [
            {"id": 95, "nombre": "Bocina Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 8, "cortejo_cristo": True},
            {"id": 96, "nombre": "Cruz de Guía", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 12, "cortejo_cristo": True},
            {"id": 97, "nombre": "Farol Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 9, "cortejo_cristo": True},
            {"id": 98, "nombre": "Senatus (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 99, "nombre": "Cirio Grande Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 100, "nombre": "Cirio Mediano Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 101, "nombre": "Cirio Pequeño Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 5, "cortejo_cristo": True},
        ]

        puestos_virgen_data_ep96 = [
            {"id": 102, "nombre": "Cirios apagados cruces (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 1, "cortejo_cristo": False},
            {"id": 103, "nombre": "Bocinas (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 8, "cortejo_cristo": False},
            {"id": 104, "nombre": "Simpecado (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 105, "nombre": "Faroles Simpecado (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 9, "cortejo_cristo": False},
            {"id": 106, "nombre": "Libro de Reglas (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 107, "nombre": "Varas Libro de Reglas (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 108, "nombre": "Estandarte (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 109, "nombre": "Varas Estandarte (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 110, "nombre": "Cirio Grande Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 111, "nombre": "Cirio Mediano Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 112, "nombre": "Cirio Pequeño Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 3, "tipo_puesto_id": 5, "cortejo_cristo": False},
        ]

        puestos_data_ep96.extend(puestos_virgen_data_ep96)

        puestos_a_crear = [Puesto(**data) for data in puestos_data_ep96]
        Puesto.objects.bulk_create(puestos_a_crear)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(puestos_a_crear)} puestos para el Acto 3 en total.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS: ACTO ID=3 (INSIGNIAS - EMITIDAS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Papeletas de Sitio (Insignias) para el Acto 3...")

        fecha_1996 = timezone.make_aware(datetime(1996, 4, 1, 15, 0, 0))
        inicio_rango_solicitud = fecha_1996 - timedelta(days=59)
        fin_rango_solicitud = fecha_1996 - timedelta(days=36)

        fecha_emision_insignias = (fecha_1996 - timedelta(days=34)).date() 

        puestos_insignias_ids = [95, 96, 97, 98, 102, 103, 104, 105, 106, 107, 108, 109]

        puestos_insignias = Puesto.objects.filter(id__in=puestos_insignias_ids)
        huecos_a_cubrir = []
        for puesto in puestos_insignias:
            huecos_a_cubrir.extend([puesto.id] * puesto.numero_maximo_asignaciones)

        cantidad_necesaria = len(huecos_a_cubrir)

        hermanos_elegibles = list(
            Hermano.objects.filter(fecha_ingreso_corporacion__lte=fecha_1996.date())
            .values_list('id', flat=True)
        )
        
        if len(hermanos_elegibles) < cantidad_necesaria:
            self.stdout.write(self.style.WARNING("⚠️ No hay suficientes hermanos elegibles para cubrir todas las insignias."))
            hermanos_seleccionados = hermanos_elegibles
            huecos_a_cubrir = huecos_a_cubrir[:len(hermanos_elegibles)]
        else:
            hermanos_seleccionados = random.sample(hermanos_elegibles, cantidad_necesaria)

        hermanos_seleccionados.sort()

        papeletas_data_acto3 = []
        codigos_usados_acto3 = set()

        ultimo_id_papeleta = PapeletaSitio.objects.order_by('-id').first()
        id_papeleta_actual = (ultimo_id_papeleta.id + 1) if ultimo_id_papeleta else 1

        numero_papeleta_secuencial = 1

        for hermano_id, puesto_id in zip(hermanos_seleccionados, huecos_a_cubrir):

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto3:
                    codigos_usados_acto3.add(codigo)
                    break

            segundos_diferencia = int((fin_rango_solicitud - inicio_rango_solicitud).total_seconds())
            segundos_aleatorios = random.randint(0, segundos_diferencia)
            fecha_solicitud = inicio_rango_solicitud + timedelta(seconds=segundos_aleatorios)

            papeletas_data_acto3.append(
                PapeletaSitio(
                    id=id_papeleta_actual,
                    estado_papeleta="EMITIDA",
                    fecha_solicitud=fecha_solicitud,
                    fecha_emision=fecha_emision_insignias,
                    codigo_verificacion=codigo,
                    anio=1996,
                    numero_papeleta=numero_papeleta_secuencial,
                    es_solicitud_insignia=True,
                    acto_id=3,
                    hermano_id=hermano_id,
                    puesto_id=puesto_id,
                    tramo_id=None,
                    vinculado_a_id=None,
                    lado=None,
                    orden_en_tramo=None
                )
            )
            numero_papeleta_secuencial += 1
            id_papeleta_actual += 1

        PapeletaSitio.objects.bulk_create(papeletas_data_acto3)

        ultimo_id_preferencia = PreferenciaSolicitud.objects.order_by('-id').first()
        id_preferencia_actual = (ultimo_id_preferencia.id + 1) if ultimo_id_preferencia else 1
        
        preferencias_data_acto3 = []
        
        for papeleta in papeletas_data_acto3:
            preferencias_data_acto3.append(
                PreferenciaSolicitud(
                    id=id_preferencia_actual,
                    orden_prioridad=1,
                    papeleta_id=papeleta.id,
                    puesto_solicitado_id=papeleta.puesto_id
                )
            )
            id_preferencia_actual += 1

            otros_puestos = [p for p in puestos_insignias_ids if p != papeleta.puesto_id]
            puestos_extra = random.sample(otros_puestos, 2)
            
            for i, puesto_extra in enumerate(puestos_extra, start=2):
                preferencias_data_acto3.append(
                    PreferenciaSolicitud(
                        id=id_preferencia_actual,
                        orden_prioridad=i,
                        papeleta_id=papeleta.id,
                        puesto_solicitado_id=puesto_extra
                    )
                )
                id_preferencia_actual += 1

        PreferenciaSolicitud.objects.bulk_create(preferencias_data_acto3)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_data_acto3)} papeletas de insignias (EMITIDAS) para el Acto 3.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS: ACTO ID=3 (CIRIOS - EMITIDAS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Papeletas de Sitio (Cirios) para el Acto 3...")

        inicio_rango_solicitud_cirios = fecha_1996 - timedelta(days=32)
        fin_rango_solicitud_cirios = fecha_1996 - timedelta(days=16)

        fecha_emision_cirios = (fecha_1996 - timedelta(days=14)).date() 

        puestos_cirios_ids = [99, 100, 101, 110, 111, 112]

        hermanos_con_insignia = PapeletaSitio.objects.filter(acto_id=3).values_list('hermano_id', flat=True)

        hermanos_elegibles_cirios = list(
            Hermano.objects.filter(fecha_ingreso_corporacion__lte=fecha_1996.date())
            .exclude(id__in=hermanos_con_insignia)
            .values_list('id', flat=True)
        )

        cantidad_a_asignar = min(800, len(hermanos_elegibles_cirios))
        hermanos_seleccionados_cirios = random.sample(hermanos_elegibles_cirios, cantidad_a_asignar)

        hermanos_seleccionados_cirios.sort()

        codigos_usados_acto3 = set(PapeletaSitio.objects.filter(acto_id=3).values_list('codigo_verificacion', flat=True))

        ultimo_id_papeleta = PapeletaSitio.objects.order_by('-id').first()
        id_papeleta_actual = (ultimo_id_papeleta.id + 1) if ultimo_id_papeleta else 1

        ultima_papeleta_acto3 = PapeletaSitio.objects.filter(acto_id=3, numero_papeleta__isnull=False).order_by('-numero_papeleta').first()
        numero_papeleta_secuencial = (ultima_papeleta_acto3.numero_papeleta + 1) if ultima_papeleta_acto3 else 1

        ultimo_id_preferencia = PreferenciaSolicitud.objects.order_by('-id').first()
        id_preferencia_actual = (ultimo_id_preferencia.id + 1) if ultimo_id_preferencia else 1

        papeletas_data_cirios_acto3 = []
        preferencias_data_cirios_acto3 = []

        for hermano_id in hermanos_seleccionados_cirios:

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto3:
                    codigos_usados_acto3.add(codigo)
                    break

            segundos_diferencia = int((fin_rango_solicitud_cirios - inicio_rango_solicitud_cirios).total_seconds())
            segundos_aleatorios = random.randint(0, segundos_diferencia)
            fecha_solicitud = inicio_rango_solicitud_cirios + timedelta(seconds=segundos_aleatorios)

            puesto_asignado = random.choice(puestos_cirios_ids)

            papeletas_data_cirios_acto3.append(
                PapeletaSitio(
                    id=id_papeleta_actual,
                    estado_papeleta="EMITIDA",
                    fecha_solicitud=fecha_solicitud,
                    fecha_emision=fecha_emision_cirios,
                    codigo_verificacion=codigo,
                    anio=1996,
                    numero_papeleta=numero_papeleta_secuencial,
                    es_solicitud_insignia=False,
                    acto_id=3,
                    hermano_id=hermano_id,
                    puesto_id=puesto_asignado,
                    tramo_id=None,
                    vinculado_a_id=None,
                    lado=None,
                    orden_en_tramo=None
                )
            )

            preferencias_data_cirios_acto3.append(
                PreferenciaSolicitud(
                    id=id_preferencia_actual,
                    orden_prioridad=1,
                    papeleta_id=id_papeleta_actual,
                    puesto_solicitado_id=puesto_asignado
                )
            )

            id_papeleta_actual += 1
            numero_papeleta_secuencial += 1
            id_preferencia_actual += 1

        PapeletaSitio.objects.bulk_create(papeletas_data_cirios_acto3)
        PreferenciaSolicitud.objects.bulk_create(preferencias_data_cirios_acto3)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_data_cirios_acto3)} papeletas de cirios (EMITIDAS) para el Acto 3.'))



        # =========================================================================
        # POBLADO DE TRAMOS DEL ACTO 3
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Tramos para el Acto 3...")

        aforo_tramo_ep96 = 200

        tramos_data_ep96 = [
            # --- TRAMOS DE CRISTO ---
            {"nombre": "Cruz de Guía", "numero_orden": 1, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep96, "acto_id": 3},
            {"nombre": "Senatus", "numero_orden": 2, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep96, "acto_id": 3},

            # --- TRAMOS DE VIRGEN ---
            {"nombre": "Cruces y Bocinas", "numero_orden": 1, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep96, "acto_id": 3},
            {"nombre": "Simpecado", "numero_orden": 2, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep96, "acto_id": 3},
            {"nombre": "Libro de Reglas", "numero_orden": 3, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep96, "acto_id": 3},
            {"nombre": "Estandarte", "numero_orden": 4, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep96, "acto_id": 3},
        ]

        tramos_a_crear_ep96 = [Tramo(**data) for data in tramos_data_ep96]
        Tramo.objects.bulk_create(tramos_a_crear_ep96)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(tramos_a_crear_ep96)} tramos para el Acto 3 en total.'))



        # =========================================================================
        # ASIGNACIÓN DE TRAMOS PARA CIRIOS DE CRISTO (ACTO 3)
        # =========================================================================
        self.stdout.write("Asignando tramos, lado y orden a los cirios de Cristo del Acto 3 (Distribución equitativa)...")

        papeletas_cristo = list(PapeletaSitio.objects.filter(
            acto_id=3, 
            puesto_id__in=[99, 100, 101],
            estado_papeleta="EMITIDA"
        ).select_related('hermano').order_by('-hermano__fecha_ingreso_corporacion'))

        tramos_cristo = list(Tramo.objects.filter(
            acto_id=3, 
            paso='CRISTO'
        ).order_by('numero_orden'))

        papeletas_a_actualizar = []
        
        num_papeletas_cristo = len(papeletas_cristo)
        num_tramos_cristo = len(tramos_cristo)

        if num_tramos_cristo > 0 and num_papeletas_cristo > 0:
            base_por_tramo = num_papeletas_cristo // num_tramos_cristo
            resto = num_papeletas_cristo % num_tramos_cristo
            
            indice_papeleta = 0

            for tramo in tramos_cristo:
                cantidad_asignar = base_por_tramo + (1 if resto > 0 else 0)
                if resto > 0:
                    resto -= 1

                cantidad_asignar = min(cantidad_asignar, tramo.numero_maximo_cirios)

                papeletas_tramo = papeletas_cristo[indice_papeleta : indice_papeleta + cantidad_asignar]

                if not papeletas_tramo:
                    break

                papeletas_tramo.sort(key=lambda p: p.hermano.fecha_ingreso_corporacion)

                orden_actual = 1
                for papeleta in papeletas_tramo:
                    papeleta.tramo = tramo
                    papeleta.orden_en_tramo = orden_actual

                    papeleta.lado = "IZQUIERDA" if orden_actual % 2 != 0 else "DERECHA"
                    
                    papeletas_a_actualizar.append(papeleta)
                    orden_actual += 1
                    
                indice_papeleta += len(papeletas_tramo)

        if papeletas_a_actualizar:
            PapeletaSitio.objects.bulk_update(papeletas_a_actualizar, ['tramo', 'orden_en_tramo', 'lado'])
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han asignado equitativamente {len(papeletas_a_actualizar)} papeletas de cirios de Cristo en {num_tramos_cristo} tramos.'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron papeletas de Cristo para asignar a los tramos en el Acto 3.'))



        # =========================================================================
        # ASIGNACIÓN DE TRAMOS PARA CIRIOS DE VIRGEN (ACTO 3)
        # =========================================================================
        self.stdout.write("Asignando tramos, lado y orden a los cirios de Virgen del Acto 3 (Distribución equitativa)...")

        papeletas_virgen = list(PapeletaSitio.objects.filter(
            acto_id=3, 
            puesto_id__in=[110, 111, 112],
            estado_papeleta="EMITIDA"
        ).select_related('hermano').order_by('-hermano__fecha_ingreso_corporacion'))

        tramos_virgen = list(Tramo.objects.filter(
            acto_id=3, 
            paso='VIRGEN'
        ).order_by('numero_orden'))

        papeletas_virgen_actualizar = []
        
        num_papeletas_virgen = len(papeletas_virgen)
        num_tramos_virgen = len(tramos_virgen)

        if num_tramos_virgen > 0 and num_papeletas_virgen > 0:
            base_por_tramo_v = num_papeletas_virgen // num_tramos_virgen
            resto_v = num_papeletas_virgen % num_tramos_virgen
            
            indice_papeleta_virgen = 0

            for tramo in tramos_virgen:
                cantidad_asignar_v = base_por_tramo_v + (1 if resto_v > 0 else 0)
                if resto_v > 0:
                    resto_v -= 1
                
                cantidad_asignar_v = min(cantidad_asignar_v, tramo.numero_maximo_cirios)

                papeletas_tramo = papeletas_virgen[indice_papeleta_virgen : indice_papeleta_virgen + cantidad_asignar_v]

                if not papeletas_tramo:
                    break

                papeletas_tramo.sort(key=lambda p: p.hermano.fecha_ingreso_corporacion)

                orden_actual = 1
                for papeleta in papeletas_tramo:
                    papeleta.tramo = tramo
                    papeleta.orden_en_tramo = orden_actual

                    papeleta.lado = "IZQUIERDA" if orden_actual % 2 != 0 else "DERECHA"
                    
                    papeletas_virgen_actualizar.append(papeleta)
                    orden_actual += 1
                    
                indice_papeleta_virgen += len(papeletas_tramo)

        if papeletas_virgen_actualizar:
            PapeletaSitio.objects.bulk_update(papeletas_virgen_actualizar, ['tramo', 'orden_en_tramo', 'lado'])
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han asignado equitativamente {len(papeletas_virgen_actualizar)} papeletas de cirios de Virgen en {num_tramos_virgen} tramos.'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron papeletas de Virgen para asignar a los tramos en el Acto 3.'))



        # =========================================================================
        # POBLADO DE ACTO: ESTACIÓN DE PENITENCIA 1997 (ID=4)
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Acto: Estación de Penitencia 1997...")

        fecha_1997 = datetime(1997, 3, 24, 15, 0, 0, tzinfo=timezone.get_current_timezone())

        Acto.objects.filter(id=4).delete()

        descripcion_acto_97 = (
                "La Estación de Penitencia a la Santa Iglesia Catedral es el acto central y culminante "
                "de la vida de nuestra Hermandad de San Gonzalo. En este año 1997, nos preparamos para vivir "
                "nuevamente este encuentro íntimo con nuestro Señor en su Soberano Poder ante Caifás y nuestra "
                "Madre y Señora de la Salud. Este solemne acto público de fe es la manifestación más genuina de nuestro "
                "compromiso cristiano, donde cada nazareno, costalero, acólito y hermano se convierte en un "
                "testimonio vivo del Evangelio por las calles de nuestro barrio de Triana y de toda Sevilla. "
                "Durante nuestro caminar, la túnica blanca se transforma en nuestra piel, igualándonos a todos "
                "bajo la cruz de Cristo. La cofradía no es solo un cortejo estético, es una auténtica comunidad en "
                "movimiento que reza, que acompaña y que sostiene a los Sagrados Titulares en su discurrir. "
                "Se invita a todos los hermanos a participar con recogimiento, orden y profundo sentido de "
                "pertenencia, haciendo de cada paso una oración y de cada cirio encendido una luz de esperanza "
                "para aquellos que más lo necesitan en estos tiempos. Que esta nueva Estación de Penitencia renueve "
                "nuestra vocación de servicio, fortaleciendo firmemente los lazos de fraternidad que nos unen "
                "como corporación cristiana y acercándonos aún más a la misericordia infinita de Dios, viviendo la "
                "caridad, la esperanza y la inquebrantable devoción en cada instante de nuestra procesión."
            )

        acto_ep97 = Acto(
            id=4,
            nombre="Estación de Penitencia 1997",
            lugar="Parroquia de San Gonzalo",
            descripcion=descripcion_acto_97,
            fecha=fecha_1997,
            modalidad="TRADICIONAL",
            tipo_acto_id=1,
            inicio_solicitud=fecha_1997 - timedelta(days=60),
            fin_solicitud=fecha_1997 - timedelta(days=35),
            fecha_ejecucion_reparto= fecha_1997 - timedelta(days=34),
            inicio_solicitud_cirios = fecha_1997 - timedelta(days=33),
            fin_solicitud_cirios= fecha_1997 - timedelta(days=15),
            fecha_ejecucion_cirios = fecha_1997 - timedelta(days=14),
        )

        ruta_imagen_97 = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'EstacionPenitencia1997.jpg')
        
        if os.path.exists(ruta_imagen_97):
            with open(ruta_imagen_97, 'rb') as f:
                acto_ep97.imagen_portada.save('EstacionPenitencia1997.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Acto 4.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen_97}'))

        acto_ep97.save()
        
        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Acto Estación de Penitencia 1997 con ID 4.'))



        # =========================================================================
        # POBLADO DE PUESTOS DEL ACTO 4
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Puestos para el Acto 4...")

        puestos_data_ep97 = [
            {"id": 113, "nombre": "Bocina Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 8, "cortejo_cristo": True},
            {"id": 114, "nombre": "Cruz de Guía", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 12, "cortejo_cristo": True},
            {"id": 115, "nombre": "Farol Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 9, "cortejo_cristo": True},
            {"id": 116, "nombre": "Senatus (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 117, "nombre": "Cirio Grande Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 118, "nombre": "Cirio Mediano Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 119, "nombre": "Cirio Pequeño Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 5, "cortejo_cristo": True},
        ]

        puestos_virgen_data_ep97 = [
            {"id": 120, "nombre": "Cirios apagados cruces (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 1, "cortejo_cristo": False},
            {"id": 121, "nombre": "Bocinas (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 8, "cortejo_cristo": False},
            {"id": 122, "nombre": "Simpecado (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 123, "nombre": "Faroles Simpecado (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 9, "cortejo_cristo": False},
            {"id": 124, "nombre": "Libro de Reglas (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 125, "nombre": "Varas Libro de Reglas (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 126, "nombre": "Estandarte (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 127, "nombre": "Varas Estandarte (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 128, "nombre": "Cirio Grande Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 129, "nombre": "Cirio Mediano Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 130, "nombre": "Cirio Pequeño Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 4, "tipo_puesto_id": 5, "cortejo_cristo": False},
        ]

        puestos_data_ep97.extend(puestos_virgen_data_ep97)

        puestos_a_crear_97 = [Puesto(**data) for data in puestos_data_ep97]
        Puesto.objects.bulk_create(puestos_a_crear_97)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(puestos_a_crear_97)} puestos para el Acto 4 en total.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS: ACTO ID=4 (INSIGNIAS - EMITIDAS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Papeletas de Sitio (Insignias) para el Acto 4...")

        inicio_rango_solicitud_97 = fecha_1997 - timedelta(days=59)
        fin_rango_solicitud_97 = fecha_1997 - timedelta(days=36)

        fecha_emision_insignias_97 = (fecha_1997 - timedelta(days=34)).date() 

        puestos_insignias_ids_97 = [113, 114, 115, 116, 120, 121, 122, 123, 124, 125, 126, 127]

        puestos_insignias_97 = Puesto.objects.filter(id__in=puestos_insignias_ids_97)
        huecos_a_cubrir_97 = []
        for puesto in puestos_insignias_97:
            huecos_a_cubrir_97.extend([puesto.id] * puesto.numero_maximo_asignaciones)

        cantidad_necesaria_97 = len(huecos_a_cubrir_97)

        hermanos_elegibles_97 = list(
            Hermano.objects.filter(fecha_ingreso_corporacion__lte=fecha_1997.date())
            .values_list('id', flat=True)
        )
        
        if len(hermanos_elegibles_97) < cantidad_necesaria_97:
            self.stdout.write(self.style.WARNING("⚠️ No hay suficientes hermanos elegibles para cubrir todas las insignias."))
            hermanos_seleccionados_97 = hermanos_elegibles_97
            huecos_a_cubrir_97 = huecos_a_cubrir_97[:len(hermanos_elegibles_97)]
        else:
            hermanos_seleccionados_97 = random.sample(hermanos_elegibles_97, cantidad_necesaria_97)

        hermanos_seleccionados_97.sort()

        papeletas_data_acto4 = []
        codigos_usados_acto4 = set()

        ultimo_id_papeleta = PapeletaSitio.objects.order_by('-id').first()
        id_papeleta_actual = (ultimo_id_papeleta.id + 1) if ultimo_id_papeleta else 1

        numero_papeleta_secuencial = 1

        for hermano_id, puesto_id in zip(hermanos_seleccionados_97, huecos_a_cubrir_97):

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto4:
                    codigos_usados_acto4.add(codigo)
                    break

            segundos_diferencia = int((fin_rango_solicitud_97 - inicio_rango_solicitud_97).total_seconds())
            segundos_aleatorios = random.randint(0, segundos_diferencia)
            fecha_solicitud = inicio_rango_solicitud_97 + timedelta(seconds=segundos_aleatorios)

            papeletas_data_acto4.append(
                PapeletaSitio(
                    id=id_papeleta_actual,
                    estado_papeleta="EMITIDA",
                    fecha_solicitud=fecha_solicitud,
                    fecha_emision=fecha_emision_insignias_97,
                    codigo_verificacion=codigo,
                    anio=1997,
                    numero_papeleta=numero_papeleta_secuencial,
                    es_solicitud_insignia=True,
                    acto_id=4,
                    hermano_id=hermano_id,
                    puesto_id=puesto_id,
                    tramo_id=None,
                    vinculado_a_id=None,
                    lado=None,
                    orden_en_tramo=None
                )
            )
            numero_papeleta_secuencial += 1
            id_papeleta_actual += 1

        PapeletaSitio.objects.bulk_create(papeletas_data_acto4)

        ultimo_id_preferencia = PreferenciaSolicitud.objects.order_by('-id').first()
        id_preferencia_actual = (ultimo_id_preferencia.id + 1) if ultimo_id_preferencia else 1
        
        preferencias_data_acto4 = []
        
        for papeleta in papeletas_data_acto4:
            preferencias_data_acto4.append(
                PreferenciaSolicitud(
                    id=id_preferencia_actual,
                    orden_prioridad=1,
                    papeleta_id=papeleta.id,
                    puesto_solicitado_id=papeleta.puesto_id
                )
            )
            id_preferencia_actual += 1

            otros_puestos = [p for p in puestos_insignias_ids_97 if p != papeleta.puesto_id]
            puestos_extra = random.sample(otros_puestos, 2)
            
            for i, puesto_extra in enumerate(puestos_extra, start=2):
                preferencias_data_acto4.append(
                    PreferenciaSolicitud(
                        id=id_preferencia_actual,
                        orden_prioridad=i,
                        papeleta_id=papeleta.id,
                        puesto_solicitado_id=puesto_extra
                    )
                )
                id_preferencia_actual += 1

        PreferenciaSolicitud.objects.bulk_create(preferencias_data_acto4)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_data_acto4)} papeletas de insignias (EMITIDAS) para el Acto 4.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS: ACTO ID=4 (CIRIOS - EMITIDAS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Papeletas de Sitio (Cirios) para el Acto 4...")

        inicio_rango_solicitud_cirios_97 = fecha_1997 - timedelta(days=32)
        fin_rango_solicitud_cirios_97 = fecha_1997 - timedelta(days=16)

        fecha_emision_cirios_97 = (fecha_1997 - timedelta(days=14)).date() 

        puestos_cirios_ids_97 = [117, 118, 119, 128, 129, 130]

        hermanos_con_insignia_97 = PapeletaSitio.objects.filter(acto_id=4).values_list('hermano_id', flat=True)

        hermanos_elegibles_cirios_97 = list(
            Hermano.objects.filter(fecha_ingreso_corporacion__lte=fecha_1997.date())
            .exclude(id__in=hermanos_con_insignia_97)
            .values_list('id', flat=True)
        )

        cantidad_a_asignar_97 = min(800, len(hermanos_elegibles_cirios_97))
        hermanos_seleccionados_cirios_97 = random.sample(hermanos_elegibles_cirios_97, cantidad_a_asignar_97)

        hermanos_seleccionados_cirios_97.sort()

        codigos_usados_acto4_cirios = set(PapeletaSitio.objects.filter(acto_id=4).values_list('codigo_verificacion', flat=True))

        ultimo_id_papeleta = PapeletaSitio.objects.order_by('-id').first()
        id_papeleta_actual = (ultimo_id_papeleta.id + 1) if ultimo_id_papeleta else 1

        ultima_papeleta_acto4 = PapeletaSitio.objects.filter(acto_id=4, numero_papeleta__isnull=False).order_by('-numero_papeleta').first()
        numero_papeleta_secuencial = (ultima_papeleta_acto4.numero_papeleta + 1) if ultima_papeleta_acto4 else 1

        ultimo_id_preferencia = PreferenciaSolicitud.objects.order_by('-id').first()
        id_preferencia_actual = (ultimo_id_preferencia.id + 1) if ultimo_id_preferencia else 1

        papeletas_data_cirios_acto4 = []
        preferencias_data_cirios_acto4 = []

        for hermano_id in hermanos_seleccionados_cirios_97:

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto4_cirios:
                    codigos_usados_acto4_cirios.add(codigo)
                    break

            segundos_diferencia = int((fin_rango_solicitud_cirios_97 - inicio_rango_solicitud_cirios_97).total_seconds())
            segundos_aleatorios = random.randint(0, segundos_diferencia)
            fecha_solicitud = inicio_rango_solicitud_cirios_97 + timedelta(seconds=segundos_aleatorios)

            puesto_asignado = random.choice(puestos_cirios_ids_97)

            papeletas_data_cirios_acto4.append(
                PapeletaSitio(
                    id=id_papeleta_actual,
                    estado_papeleta="EMITIDA",
                    fecha_solicitud=fecha_solicitud,
                    fecha_emision=fecha_emision_cirios_97,
                    codigo_verificacion=codigo,
                    anio=1997,
                    numero_papeleta=numero_papeleta_secuencial,
                    es_solicitud_insignia=False,
                    acto_id=4,
                    hermano_id=hermano_id,
                    puesto_id=puesto_asignado,
                    tramo_id=None,
                    vinculado_a_id=None,
                    lado=None,
                    orden_en_tramo=None
                )
            )

            preferencias_data_cirios_acto4.append(
                PreferenciaSolicitud(
                    id=id_preferencia_actual,
                    orden_prioridad=1,
                    papeleta_id=id_papeleta_actual,
                    puesto_solicitado_id=puesto_asignado
                )
            )

            id_papeleta_actual += 1
            numero_papeleta_secuencial += 1
            id_preferencia_actual += 1

        PapeletaSitio.objects.bulk_create(papeletas_data_cirios_acto4)
        PreferenciaSolicitud.objects.bulk_create(preferencias_data_cirios_acto4)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_data_cirios_acto4)} papeletas de cirios (EMITIDAS) para el Acto 4.'))



        # =========================================================================
        # POBLADO DE TRAMOS DEL ACTO 4
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Tramos para el Acto 4...")

        aforo_tramo_ep97 = 200

        tramos_data_ep97 = [
            # --- TRAMOS DE CRISTO ---
            {"nombre": "Cruz de Guía", "numero_orden": 1, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep97, "acto_id": 4},
            {"nombre": "Senatus", "numero_orden": 2, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep97, "acto_id": 4},

            # --- TRAMOS DE VIRGEN ---
            {"nombre": "Cruces y Bocinas", "numero_orden": 1, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep97, "acto_id": 4},
            {"nombre": "Simpecado", "numero_orden": 2, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep97, "acto_id": 4},
            {"nombre": "Libro de Reglas", "numero_orden": 3, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep97, "acto_id": 4},
            {"nombre": "Estandarte", "numero_orden": 4, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep97, "acto_id": 4},
        ]

        tramos_a_crear_ep97 = [Tramo(**data) for data in tramos_data_ep97]
        Tramo.objects.bulk_create(tramos_a_crear_ep97)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(tramos_a_crear_ep97)} tramos para el Acto 4 en total.'))



        # =========================================================================
        # ASIGNACIÓN DE TRAMOS PARA CIRIOS DE CRISTO (ACTO 4)
        # =========================================================================
        self.stdout.write("Asignando tramos, lado y orden a los cirios de Cristo del Acto 4 (Distribución equitativa)...")

        papeletas_cristo_97 = list(PapeletaSitio.objects.filter(
            acto_id=4, 
            puesto_id__in=[117, 118, 119],
            estado_papeleta="EMITIDA"
        ).select_related('hermano').order_by('-hermano__fecha_ingreso_corporacion'))

        tramos_cristo_97 = list(Tramo.objects.filter(
            acto_id=4, 
            paso='CRISTO'
        ).order_by('numero_orden'))

        papeletas_a_actualizar_97 = []
        
        num_papeletas_cristo_97 = len(papeletas_cristo_97)
        num_tramos_cristo_97 = len(tramos_cristo_97)

        if num_tramos_cristo_97 > 0 and num_papeletas_cristo_97 > 0:
            base_por_tramo = num_papeletas_cristo_97 // num_tramos_cristo_97
            resto = num_papeletas_cristo_97 % num_tramos_cristo_97
            
            indice_papeleta = 0

            for tramo in tramos_cristo_97:
                cantidad_asignar = base_por_tramo + (1 if resto > 0 else 0)
                if resto > 0:
                    resto -= 1

                cantidad_asignar = min(cantidad_asignar, tramo.numero_maximo_cirios)

                papeletas_tramo = papeletas_cristo_97[indice_papeleta : indice_papeleta + cantidad_asignar]

                if not papeletas_tramo:
                    break

                papeletas_tramo.sort(key=lambda p: p.hermano.fecha_ingreso_corporacion)

                orden_actual = 1
                for papeleta in papeletas_tramo:
                    papeleta.tramo = tramo
                    papeleta.orden_en_tramo = orden_actual

                    papeleta.lado = "IZQUIERDA" if orden_actual % 2 != 0 else "DERECHA"
                    
                    papeletas_a_actualizar_97.append(papeleta)
                    orden_actual += 1
                    
                indice_papeleta += len(papeletas_tramo)

        if papeletas_a_actualizar_97:
            PapeletaSitio.objects.bulk_update(papeletas_a_actualizar_97, ['tramo', 'orden_en_tramo', 'lado'])
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han asignado equitativamente {len(papeletas_a_actualizar_97)} papeletas de cirios de Cristo en {num_tramos_cristo_97} tramos.'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron papeletas de Cristo para asignar a los tramos en el Acto 4.'))



        # =========================================================================
        # ASIGNACIÓN DE TRAMOS PARA CIRIOS DE VIRGEN (ACTO 4)
        # =========================================================================
        self.stdout.write("Asignando tramos, lado y orden a los cirios de Virgen del Acto 4 (Distribución equitativa)...")

        papeletas_virgen_97 = list(PapeletaSitio.objects.filter(
            acto_id=4, 
            puesto_id__in=[128, 129, 130],
            estado_papeleta="EMITIDA"
        ).select_related('hermano').order_by('-hermano__fecha_ingreso_corporacion'))

        tramos_virgen_97 = list(Tramo.objects.filter(
            acto_id=4, 
            paso='VIRGEN'
        ).order_by('numero_orden'))

        papeletas_virgen_actualizar_97 = []
        
        num_papeletas_virgen_97 = len(papeletas_virgen_97)
        num_tramos_virgen_97 = len(tramos_virgen_97)

        if num_tramos_virgen_97 > 0 and num_papeletas_virgen_97 > 0:
            base_por_tramo_v = num_papeletas_virgen_97 // num_tramos_virgen_97
            resto_v = num_papeletas_virgen_97 % num_tramos_virgen_97
            
            indice_papeleta_virgen = 0

            for tramo in tramos_virgen_97:
                cantidad_asignar_v = base_por_tramo_v + (1 if resto_v > 0 else 0)
                if resto_v > 0:
                    resto_v -= 1
                
                cantidad_asignar_v = min(cantidad_asignar_v, tramo.numero_maximo_cirios)

                papeletas_tramo = papeletas_virgen_97[indice_papeleta_virgen : indice_papeleta_virgen + cantidad_asignar_v]

                if not papeletas_tramo:
                    break

                papeletas_tramo.sort(key=lambda p: p.hermano.fecha_ingreso_corporacion)

                orden_actual = 1
                for papeleta in papeletas_tramo:
                    papeleta.tramo = tramo
                    papeleta.orden_en_tramo = orden_actual

                    papeleta.lado = "IZQUIERDA" if orden_actual % 2 != 0 else "DERECHA"
                    
                    papeletas_virgen_actualizar_97.append(papeleta)
                    orden_actual += 1
                    
                indice_papeleta_virgen += len(papeletas_tramo)

        if papeletas_virgen_actualizar_97:
            PapeletaSitio.objects.bulk_update(papeletas_virgen_actualizar_97, ['tramo', 'orden_en_tramo', 'lado'])
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han asignado equitativamente {len(papeletas_virgen_actualizar_97)} papeletas de cirios de Virgen en {num_tramos_virgen_97} tramos.'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron papeletas de Virgen para asignar a los tramos en el Acto 4.'))



        # =========================================================================
        # POBLADO DE ACTO: ESTACIÓN DE PENITENCIA 1998 (ID=5)
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Acto: Estación de Penitencia 1998...")

        # Lunes Santo de 1998 fue el 6 de abril
        fecha_1998 = datetime(1998, 4, 6, 15, 0, 0, tzinfo=timezone.get_current_timezone())

        Acto.objects.filter(id=5).delete()

        descripcion_acto_98 = (
                "La Estación de Penitencia a la Santa Iglesia Catedral es el acto central y culminante "
                "de la vida de nuestra Hermandad de San Gonzalo. En este año 1998, nos preparamos para vivir "
                "nuevamente este encuentro íntimo con nuestro Señor en su Soberano Poder ante Caifás y nuestra "
                "Madre y Señora de la Salud. Este solemne acto público de fe es la manifestación más genuina de nuestro "
                "compromiso cristiano, donde cada nazareno, costalero, acólito y hermano se convierte en un "
                "testimonio vivo del Evangelio por las calles de nuestro barrio de Triana y de toda Sevilla. "
                "Durante nuestro caminar, la túnica blanca se transforma en nuestra piel, igualándonos a todos "
                "bajo la cruz de Cristo. La cofradía no es solo un cortejo estético, es una auténtica comunidad en "
                "movimiento que reza, que acompaña y que sostiene a los Sagrados Titulares en su discurrir. "
                "Se invita a todos los hermanos a participar con recogimiento, orden y profundo sentido de "
                "pertenencia, haciendo de cada paso una oración y de cada cirio encendido una luz de esperanza "
                "para aquellos que más lo necesitan en estos tiempos. Que esta nueva Estación de Penitencia renueve "
                "nuestra vocación de servicio, fortaleciendo firmemente los lazos de fraternidad que nos unen "
                "como corporación cristiana y acercándonos aún más a la misericordia infinita de Dios, viviendo la "
                "caridad, la esperanza y la inquebrantable devoción en cada instante de nuestra procesión."
            )

        acto_ep98 = Acto(
            id=5,
            nombre="Estación de Penitencia 1998",
            lugar="Parroquia de San Gonzalo",
            descripcion=descripcion_acto_98,
            fecha=fecha_1998,
            modalidad="TRADICIONAL",
            tipo_acto_id=1,
            inicio_solicitud=fecha_1998 - timedelta(days=60),
            fin_solicitud=fecha_1998 - timedelta(days=35),
            fecha_ejecucion_reparto= fecha_1998 - timedelta(days=34),
            inicio_solicitud_cirios = fecha_1998 - timedelta(days=33),
            fin_solicitud_cirios= fecha_1998 - timedelta(days=15),
            fecha_ejecucion_cirios = fecha_1998 - timedelta(days=14),
        )

        ruta_imagen_98 = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'EstacionPenitencia1998.jpg')
        
        if os.path.exists(ruta_imagen_98):
            with open(ruta_imagen_98, 'rb') as f:
                acto_ep98.imagen_portada.save('EstacionPenitencia1998.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Acto 5.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen_98}'))

        acto_ep98.save()
        
        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Acto Estación de Penitencia 1998 con ID 5.'))



        # =========================================================================
        # POBLADO DE PUESTOS DEL ACTO 5
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Puestos para el Acto 5...")

        puestos_data_ep98 = [
            {"id": 131, "nombre": "Bocina Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 8, "cortejo_cristo": True},
            {"id": 132, "nombre": "Cruz de Guía", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 12, "cortejo_cristo": True},
            {"id": 133, "nombre": "Farol Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 9, "cortejo_cristo": True},
            {"id": 134, "nombre": "Senatus (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 135, "nombre": "Cirio Grande Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 136, "nombre": "Cirio Mediano Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 137, "nombre": "Cirio Pequeño Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 5, "cortejo_cristo": True},
        ]

        puestos_virgen_data_ep98 = [
            {"id": 138, "nombre": "Cirios apagados cruces (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 1, "cortejo_cristo": False},
            {"id": 139, "nombre": "Bocinas (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 8, "cortejo_cristo": False},
            {"id": 140, "nombre": "Simpecado (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 141, "nombre": "Faroles Simpecado (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 9, "cortejo_cristo": False},
            {"id": 142, "nombre": "Libro de Reglas (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 143, "nombre": "Varas Libro de Reglas (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 144, "nombre": "Estandarte (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 145, "nombre": "Varas Estandarte (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 146, "nombre": "Cirio Grande Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 147, "nombre": "Cirio Mediano Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 148, "nombre": "Cirio Pequeño Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 5, "tipo_puesto_id": 5, "cortejo_cristo": False},
        ]

        puestos_data_ep98.extend(puestos_virgen_data_ep98)

        puestos_a_crear_98 = [Puesto(**data) for data in puestos_data_ep98]
        Puesto.objects.bulk_create(puestos_a_crear_98)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(puestos_a_crear_98)} puestos para el Acto 5 en total.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS: ACTO ID=5 (INSIGNIAS - EMITIDAS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Papeletas de Sitio (Insignias) para el Acto 5...")

        inicio_rango_solicitud_98 = fecha_1998 - timedelta(days=59)
        fin_rango_solicitud_98 = fecha_1998 - timedelta(days=36)

        fecha_emision_insignias_98 = (fecha_1998 - timedelta(days=34)).date() 

        puestos_insignias_ids_98 = [131, 132, 133, 134, 138, 139, 140, 141, 142, 143, 144, 145]

        puestos_insignias_98 = Puesto.objects.filter(id__in=puestos_insignias_ids_98)
        huecos_a_cubrir_98 = []
        for puesto in puestos_insignias_98:
            huecos_a_cubrir_98.extend([puesto.id] * puesto.numero_maximo_asignaciones)

        cantidad_necesaria_98 = len(huecos_a_cubrir_98)

        hermanos_elegibles_98 = list(
            Hermano.objects.filter(fecha_ingreso_corporacion__lte=fecha_1998.date())
            .values_list('id', flat=True)
        )
        
        if len(hermanos_elegibles_98) < cantidad_necesaria_98:
            self.stdout.write(self.style.WARNING("⚠️ No hay suficientes hermanos elegibles para cubrir todas las insignias."))
            hermanos_seleccionados_98 = hermanos_elegibles_98
            huecos_a_cubrir_98 = huecos_a_cubrir_98[:len(hermanos_elegibles_98)]
        else:
            hermanos_seleccionados_98 = random.sample(hermanos_elegibles_98, cantidad_necesaria_98)

        hermanos_seleccionados_98.sort()

        papeletas_data_acto5 = []
        codigos_usados_acto5 = set()

        ultimo_id_papeleta = PapeletaSitio.objects.order_by('-id').first()
        id_papeleta_actual = (ultimo_id_papeleta.id + 1) if ultimo_id_papeleta else 1

        numero_papeleta_secuencial = 1

        for hermano_id, puesto_id in zip(hermanos_seleccionados_98, huecos_a_cubrir_98):

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto5:
                    codigos_usados_acto5.add(codigo)
                    break

            segundos_diferencia = int((fin_rango_solicitud_98 - inicio_rango_solicitud_98).total_seconds())
            segundos_aleatorios = random.randint(0, segundos_diferencia)
            fecha_solicitud = inicio_rango_solicitud_98 + timedelta(seconds=segundos_aleatorios)

            papeletas_data_acto5.append(
                PapeletaSitio(
                    id=id_papeleta_actual,
                    estado_papeleta="EMITIDA",
                    fecha_solicitud=fecha_solicitud,
                    fecha_emision=fecha_emision_insignias_98,
                    codigo_verificacion=codigo,
                    anio=1998,
                    numero_papeleta=numero_papeleta_secuencial,
                    es_solicitud_insignia=True,
                    acto_id=5,
                    hermano_id=hermano_id,
                    puesto_id=puesto_id,
                    tramo_id=None,
                    vinculado_a_id=None,
                    lado=None,
                    orden_en_tramo=None
                )
            )
            numero_papeleta_secuencial += 1
            id_papeleta_actual += 1

        PapeletaSitio.objects.bulk_create(papeletas_data_acto5)

        ultimo_id_preferencia = PreferenciaSolicitud.objects.order_by('-id').first()
        id_preferencia_actual = (ultimo_id_preferencia.id + 1) if ultimo_id_preferencia else 1
        
        preferencias_data_acto5 = []
        
        for papeleta in papeletas_data_acto5:
            preferencias_data_acto5.append(
                PreferenciaSolicitud(
                    id=id_preferencia_actual,
                    orden_prioridad=1,
                    papeleta_id=papeleta.id,
                    puesto_solicitado_id=papeleta.puesto_id
                )
            )
            id_preferencia_actual += 1

            otros_puestos = [p for p in puestos_insignias_ids_98 if p != papeleta.puesto_id]
            puestos_extra = random.sample(otros_puestos, 2)
            
            for i, puesto_extra in enumerate(puestos_extra, start=2):
                preferencias_data_acto5.append(
                    PreferenciaSolicitud(
                        id=id_preferencia_actual,
                        orden_prioridad=i,
                        papeleta_id=papeleta.id,
                        puesto_solicitado_id=puesto_extra
                    )
                )
                id_preferencia_actual += 1

        PreferenciaSolicitud.objects.bulk_create(preferencias_data_acto5)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_data_acto5)} papeletas de insignias (EMITIDAS) para el Acto 5.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS: ACTO ID=5 (CIRIOS - EMITIDAS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Papeletas de Sitio (Cirios) para el Acto 5...")

        inicio_rango_solicitud_cirios_98 = fecha_1998 - timedelta(days=32)
        fin_rango_solicitud_cirios_98 = fecha_1998 - timedelta(days=16)

        fecha_emision_cirios_98 = (fecha_1998 - timedelta(days=14)).date() 

        puestos_cirios_ids_98 = [135, 136, 137, 146, 147, 148]

        hermanos_con_insignia_98 = PapeletaSitio.objects.filter(acto_id=5).values_list('hermano_id', flat=True)

        hermanos_elegibles_cirios_98 = list(
            Hermano.objects.filter(fecha_ingreso_corporacion__lte=fecha_1998.date())
            .exclude(id__in=hermanos_con_insignia_98)
            .values_list('id', flat=True)
        )

        cantidad_a_asignar_98 = min(800, len(hermanos_elegibles_cirios_98))
        hermanos_seleccionados_cirios_98 = random.sample(hermanos_elegibles_cirios_98, cantidad_a_asignar_98)

        hermanos_seleccionados_cirios_98.sort()

        codigos_usados_acto5_cirios = set(PapeletaSitio.objects.filter(acto_id=5).values_list('codigo_verificacion', flat=True))

        ultimo_id_papeleta = PapeletaSitio.objects.order_by('-id').first()
        id_papeleta_actual = (ultimo_id_papeleta.id + 1) if ultimo_id_papeleta else 1

        ultima_papeleta_acto5 = PapeletaSitio.objects.filter(acto_id=5, numero_papeleta__isnull=False).order_by('-numero_papeleta').first()
        numero_papeleta_secuencial = (ultima_papeleta_acto5.numero_papeleta + 1) if ultima_papeleta_acto5 else 1

        ultimo_id_preferencia = PreferenciaSolicitud.objects.order_by('-id').first()
        id_preferencia_actual = (ultimo_id_preferencia.id + 1) if ultimo_id_preferencia else 1

        papeletas_data_cirios_acto5 = []
        preferencias_data_cirios_acto5 = []

        for hermano_id in hermanos_seleccionados_cirios_98:

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto5_cirios:
                    codigos_usados_acto5_cirios.add(codigo)
                    break

            segundos_diferencia = int((fin_rango_solicitud_cirios_98 - inicio_rango_solicitud_cirios_98).total_seconds())
            segundos_aleatorios = random.randint(0, segundos_diferencia)
            fecha_solicitud = inicio_rango_solicitud_cirios_98 + timedelta(seconds=segundos_aleatorios)

            puesto_asignado = random.choice(puestos_cirios_ids_98)

            papeletas_data_cirios_acto5.append(
                PapeletaSitio(
                    id=id_papeleta_actual,
                    estado_papeleta="EMITIDA",
                    fecha_solicitud=fecha_solicitud,
                    fecha_emision=fecha_emision_cirios_98,
                    codigo_verificacion=codigo,
                    anio=1998,
                    numero_papeleta=numero_papeleta_secuencial,
                    es_solicitud_insignia=False,
                    acto_id=5,
                    hermano_id=hermano_id,
                    puesto_id=puesto_asignado,
                    tramo_id=None,
                    vinculado_a_id=None,
                    lado=None,
                    orden_en_tramo=None
                )
            )

            preferencias_data_cirios_acto5.append(
                PreferenciaSolicitud(
                    id=id_preferencia_actual,
                    orden_prioridad=1,
                    papeleta_id=id_papeleta_actual,
                    puesto_solicitado_id=puesto_asignado
                )
            )

            id_papeleta_actual += 1
            numero_papeleta_secuencial += 1
            id_preferencia_actual += 1

        PapeletaSitio.objects.bulk_create(papeletas_data_cirios_acto5)
        PreferenciaSolicitud.objects.bulk_create(preferencias_data_cirios_acto5)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_data_cirios_acto5)} papeletas de cirios (EMITIDAS) para el Acto 5.'))



        # =========================================================================
        # POBLADO DE TRAMOS DEL ACTO 5
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Tramos para el Acto 5...")

        aforo_tramo_ep98 = 200

        tramos_data_ep98 = [
            # --- TRAMOS DE CRISTO ---
            {"nombre": "Cruz de Guía", "numero_orden": 1, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep98, "acto_id": 5},
            {"nombre": "Senatus", "numero_orden": 2, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep98, "acto_id": 5},

            # --- TRAMOS DE VIRGEN ---
            {"nombre": "Cruces y Bocinas", "numero_orden": 1, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep98, "acto_id": 5},
            {"nombre": "Simpecado", "numero_orden": 2, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep98, "acto_id": 5},
            {"nombre": "Libro de Reglas", "numero_orden": 3, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep98, "acto_id": 5},
            {"nombre": "Estandarte", "numero_orden": 4, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep98, "acto_id": 5},
        ]

        tramos_a_crear_ep98 = [Tramo(**data) for data in tramos_data_ep98]
        Tramo.objects.bulk_create(tramos_a_crear_ep98)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(tramos_a_crear_ep98)} tramos para el Acto 5 en total.'))



        # =========================================================================
        # ASIGNACIÓN DE TRAMOS PARA CIRIOS DE CRISTO (ACTO 5)
        # =========================================================================
        self.stdout.write("Asignando tramos, lado y orden a los cirios de Cristo del Acto 5 (Distribución equitativa)...")

        papeletas_cristo_98 = list(PapeletaSitio.objects.filter(
            acto_id=5, 
            puesto_id__in=[135, 136, 137],
            estado_papeleta="EMITIDA"
        ).select_related('hermano').order_by('-hermano__fecha_ingreso_corporacion'))

        tramos_cristo_98 = list(Tramo.objects.filter(
            acto_id=5, 
            paso='CRISTO'
        ).order_by('numero_orden'))

        papeletas_a_actualizar_98 = []
        
        num_papeletas_cristo_98 = len(papeletas_cristo_98)
        num_tramos_cristo_98 = len(tramos_cristo_98)

        if num_tramos_cristo_98 > 0 and num_papeletas_cristo_98 > 0:
            base_por_tramo = num_papeletas_cristo_98 // num_tramos_cristo_98
            resto = num_papeletas_cristo_98 % num_tramos_cristo_98
            
            indice_papeleta = 0

            for tramo in tramos_cristo_98:
                cantidad_asignar = base_por_tramo + (1 if resto > 0 else 0)
                if resto > 0:
                    resto -= 1

                cantidad_asignar = min(cantidad_asignar, tramo.numero_maximo_cirios)

                papeletas_tramo = papeletas_cristo_98[indice_papeleta : indice_papeleta + cantidad_asignar]

                if not papeletas_tramo:
                    break

                papeletas_tramo.sort(key=lambda p: p.hermano.fecha_ingreso_corporacion)

                orden_actual = 1
                for papeleta in papeletas_tramo:
                    papeleta.tramo = tramo
                    papeleta.orden_en_tramo = orden_actual

                    papeleta.lado = "IZQUIERDA" if orden_actual % 2 != 0 else "DERECHA"
                    
                    papeletas_a_actualizar_98.append(papeleta)
                    orden_actual += 1
                    
                indice_papeleta += len(papeletas_tramo)

        if papeletas_a_actualizar_98:
            PapeletaSitio.objects.bulk_update(papeletas_a_actualizar_98, ['tramo', 'orden_en_tramo', 'lado'])
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han asignado equitativamente {len(papeletas_a_actualizar_98)} papeletas de cirios de Cristo en {num_tramos_cristo_98} tramos.'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron papeletas de Cristo para asignar a los tramos en el Acto 5.'))



        # =========================================================================
        # ASIGNACIÓN DE TRAMOS PARA CIRIOS DE VIRGEN (ACTO 5)
        # =========================================================================
        self.stdout.write("Asignando tramos, lado y orden a los cirios de Virgen del Acto 5 (Distribución equitativa)...")

        papeletas_virgen_98 = list(PapeletaSitio.objects.filter(
            acto_id=5, 
            puesto_id__in=[146, 147, 148],
            estado_papeleta="EMITIDA"
        ).select_related('hermano').order_by('-hermano__fecha_ingreso_corporacion'))

        tramos_virgen_98 = list(Tramo.objects.filter(
            acto_id=5, 
            paso='VIRGEN'
        ).order_by('numero_orden'))

        papeletas_virgen_actualizar_98 = []
        
        num_papeletas_virgen_98 = len(papeletas_virgen_98)
        num_tramos_virgen_98 = len(tramos_virgen_98)

        if num_tramos_virgen_98 > 0 and num_papeletas_virgen_98 > 0:
            base_por_tramo_v = num_papeletas_virgen_98 // num_tramos_virgen_98
            resto_v = num_papeletas_virgen_98 % num_tramos_virgen_98
            
            indice_papeleta_virgen = 0

            for tramo in tramos_virgen_98:
                cantidad_asignar_v = base_por_tramo_v + (1 if resto_v > 0 else 0)
                if resto_v > 0:
                    resto_v -= 1
                
                cantidad_asignar_v = min(cantidad_asignar_v, tramo.numero_maximo_cirios)

                papeletas_tramo = papeletas_virgen_98[indice_papeleta_virgen : indice_papeleta_virgen + cantidad_asignar_v]

                if not papeletas_tramo:
                    break

                papeletas_tramo.sort(key=lambda p: p.hermano.fecha_ingreso_corporacion)

                orden_actual = 1
                for papeleta in papeletas_tramo:
                    papeleta.tramo = tramo
                    papeleta.orden_en_tramo = orden_actual

                    papeleta.lado = "IZQUIERDA" if orden_actual % 2 != 0 else "DERECHA"
                    
                    papeletas_virgen_actualizar_98.append(papeleta)
                    orden_actual += 1
                    
                indice_papeleta_virgen += len(papeletas_tramo)

        if papeletas_virgen_actualizar_98:
            PapeletaSitio.objects.bulk_update(papeletas_virgen_actualizar_98, ['tramo', 'orden_en_tramo', 'lado'])
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han asignado equitativamente {len(papeletas_virgen_actualizar_98)} papeletas de cirios de Virgen en {num_tramos_virgen_98} tramos.'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron papeletas de Virgen para asignar a los tramos en el Acto 5.'))



        # =========================================================================
        # POBLADO DE ACTO: ESTACIÓN DE PENITENCIA 1999 (ID=6)
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Acto: Estación de Penitencia 1999...")

        # Lunes Santo de 1999 fue el 29 de marzo
        fecha_1999 = datetime(1999, 3, 29, 15, 0, 0, tzinfo=timezone.get_current_timezone())

        Acto.objects.filter(id=6).delete()

        descripcion_acto_99 = (
                "La Estación de Penitencia a la Santa Iglesia Catedral es el acto central y culminante "
                "de la vida de nuestra Hermandad de San Gonzalo. En este año 1999, nos preparamos para vivir "
                "nuevamente este encuentro íntimo con nuestro Señor en su Soberano Poder ante Caifás y nuestra "
                "Madre y Señora de la Salud. Este solemne acto público de fe es la manifestación más genuina de nuestro "
                "compromiso cristiano, donde cada nazareno, costalero, acólito y hermano se convierte en un "
                "testimonio vivo del Evangelio por las calles de nuestro barrio de Triana y de toda Sevilla. "
                "Durante nuestro caminar, la túnica blanca se transforma en nuestra piel, igualándonos a todos "
                "bajo la cruz de Cristo. La cofradía no es solo un cortejo estético, es una auténtica comunidad en "
                "movimiento que reza, que acompaña y que sostiene a los Sagrados Titulares en su discurrir. "
                "Se invita a todos los hermanos a participar con recogimiento, orden y profundo sentido de "
                "pertenencia, haciendo de cada paso una oración y de cada cirio encendido una luz de esperanza "
                "para aquellos que más lo necesitan en estos tiempos. Que esta nueva Estación de Penitencia renueve "
                "nuestra vocación de servicio, fortaleciendo firmemente los lazos de fraternidad que nos unen "
                "como corporación cristiana y acercándonos aún más a la misericordia infinita de Dios, viviendo la "
                "caridad, la esperanza y la inquebrantable devoción en cada instante de nuestra procesión."
            )

        acto_ep99 = Acto(
            id=6,
            nombre="Estación de Penitencia 1999",
            lugar="Parroquia de San Gonzalo",
            descripcion=descripcion_acto_99,
            fecha=fecha_1999,
            modalidad="TRADICIONAL",
            tipo_acto_id=1,
            inicio_solicitud=fecha_1999 - timedelta(days=60),
            fin_solicitud=fecha_1999 - timedelta(days=35),
            fecha_ejecucion_reparto= fecha_1999 - timedelta(days=34),
            inicio_solicitud_cirios = fecha_1999 - timedelta(days=33),
            fin_solicitud_cirios= fecha_1999 - timedelta(days=15),
            fecha_ejecucion_cirios = fecha_1999 - timedelta(days=14),
        )

        ruta_imagen_99 = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'EstacionPenitencia1999.jpg')
        
        if os.path.exists(ruta_imagen_99):
            with open(ruta_imagen_99, 'rb') as f:
                acto_ep99.imagen_portada.save('EstacionPenitencia1999.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Acto 6.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen_99}'))

        acto_ep99.save()
        
        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Acto Estación de Penitencia 1999 con ID 6.'))



        # =========================================================================
        # POBLADO DE PUESTOS DEL ACTO 6
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Puestos para el Acto 6...")

        puestos_data_ep99 = [
            {"id": 149, "nombre": "Bocina Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 8, "cortejo_cristo": True},
            {"id": 150, "nombre": "Cruz de Guía", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 12, "cortejo_cristo": True},
            {"id": 151, "nombre": "Farol Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 9, "cortejo_cristo": True},
            {"id": 152, "nombre": "Senatus (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 153, "nombre": "Cirio Grande Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 154, "nombre": "Cirio Mediano Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 155, "nombre": "Cirio Pequeño Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 5, "cortejo_cristo": True},
        ]

        puestos_virgen_data_ep99 = [
            {"id": 156, "nombre": "Cirios apagados cruces (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 1, "cortejo_cristo": False},
            {"id": 157, "nombre": "Bocinas (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 8, "cortejo_cristo": False},
            {"id": 158, "nombre": "Simpecado (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 159, "nombre": "Faroles Simpecado (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 9, "cortejo_cristo": False},
            {"id": 160, "nombre": "Libro de Reglas (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 161, "nombre": "Varas Libro de Reglas (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 162, "nombre": "Estandarte (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 163, "nombre": "Varas Estandarte (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 164, "nombre": "Cirio Grande Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 165, "nombre": "Cirio Mediano Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 166, "nombre": "Cirio Pequeño Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 6, "tipo_puesto_id": 5, "cortejo_cristo": False},
        ]

        puestos_data_ep99.extend(puestos_virgen_data_ep99)

        puestos_a_crear_99 = [Puesto(**data) for data in puestos_data_ep99]
        Puesto.objects.bulk_create(puestos_a_crear_99)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(puestos_a_crear_99)} puestos para el Acto 6 en total.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS: ACTO ID=6 (INSIGNIAS - EMITIDAS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Papeletas de Sitio (Insignias) para el Acto 6...")

        inicio_rango_solicitud_99 = fecha_1999 - timedelta(days=59)
        fin_rango_solicitud_99 = fecha_1999 - timedelta(days=36)

        fecha_emision_insignias_99 = (fecha_1999 - timedelta(days=34)).date() 

        puestos_insignias_ids_99 = [149, 150, 151, 152, 156, 157, 158, 159, 160, 161, 162, 163]

        puestos_insignias_99 = Puesto.objects.filter(id__in=puestos_insignias_ids_99)
        huecos_a_cubrir_99 = []
        for puesto in puestos_insignias_99:
            huecos_a_cubrir_99.extend([puesto.id] * puesto.numero_maximo_asignaciones)

        cantidad_necesaria_99 = len(huecos_a_cubrir_99)

        hermanos_elegibles_99 = list(
            Hermano.objects.filter(fecha_ingreso_corporacion__lte=fecha_1999.date())
            .values_list('id', flat=True)
        )
        
        if len(hermanos_elegibles_99) < cantidad_necesaria_99:
            self.stdout.write(self.style.WARNING("⚠️ No hay suficientes hermanos elegibles para cubrir todas las insignias."))
            hermanos_seleccionados_99 = hermanos_elegibles_99
            huecos_a_cubrir_99 = huecos_a_cubrir_99[:len(hermanos_elegibles_99)]
        else:
            hermanos_seleccionados_99 = random.sample(hermanos_elegibles_99, cantidad_necesaria_99)

        hermanos_seleccionados_99.sort()

        papeletas_data_acto6 = []
        codigos_usados_acto6 = set()

        ultimo_id_papeleta = PapeletaSitio.objects.order_by('-id').first()
        id_papeleta_actual = (ultimo_id_papeleta.id + 1) if ultimo_id_papeleta else 1

        numero_papeleta_secuencial = 1

        for hermano_id, puesto_id in zip(hermanos_seleccionados_99, huecos_a_cubrir_99):

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto6:
                    codigos_usados_acto6.add(codigo)
                    break

            segundos_diferencia = int((fin_rango_solicitud_99 - inicio_rango_solicitud_99).total_seconds())
            segundos_aleatorios = random.randint(0, segundos_diferencia)
            fecha_solicitud = inicio_rango_solicitud_99 + timedelta(seconds=segundos_aleatorios)

            papeletas_data_acto6.append(
                PapeletaSitio(
                    id=id_papeleta_actual,
                    estado_papeleta="EMITIDA",
                    fecha_solicitud=fecha_solicitud,
                    fecha_emision=fecha_emision_insignias_99,
                    codigo_verificacion=codigo,
                    anio=1999,
                    numero_papeleta=numero_papeleta_secuencial,
                    es_solicitud_insignia=True,
                    acto_id=6,
                    hermano_id=hermano_id,
                    puesto_id=puesto_id,
                    tramo_id=None,
                    vinculado_a_id=None,
                    lado=None,
                    orden_en_tramo=None
                )
            )
            numero_papeleta_secuencial += 1
            id_papeleta_actual += 1

        PapeletaSitio.objects.bulk_create(papeletas_data_acto6)

        ultimo_id_preferencia = PreferenciaSolicitud.objects.order_by('-id').first()
        id_preferencia_actual = (ultimo_id_preferencia.id + 1) if ultimo_id_preferencia else 1
        
        preferencias_data_acto6 = []
        
        for papeleta in papeletas_data_acto6:
            preferencias_data_acto6.append(
                PreferenciaSolicitud(
                    id=id_preferencia_actual,
                    orden_prioridad=1,
                    papeleta_id=papeleta.id,
                    puesto_solicitado_id=papeleta.puesto_id
                )
            )
            id_preferencia_actual += 1

            otros_puestos = [p for p in puestos_insignias_ids_99 if p != papeleta.puesto_id]
            puestos_extra = random.sample(otros_puestos, 2)
            
            for i, puesto_extra in enumerate(puestos_extra, start=2):
                preferencias_data_acto6.append(
                    PreferenciaSolicitud(
                        id=id_preferencia_actual,
                        orden_prioridad=i,
                        papeleta_id=papeleta.id,
                        puesto_solicitado_id=puesto_extra
                    )
                )
                id_preferencia_actual += 1

        PreferenciaSolicitud.objects.bulk_create(preferencias_data_acto6)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_data_acto6)} papeletas de insignias (EMITIDAS) para el Acto 6.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS: ACTO ID=6 (CIRIOS - EMITIDAS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Papeletas de Sitio (Cirios) para el Acto 6...")

        inicio_rango_solicitud_cirios_99 = fecha_1999 - timedelta(days=32)
        fin_rango_solicitud_cirios_99 = fecha_1999 - timedelta(days=16)

        fecha_emision_cirios_99 = (fecha_1999 - timedelta(days=14)).date() 

        puestos_cirios_ids_99 = [153, 154, 155, 164, 165, 166]

        hermanos_con_insignia_99 = PapeletaSitio.objects.filter(acto_id=6).values_list('hermano_id', flat=True)

        hermanos_elegibles_cirios_99 = list(
            Hermano.objects.filter(fecha_ingreso_corporacion__lte=fecha_1999.date())
            .exclude(id__in=hermanos_con_insignia_99)
            .values_list('id', flat=True)
        )

        cantidad_a_asignar_99 = min(800, len(hermanos_elegibles_cirios_99))
        hermanos_seleccionados_cirios_99 = random.sample(hermanos_elegibles_cirios_99, cantidad_a_asignar_99)

        hermanos_seleccionados_cirios_99.sort()

        codigos_usados_acto6_cirios = set(PapeletaSitio.objects.filter(acto_id=6).values_list('codigo_verificacion', flat=True))

        ultimo_id_papeleta = PapeletaSitio.objects.order_by('-id').first()
        id_papeleta_actual = (ultimo_id_papeleta.id + 1) if ultimo_id_papeleta else 1

        ultima_papeleta_acto6 = PapeletaSitio.objects.filter(acto_id=6, numero_papeleta__isnull=False).order_by('-numero_papeleta').first()
        numero_papeleta_secuencial = (ultima_papeleta_acto6.numero_papeleta + 1) if ultima_papeleta_acto6 else 1

        ultimo_id_preferencia = PreferenciaSolicitud.objects.order_by('-id').first()
        id_preferencia_actual = (ultimo_id_preferencia.id + 1) if ultimo_id_preferencia else 1

        papeletas_data_cirios_acto6 = []
        preferencias_data_cirios_acto6 = []

        for hermano_id in hermanos_seleccionados_cirios_99:

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto6_cirios:
                    codigos_usados_acto6_cirios.add(codigo)
                    break

            segundos_diferencia = int((fin_rango_solicitud_cirios_99 - inicio_rango_solicitud_cirios_99).total_seconds())
            segundos_aleatorios = random.randint(0, segundos_diferencia)
            fecha_solicitud = inicio_rango_solicitud_cirios_99 + timedelta(seconds=segundos_aleatorios)

            puesto_asignado = random.choice(puestos_cirios_ids_99)

            papeletas_data_cirios_acto6.append(
                PapeletaSitio(
                    id=id_papeleta_actual,
                    estado_papeleta="EMITIDA",
                    fecha_solicitud=fecha_solicitud,
                    fecha_emision=fecha_emision_cirios_99,
                    codigo_verificacion=codigo,
                    anio=1999,
                    numero_papeleta=numero_papeleta_secuencial,
                    es_solicitud_insignia=False,
                    acto_id=6,
                    hermano_id=hermano_id,
                    puesto_id=puesto_asignado,
                    tramo_id=None,
                    vinculado_a_id=None,
                    lado=None,
                    orden_en_tramo=None
                )
            )

            preferencias_data_cirios_acto6.append(
                PreferenciaSolicitud(
                    id=id_preferencia_actual,
                    orden_prioridad=1,
                    papeleta_id=id_papeleta_actual,
                    puesto_solicitado_id=puesto_asignado
                )
            )

            id_papeleta_actual += 1
            numero_papeleta_secuencial += 1
            id_preferencia_actual += 1

        PapeletaSitio.objects.bulk_create(papeletas_data_cirios_acto6)
        PreferenciaSolicitud.objects.bulk_create(preferencias_data_cirios_acto6)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_data_cirios_acto6)} papeletas de cirios (EMITIDAS) para el Acto 6.'))



        # =========================================================================
        # POBLADO DE TRAMOS DEL ACTO 6
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Tramos para el Acto 6...")

        aforo_tramo_ep99 = 200

        tramos_data_ep99 = [
            # --- TRAMOS DE CRISTO ---
            {"nombre": "Cruz de Guía", "numero_orden": 1, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep99, "acto_id": 6},
            {"nombre": "Senatus", "numero_orden": 2, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep99, "acto_id": 6},

            # --- TRAMOS DE VIRGEN ---
            {"nombre": "Cruces y Bocinas", "numero_orden": 1, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep99, "acto_id": 6},
            {"nombre": "Simpecado", "numero_orden": 2, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep99, "acto_id": 6},
            {"nombre": "Libro de Reglas", "numero_orden": 3, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep99, "acto_id": 6},
            {"nombre": "Estandarte", "numero_orden": 4, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep99, "acto_id": 6},
        ]

        tramos_a_crear_ep99 = [Tramo(**data) for data in tramos_data_ep99]
        Tramo.objects.bulk_create(tramos_a_crear_ep99)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(tramos_a_crear_ep99)} tramos para el Acto 6 en total.'))



        # =========================================================================
        # ASIGNACIÓN DE TRAMOS PARA CIRIOS DE CRISTO (ACTO 6)
        # =========================================================================
        self.stdout.write("Asignando tramos, lado y orden a los cirios de Cristo del Acto 6 (Distribución equitativa)...")

        papeletas_cristo_99 = list(PapeletaSitio.objects.filter(
            acto_id=6, 
            puesto_id__in=[153, 154, 155],
            estado_papeleta="EMITIDA"
        ).select_related('hermano').order_by('-hermano__fecha_ingreso_corporacion'))

        tramos_cristo_99 = list(Tramo.objects.filter(
            acto_id=6, 
            paso='CRISTO'
        ).order_by('numero_orden'))

        papeletas_a_actualizar_99 = []
        
        num_papeletas_cristo_99 = len(papeletas_cristo_99)
        num_tramos_cristo_99 = len(tramos_cristo_99)

        if num_tramos_cristo_99 > 0 and num_papeletas_cristo_99 > 0:
            base_por_tramo = num_papeletas_cristo_99 // num_tramos_cristo_99
            resto = num_papeletas_cristo_99 % num_tramos_cristo_99
            
            indice_papeleta = 0

            for tramo in tramos_cristo_99:
                cantidad_asignar = base_por_tramo + (1 if resto > 0 else 0)
                if resto > 0:
                    resto -= 1

                cantidad_asignar = min(cantidad_asignar, tramo.numero_maximo_cirios)

                papeletas_tramo = papeletas_cristo_99[indice_papeleta : indice_papeleta + cantidad_asignar]

                if not papeletas_tramo:
                    break

                papeletas_tramo.sort(key=lambda p: p.hermano.fecha_ingreso_corporacion)

                orden_actual = 1
                for papeleta in papeletas_tramo:
                    papeleta.tramo = tramo
                    papeleta.orden_en_tramo = orden_actual

                    papeleta.lado = "IZQUIERDA" if orden_actual % 2 != 0 else "DERECHA"
                    
                    papeletas_a_actualizar_99.append(papeleta)
                    orden_actual += 1
                    
                indice_papeleta += len(papeletas_tramo)

        if papeletas_a_actualizar_99:
            PapeletaSitio.objects.bulk_update(papeletas_a_actualizar_99, ['tramo', 'orden_en_tramo', 'lado'])
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han asignado equitativamente {len(papeletas_a_actualizar_99)} papeletas de cirios de Cristo en {num_tramos_cristo_99} tramos.'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron papeletas de Cristo para asignar a los tramos en el Acto 6.'))



        # =========================================================================
        # ASIGNACIÓN DE TRAMOS PARA CIRIOS DE VIRGEN (ACTO 6)
        # =========================================================================
        self.stdout.write("Asignando tramos, lado y orden a los cirios de Virgen del Acto 6 (Distribución equitativa)...")

        papeletas_virgen_99 = list(PapeletaSitio.objects.filter(
            acto_id=6, 
            puesto_id__in=[164, 165, 166],
            estado_papeleta="EMITIDA"
        ).select_related('hermano').order_by('-hermano__fecha_ingreso_corporacion'))

        tramos_virgen_99 = list(Tramo.objects.filter(
            acto_id=6, 
            paso='VIRGEN'
        ).order_by('numero_orden'))

        papeletas_virgen_actualizar_99 = []
        
        num_papeletas_virgen_99 = len(papeletas_virgen_99)
        num_tramos_virgen_99 = len(tramos_virgen_99)

        if num_tramos_virgen_99 > 0 and num_papeletas_virgen_99 > 0:
            base_por_tramo_v = num_papeletas_virgen_99 // num_tramos_virgen_99
            resto_v = num_papeletas_virgen_99 % num_tramos_virgen_99
            
            indice_papeleta_virgen = 0

            for tramo in tramos_virgen_99:
                cantidad_asignar_v = base_por_tramo_v + (1 if resto_v > 0 else 0)
                if resto_v > 0:
                    resto_v -= 1
                
                cantidad_asignar_v = min(cantidad_asignar_v, tramo.numero_maximo_cirios)

                papeletas_tramo = papeletas_virgen_99[indice_papeleta_virgen : indice_papeleta_virgen + cantidad_asignar_v]

                if not papeletas_tramo:
                    break

                papeletas_tramo.sort(key=lambda p: p.hermano.fecha_ingreso_corporacion)

                orden_actual = 1
                for papeleta in papeletas_tramo:
                    papeleta.tramo = tramo
                    papeleta.orden_en_tramo = orden_actual

                    papeleta.lado = "IZQUIERDA" if orden_actual % 2 != 0 else "DERECHA"
                    
                    papeletas_virgen_actualizar_99.append(papeleta)
                    orden_actual += 1
                    
                indice_papeleta_virgen += len(papeletas_tramo)

        if papeletas_virgen_actualizar_99:
            PapeletaSitio.objects.bulk_update(papeletas_virgen_actualizar_99, ['tramo', 'orden_en_tramo', 'lado'])
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han asignado equitativamente {len(papeletas_virgen_actualizar_99)} papeletas de cirios de Virgen en {num_tramos_virgen_99} tramos.'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron papeletas de Virgen para asignar a los tramos en el Acto 6.'))



        # =========================================================================
        # POBLADO DE ACTO: ESTACIÓN DE PENITENCIA 2000 (ID=7)
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Acto: Estación de Penitencia 2000...")

        # Lunes Santo de 2000 fue el 17 de abril
        fecha_2000 = datetime(2000, 4, 17, 15, 0, 0, tzinfo=timezone.get_current_timezone())

        Acto.objects.filter(id=7).delete()

        descripcion_acto_00 = (
                "La Estación de Penitencia a la Santa Iglesia Catedral es el acto central y culminante "
                "de la vida de nuestra Hermandad de San Gonzalo. En este año 2000, nos preparamos para vivir "
                "nuevamente este encuentro íntimo con nuestro Señor en su Soberano Poder ante Caifás y nuestra "
                "Madre y Señora de la Salud. Este solemne acto público de fe es la manifestación más genuina de nuestro "
                "compromiso cristiano, donde cada nazareno, costalero, acólito y hermano se convierte en un "
                "testimonio vivo del Evangelio por las calles de nuestro barrio de Triana y de toda Sevilla. "
                "Durante nuestro caminar, la túnica blanca se transforma en nuestra piel, igualándonos a todos "
                "bajo la cruz de Cristo. La cofradía no es solo un cortejo estético, es una auténtica comunidad en "
                "movimiento que reza, que acompaña y que sostiene a los Sagrados Titulares en su discurrir. "
                "Se invita a todos los hermanos a participar con recogimiento, orden y profundo sentido de "
                "pertenencia, haciendo de cada paso una oración y de cada cirio encendido una luz de esperanza "
                "para aquellos que más lo necesitan en estos tiempos. Que esta nueva Estación de Penitencia renueve "
                "nuestra vocación de servicio, fortaleciendo firmemente los lazos de fraternidad que nos unen "
                "como corporación cristiana y acercándonos aún más a la misericordia infinita de Dios, viviendo la "
                "caridad, la esperanza y la inquebrantable devoción en cada instante de nuestra procesión."
            )

        acto_ep00 = Acto(
            id=7,
            nombre="Estación de Penitencia 2000",
            lugar="Parroquia de San Gonzalo",
            descripcion=descripcion_acto_00,
            fecha=fecha_2000,
            modalidad="TRADICIONAL",
            tipo_acto_id=1,
            inicio_solicitud=fecha_2000 - timedelta(days=60),
            fin_solicitud=fecha_2000 - timedelta(days=35),
            fecha_ejecucion_reparto= fecha_2000 - timedelta(days=34),
            inicio_solicitud_cirios = fecha_2000 - timedelta(days=33),
            fin_solicitud_cirios= fecha_2000 - timedelta(days=15),
            fecha_ejecucion_cirios = fecha_2000 - timedelta(days=14),
        )

        ruta_imagen_00 = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'EstacionPenitencia2000.jpg')
        
        if os.path.exists(ruta_imagen_00):
            with open(ruta_imagen_00, 'rb') as f:
                acto_ep00.imagen_portada.save('EstacionPenitencia2000.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Acto 7.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen_00}'))

        acto_ep00.save()
        
        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Acto Estación de Penitencia 2000 con ID 7.'))



        # =========================================================================
        # POBLADO DE PUESTOS DEL ACTO 7
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Puestos para el Acto 7...")

        puestos_data_ep00 = [
            {"id": 167, "nombre": "Bocina Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 8, "cortejo_cristo": True},
            {"id": 168, "nombre": "Cruz de Guía", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 12, "cortejo_cristo": True},
            {"id": 169, "nombre": "Farol Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 9, "cortejo_cristo": True},
            {"id": 170, "nombre": "Senatus (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 171, "nombre": "Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 172, "nombre": "Varas Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 173, "nombre": "Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 174, "nombre": "Varas Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 6, "cortejo_cristo": True},
            
            {"id": 175, "nombre": "Cirio Grande Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 176, "nombre": "Cirio Mediano Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 177, "nombre": "Cirio Pequeño Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 5, "cortejo_cristo": True},
        ]

        puestos_virgen_data_ep00 = [
            {"id": 178, "nombre": "Cirios apagados cruces (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 1, "cortejo_cristo": False},
            {"id": 179, "nombre": "Bocinas (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 8, "cortejo_cristo": False},
            {"id": 180, "nombre": "Simpecado (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 181, "nombre": "Faroles Simpecado (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 9, "cortejo_cristo": False},
            {"id": 182, "nombre": "Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 183, "nombre": "Varas Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 184, "nombre": "Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 185, "nombre": "Varas Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 186, "nombre": "Libro de Reglas (tramo 5)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 187, "nombre": "Varas Libro de Reglas (tramo 5)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 188, "nombre": "Estandarte (tramo 6)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 189, "nombre": "Varas Estandarte (tramo 6)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 6, "cortejo_cristo": False},
            
            {"id": 190, "nombre": "Cirio Grande Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 191, "nombre": "Cirio Mediano Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 192, "nombre": "Cirio Pequeño Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 7, "tipo_puesto_id": 5, "cortejo_cristo": False},
        ]

        puestos_data_ep00.extend(puestos_virgen_data_ep00)

        puestos_a_crear_00 = [Puesto(**data) for data in puestos_data_ep00]
        Puesto.objects.bulk_create(puestos_a_crear_00)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(puestos_a_crear_00)} puestos para el Acto 7 en total.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS: ACTO ID=7 (INSIGNIAS - EMITIDAS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Papeletas de Sitio (Insignias) para el Acto 7...")

        inicio_rango_solicitud_00 = fecha_2000 - timedelta(days=59)
        fin_rango_solicitud_00 = fecha_2000 - timedelta(days=36)

        fecha_emision_insignias_00 = (fecha_2000 - timedelta(days=34)).date() 

        puestos_insignias_ids_00 = [167, 168, 169, 170, 171, 172, 173, 174, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189]

        puestos_insignias_00 = Puesto.objects.filter(id__in=puestos_insignias_ids_00)
        huecos_a_cubrir_00 = []
        for puesto in puestos_insignias_00:
            huecos_a_cubrir_00.extend([puesto.id] * puesto.numero_maximo_asignaciones)

        cantidad_necesaria_00 = len(huecos_a_cubrir_00)

        hermanos_elegibles_00 = list(
            Hermano.objects.filter(fecha_ingreso_corporacion__lte=fecha_2000.date())
            .values_list('id', flat=True)
        )
        
        if len(hermanos_elegibles_00) < cantidad_necesaria_00:
            self.stdout.write(self.style.WARNING("⚠️ No hay suficientes hermanos elegibles para cubrir todas las insignias."))
            hermanos_seleccionados_00 = hermanos_elegibles_00
            huecos_a_cubrir_00 = huecos_a_cubrir_00[:len(hermanos_elegibles_00)]
        else:
            hermanos_seleccionados_00 = random.sample(hermanos_elegibles_00, cantidad_necesaria_00)

        hermanos_seleccionados_00.sort()

        papeletas_data_acto7 = []
        codigos_usados_acto7 = set()

        ultimo_id_papeleta = PapeletaSitio.objects.order_by('-id').first()
        id_papeleta_actual = (ultimo_id_papeleta.id + 1) if ultimo_id_papeleta else 1

        numero_papeleta_secuencial = 1

        for hermano_id, puesto_id in zip(hermanos_seleccionados_00, huecos_a_cubrir_00):

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto7:
                    codigos_usados_acto7.add(codigo)
                    break

            segundos_diferencia = int((fin_rango_solicitud_00 - inicio_rango_solicitud_00).total_seconds())
            segundos_aleatorios = random.randint(0, segundos_diferencia)
            fecha_solicitud = inicio_rango_solicitud_00 + timedelta(seconds=segundos_aleatorios)

            papeletas_data_acto7.append(
                PapeletaSitio(
                    id=id_papeleta_actual,
                    estado_papeleta="EMITIDA",
                    fecha_solicitud=fecha_solicitud,
                    fecha_emision=fecha_emision_insignias_00,
                    codigo_verificacion=codigo,
                    anio=2000,
                    numero_papeleta=numero_papeleta_secuencial,
                    es_solicitud_insignia=True,
                    acto_id=7,
                    hermano_id=hermano_id,
                    puesto_id=puesto_id,
                    tramo_id=None,
                    vinculado_a_id=None,
                    lado=None,
                    orden_en_tramo=None
                )
            )
            numero_papeleta_secuencial += 1
            id_papeleta_actual += 1

        PapeletaSitio.objects.bulk_create(papeletas_data_acto7)

        ultimo_id_preferencia = PreferenciaSolicitud.objects.order_by('-id').first()
        id_preferencia_actual = (ultimo_id_preferencia.id + 1) if ultimo_id_preferencia else 1
        
        preferencias_data_acto7 = []
        
        for papeleta in papeletas_data_acto7:
            preferencias_data_acto7.append(
                PreferenciaSolicitud(
                    id=id_preferencia_actual,
                    orden_prioridad=1,
                    papeleta_id=papeleta.id,
                    puesto_solicitado_id=papeleta.puesto_id
                )
            )
            id_preferencia_actual += 1

            otros_puestos = [p for p in puestos_insignias_ids_00 if p != papeleta.puesto_id]
            puestos_extra = random.sample(otros_puestos, 2)
            
            for i, puesto_extra in enumerate(puestos_extra, start=2):
                preferencias_data_acto7.append(
                    PreferenciaSolicitud(
                        id=id_preferencia_actual,
                        orden_prioridad=i,
                        papeleta_id=papeleta.id,
                        puesto_solicitado_id=puesto_extra
                    )
                )
                id_preferencia_actual += 1

        PreferenciaSolicitud.objects.bulk_create(preferencias_data_acto7)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_data_acto7)} papeletas de insignias (EMITIDAS) para el Acto 7.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS: ACTO ID=7 (CIRIOS - EMITIDAS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Papeletas de Sitio (Cirios) para el Acto 7...")

        inicio_rango_solicitud_cirios_00 = fecha_2000 - timedelta(days=32)
        fin_rango_solicitud_cirios_00 = fecha_2000 - timedelta(days=16)

        fecha_emision_cirios_00 = (fecha_2000 - timedelta(days=14)).date() 

        puestos_cirios_ids_00 = [175, 176, 177, 190, 191, 192]

        hermanos_con_insignia_00 = PapeletaSitio.objects.filter(acto_id=7).values_list('hermano_id', flat=True)

        hermanos_elegibles_cirios_00 = list(
            Hermano.objects.filter(fecha_ingreso_corporacion__lte=fecha_2000.date())
            .exclude(id__in=hermanos_con_insignia_00)
            .values_list('id', flat=True)
        )

        cantidad_a_asignar_00 = min(800, len(hermanos_elegibles_cirios_00))
        hermanos_seleccionados_cirios_00 = random.sample(hermanos_elegibles_cirios_00, cantidad_a_asignar_00)

        hermanos_seleccionados_cirios_00.sort()

        codigos_usados_acto7_cirios = set(PapeletaSitio.objects.filter(acto_id=7).values_list('codigo_verificacion', flat=True))

        ultimo_id_papeleta = PapeletaSitio.objects.order_by('-id').first()
        id_papeleta_actual = (ultimo_id_papeleta.id + 1) if ultimo_id_papeleta else 1

        ultima_papeleta_acto7 = PapeletaSitio.objects.filter(acto_id=7, numero_papeleta__isnull=False).order_by('-numero_papeleta').first()
        numero_papeleta_secuencial = (ultima_papeleta_acto7.numero_papeleta + 1) if ultima_papeleta_acto7 else 1

        ultimo_id_preferencia = PreferenciaSolicitud.objects.order_by('-id').first()
        id_preferencia_actual = (ultimo_id_preferencia.id + 1) if ultimo_id_preferencia else 1

        papeletas_data_cirios_acto7 = []
        preferencias_data_cirios_acto7 = []

        for hermano_id in hermanos_seleccionados_cirios_00:

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto7_cirios:
                    codigos_usados_acto7_cirios.add(codigo)
                    break

            segundos_diferencia = int((fin_rango_solicitud_cirios_00 - inicio_rango_solicitud_cirios_00).total_seconds())
            segundos_aleatorios = random.randint(0, segundos_diferencia)
            fecha_solicitud = inicio_rango_solicitud_cirios_00 + timedelta(seconds=segundos_aleatorios)

            puesto_asignado = random.choice(puestos_cirios_ids_00)

            papeletas_data_cirios_acto7.append(
                PapeletaSitio(
                    id=id_papeleta_actual,
                    estado_papeleta="EMITIDA",
                    fecha_solicitud=fecha_solicitud,
                    fecha_emision=fecha_emision_cirios_00,
                    codigo_verificacion=codigo,
                    anio=2000,
                    numero_papeleta=numero_papeleta_secuencial,
                    es_solicitud_insignia=False,
                    acto_id=7,
                    hermano_id=hermano_id,
                    puesto_id=puesto_asignado,
                    tramo_id=None,
                    vinculado_a_id=None,
                    lado=None,
                    orden_en_tramo=None
                )
            )

            preferencias_data_cirios_acto7.append(
                PreferenciaSolicitud(
                    id=id_preferencia_actual,
                    orden_prioridad=1,
                    papeleta_id=id_papeleta_actual,
                    puesto_solicitado_id=puesto_asignado
                )
            )

            id_papeleta_actual += 1
            numero_papeleta_secuencial += 1
            id_preferencia_actual += 1

        PapeletaSitio.objects.bulk_create(papeletas_data_cirios_acto7)
        PreferenciaSolicitud.objects.bulk_create(preferencias_data_cirios_acto7)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_data_cirios_acto7)} papeletas de cirios (EMITIDAS) para el Acto 7.'))



        # =========================================================================
        # POBLADO DE TRAMOS DEL ACTO 7
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Tramos para el Acto 7...")

        aforo_tramo_ep00 = 200

        tramos_data_ep00 = [
            # --- TRAMOS DE CRISTO ---
            {"nombre": "Cruz de Guía", "numero_orden": 1, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep00, "acto_id": 7},
            {"nombre": "Senatus", "numero_orden": 2, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep00, "acto_id": 7},
            {"nombre": "Bandera Morada", "numero_orden": 3, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep00, "acto_id": 7},
            {"nombre": "Bandera Pontificia", "numero_orden": 4, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep00, "acto_id": 7},

            # --- TRAMOS DE VIRGEN ---
            {"nombre": "Cruces y Bocinas", "numero_orden": 1, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep00, "acto_id": 7},
            {"nombre": "Simpecado", "numero_orden": 2, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep00, "acto_id": 7},
            {"nombre": "Bandera Blanca y Celeste", "numero_orden": 3, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep00, "acto_id": 7},
            {"nombre": "Bandera Asuncionista", "numero_orden": 4, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep00, "acto_id": 7},
            {"nombre": "Libro de Reglas", "numero_orden": 5, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep00, "acto_id": 7},
            {"nombre": "Estandarte", "numero_orden": 6, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep00, "acto_id": 7},
        ]

        tramos_a_crear_ep00 = [Tramo(**data) for data in tramos_data_ep00]
        Tramo.objects.bulk_create(tramos_a_crear_ep00)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(tramos_a_crear_ep00)} tramos para el Acto 7 en total.'))



        # =========================================================================
        # ASIGNACIÓN DE TRAMOS PARA CIRIOS DE CRISTO (ACTO 7)
        # =========================================================================
        self.stdout.write("Asignando tramos, lado y orden a los cirios de Cristo del Acto 7 (Distribución equitativa)...")

        papeletas_cristo_00 = list(PapeletaSitio.objects.filter(
            acto_id=7, 
            puesto_id__in=[175, 176, 177],
            estado_papeleta="EMITIDA"
        ).select_related('hermano').order_by('-hermano__fecha_ingreso_corporacion'))

        tramos_cristo_00 = list(Tramo.objects.filter(
            acto_id=7, 
            paso='CRISTO'
        ).order_by('numero_orden'))

        papeletas_a_actualizar_00 = []
        
        num_papeletas_cristo_00 = len(papeletas_cristo_00)
        num_tramos_cristo_00 = len(tramos_cristo_00)

        if num_tramos_cristo_00 > 0 and num_papeletas_cristo_00 > 0:
            base_por_tramo = num_papeletas_cristo_00 // num_tramos_cristo_00
            resto = num_papeletas_cristo_00 % num_tramos_cristo_00
            
            indice_papeleta = 0

            for tramo in tramos_cristo_00:
                cantidad_asignar = base_por_tramo + (1 if resto > 0 else 0)
                if resto > 0:
                    resto -= 1

                cantidad_asignar = min(cantidad_asignar, tramo.numero_maximo_cirios)

                papeletas_tramo = papeletas_cristo_00[indice_papeleta : indice_papeleta + cantidad_asignar]

                if not papeletas_tramo:
                    break

                papeletas_tramo.sort(key=lambda p: p.hermano.fecha_ingreso_corporacion)

                orden_actual = 1
                for papeleta in papeletas_tramo:
                    papeleta.tramo = tramo
                    papeleta.orden_en_tramo = orden_actual

                    papeleta.lado = "IZQUIERDA" if orden_actual % 2 != 0 else "DERECHA"
                    
                    papeletas_a_actualizar_00.append(papeleta)
                    orden_actual += 1
                    
                indice_papeleta += len(papeletas_tramo)

        if papeletas_a_actualizar_00:
            PapeletaSitio.objects.bulk_update(papeletas_a_actualizar_00, ['tramo', 'orden_en_tramo', 'lado'])
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han asignado equitativamente {len(papeletas_a_actualizar_00)} papeletas de cirios de Cristo en {num_tramos_cristo_00} tramos.'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron papeletas de Cristo para asignar a los tramos en el Acto 7.'))



        # =========================================================================
        # ASIGNACIÓN DE TRAMOS PARA CIRIOS DE VIRGEN (ACTO 7)
        # =========================================================================
        self.stdout.write("Asignando tramos, lado y orden a los cirios de Virgen del Acto 7 (Distribución equitativa)...")

        papeletas_virgen_00 = list(PapeletaSitio.objects.filter(
            acto_id=7, 
            puesto_id__in=[190, 191, 192],
            estado_papeleta="EMITIDA"
        ).select_related('hermano').order_by('-hermano__fecha_ingreso_corporacion'))

        tramos_virgen_00 = list(Tramo.objects.filter(
            acto_id=7, 
            paso='VIRGEN'
        ).order_by('numero_orden'))

        papeletas_virgen_actualizar_00 = []
        
        num_papeletas_virgen_00 = len(papeletas_virgen_00)
        num_tramos_virgen_00 = len(tramos_virgen_00)

        if num_tramos_virgen_00 > 0 and num_papeletas_virgen_00 > 0:
            base_por_tramo_v = num_papeletas_virgen_00 // num_tramos_virgen_00
            resto_v = num_papeletas_virgen_00 % num_tramos_virgen_00
            
            indice_papeleta_virgen = 0

            for tramo in tramos_virgen_00:
                cantidad_asignar_v = base_por_tramo_v + (1 if resto_v > 0 else 0)
                if resto_v > 0:
                    resto_v -= 1
                
                cantidad_asignar_v = min(cantidad_asignar_v, tramo.numero_maximo_cirios)

                papeletas_tramo = papeletas_virgen_00[indice_papeleta_virgen : indice_papeleta_virgen + cantidad_asignar_v]

                if not papeletas_tramo:
                    break

                papeletas_tramo.sort(key=lambda p: p.hermano.fecha_ingreso_corporacion)

                orden_actual = 1
                for papeleta in papeletas_tramo:
                    papeleta.tramo = tramo
                    papeleta.orden_en_tramo = orden_actual

                    papeleta.lado = "IZQUIERDA" if orden_actual % 2 != 0 else "DERECHA"
                    
                    papeletas_virgen_actualizar_00.append(papeleta)
                    orden_actual += 1
                    
                indice_papeleta_virgen += len(papeletas_tramo)

        if papeletas_virgen_actualizar_00:
            PapeletaSitio.objects.bulk_update(papeletas_virgen_actualizar_00, ['tramo', 'orden_en_tramo', 'lado'])
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han asignado equitativamente {len(papeletas_virgen_actualizar_00)} papeletas de cirios de Virgen en {num_tramos_virgen_00} tramos.'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron papeletas de Virgen para asignar a los tramos en el Acto 7.'))



        # =========================================================================
        # POBLADO DE ACTO: ESTACIÓN DE PENITENCIA 2001 (ID=8)
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Acto: Estación de Penitencia 2001...")

        # Lunes Santo de 2001 fue el 9 de abril
        fecha_2001 = datetime(2001, 4, 9, 15, 0, 0, tzinfo=timezone.get_current_timezone())

        Acto.objects.filter(id=8).delete()

        descripcion_acto_01 = (
                "La Estación de Penitencia a la Santa Iglesia Catedral es el acto central y culminante "
                "de la vida de nuestra Hermandad de San Gonzalo. En este año 2001, nos preparamos para vivir "
                "nuevamente este encuentro íntimo con nuestro Señor en su Soberano Poder ante Caifás y nuestra "
                "Madre y Señora de la Salud. Este solemne acto público de fe es la manifestación más genuina de nuestro "
                "compromiso cristiano, donde cada nazareno, costalero, acólito y hermano se convierte en un "
                "testimonio vivo del Evangelio por las calles de nuestro barrio de Triana y de toda Sevilla. "
                "Durante nuestro caminar, la túnica blanca se transforma en nuestra piel, igualándonos a todos "
                "bajo la cruz de Cristo. La cofradía no es solo un cortejo estético, es una auténtica comunidad en "
                "movimiento que reza, que acompaña y que sostiene a los Sagrados Titulares en su discurrir. "
                "Se invita a todos los hermanos a participar con recogimiento, orden y profundo sentido de "
                "pertenencia, haciendo de cada paso una oración y de cada cirio encendido una luz de esperanza "
                "para aquellos que más lo necesitan en estos tiempos. Que esta nueva Estación de Penitencia renueve "
                "nuestra vocación de servicio, fortaleciendo firmemente los lazos de fraternidad que nos unen "
                "como corporación cristiana y acercándonos aún más a la misericordia infinita de Dios, viviendo la "
                "caridad, la esperanza y la inquebrantable devoción en cada instante de nuestra procesión."
            )

        acto_ep01 = Acto(
            id=8,
            nombre="Estación de Penitencia 2001",
            lugar="Parroquia de San Gonzalo",
            descripcion=descripcion_acto_01,
            fecha=fecha_2001,
            modalidad="TRADICIONAL",
            tipo_acto_id=1,
            inicio_solicitud=fecha_2001 - timedelta(days=60),
            fin_solicitud=fecha_2001 - timedelta(days=35),
            fecha_ejecucion_reparto= fecha_2001 - timedelta(days=34),
            inicio_solicitud_cirios = fecha_2001 - timedelta(days=33),
            fin_solicitud_cirios= fecha_2001 - timedelta(days=15),
            fecha_ejecucion_cirios = fecha_2001 - timedelta(days=14),
        )

        ruta_imagen_01 = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'EstacionPenitencia2001.jpg')
        
        if os.path.exists(ruta_imagen_01):
            with open(ruta_imagen_01, 'rb') as f:
                acto_ep01.imagen_portada.save('EstacionPenitencia2001.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Acto 8.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen_01}'))

        acto_ep01.save()
        
        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Acto Estación de Penitencia 2001 con ID 8.'))



        # =========================================================================
        # POBLADO DE PUESTOS DEL ACTO 8
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Puestos para el Acto 8...")

        puestos_data_ep01 = [
            {"id": 193, "nombre": "Bocina Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 8, "cortejo_cristo": True},
            {"id": 194, "nombre": "Cruz de Guía", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 12, "cortejo_cristo": True},
            {"id": 195, "nombre": "Farol Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 9, "cortejo_cristo": True},
            {"id": 196, "nombre": "Senatus (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 197, "nombre": "Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 198, "nombre": "Varas Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 199, "nombre": "Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 200, "nombre": "Varas Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 6, "cortejo_cristo": True},
            
            {"id": 201, "nombre": "Cirio Grande Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 202, "nombre": "Cirio Mediano Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 203, "nombre": "Cirio Pequeño Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 5, "cortejo_cristo": True},
        ]

        puestos_virgen_data_ep01 = [
            {"id": 204, "nombre": "Cirios apagados cruces (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 1, "cortejo_cristo": False},
            {"id": 205, "nombre": "Bocinas (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 8, "cortejo_cristo": False},
            {"id": 206, "nombre": "Simpecado (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 207, "nombre": "Faroles Simpecado (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 9, "cortejo_cristo": False},
            {"id": 208, "nombre": "Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 209, "nombre": "Varas Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 210, "nombre": "Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 211, "nombre": "Varas Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 212, "nombre": "Libro de Reglas (tramo 5)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 213, "nombre": "Varas Libro de Reglas (tramo 5)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 214, "nombre": "Estandarte (tramo 6)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 215, "nombre": "Varas Estandarte (tramo 6)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 6, "cortejo_cristo": False},
            
            {"id": 216, "nombre": "Cirio Grande Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 217, "nombre": "Cirio Mediano Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 218, "nombre": "Cirio Pequeño Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 8, "tipo_puesto_id": 5, "cortejo_cristo": False},
        ]

        puestos_data_ep01.extend(puestos_virgen_data_ep01)

        puestos_a_crear_01 = [Puesto(**data) for data in puestos_data_ep01]
        Puesto.objects.bulk_create(puestos_a_crear_01)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(puestos_a_crear_01)} puestos para el Acto 8 en total.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS: ACTO ID=8 (INSIGNIAS - EMITIDAS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Papeletas de Sitio (Insignias) para el Acto 8...")

        inicio_rango_solicitud_01 = fecha_2001 - timedelta(days=59)
        fin_rango_solicitud_01 = fecha_2001 - timedelta(days=36)

        fecha_emision_insignias_01 = (fecha_2001 - timedelta(days=34)).date() 

        puestos_insignias_ids_01 = [193, 194, 195, 196, 197, 198, 199, 200, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215]

        puestos_insignias_01 = Puesto.objects.filter(id__in=puestos_insignias_ids_01)
        huecos_a_cubrir_01 = []
        for puesto in puestos_insignias_01:
            huecos_a_cubrir_01.extend([puesto.id] * puesto.numero_maximo_asignaciones)

        cantidad_necesaria_01 = len(huecos_a_cubrir_01)

        hermanos_elegibles_01 = list(
            Hermano.objects.filter(fecha_ingreso_corporacion__lte=fecha_2001.date())
            .values_list('id', flat=True)
        )
        
        if len(hermanos_elegibles_01) < cantidad_necesaria_01:
            self.stdout.write(self.style.WARNING("⚠️ No hay suficientes hermanos elegibles para cubrir todas las insignias."))
            hermanos_seleccionados_01 = hermanos_elegibles_01
            huecos_a_cubrir_01 = huecos_a_cubrir_01[:len(hermanos_elegibles_01)]
        else:
            hermanos_seleccionados_01 = random.sample(hermanos_elegibles_01, cantidad_necesaria_01)

        hermanos_seleccionados_01.sort()

        papeletas_data_acto8 = []
        codigos_usados_acto8 = set()

        ultimo_id_papeleta = PapeletaSitio.objects.order_by('-id').first()
        id_papeleta_actual = (ultimo_id_papeleta.id + 1) if ultimo_id_papeleta else 1

        numero_papeleta_secuencial = 1

        for hermano_id, puesto_id in zip(hermanos_seleccionados_01, huecos_a_cubrir_01):

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto8:
                    codigos_usados_acto8.add(codigo)
                    break

            segundos_diferencia = int((fin_rango_solicitud_01 - inicio_rango_solicitud_01).total_seconds())
            segundos_aleatorios = random.randint(0, segundos_diferencia)
            fecha_solicitud = inicio_rango_solicitud_01 + timedelta(seconds=segundos_aleatorios)

            papeletas_data_acto8.append(
                PapeletaSitio(
                    id=id_papeleta_actual,
                    estado_papeleta="EMITIDA",
                    fecha_solicitud=fecha_solicitud,
                    fecha_emision=fecha_emision_insignias_01,
                    codigo_verificacion=codigo,
                    anio=2001,
                    numero_papeleta=numero_papeleta_secuencial,
                    es_solicitud_insignia=True,
                    acto_id=8,
                    hermano_id=hermano_id,
                    puesto_id=puesto_id,
                    tramo_id=None,
                    vinculado_a_id=None,
                    lado=None,
                    orden_en_tramo=None
                )
            )
            numero_papeleta_secuencial += 1
            id_papeleta_actual += 1

        PapeletaSitio.objects.bulk_create(papeletas_data_acto8)

        ultimo_id_preferencia = PreferenciaSolicitud.objects.order_by('-id').first()
        id_preferencia_actual = (ultimo_id_preferencia.id + 1) if ultimo_id_preferencia else 1
        
        preferencias_data_acto8 = []
        
        for papeleta in papeletas_data_acto8:
            preferencias_data_acto8.append(
                PreferenciaSolicitud(
                    id=id_preferencia_actual,
                    orden_prioridad=1,
                    papeleta_id=papeleta.id,
                    puesto_solicitado_id=papeleta.puesto_id
                )
            )
            id_preferencia_actual += 1

            otros_puestos = [p for p in puestos_insignias_ids_01 if p != papeleta.puesto_id]
            puestos_extra = random.sample(otros_puestos, 2)
            
            for i, puesto_extra in enumerate(puestos_extra, start=2):
                preferencias_data_acto8.append(
                    PreferenciaSolicitud(
                        id=id_preferencia_actual,
                        orden_prioridad=i,
                        papeleta_id=papeleta.id,
                        puesto_solicitado_id=puesto_extra
                    )
                )
                id_preferencia_actual += 1

        PreferenciaSolicitud.objects.bulk_create(preferencias_data_acto8)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_data_acto8)} papeletas de insignias (EMITIDAS) para el Acto 8.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS: ACTO ID=8 (CIRIOS - EMITIDAS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Papeletas de Sitio (Cirios) para el Acto 8...")

        inicio_rango_solicitud_cirios_01 = fecha_2001 - timedelta(days=32)
        fin_rango_solicitud_cirios_01 = fecha_2001 - timedelta(days=16)

        fecha_emision_cirios_01 = (fecha_2001 - timedelta(days=14)).date() 

        puestos_cirios_ids_01 = [201, 202, 203, 216, 217, 218]

        hermanos_con_insignia_01 = PapeletaSitio.objects.filter(acto_id=8).values_list('hermano_id', flat=True)

        hermanos_elegibles_cirios_01 = list(
            Hermano.objects.filter(fecha_ingreso_corporacion__lte=fecha_2001.date())
            .exclude(id__in=hermanos_con_insignia_01)
            .values_list('id', flat=True)
        )

        cantidad_a_asignar_01 = min(800, len(hermanos_elegibles_cirios_01))
        hermanos_seleccionados_cirios_01 = random.sample(hermanos_elegibles_cirios_01, cantidad_a_asignar_01)

        hermanos_seleccionados_cirios_01.sort()

        codigos_usados_acto8_cirios = set(PapeletaSitio.objects.filter(acto_id=8).values_list('codigo_verificacion', flat=True))

        ultimo_id_papeleta = PapeletaSitio.objects.order_by('-id').first()
        id_papeleta_actual = (ultimo_id_papeleta.id + 1) if ultimo_id_papeleta else 1

        ultima_papeleta_acto8 = PapeletaSitio.objects.filter(acto_id=8, numero_papeleta__isnull=False).order_by('-numero_papeleta').first()
        numero_papeleta_secuencial = (ultima_papeleta_acto8.numero_papeleta + 1) if ultima_papeleta_acto8 else 1

        ultimo_id_preferencia = PreferenciaSolicitud.objects.order_by('-id').first()
        id_preferencia_actual = (ultimo_id_preferencia.id + 1) if ultimo_id_preferencia else 1

        papeletas_data_cirios_acto8 = []
        preferencias_data_cirios_acto8 = []

        for hermano_id in hermanos_seleccionados_cirios_01:

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto8_cirios:
                    codigos_usados_acto8_cirios.add(codigo)
                    break

            segundos_diferencia = int((fin_rango_solicitud_cirios_01 - inicio_rango_solicitud_cirios_01).total_seconds())
            segundos_aleatorios = random.randint(0, segundos_diferencia)
            fecha_solicitud = inicio_rango_solicitud_cirios_01 + timedelta(seconds=segundos_aleatorios)

            puesto_asignado = random.choice(puestos_cirios_ids_01)

            papeletas_data_cirios_acto8.append(
                PapeletaSitio(
                    id=id_papeleta_actual,
                    estado_papeleta="EMITIDA",
                    fecha_solicitud=fecha_solicitud,
                    fecha_emision=fecha_emision_cirios_01,
                    codigo_verificacion=codigo,
                    anio=2001,
                    numero_papeleta=numero_papeleta_secuencial,
                    es_solicitud_insignia=False,
                    acto_id=8,
                    hermano_id=hermano_id,
                    puesto_id=puesto_asignado,
                    tramo_id=None,
                    vinculado_a_id=None,
                    lado=None,
                    orden_en_tramo=None
                )
            )

            preferencias_data_cirios_acto8.append(
                PreferenciaSolicitud(
                    id=id_preferencia_actual,
                    orden_prioridad=1,
                    papeleta_id=id_papeleta_actual,
                    puesto_solicitado_id=puesto_asignado
                )
            )

            id_papeleta_actual += 1
            numero_papeleta_secuencial += 1
            id_preferencia_actual += 1

        PapeletaSitio.objects.bulk_create(papeletas_data_cirios_acto8)
        PreferenciaSolicitud.objects.bulk_create(preferencias_data_cirios_acto8)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_data_cirios_acto8)} papeletas de cirios (EMITIDAS) para el Acto 8.'))



        # =========================================================================
        # POBLADO DE TRAMOS DEL ACTO 8
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Tramos para el Acto 8...")

        aforo_tramo_ep01 = 200

        tramos_data_ep01 = [
            # --- TRAMOS DE CRISTO ---
            {"nombre": "Cruz de Guía", "numero_orden": 1, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep01, "acto_id": 8},
            {"nombre": "Senatus", "numero_orden": 2, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep01, "acto_id": 8},
            {"nombre": "Bandera Morada", "numero_orden": 3, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep01, "acto_id": 8},
            {"nombre": "Bandera Pontificia", "numero_orden": 4, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep01, "acto_id": 8},

            # --- TRAMOS DE VIRGEN ---
            {"nombre": "Cruces y Bocinas", "numero_orden": 1, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep01, "acto_id": 8},
            {"nombre": "Simpecado", "numero_orden": 2, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep01, "acto_id": 8},
            {"nombre": "Bandera Blanca y Celeste", "numero_orden": 3, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep01, "acto_id": 8},
            {"nombre": "Bandera Asuncionista", "numero_orden": 4, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep01, "acto_id": 8},
            {"nombre": "Libro de Reglas", "numero_orden": 5, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep01, "acto_id": 8},
            {"nombre": "Estandarte", "numero_orden": 6, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep01, "acto_id": 8},
        ]

        tramos_a_crear_ep01 = [Tramo(**data) for data in tramos_data_ep01]
        Tramo.objects.bulk_create(tramos_a_crear_ep01)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(tramos_a_crear_ep01)} tramos para el Acto 8 en total.'))



        # =========================================================================
        # ASIGNACIÓN DE TRAMOS PARA CIRIOS DE CRISTO (ACTO 8)
        # =========================================================================
        self.stdout.write("Asignando tramos, lado y orden a los cirios de Cristo del Acto 8 (Distribución equitativa)...")

        papeletas_cristo_01 = list(PapeletaSitio.objects.filter(
            acto_id=8, 
            puesto_id__in=[201, 202, 203],
            estado_papeleta="EMITIDA"
        ).select_related('hermano').order_by('-hermano__fecha_ingreso_corporacion'))

        tramos_cristo_01 = list(Tramo.objects.filter(
            acto_id=8, 
            paso='CRISTO'
        ).order_by('numero_orden'))

        papeletas_a_actualizar_01 = []
        
        num_papeletas_cristo_01 = len(papeletas_cristo_01)
        num_tramos_cristo_01 = len(tramos_cristo_01)

        if num_tramos_cristo_01 > 0 and num_papeletas_cristo_01 > 0:
            base_por_tramo = num_papeletas_cristo_01 // num_tramos_cristo_01
            resto = num_papeletas_cristo_01 % num_tramos_cristo_01
            
            indice_papeleta = 0

            for tramo in tramos_cristo_01:
                cantidad_asignar = base_por_tramo + (1 if resto > 0 else 0)
                if resto > 0:
                    resto -= 1

                cantidad_asignar = min(cantidad_asignar, tramo.numero_maximo_cirios)

                papeletas_tramo = papeletas_cristo_01[indice_papeleta : indice_papeleta + cantidad_asignar]

                if not papeletas_tramo:
                    break

                papeletas_tramo.sort(key=lambda p: p.hermano.fecha_ingreso_corporacion)

                orden_actual = 1
                for papeleta in papeletas_tramo:
                    papeleta.tramo = tramo
                    papeleta.orden_en_tramo = orden_actual

                    papeleta.lado = "IZQUIERDA" if orden_actual % 2 != 0 else "DERECHA"
                    
                    papeletas_a_actualizar_01.append(papeleta)
                    orden_actual += 1
                    
                indice_papeleta += len(papeletas_tramo)

        if papeletas_a_actualizar_01:
            PapeletaSitio.objects.bulk_update(papeletas_a_actualizar_01, ['tramo', 'orden_en_tramo', 'lado'])
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han asignado equitativamente {len(papeletas_a_actualizar_01)} papeletas de cirios de Cristo en {num_tramos_cristo_01} tramos.'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron papeletas de Cristo para asignar a los tramos en el Acto 8.'))



        # =========================================================================
        # ASIGNACIÓN DE TRAMOS PARA CIRIOS DE VIRGEN (ACTO 8)
        # =========================================================================
        self.stdout.write("Asignando tramos, lado y orden a los cirios de Virgen del Acto 8 (Distribución equitativa)...")

        papeletas_virgen_01 = list(PapeletaSitio.objects.filter(
            acto_id=8, 
            puesto_id__in=[216, 217, 218],
            estado_papeleta="EMITIDA"
        ).select_related('hermano').order_by('-hermano__fecha_ingreso_corporacion'))

        tramos_virgen_01 = list(Tramo.objects.filter(
            acto_id=8, 
            paso='VIRGEN'
        ).order_by('numero_orden'))

        papeletas_virgen_actualizar_01 = []
        
        num_papeletas_virgen_01 = len(papeletas_virgen_01)
        num_tramos_virgen_01 = len(tramos_virgen_01)

        if num_tramos_virgen_01 > 0 and num_papeletas_virgen_01 > 0:
            base_por_tramo_v = num_papeletas_virgen_01 // num_tramos_virgen_01
            resto_v = num_papeletas_virgen_01 % num_tramos_virgen_01
            
            indice_papeleta_virgen = 0

            for tramo in tramos_virgen_01:
                cantidad_asignar_v = base_por_tramo_v + (1 if resto_v > 0 else 0)
                if resto_v > 0:
                    resto_v -= 1
                
                cantidad_asignar_v = min(cantidad_asignar_v, tramo.numero_maximo_cirios)

                papeletas_tramo = papeletas_virgen_01[indice_papeleta_virgen : indice_papeleta_virgen + cantidad_asignar_v]

                if not papeletas_tramo:
                    break

                papeletas_tramo.sort(key=lambda p: p.hermano.fecha_ingreso_corporacion)

                orden_actual = 1
                for papeleta in papeletas_tramo:
                    papeleta.tramo = tramo
                    papeleta.orden_en_tramo = orden_actual

                    papeleta.lado = "IZQUIERDA" if orden_actual % 2 != 0 else "DERECHA"
                    
                    papeletas_virgen_actualizar_01.append(papeleta)
                    orden_actual += 1
                    
                indice_papeleta_virgen += len(papeletas_tramo)

        if papeletas_virgen_actualizar_01:
            PapeletaSitio.objects.bulk_update(papeletas_virgen_actualizar_01, ['tramo', 'orden_en_tramo', 'lado'])
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han asignado equitativamente {len(papeletas_virgen_actualizar_01)} papeletas de cirios de Virgen en {num_tramos_virgen_01} tramos.'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron papeletas de Virgen para asignar a los tramos en el Acto 8.'))



        # =========================================================================
        # POBLADO DE ACTO: ESTACIÓN DE PENITENCIA 2002 (ID=9)
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Acto: Estación de Penitencia 2002...")

        # Lunes Santo de 2002 fue el 25 de marzo
        fecha_2002 = datetime(2002, 3, 25, 15, 0, 0, tzinfo=timezone.get_current_timezone())

        Acto.objects.filter(id=9).delete()

        descripcion_acto_02 = (
                "La Estación de Penitencia a la Santa Iglesia Catedral es el acto central y culminante "
                "de la vida de nuestra Hermandad de San Gonzalo. En este año 2002, nos preparamos para vivir "
                "nuevamente este encuentro íntimo con nuestro Señor en su Soberano Poder ante Caifás y nuestra "
                "Madre y Señora de la Salud. Este solemne acto público de fe es la manifestación más genuina de nuestro "
                "compromiso cristiano, donde cada nazareno, costalero, acólito y hermano se convierte en un "
                "testimonio vivo del Evangelio por las calles de nuestro barrio de Triana y de toda Sevilla. "
                "Durante nuestro caminar, la túnica blanca se transforma en nuestra piel, igualándonos a todos "
                "bajo la cruz de Cristo. La cofradía no es solo un cortejo estético, es una auténtica comunidad en "
                "movimiento que reza, que acompaña y que sostiene a los Sagrados Titulares en su discurrir. "
                "Se invita a todos los hermanos a participar con recogimiento, orden y profundo sentido de "
                "pertenencia, haciendo de cada paso una oración y de cada cirio encendido una luz de esperanza "
                "para aquellos que más lo necesitan en estos tiempos. Que esta nueva Estación de Penitencia renueve "
                "nuestra vocación de servicio, fortaleciendo firmemente los lazos de fraternidad que nos unen "
                "como corporación cristiana y acercándonos aún más a la misericordia infinita de Dios, viviendo la "
                "caridad, la esperanza y la inquebrantable devoción en cada instante de nuestra procesión."
            )

        acto_ep02 = Acto(
            id=9,
            nombre="Estación de Penitencia 2002",
            lugar="Parroquia de San Gonzalo",
            descripcion=descripcion_acto_02,
            fecha=fecha_2002,
            modalidad="TRADICIONAL",
            tipo_acto_id=1,
            inicio_solicitud=fecha_2002 - timedelta(days=60),
            fin_solicitud=fecha_2002 - timedelta(days=35),
            fecha_ejecucion_reparto= fecha_2002 - timedelta(days=34),
            inicio_solicitud_cirios = fecha_2002 - timedelta(days=33),
            fin_solicitud_cirios= fecha_2002 - timedelta(days=15),
            fecha_ejecucion_cirios = fecha_2002 - timedelta(days=14),
        )

        ruta_imagen_02 = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'EstacionPenitencia2002.jpg')
        
        if os.path.exists(ruta_imagen_02):
            with open(ruta_imagen_02, 'rb') as f:
                acto_ep02.imagen_portada.save('EstacionPenitencia2002.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Acto 9.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen_02}'))

        acto_ep02.save()
        
        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Acto Estación de Penitencia 2002 con ID 9.'))



        # =========================================================================
        # POBLADO DE PUESTOS DEL ACTO 9
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Puestos para el Acto 9...")

        puestos_data_ep02 = [
            {"id": 219, "nombre": "Bocina Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 8, "cortejo_cristo": True},
            {"id": 220, "nombre": "Cruz de Guía", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 12, "cortejo_cristo": True},
            {"id": 221, "nombre": "Farol Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 9, "cortejo_cristo": True},
            {"id": 222, "nombre": "Senatus (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 223, "nombre": "Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 224, "nombre": "Varas Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 225, "nombre": "Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 226, "nombre": "Varas Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 227, "nombre": "Banderín Sacramental (tramo 5)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 228, "nombre": "Varas Banderín Sacramental (tramo 5)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 229, "nombre": "Guión del Cincuentenario (tramo 6)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 230, "nombre": "Varas Guión del Cincuentenario (tramo 6)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 231, "nombre": "Banderín de la Juventud (tramo 7)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 232, "nombre": "Varas Banderín de la Juventud (tramo 7)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 6, "cortejo_cristo": True},
            
            {"id": 233, "nombre": "Cirio Grande Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 234, "nombre": "Cirio Mediano Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 235, "nombre": "Cirio Pequeño Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 5, "cortejo_cristo": True},
        ]

        puestos_virgen_data_ep02 = [
            {"id": 236, "nombre": "Cirios apagados cruces (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 1, "cortejo_cristo": False},
            {"id": 237, "nombre": "Bocinas (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 8, "cortejo_cristo": False},
            {"id": 238, "nombre": "Simpecado (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 239, "nombre": "Faroles Simpecado (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 9, "cortejo_cristo": False},
            {"id": 240, "nombre": "Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 241, "nombre": "Varas Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 242, "nombre": "Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 243, "nombre": "Varas Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 244, "nombre": "Bandera Concepcionista (tramo 5)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 245, "nombre": "Varas Bandera Concepcionista (tramo 5)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 246, "nombre": "Bandera Realeza de María (tramo 6)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 247, "nombre": "Varas Bandera Realeza de María (tramo 6)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 248, "nombre": "Libro de Reglas (tramo 7)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 249, "nombre": "Varas Libro de Reglas (tramo 7)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 250, "nombre": "Estandarte (tramo 8)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 251, "nombre": "Varas Estandarte (tramo 8)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 6, "cortejo_cristo": False},
            
            {"id": 252, "nombre": "Cirio Grande Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 253, "nombre": "Cirio Mediano Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 254, "nombre": "Cirio Pequeño Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 9, "tipo_puesto_id": 5, "cortejo_cristo": False},
        ]

        puestos_data_ep02.extend(puestos_virgen_data_ep02)

        puestos_a_crear_02 = [Puesto(**data) for data in puestos_data_ep02]
        Puesto.objects.bulk_create(puestos_a_crear_02)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(puestos_a_crear_02)} puestos para el Acto 9 en total.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS: ACTO ID=9 (INSIGNIAS - EMITIDAS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Papeletas de Sitio (Insignias) para el Acto 9...")

        inicio_rango_solicitud_02 = fecha_2002 - timedelta(days=59)
        fin_rango_solicitud_02 = fecha_2002 - timedelta(days=36)

        fecha_emision_insignias_02 = (fecha_2002 - timedelta(days=34)).date() 

        # Incluyendo todos los IDs de insignias (Cristo y Virgen)
        puestos_insignias_ids_02 = [
            219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 
            236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251
        ]

        puestos_insignias_02 = Puesto.objects.filter(id__in=puestos_insignias_ids_02)
        huecos_a_cubrir_02 = []
        for puesto in puestos_insignias_02:
            huecos_a_cubrir_02.extend([puesto.id] * puesto.numero_maximo_asignaciones)

        cantidad_necesaria_02 = len(huecos_a_cubrir_02)

        hermanos_elegibles_02 = list(
            Hermano.objects.filter(fecha_ingreso_corporacion__lte=fecha_2002.date())
            .values_list('id', flat=True)
        )
        
        if len(hermanos_elegibles_02) < cantidad_necesaria_02:
            self.stdout.write(self.style.WARNING("⚠️ No hay suficientes hermanos elegibles para cubrir todas las insignias."))
            hermanos_seleccionados_02 = hermanos_elegibles_02
            huecos_a_cubrir_02 = huecos_a_cubrir_02[:len(hermanos_elegibles_02)]
        else:
            hermanos_seleccionados_02 = random.sample(hermanos_elegibles_02, cantidad_necesaria_02)

        hermanos_seleccionados_02.sort()

        papeletas_data_acto9 = []
        codigos_usados_acto9 = set()

        ultimo_id_papeleta = PapeletaSitio.objects.order_by('-id').first()
        id_papeleta_actual = (ultimo_id_papeleta.id + 1) if ultimo_id_papeleta else 1

        numero_papeleta_secuencial = 1

        for hermano_id, puesto_id in zip(hermanos_seleccionados_02, huecos_a_cubrir_02):

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto9:
                    codigos_usados_acto9.add(codigo)
                    break

            segundos_diferencia = int((fin_rango_solicitud_02 - inicio_rango_solicitud_02).total_seconds())
            segundos_aleatorios = random.randint(0, segundos_diferencia)
            fecha_solicitud = inicio_rango_solicitud_02 + timedelta(seconds=segundos_aleatorios)

            papeletas_data_acto9.append(
                PapeletaSitio(
                    id=id_papeleta_actual,
                    estado_papeleta="EMITIDA",
                    fecha_solicitud=fecha_solicitud,
                    fecha_emision=fecha_emision_insignias_02,
                    codigo_verificacion=codigo,
                    anio=2002,
                    numero_papeleta=numero_papeleta_secuencial,
                    es_solicitud_insignia=True,
                    acto_id=9,
                    hermano_id=hermano_id,
                    puesto_id=puesto_id,
                    tramo_id=None,
                    vinculado_a_id=None,
                    lado=None,
                    orden_en_tramo=None
                )
            )
            numero_papeleta_secuencial += 1
            id_papeleta_actual += 1

        PapeletaSitio.objects.bulk_create(papeletas_data_acto9)

        ultimo_id_preferencia = PreferenciaSolicitud.objects.order_by('-id').first()
        id_preferencia_actual = (ultimo_id_preferencia.id + 1) if ultimo_id_preferencia else 1
        
        preferencias_data_acto9 = []
        
        for papeleta in papeletas_data_acto9:
            preferencias_data_acto9.append(
                PreferenciaSolicitud(
                    id=id_preferencia_actual,
                    orden_prioridad=1,
                    papeleta_id=papeleta.id,
                    puesto_solicitado_id=papeleta.puesto_id
                )
            )
            id_preferencia_actual += 1

            otros_puestos = [p for p in puestos_insignias_ids_02 if p != papeleta.puesto_id]
            puestos_extra = random.sample(otros_puestos, 2)
            
            for i, puesto_extra in enumerate(puestos_extra, start=2):
                preferencias_data_acto9.append(
                    PreferenciaSolicitud(
                        id=id_preferencia_actual,
                        orden_prioridad=i,
                        papeleta_id=papeleta.id,
                        puesto_solicitado_id=puesto_extra
                    )
                )
                id_preferencia_actual += 1

        PreferenciaSolicitud.objects.bulk_create(preferencias_data_acto9)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_data_acto9)} papeletas de insignias (EMITIDAS) para el Acto 9.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS: ACTO ID=9 (CIRIOS - EMITIDAS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Papeletas de Sitio (Cirios) para el Acto 9...")

        inicio_rango_solicitud_cirios_02 = fecha_2002 - timedelta(days=32)
        fin_rango_solicitud_cirios_02 = fecha_2002 - timedelta(days=16)

        fecha_emision_cirios_02 = (fecha_2002 - timedelta(days=14)).date() 

        puestos_cirios_ids_02 = [233, 234, 235, 252, 253, 254]

        hermanos_con_insignia_02 = PapeletaSitio.objects.filter(acto_id=9).values_list('hermano_id', flat=True)

        hermanos_elegibles_cirios_02 = list(
            Hermano.objects.filter(fecha_ingreso_corporacion__lte=fecha_2002.date())
            .exclude(id__in=hermanos_con_insignia_02)
            .values_list('id', flat=True)
        )

        cantidad_a_asignar_02 = min(800, len(hermanos_elegibles_cirios_02))
        hermanos_seleccionados_cirios_02 = random.sample(hermanos_elegibles_cirios_02, cantidad_a_asignar_02)

        hermanos_seleccionados_cirios_02.sort()

        codigos_usados_acto9_cirios = set(PapeletaSitio.objects.filter(acto_id=9).values_list('codigo_verificacion', flat=True))

        ultimo_id_papeleta = PapeletaSitio.objects.order_by('-id').first()
        id_papeleta_actual = (ultimo_id_papeleta.id + 1) if ultimo_id_papeleta else 1

        ultima_papeleta_acto9 = PapeletaSitio.objects.filter(acto_id=9, numero_papeleta__isnull=False).order_by('-numero_papeleta').first()
        numero_papeleta_secuencial = (ultima_papeleta_acto9.numero_papeleta + 1) if ultima_papeleta_acto9 else 1

        ultimo_id_preferencia = PreferenciaSolicitud.objects.order_by('-id').first()
        id_preferencia_actual = (ultimo_id_preferencia.id + 1) if ultimo_id_preferencia else 1

        papeletas_data_cirios_acto9 = []
        preferencias_data_cirios_acto9 = []

        for hermano_id in hermanos_seleccionados_cirios_02:

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto9_cirios:
                    codigos_usados_acto9_cirios.add(codigo)
                    break

            segundos_diferencia = int((fin_rango_solicitud_cirios_02 - inicio_rango_solicitud_cirios_02).total_seconds())
            segundos_aleatorios = random.randint(0, segundos_diferencia)
            fecha_solicitud = inicio_rango_solicitud_cirios_02 + timedelta(seconds=segundos_aleatorios)

            puesto_asignado = random.choice(puestos_cirios_ids_02)

            papeletas_data_cirios_acto9.append(
                PapeletaSitio(
                    id=id_papeleta_actual,
                    estado_papeleta="EMITIDA",
                    fecha_solicitud=fecha_solicitud,
                    fecha_emision=fecha_emision_cirios_02,
                    codigo_verificacion=codigo,
                    anio=2002,
                    numero_papeleta=numero_papeleta_secuencial,
                    es_solicitud_insignia=False,
                    acto_id=9,
                    hermano_id=hermano_id,
                    puesto_id=puesto_asignado,
                    tramo_id=None,
                    vinculado_a_id=None,
                    lado=None,
                    orden_en_tramo=None
                )
            )

            preferencias_data_cirios_acto9.append(
                PreferenciaSolicitud(
                    id=id_preferencia_actual,
                    orden_prioridad=1,
                    papeleta_id=id_papeleta_actual,
                    puesto_solicitado_id=puesto_asignado
                )
            )

            id_papeleta_actual += 1
            numero_papeleta_secuencial += 1
            id_preferencia_actual += 1

        PapeletaSitio.objects.bulk_create(papeletas_data_cirios_acto9)
        PreferenciaSolicitud.objects.bulk_create(preferencias_data_cirios_acto9)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_data_cirios_acto9)} papeletas de cirios (EMITIDAS) para el Acto 9.'))



        # =========================================================================
        # POBLADO DE TRAMOS DEL ACTO 9
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Tramos para el Acto 9...")

        aforo_tramo_ep02 = 200

        tramos_data_ep02 = [
            # --- TRAMOS DE CRISTO (7 Tramos) ---
            {"nombre": "Cruz de Guía", "numero_orden": 1, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep02, "acto_id": 9},
            {"nombre": "Senatus", "numero_orden": 2, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep02, "acto_id": 9},
            {"nombre": "Bandera Morada", "numero_orden": 3, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep02, "acto_id": 9},
            {"nombre": "Bandera Pontificia", "numero_orden": 4, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep02, "acto_id": 9},
            {"nombre": "Banderín Sacramental", "numero_orden": 5, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep02, "acto_id": 9},
            {"nombre": "Guión del Cincuentenario", "numero_orden": 6, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep02, "acto_id": 9},
            {"nombre": "Banderín de la Juventud", "numero_orden": 7, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep02, "acto_id": 9},

            # --- TRAMOS DE VIRGEN (9 Tramos) ---
            {"nombre": "Cruces y Bocinas", "numero_orden": 1, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep02, "acto_id": 9},
            {"nombre": "Simpecado", "numero_orden": 2, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep02, "acto_id": 9},
            {"nombre": "Bandera Blanca y Celeste", "numero_orden": 3, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep02, "acto_id": 9},
            {"nombre": "Bandera Asuncionista", "numero_orden": 4, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep02, "acto_id": 9},
            {"nombre": "Bandera Concepcionista", "numero_orden": 5, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep02, "acto_id": 9},
            {"nombre": "Bandera Realeza de María", "numero_orden": 6, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep02, "acto_id": 9},
            {"nombre": "Libro de Reglas", "numero_orden": 7, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep02, "acto_id": 9},
            {"nombre": "Estandarte", "numero_orden": 8, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep02, "acto_id": 9},
        ]

        tramos_a_crear_ep02 = [Tramo(**data) for data in tramos_data_ep02]
        Tramo.objects.bulk_create(tramos_a_crear_ep02)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(tramos_a_crear_ep02)} tramos para el Acto 9 en total.'))



        # =========================================================================
        # ASIGNACIÓN DE TRAMOS PARA CIRIOS DE CRISTO (ACTO 9)
        # =========================================================================
        self.stdout.write("Asignando tramos, lado y orden a los cirios de Cristo del Acto 9 (Distribución equitativa)...")

        papeletas_cristo_02 = list(PapeletaSitio.objects.filter(
            acto_id=9, 
            puesto_id__in=[233, 234, 235],
            estado_papeleta="EMITIDA"
        ).select_related('hermano').order_by('-hermano__fecha_ingreso_corporacion'))

        tramos_cristo_02 = list(Tramo.objects.filter(
            acto_id=9, 
            paso='CRISTO'
        ).order_by('numero_orden'))

        papeletas_a_actualizar_02 = []
        
        num_papeletas_cristo_02 = len(papeletas_cristo_02)
        num_tramos_cristo_02 = len(tramos_cristo_02)

        if num_tramos_cristo_02 > 0 and num_papeletas_cristo_02 > 0:
            base_por_tramo = num_papeletas_cristo_02 // num_tramos_cristo_02
            resto = num_papeletas_cristo_02 % num_tramos_cristo_02
            
            indice_papeleta = 0

            for tramo in tramos_cristo_02:
                cantidad_asignar = base_por_tramo + (1 if resto > 0 else 0)
                if resto > 0:
                    resto -= 1

                cantidad_asignar = min(cantidad_asignar, tramo.numero_maximo_cirios)

                papeletas_tramo = papeletas_cristo_02[indice_papeleta : indice_papeleta + cantidad_asignar]

                if not papeletas_tramo:
                    break

                papeletas_tramo.sort(key=lambda p: p.hermano.fecha_ingreso_corporacion)

                orden_actual = 1
                for papeleta in papeletas_tramo:
                    papeleta.tramo = tramo
                    papeleta.orden_en_tramo = orden_actual

                    papeleta.lado = "IZQUIERDA" if orden_actual % 2 != 0 else "DERECHA"
                    
                    papeletas_a_actualizar_02.append(papeleta)
                    orden_actual += 1
                    
                indice_papeleta += len(papeletas_tramo)

        if papeletas_a_actualizar_02:
            PapeletaSitio.objects.bulk_update(papeletas_a_actualizar_02, ['tramo', 'orden_en_tramo', 'lado'])
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han asignado equitativamente {len(papeletas_a_actualizar_02)} papeletas de cirios de Cristo en {num_tramos_cristo_02} tramos.'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron papeletas de Cristo para asignar a los tramos en el Acto 9.'))



        # =========================================================================
        # ASIGNACIÓN DE TRAMOS PARA CIRIOS DE VIRGEN (ACTO 9)
        # =========================================================================
        self.stdout.write("Asignando tramos, lado y orden a los cirios de Virgen del Acto 9 (Distribución equitativa)...")

        papeletas_virgen_02 = list(PapeletaSitio.objects.filter(
            acto_id=9, 
            puesto_id__in=[252, 253, 254],
            estado_papeleta="EMITIDA"
        ).select_related('hermano').order_by('-hermano__fecha_ingreso_corporacion'))

        tramos_virgen_02 = list(Tramo.objects.filter(
            acto_id=9, 
            paso='VIRGEN'
        ).order_by('numero_orden'))

        papeletas_virgen_actualizar_02 = []
        
        num_papeletas_virgen_02 = len(papeletas_virgen_02)
        num_tramos_virgen_02 = len(tramos_virgen_02)

        if num_tramos_virgen_02 > 0 and num_papeletas_virgen_02 > 0:
            base_por_tramo_v = num_papeletas_virgen_02 // num_tramos_virgen_02
            resto_v = num_papeletas_virgen_02 % num_tramos_virgen_02
            
            indice_papeleta_virgen = 0

            for tramo in tramos_virgen_02:
                cantidad_asignar_v = base_por_tramo_v + (1 if resto_v > 0 else 0)
                if resto_v > 0:
                    resto_v -= 1
                
                cantidad_asignar_v = min(cantidad_asignar_v, tramo.numero_maximo_cirios)

                papeletas_tramo = papeletas_virgen_02[indice_papeleta_virgen : indice_papeleta_virgen + cantidad_asignar_v]

                if not papeletas_tramo:
                    break

                papeletas_tramo.sort(key=lambda p: p.hermano.fecha_ingreso_corporacion)

                orden_actual = 1
                for papeleta in papeletas_tramo:
                    papeleta.tramo = tramo
                    papeleta.orden_en_tramo = orden_actual

                    papeleta.lado = "IZQUIERDA" if orden_actual % 2 != 0 else "DERECHA"
                    
                    papeletas_virgen_actualizar_02.append(papeleta)
                    orden_actual += 1
                    
                indice_papeleta_virgen += len(papeletas_tramo)

        if papeletas_virgen_actualizar_02:
            PapeletaSitio.objects.bulk_update(papeletas_virgen_actualizar_02, ['tramo', 'orden_en_tramo', 'lado'])
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han asignado equitativamente {len(papeletas_virgen_actualizar_02)} papeletas de cirios de Virgen en {num_tramos_virgen_02} tramos.'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron papeletas de Virgen para asignar a los tramos en el Acto 9.'))



        # =========================================================================
        # POBLADO DE ACTO: ESTACIÓN DE PENITENCIA 2003 (ID=10)
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Acto: Estación de Penitencia 2003...")

        # Lunes Santo de 2003 fue el 14 de abril
        fecha_2003 = datetime(2003, 4, 14, 15, 0, 0, tzinfo=timezone.get_current_timezone())

        Acto.objects.filter(id=10).delete()

        descripcion_acto_03 = (
                "La Estación de Penitencia a la Santa Iglesia Catedral es el acto central y culminante "
                "de la vida de nuestra Hermandad de San Gonzalo. En este año 2003, nos preparamos para vivir "
                "nuevamente este encuentro íntimo con nuestro Señor en su Soberano Poder ante Caifás y nuestra "
                "Madre y Señora de la Salud. Este solemne acto público de fe es la manifestación más genuina de nuestro "
                "compromiso cristiano, donde cada nazareno, costalero, acólito y hermano se convierte en un "
                "testimonio vivo del Evangelio por las calles de nuestro barrio de Triana y de toda Sevilla. "
                "Durante nuestro caminar, la túnica blanca se transforma en nuestra piel, igualándonos a todos "
                "bajo la cruz de Cristo. La cofradía no es solo un cortejo estético, es una auténtica comunidad en "
                "movimiento que reza, que acompaña y que sostiene a los Sagrados Titulares en su discurrir. "
                "Se invita a todos los hermanos a participar con recogimiento, orden y profundo sentido de "
                "pertenencia, haciendo de cada paso una oración y de cada cirio encendido una luz de esperanza "
                "para aquellos que más lo necesitan en estos tiempos. Que esta nueva Estación de Penitencia renueve "
                "nuestra vocación de servicio, fortaleciendo firmemente los lazos de fraternidad que nos unen "
                "como corporación cristiana y acercándonos aún más a la misericordia infinita de Dios, viviendo la "
                "caridad, la esperanza y la inquebrantable devoción en cada instante de nuestra procesión."
            )

        acto_ep03 = Acto(
            id=10,
            nombre="Estación de Penitencia 2003",
            lugar="Parroquia de San Gonzalo",
            descripcion=descripcion_acto_03,
            fecha=fecha_2003,
            modalidad="TRADICIONAL",
            tipo_acto_id=1,
            inicio_solicitud=fecha_2003 - timedelta(days=60),
            fin_solicitud=fecha_2003 - timedelta(days=35),
            fecha_ejecucion_reparto= fecha_2003 - timedelta(days=34),
            inicio_solicitud_cirios = fecha_2003 - timedelta(days=33),
            fin_solicitud_cirios= fecha_2003 - timedelta(days=15),
            fecha_ejecucion_cirios = fecha_2003 - timedelta(days=14),
        )

        ruta_imagen_03 = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'EstacionPenitencia2003.jpg')
        
        if os.path.exists(ruta_imagen_03):
            with open(ruta_imagen_03, 'rb') as f:
                acto_ep03.imagen_portada.save('EstacionPenitencia2003.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Acto 10.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen_03}'))

        acto_ep03.save()
        
        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Acto Estación de Penitencia 2003 con ID 10.'))



        # =========================================================================
        # POBLADO DE PUESTOS DEL ACTO 10
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Puestos para el Acto 10...")

        puestos_data_ep03 = [
            {"id": 255, "nombre": "Bocina Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 8, "cortejo_cristo": True},
            {"id": 256, "nombre": "Cruz de Guía", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 12, "cortejo_cristo": True},
            {"id": 257, "nombre": "Farol Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 9, "cortejo_cristo": True},
            {"id": 258, "nombre": "Senatus (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 259, "nombre": "Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 260, "nombre": "Varas Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 261, "nombre": "Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 262, "nombre": "Varas Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 263, "nombre": "Banderín Sacramental (tramo 5)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 264, "nombre": "Varas Banderín Sacramental (tramo 5)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 265, "nombre": "Guión del Cincuentenario (tramo 6)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 266, "nombre": "Varas Guión del Cincuentenario (tramo 6)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 267, "nombre": "Banderín de la Juventud (tramo 7)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 268, "nombre": "Varas Banderín de la Juventud (tramo 7)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 6, "cortejo_cristo": True},
            
            {"id": 269, "nombre": "Cirio Grande Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 270, "nombre": "Cirio Mediano Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 271, "nombre": "Cirio Pequeño Cristo", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 5, "cortejo_cristo": True},
        ]

        puestos_virgen_data_ep03 = [
            {"id": 272, "nombre": "Cirios apagados cruces (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 1, "cortejo_cristo": False},
            {"id": 273, "nombre": "Bocinas (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 8, "cortejo_cristo": False},
            {"id": 274, "nombre": "Simpecado (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 275, "nombre": "Faroles Simpecado (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 9, "cortejo_cristo": False},
            {"id": 276, "nombre": "Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 277, "nombre": "Varas Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 278, "nombre": "Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 279, "nombre": "Varas Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 280, "nombre": "Bandera Concepcionista (tramo 5)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 281, "nombre": "Varas Bandera Concepcionista (tramo 5)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 282, "nombre": "Bandera Realeza de María (tramo 6)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 283, "nombre": "Varas Bandera Realeza de María (tramo 6)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 284, "nombre": "Libro de Reglas (tramo 7)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 285, "nombre": "Varas Libro de Reglas (tramo 7)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 286, "nombre": "Estandarte (tramo 8)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 287, "nombre": "Varas Estandarte (tramo 8)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 6, "cortejo_cristo": False},
            
            {"id": 288, "nombre": "Cirio Grande Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 289, "nombre": "Cirio Mediano Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": 290, "nombre": "Cirio Pequeño Virgen", "numero_maximo_asignaciones": 200, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 10, "tipo_puesto_id": 5, "cortejo_cristo": False},
        ]

        puestos_data_ep03.extend(puestos_virgen_data_ep03)

        puestos_a_crear_03 = [Puesto(**data) for data in puestos_data_ep03]
        Puesto.objects.bulk_create(puestos_a_crear_03)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(puestos_a_crear_03)} puestos para el Acto 10 en total.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS: ACTO ID=10 (INSIGNIAS - EMITIDAS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Papeletas de Sitio (Insignias) para el Acto 10...")

        inicio_rango_solicitud_03 = fecha_2003 - timedelta(days=59)
        fin_rango_solicitud_03 = fecha_2003 - timedelta(days=36)

        fecha_emision_insignias_03 = (fecha_2003 - timedelta(days=34)).date() 

        # Incluyendo todos los IDs de insignias (Cristo y Virgen)
        puestos_insignias_ids_03 = [
            255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 
            272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287
        ]

        puestos_insignias_03 = Puesto.objects.filter(id__in=puestos_insignias_ids_03)
        huecos_a_cubrir_03 = []
        for puesto in puestos_insignias_03:
            huecos_a_cubrir_03.extend([puesto.id] * puesto.numero_maximo_asignaciones)

        cantidad_necesaria_03 = len(huecos_a_cubrir_03)

        hermanos_elegibles_03 = list(
            Hermano.objects.filter(fecha_ingreso_corporacion__lte=fecha_2003.date())
            .values_list('id', flat=True)
        )
        
        if len(hermanos_elegibles_03) < cantidad_necesaria_03:
            self.stdout.write(self.style.WARNING("⚠️ No hay suficientes hermanos elegibles para cubrir todas las insignias."))
            hermanos_seleccionados_03 = hermanos_elegibles_03
            huecos_a_cubrir_03 = huecos_a_cubrir_03[:len(hermanos_elegibles_03)]
        else:
            hermanos_seleccionados_03 = random.sample(hermanos_elegibles_03, cantidad_necesaria_03)

        hermanos_seleccionados_03.sort()

        papeletas_data_acto10 = []
        codigos_usados_acto10 = set()

        ultimo_id_papeleta = PapeletaSitio.objects.order_by('-id').first()
        id_papeleta_actual = (ultimo_id_papeleta.id + 1) if ultimo_id_papeleta else 1

        numero_papeleta_secuencial = 1

        for hermano_id, puesto_id in zip(hermanos_seleccionados_03, huecos_a_cubrir_03):

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto10:
                    codigos_usados_acto10.add(codigo)
                    break

            segundos_diferencia = int((fin_rango_solicitud_03 - inicio_rango_solicitud_03).total_seconds())
            segundos_aleatorios = random.randint(0, segundos_diferencia)
            fecha_solicitud = inicio_rango_solicitud_03 + timedelta(seconds=segundos_aleatorios)

            papeletas_data_acto10.append(
                PapeletaSitio(
                    id=id_papeleta_actual,
                    estado_papeleta="EMITIDA",
                    fecha_solicitud=fecha_solicitud,
                    fecha_emision=fecha_emision_insignias_03,
                    codigo_verificacion=codigo,
                    anio=2003,
                    numero_papeleta=numero_papeleta_secuencial,
                    es_solicitud_insignia=True,
                    acto_id=10,
                    hermano_id=hermano_id,
                    puesto_id=puesto_id,
                    tramo_id=None,
                    vinculado_a_id=None,
                    lado=None,
                    orden_en_tramo=None
                )
            )
            numero_papeleta_secuencial += 1
            id_papeleta_actual += 1

        PapeletaSitio.objects.bulk_create(papeletas_data_acto10)

        ultimo_id_preferencia = PreferenciaSolicitud.objects.order_by('-id').first()
        id_preferencia_actual = (ultimo_id_preferencia.id + 1) if ultimo_id_preferencia else 1
        
        preferencias_data_acto10 = []
        
        for papeleta in papeletas_data_acto10:
            preferencias_data_acto10.append(
                PreferenciaSolicitud(
                    id=id_preferencia_actual,
                    orden_prioridad=1,
                    papeleta_id=papeleta.id,
                    puesto_solicitado_id=papeleta.puesto_id
                )
            )
            id_preferencia_actual += 1

            otros_puestos = [p for p in puestos_insignias_ids_03 if p != papeleta.puesto_id]
            puestos_extra = random.sample(otros_puestos, 2)
            
            for i, puesto_extra in enumerate(puestos_extra, start=2):
                preferencias_data_acto10.append(
                    PreferenciaSolicitud(
                        id=id_preferencia_actual,
                        orden_prioridad=i,
                        papeleta_id=papeleta.id,
                        puesto_solicitado_id=puesto_extra
                    )
                )
                id_preferencia_actual += 1

        PreferenciaSolicitud.objects.bulk_create(preferencias_data_acto10)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_data_acto10)} papeletas de insignias (EMITIDAS) para el Acto 10.'))



        # =========================================================================
        # POBLADO DE PAPELETAS Y PREFERENCIAS: ACTO ID=10 (CIRIOS - EMITIDAS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Papeletas de Sitio (Cirios) para el Acto 10...")

        inicio_rango_solicitud_cirios_03 = fecha_2003 - timedelta(days=32)
        fin_rango_solicitud_cirios_03 = fecha_2003 - timedelta(days=16)

        fecha_emision_cirios_03 = (fecha_2003 - timedelta(days=14)).date() 

        puestos_cirios_ids_03 = [269, 270, 271, 288, 289, 290]

        hermanos_con_insignia_03 = PapeletaSitio.objects.filter(acto_id=10).values_list('hermano_id', flat=True)

        hermanos_elegibles_cirios_03 = list(
            Hermano.objects.filter(fecha_ingreso_corporacion__lte=fecha_2003.date())
            .exclude(id__in=hermanos_con_insignia_03)
            .values_list('id', flat=True)
        )

        cantidad_a_asignar_03 = min(800, len(hermanos_elegibles_cirios_03))
        hermanos_seleccionados_cirios_03 = random.sample(hermanos_elegibles_cirios_03, cantidad_a_asignar_03)

        hermanos_seleccionados_cirios_03.sort()

        codigos_usados_acto10_cirios = set(PapeletaSitio.objects.filter(acto_id=10).values_list('codigo_verificacion', flat=True))

        ultimo_id_papeleta = PapeletaSitio.objects.order_by('-id').first()
        id_papeleta_actual = (ultimo_id_papeleta.id + 1) if ultimo_id_papeleta else 1

        ultima_papeleta_acto10 = PapeletaSitio.objects.filter(acto_id=10, numero_papeleta__isnull=False).order_by('-numero_papeleta').first()
        numero_papeleta_secuencial = (ultima_papeleta_acto10.numero_papeleta + 1) if ultima_papeleta_acto10 else 1

        ultimo_id_preferencia = PreferenciaSolicitud.objects.order_by('-id').first()
        id_preferencia_actual = (ultimo_id_preferencia.id + 1) if ultimo_id_preferencia else 1

        papeletas_data_cirios_acto10 = []
        preferencias_data_cirios_acto10 = []

        for hermano_id in hermanos_seleccionados_cirios_03:

            while True:
                codigo = f"{random.randint(0, 99999999):08d}"
                if codigo not in codigos_usados_acto10_cirios:
                    codigos_usados_acto10_cirios.add(codigo)
                    break

            segundos_diferencia = int((fin_rango_solicitud_cirios_03 - inicio_rango_solicitud_cirios_03).total_seconds())
            segundos_aleatorios = random.randint(0, segundos_diferencia)
            fecha_solicitud = inicio_rango_solicitud_cirios_03 + timedelta(seconds=segundos_aleatorios)

            puesto_asignado = random.choice(puestos_cirios_ids_03)

            papeletas_data_cirios_acto10.append(
                PapeletaSitio(
                    id=id_papeleta_actual,
                    estado_papeleta="EMITIDA",
                    fecha_solicitud=fecha_solicitud,
                    fecha_emision=fecha_emision_cirios_03,
                    codigo_verificacion=codigo,
                    anio=2003,
                    numero_papeleta=numero_papeleta_secuencial,
                    es_solicitud_insignia=False,
                    acto_id=10,
                    hermano_id=hermano_id,
                    puesto_id=puesto_asignado,
                    tramo_id=None,
                    vinculado_a_id=None,
                    lado=None,
                    orden_en_tramo=None
                )
            )

            preferencias_data_cirios_acto10.append(
                PreferenciaSolicitud(
                    id=id_preferencia_actual,
                    orden_prioridad=1,
                    papeleta_id=id_papeleta_actual,
                    puesto_solicitado_id=puesto_asignado
                )
            )

            id_papeleta_actual += 1
            numero_papeleta_secuencial += 1
            id_preferencia_actual += 1

        PapeletaSitio.objects.bulk_create(papeletas_data_cirios_acto10)
        PreferenciaSolicitud.objects.bulk_create(preferencias_data_cirios_acto10)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(papeletas_data_cirios_acto10)} papeletas de cirios (EMITIDAS) para el Acto 10.'))



        # =========================================================================
        # POBLADO DE TRAMOS DEL ACTO 10
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Tramos para el Acto 10...")

        aforo_tramo_ep03 = 200

        tramos_data_ep03 = [
            # --- TRAMOS DE CRISTO (7 Tramos) ---
            {"nombre": "Cruz de Guía", "numero_orden": 1, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep03, "acto_id": 10},
            {"nombre": "Senatus", "numero_orden": 2, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep03, "acto_id": 10},
            {"nombre": "Bandera Morada", "numero_orden": 3, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep03, "acto_id": 10},
            {"nombre": "Bandera Pontificia", "numero_orden": 4, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep03, "acto_id": 10},
            {"nombre": "Banderín Sacramental", "numero_orden": 5, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep03, "acto_id": 10},
            {"nombre": "Guión del Cincuentenario", "numero_orden": 6, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep03, "acto_id": 10},
            {"nombre": "Banderín de la Juventud", "numero_orden": 7, "paso": "CRISTO", "numero_maximo_cirios": aforo_tramo_ep03, "acto_id": 10},

            # --- TRAMOS DE VIRGEN (8 Tramos) ---
            {"nombre": "Cruces y Bocinas", "numero_orden": 1, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep03, "acto_id": 10},
            {"nombre": "Simpecado", "numero_orden": 2, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep03, "acto_id": 10},
            {"nombre": "Bandera Blanca y Celeste", "numero_orden": 3, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep03, "acto_id": 10},
            {"nombre": "Bandera Asuncionista", "numero_orden": 4, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep03, "acto_id": 10},
            {"nombre": "Bandera Concepcionista", "numero_orden": 5, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep03, "acto_id": 10},
            {"nombre": "Bandera Realeza de María", "numero_orden": 6, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep03, "acto_id": 10},
            {"nombre": "Libro de Reglas", "numero_orden": 7, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep03, "acto_id": 10},
            {"nombre": "Estandarte", "numero_orden": 8, "paso": "VIRGEN", "numero_maximo_cirios": aforo_tramo_ep03, "acto_id": 10},
        ]

        tramos_a_crear_ep03 = [Tramo(**data) for data in tramos_data_ep03]
        Tramo.objects.bulk_create(tramos_a_crear_ep03)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(tramos_a_crear_ep03)} tramos para el Acto 10 en total.'))



        # =========================================================================
        # ASIGNACIÓN DE TRAMOS PARA CIRIOS DE CRISTO (ACTO 10)
        # =========================================================================
        self.stdout.write("Asignando tramos, lado y orden a los cirios de Cristo del Acto 10 (Distribución equitativa)...")

        papeletas_cristo_03 = list(PapeletaSitio.objects.filter(
            acto_id=10, 
            puesto_id__in=[269, 270, 271],
            estado_papeleta="EMITIDA"
        ).select_related('hermano').order_by('-hermano__fecha_ingreso_corporacion'))

        tramos_cristo_03 = list(Tramo.objects.filter(
            acto_id=10, 
            paso='CRISTO'
        ).order_by('numero_orden'))

        papeletas_a_actualizar_03 = []
        
        num_papeletas_cristo_03 = len(papeletas_cristo_03)
        num_tramos_cristo_03 = len(tramos_cristo_03)

        if num_tramos_cristo_03 > 0 and num_papeletas_cristo_03 > 0:
            base_por_tramo = num_papeletas_cristo_03 // num_tramos_cristo_03
            resto = num_papeletas_cristo_03 % num_tramos_cristo_03
            
            indice_papeleta = 0

            for tramo in tramos_cristo_03:
                cantidad_asignar = base_por_tramo + (1 if resto > 0 else 0)
                if resto > 0:
                    resto -= 1

                cantidad_asignar = min(cantidad_asignar, tramo.numero_maximo_cirios)

                papeletas_tramo = papeletas_cristo_03[indice_papeleta : indice_papeleta + cantidad_asignar]

                if not papeletas_tramo:
                    break

                papeletas_tramo.sort(key=lambda p: p.hermano.fecha_ingreso_corporacion)

                orden_actual = 1
                for papeleta in papeletas_tramo:
                    papeleta.tramo = tramo
                    papeleta.orden_en_tramo = orden_actual

                    papeleta.lado = "IZQUIERDA" if orden_actual % 2 != 0 else "DERECHA"
                    
                    papeletas_a_actualizar_03.append(papeleta)
                    orden_actual += 1
                    
                indice_papeleta += len(papeletas_tramo)

        if papeletas_a_actualizar_03:
            PapeletaSitio.objects.bulk_update(papeletas_a_actualizar_03, ['tramo', 'orden_en_tramo', 'lado'])
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han asignado equitativamente {len(papeletas_a_actualizar_03)} papeletas de cirios de Cristo en {num_tramos_cristo_03} tramos.'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron papeletas de Cristo para asignar a los tramos en el Acto 10.'))



        # =========================================================================
        # ASIGNACIÓN DE TRAMOS PARA CIRIOS DE VIRGEN (ACTO 10)
        # =========================================================================
        self.stdout.write("Asignando tramos, lado y orden a los cirios de Virgen del Acto 10 (Distribución equitativa)...")

        papeletas_virgen_03 = list(PapeletaSitio.objects.filter(
            acto_id=10, 
            puesto_id__in=[288, 289, 290],
            estado_papeleta="EMITIDA"
        ).select_related('hermano').order_by('-hermano__fecha_ingreso_corporacion'))

        tramos_virgen_03 = list(Tramo.objects.filter(
            acto_id=10, 
            paso='VIRGEN'
        ).order_by('numero_orden'))

        papeletas_virgen_actualizar_03 = []
        
        num_papeletas_virgen_03 = len(papeletas_virgen_03)
        num_tramos_virgen_03 = len(tramos_virgen_03)

        if num_tramos_virgen_03 > 0 and num_papeletas_virgen_03 > 0:
            base_por_tramo_v = num_papeletas_virgen_03 // num_tramos_virgen_03
            resto_v = num_papeletas_virgen_03 % num_tramos_virgen_03
            
            indice_papeleta_virgen = 0

            for tramo in tramos_virgen_03:
                cantidad_asignar_v = base_por_tramo_v + (1 if resto_v > 0 else 0)
                if resto_v > 0:
                    resto_v -= 1
                
                cantidad_asignar_v = min(cantidad_asignar_v, tramo.numero_maximo_cirios)

                papeletas_tramo = papeletas_virgen_03[indice_papeleta_virgen : indice_papeleta_virgen + cantidad_asignar_v]

                if not papeletas_tramo:
                    break

                papeletas_tramo.sort(key=lambda p: p.hermano.fecha_ingreso_corporacion)

                orden_actual = 1
                for papeleta in papeletas_tramo:
                    papeleta.tramo = tramo
                    papeleta.orden_en_tramo = orden_actual

                    papeleta.lado = "IZQUIERDA" if orden_actual % 2 != 0 else "DERECHA"
                    
                    papeletas_virgen_actualizar_03.append(papeleta)
                    orden_actual += 1
                    
                indice_papeleta_virgen += len(papeletas_tramo)

        if papeletas_virgen_actualizar_03:
            PapeletaSitio.objects.bulk_update(papeletas_virgen_actualizar_03, ['tramo', 'orden_en_tramo', 'lado'])
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han asignado equitativamente {len(papeletas_virgen_actualizar_03)} papeletas de cirios de Virgen en {num_tramos_virgen_03} tramos.'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron papeletas de Virgen para asignar a los tramos en el Acto 10.'))



        # =========================================================================
        # POBLADO DE COMUNICADO 1
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Comunicado 1...")

        contenido_comunicado_1 = (
            "Durante los días de la Semana Santa, nuestra hermandad participará en los distintos cultos "
            "y actos que se desarrollarán en la Parroquia de San Gonzalo, detallándose a continuación "
            "cómo se vivirán los días sacros.\n\n"
            "DOMINGO DE RAMOS, 13 de abril\n"
            "• Eucaristías a las 9:00 horas (bendición de palmas y procesión de las comunidades neocatecumenales), "
            "10:00 y 11:30 horas (bendición de palmas y procesión).\n\n"
            "LUNES SANTO, 14 de abril\n"
            "• Misa de hermandad a las 9:30 horas, emitiéndose en directo por el canal de YouTube de la hermandad. "
            "La parroquia cerrará a las 12:00 horas para comenzar a preparar la cofradía.\n"
            "• Estación de penitencia a la Santa, Metropolitana y Patriarcal Iglesia Catedral de Santa María de "
            "la Asunción y de la Sede a las 15:00 horas.\n\n"
            "MARTES SANTO, 15 de abril\n"
            "• La misa crismal será en la Santa Iglesia Catedral a las 11:00 horas.\n"
            "• Eucaristía en la Parroquia. 20:00 horas.\n\n"
            "MIÉRCOLES SANTO, 16 de abril\n"
            "• Eucaristías en la Parroquia a las 10:00 horas y a las 20:00 horas.\n\n"
            "JUEVES SANTO, 17 de abril\n"
            "• Laudes y meditación sobre el Jueves Santo a las 10:00 horas.\n"
            "• Celebración de la Cena del Señor a las 17:00 horas.\n"
            "• Hora santa ante el Monumento a las 20:00 horas.\n\n"
            "VIERNES SANTO, 18 de abril\n"
            "• Meditación del Vía crucis a las 13:00 horas.\n"
            "• Celebración de la Muerte del Señor a las 17:00 horas.\n\n"
            "SÁBADO SANTO, 19 de abril\n"
            "• Laudes y meditación con María a las 10:00 horas.\n"
            "• Solemne Vigilia Pascual a las 22:00 horas.\n\n"
            "DOMINGO DE RESURRECCIÓN, 20 de abril\n"
            "• Eucaristías a las 10:00, 11:30, 13:00 y 20:00 horas."
        )

        comunicado_1 = Comunicado(
            titulo="Horarios y cultos de la Parroquia de San Gonzalo en la Semana Santa de 2025",
            contenido=contenido_comunicado_1,
            fecha_emision=make_aware(datetime(2025, 4, 7, 10, 0)),
            tipo_comunicacion='GENERAL',
            autor_id=29,
            embedding = [-0.0036156958, 0.02633657, 0.030822897, -0.043637194, -0.012035134, 0.01675095, -0.0075424784, 0.0074111256, -0.0175064, -0.0065236855, -0.021755844, -0.0034895914, -0.016520964, -0.00015666753, 0.112815745, 0.006178681, 0.0045511783, 0.009115889, -0.008990799, 0.00936294, 0.031208172, -0.026618084, -0.008469969, -0.013791753, -0.016179493, 0.017803516, 0.017535213, -0.003849115, 0.055034682, -0.024611106, -0.008974789, 0.009950784, -0.015855465, -0.015974166, -0.0032992577, 0.012744429, -0.02257757, 0.00066067744, -0.013712919, 0.006990629, -0.018510016, 0.008027872, -0.0071479813, -0.008364593, -0.0033012973, -0.0038218226, -0.009127707, -0.033630766, 0.0068855505, 0.0008659034, 0.011403227, -0.0029171722, -0.03199255, -0.1883819, -0.014823372, 0.0061421874, -0.014318994, -0.01015957, 0.006551342, -0.00023322784, -0.014163183, 0.012352222, -0.015743047, -0.006742478, 0.00640012, -0.012633438, -0.0068382355, 0.05978841, -0.024363197, 0.007046703, -0.0017447683, -0.006473108, 0.00026440242, -0.0032597033, -0.010327979, -0.020821914, 0.0068883873, 0.0062220837, -0.016774097, 0.03210548, -0.012900659, 4.1897805e-05, -0.0030768292, -0.015735464, -0.0061611263, -0.014981842, 0.026689647, -0.016128952, -0.0022656443, 0.0078894, 0.008050368, 0.02856563, -0.010878026, -0.016755868, 0.019610513, 0.002120529, 0.021376781, 0.00028382236, -0.016866371, -0.017232541, -0.012233178, -0.003617589, -0.0014269918, 1.36348735e-05, 0.0022383225, -0.030889878, 0.018091286, 0.01123449, 0.001811767, 0.00018536186, -0.010197252, 0.0005386618, -0.0022831988, 0.009585391, -0.0004168875, -0.1822966, 0.008722838, -0.00054338505, -0.010551849, -0.024722595, 0.019673213, 0.0013622401, -0.008624067, 0.035809703, 0.0017431647, -0.004661212, 0.021419406, -0.0135479085, -0.019798925, -0.013026004, 0.016147178, -0.01283361, 0.018426044, 0.016597275, -0.028725488, 0.027759196, -0.024844524, -0.013716245, 0.011365834, 0.00025309154, 0.020433044, 0.022212828, -0.0007541929, 0.0035435, -0.00040259224, 0.0060875695, 0.010734586, -0.0064346683, -0.021169923, -0.006799743, 0.023219008, 0.009308992, -0.017075447, -0.0015595193, -0.0038960085, -0.020247797, 0.012102003, 0.0040730615, 0.012177488, 0.006871818, -0.0050898, -0.007065076, -0.0066562095, 0.0059614466, 0.008324015, 0.00795466, -0.027933879, -0.013889138, -0.01809094, 0.0008987773, -0.02039869, -0.01388883, -0.014992886, -0.009330984, -0.018762281, -0.0044576963, -0.0005348025, -0.042958856, 0.02259564, -0.008562872, 0.004896835, -0.009114849, -0.017226098, 0.0078559695, 0.012827215, -0.02506158, -0.0031533006, 0.0060327016, 0.0019206268, -0.0062799393, -0.009668376, -0.0239618, 0.009870289, -0.012129658, -0.007265261, -0.0052291225, -0.0035426957, -0.016061202, 0.017749911, -0.014542, 0.020296074, -0.006982402, 0.002810885, -0.00077748316, 0.003427771, 0.010127315, -0.020301085, -0.004568646, -0.0155821955, 0.012385444, -0.0024876597, -0.009193806, 0.014510464, -0.029498046, 0.012469921, -0.008211285, -0.024976961, 0.010188084, -0.018775016, -0.025342489, -0.010843463, -0.002329142, -0.015831416, 0.043953385, -0.0015468119, -0.006615777, 0.0017983416, -0.022387292, 0.023468977, 0.023026403, 0.00339078, 0.005321417, 0.024648111, 0.019034619, 0.034023654, -0.00046209514, 0.012433214, -0.0072441297, 0.0397325, 0.01835212, 0.0017883442, -0.016444463, -0.009586719, -0.01533544, 0.007960454, 0.011326132, 0.008032181, -0.014757766, -0.0002817785, -0.027623408, 0.00069938716, 0.013962856, 0.0060953307, -0.0021261666, -0.021558924, 0.013638511, -0.010827649, 0.012624781, -0.023730846, -0.020206869, -0.015531261, -0.008730007, -0.011316279, -0.013544834, -0.0005389264, -7.510544e-05, 0.009947514, 0.034005307, -0.016267803, -0.0013274899, 0.014934804, 0.003314801, -0.0008572649, -0.013236187, 0.002424477, 0.0035588066, -0.14258224, 0.03592168, -0.029791614, -0.009842101, -0.0045555364, -0.017434083, -0.011653919, 0.010443277, -0.01921199, -0.0061313175, 0.00097220106, -0.02894477, -0.009325464, -0.021888738, -0.0024349384, 0.019661086, 0.003779664, 0.013046364, 0.0051592495, -0.04495696, 0.032336056, -0.009830727, -0.024566362, -0.014240311, 0.014778733, -0.0029625061, -0.024289805, 0.025523948, 0.023741033, -0.0007929502, 0.006023514, -0.0058214935, -0.0027839309, 0.0020700134, 0.01951366, 0.006686814, 0.027413383, -0.02387804, -0.006621398, 0.010945592, 0.035040826, 0.00054875185, 0.024058469, 0.03890555, -0.028186226, -0.013865644, -0.01316106, -0.010647755, -0.0008742605, 0.025067206, -0.024032084, -0.0019476138, 0.01860584, -0.0041596307, -0.010718697, -0.01697574, 0.017247628, 0.0055902707, -0.01755229, -0.0045020115, -0.021126058, 0.0012013525, 0.0048880163, 0.0060669845, -0.001465217, 0.014560503, 0.0083548715, -0.0044358885, -0.013988121, 0.034320705, 0.0038944813, -0.038729724, 0.026223006, -0.039793175, 0.005188171, -0.008496979, -0.0021582248, -0.0039132573, -0.00020559075, 0.0059150904, -0.022327255, -0.0010950209, 0.008087291, 0.041035477, 0.025451507, -0.014619377, -0.014878291, -0.0050453423, -0.001151988, -0.0074841636, -0.010180396, 0.0019375484, -0.0008368217, 0.0051048244, -0.026711155, -0.013364184, -0.01180464, -0.0036040507, -0.0021790154, 0.038436968, -0.018396845, 0.002669943, 0.009064444, 0.0011740302, -0.004189649, 0.016934669, -0.015697854, 0.0104891835, 0.0067608906, -0.0055443565, -0.0089633865, 0.00203811, 0.015916133, 0.016691042, 0.0034184384, -0.00323118, -0.0037128099, -0.0065113585, 0.0032561063, 0.008548812, -0.009306453, -0.03615672, -0.016510786, 0.0023232007, -0.011240636, 0.0072148987, 0.0005707918, -0.0052682986, 0.0056280154, -0.017134003, -0.0056957533, -0.0037405624, -0.015952721, -0.022923404, 0.017757485, 0.019301862, 0.0026941744, 0.00040313206, 0.04386225, -0.03091487, 0.015616982, 0.003511045, 0.001691058, 0.009789919, 0.01214607, 0.0063012424, -0.031066928, 0.0011296493, 0.019772522, -0.028835231, -0.015365752, -0.026693009, 0.00059953006, 0.0007245435, -0.0032312963, -0.020193323, -0.034837734, 0.002870414, -0.025182616, -0.025464075, -0.001731918, -0.021830529, -0.0061888555, 0.0066181645, 0.0072158696, -0.005348271, -0.008340618, 0.007438262, 0.02231706, -0.0019985088, 0.0063968557, 0.010916341, 0.022186814, 0.0037962825, 0.007363209, -0.0232954, 0.0073416145, -0.0036246642, -0.0024585451, -0.0019920876, -0.0055801086, -0.00029093478, 0.0034475394, 0.013761468, -0.005692742, -0.0030853206, 0.00612777, 0.0032972603, -0.015080878, 0.0017006646, -0.0061202506, 0.00013773935, 0.018132053, 0.016314723, 0.0041234754, -0.015682647, -0.021421775, 0.0120381545, -0.008594913, 0.007497993, -0.0067143207, 0.008033784, 0.001775782, -0.008405061, -0.016088786, 0.008753853, -0.015354987, 0.0049432176, -0.02598525, 0.015752092, 0.021020688, 0.011421999, 0.022020645, 0.0075051263, 0.049051125, 0.0035805004, -0.0061123124, 0.018319711, -0.012020176, 0.0029124145, -0.0028229936, 0.010967183, 0.010667237, 0.007827427, 0.008363846, 0.010068946, -0.014925452, 0.00430917, 0.0065069394, 0.0113984635, -0.009560526, 0.004765054, 0.004671902, 0.011480984, -0.011343658, -0.0057688747, -0.007994485, 0.0007175724, 0.009075692, 0.0154369995, -0.004350429, 0.0009881894, -0.008520464, 0.0045196987, -0.01342208, 0.0062933797, 0.008350494, 0.010178063, -0.023628524, 4.87355e-05, 0.0025079937, -4.025639e-05, -0.008166507, 0.006232893, -0.0122316, 0.014209186, -0.011529982, -0.018471, -0.009312681, 0.007961669, -0.010611472, 0.023762573, 0.010223139, -0.0035481115, -0.0062642726, -0.030307956, 0.008145388, 0.010079205, 0.006687945, -0.08712773, -0.0028502347, 0.0069753104, -0.01870846, 0.003796099, 0.010507038, 0.0053498396, -0.012269242, -0.007228268, 0.0062224627, -0.024833811, 0.00027818698, 0.011264603, 0.010926246, -0.009468022, -0.03522096, -0.0019375657, 0.022093136, -0.010612997, 0.008763774, -0.0022377907, 0.005137645, 0.007415309, 0.01312898, -0.013061098, -0.007125873, 0.009752871, -0.026193341, 0.006272659, -0.024071673, 0.0029320717, -0.00037828216, -0.01034524, 0.01930575, 0.0054372633, 0.02484385, 0.005796539, -0.036052477, 0.019487977, -0.017355489, 0.0011895809, 0.017593836, -0.0028100298, 0.005608813, -0.00013984225, -0.00894533, 0.016930645, -0.017239999, 0.02253727, 0.00598017, 0.0032578106, 0.012059607, 0.02371072, 0.005902832, -0.03307631, -0.008769796, 0.023726158, 0.0072071, -0.00088661193, -0.0004816407, 0.0012797917, -0.012329408, 0.042134643, -0.01423445, -0.0034784582, -0.008850483, 0.00671358, 0.0068423287, -0.009733268, 0.0029235608, -0.016772522, 0.008063955, -0.0020948972, 0.0050684395, -0.005408622, 0.022288581, 0.019006217, 0.035994623, 0.00056832307, 0.006124456, 0.0034317044, -0.00031408595, -0.08205662, -0.0228214, -0.012135657, 0.0062672747, 0.0011646862, -0.0073520094, -0.00192844, -0.006560737, -0.013897629, -0.0175093, -0.020113694, 0.017346375, -0.011151523, 0.0029785912, 0.020660143, 0.011367556, 0.0149946315, -0.022766467, -0.001300709, 0.00681642, 0.0013383903, -0.0008574972, 0.008140434, -0.011846749, 0.004191367, 0.005381891, -0.010484118, 0.024182094, -0.0044480423, -0.04162026, -0.010078379, -0.13238992, -0.0069658863, -0.01078328, 0.014640216, 0.0013649227, 0.0109033035, 0.010133985, 0.01537956, -0.0058249426, 0.009381451, 0.00028919152, -0.014058839, -0.018418508, -0.0017307985, 0.016354246, 0.12624672, 0.036166973, 0.0024385941, -0.011388976, -0.0070835887, -0.010326213, 0.0046509407, 0.012548867, -0.010831778, -0.021668095, -0.013773086, 0.001512631, 0.0021108035, 0.009561544, 0.023911783, -0.00023988147, 0.040638022, -0.0076122936, -0.0068538757, -5.8344e-05, -0.0029914798, 0.0064152987, 0.00083410664, 0.0048183617, 0.0046366616, 0.0007333187, 0.018892463, -0.003925981, -0.015042726, -0.02576336, -0.01294749, 0.0072655845, 0.005917501, 0.014512151, -0.0011896329, -0.009615698, -0.06868029, 0.010396184, 0.0028004232, 0.0064894874, 0.023880698, 0.00081235863, 0.018622963, -0.005800167, -0.017870737, 0.017947437, -0.0018278814, 0.0058996305, 0.0063928706, -0.0018749828, -0.006899958, -0.015333906, 0.017519824, 0.005998971, 0.006900513, 0.025379721, 0.024292175, -0.009370025, -0.020049945, 0.0029453505, -0.0055768765, -0.0068252124, -0.00046151443, 0.014368704, -0.015032733, 0.027543973, 0.012202177, 8.112975e-05, -0.032249775, -0.01963905, -0.02763385, -0.00095096324, 0.018334638, 0.022604996, -0.013157599, -0.00013941317, -0.007545059, 0.020868879, -0.029709186, -0.00066751573, -0.021096075, 0.01953953, -0.0047509647, -0.0038997475, 0.020509697, -0.013544403, -0.0036160238, 0.009738365, -0.020118548, -0.0010394221, -0.014670881, 0.005229354, 0.006066527, 0.008084831, -0.0041294484, 0.011329096, 0.005528614, -0.00047189, 0.007680145, 0.018701136, 0.024363201, -0.019034158, -0.0033964983, -0.012220702, -0.004692431, -0.0031972642, 0.0030308175, -0.00759384, 0.009279597, 0.012163897, -0.009809034, -0.0011883343, 0.0036338132, -0.0045436574, -0.0007384655, 0.010034143, -0.005342959, 0.0031585349, 0.002062261, 0.010856623, -0.012445937, -0.006163345, 0.008120285, 0.0012018739, -0.0007820175, 0.021578554, 0.0060571004, -0.014478986, -0.008974449, 0.0055922884, 0.00999658, -0.00460166, 0.0059380597, -0.008355459, 0.0006281168, 0.0047479994, 0.016644245, 0.0033882426, 0.014357825, -0.013444373, 0.004095969, -0.0059455894, -0.011568431, -0.0020476433, 0.004541057, 0.013857669, -0.0012997568, -0.012971506, 0.0015980955, 0.013499513, 0.005999631, -0.0084555, -0.01893152, 0.0041656336, 0.012545623, -0.0024167318, 0.014525117, 0.005515964, 0.0059595117, -0.010445103, 0.008263836, -0.005988959, 0.0068738493, 0.008112628, 0.0064613717, 0.024423389, 0.008291158, -0.015822237, 0.0030098273, 0.017653782, 0.016566603, -0.0056718085, -0.010250613, -0.017238779, -0.007054495, -0.008777307, -0.0085037295, 0.028174661, -0.002468169, 0.0018171747, 0.002757995, -0.013327688, 0.0008214922, 0.00071955816, -0.012110491, -0.0053303293, 0.0016083649, -0.0049143406, 0.0051389206, 0.001383269, 0.010053701, -0.0025331655, 0.0026290992, 0.0070170984, -0.006084164, 0.0077355406, 0.011905113, 0.009857063, -0.0013914491, 0.007991947, -0.0139019545, -0.013181827, 0.002951569, -0.010112294, 0.0017155824, 0.0029040286, 0.004438166, -0.008337886, 0.0024966851, -0.0038797248, 0.008536254, 0.013044139, 0.008551773, -0.005144869, -0.0019640017, -0.003446623, -0.0077462057, 0.0067786193, 0.018276371, -0.008343949, 0.0048730425, 0.015197243, -0.013768551, 0.015842263, -0.003956814, 0.010993323, -0.0054062386, -0.0115796, -0.025894472, 0.0019192874, -0.000401557, 0.0076317075, 0.010981334, -0.004184219, -0.007030261, 0.003676071, 0.0025720538, 0.0071895546, -0.0060441005, -0.013784146, -0.02596189, -0.0052443896, 0.011641076, -0.00089476747, -0.01655537, -0.016873235, -0.0014442638, -0.00040137247, -0.004217634, -0.009697004, -0.00048009402, 0.0015191616, -0.023256656, -0.0030822232, 0.01085395, -0.00023653227, -0.012395064, 0.0016938732, -4.389102e-05, -0.00081943016, 0.007031691, -0.016901195, -0.004048985, 0.0024570343, -0.022843326, 0.004562482, 0.019286906, -0.0085546365, -0.00077583577, 0.009145555, -0.019386247, -0.0026722318, -0.0101649305, -0.003862607, -0.02365942, -0.0053834384, 0.004551403, -0.010095757, 0.013045509, -0.0063127317, 0.03293238, 0.0062471195, -0.012513304, 0.009210856, 0.006063965, -0.0006953556, 0.0050541745, -0.0050376193, -0.005929078, 0.012386655, -0.018966103, 0.00032265263, 0.0017686868, 0.015228381, -0.0011273695, 0.10852235, -0.0065970393, 0.0073920214, 0.004204872, -0.005263982, 0.008841461, -0.004627653, -0.011297399, 0.0077111083, -0.003009532, 0.009530434, 0.02112055, 0.015701728, -0.0076933005, -0.0008795012, -0.0054722046, -0.014620998, 0.0057921703, 0.005960419, -0.01247406, -0.011595418, -0.011267436, 0.014258352, 0.004173568, 0.014630598, 0.00711212, 0.006379664, 0.0032110333, 0.02318947, -0.002524867, -0.0040543703, -0.0011587173, -0.013931901, 0.008400058, -0.022227013, 0.0048927264, 0.012512936, -0.007698991, -0.022937823, 0.010584379, 0.0065709264, -0.00073321833, -0.011566502, 0.0077773887, 0.0033480923, 0.0009809361, -0.007956807, 0.004912196, 0.014993306, 0.017557764, -0.0046632634, -0.0055724564, -0.008056567, -0.009947596, -0.0020952038, -0.00095217925, 0.010177807, 0.0054083453, 0.022363791, -0.00044358542, 0.012616112, -0.0052690078, 0.010454391, 0.0030086255, -0.0012878132, -0.0057290616, -0.0064162505, 0.0016606266, -0.0034322361, -0.0073603685, 0.00024029319, 0.0047326535, 0.013751025, -0.00023234673, 0.03709236, -0.005709207, -0.0005906554, 0.010135407, 0.00051015324, 0.0051531508, 0.006371246, 0.007148423, -0.0017032846, -0.0023674548, -0.030211208, 0.010333344, -0.0088067185, 0.007022057, 0.002764102, 0.021384696, 0.013395947, 0.0023664378, 0.007921582, 0.013052141, -0.013316017, 0.0021915527, 0.10333421, -0.007954378, -0.0071756523, 0.010110315, -0.009651805, -0.008712299, -0.008482758, -0.0072924457, 0.010453034, -0.011283, 0.027568841, -0.010341531, -0.0033094774, -0.0063687195, -0.009451377, -0.006870854, 0.021524899, -0.016808962, -0.01638216, -0.0119770635, 0.022368696, 0.004457902, 0.008026203, -0.0087813875, 0.010257499, -0.006823848, 0.0016767124, 0.020323176, 0.005595511, 0.0056834198, -0.005964765, -0.00021391205, 0.0020696733, 0.00772878, 0.010456447, -0.004394156, -0.0041437745, 0.012609904, -0.004082262, -0.011483591, -8.164101e-05, 0.0023857316, 0.016830573, -0.0049618045, -0.0027947775, -0.0044281674, -0.018423522, 0.0029117512, -0.0057858387, 0.012516971, 0.0032372135, -0.0109623475, -0.008179108, -0.0016345913, 0.008910404, 0.0006604793, -0.003064225, -0.006692611, -0.0005381949, 0.005891861, 0.012744653, 0.00870492, 0.01825226, 0.0023934299, 0.00068898726, -0.007627998, 0.0019366189, 0.0028806957, -0.0037005274, 0.011248742, 0.02696407, 0.00025755158, 0.008156117, 0.008721509, 0.005205186, 0.0013676769, 0.00700197, 0.00772223, -0.012734992, -0.0054255947, -0.0041869436, -0.029672805, 0.01069181, -0.0030627025, 0.0023678567, 0.0051676277, -0.0078079505, -0.02546413, -0.0049537965, -0.0053096055, 0.0057912106, 0.0029976065, 0.011159227, -0.009654128, -0.008303385, -0.0018620272, 0.0083874, -0.018839324, 0.015303553, 0.00902299, 0.0022967455, 0.0020651487, -0.00043992637, 0.005186473, -0.0035196478, 0.015305424, 0.0061481763, -0.010022043, 0.0071187126, -0.015609182, 0.00046875275, -0.0039218157, 0.01402368, 0.0059707426, 0.0049578724, -0.015808217, 0.02167538, 0.0010149787, -0.002607015, 0.010702729, 0.014613712, 0.00053870503, 0.0046918388, -0.0085753715, -0.00038197034, -0.001656972, -0.024010498, 0.016342595, -0.0032591596, -0.009049655, -0.0021047955, -0.027321484, -0.0070576067, -0.012985411, 0.0068026385, 0.0041048, -0.020113561, -0.0027782384, -0.03128514, -0.0031556843, -0.013736272, 0.00031341804, -0.008606425, -0.0064825504, -0.007230583, 0.0012880217, -0.011050278, 0.0067930417, -0.011466948, 0.008468649, 0.0041709444, 0.012615288, -0.004087428, 0.007283637, 0.0009949321, -0.006613796, 0.0030791382, -0.006838211, 0.0150257535, 0.0003506833, -0.008295854, -0.06323289, 0.0026637388, 0.009025295, 0.013004877, 0.0010267422, -0.0060502184, 0.010719734, 0.002052032, 0.008551328, 0.0027486056, 0.010096999, -0.0029415335, 0.0042365645, -0.0032576772, -0.0033764062, -0.010914759, -0.0037251853, 0.0028052346, -0.004664509, -0.006986074, -0.009086746, 0.0009321903, 0.00048499406, 0.010118416, 0.0032304937, -0.0054482818, 0.002723442, 0.0074695847, -0.0033046864, -0.004508095, -0.0033472795, -0.010065984, -0.01242648, 0.0057880473, -0.0015392486, 0.0190329, 0.008038351, -0.00620283, -0.0011357702, -0.008860333, -0.0021623208, -0.01844456, 0.0002212421, 0.011063334, -0.007332712, -0.02772567, 0.011803094, 0.013217541, 0.009097858, -0.0074506607, 0.01897315, -0.011539794, -0.015780995, 0.020802261, -0.021303872, -0.011031279, 0.003998141, 0.011277643, 0.01166203, -0.009929448, 0.012784043, -0.0037053043, 0.0010882635, 0.011477638, -0.0015533139, -0.0061552264, -0.008291905, -0.01304713, 0.00101053, 0.009094819, 0.0002000662, 0.018528843, -0.0094852075, -0.0011434495, -0.001441344, -0.009119995, 0.017975533, -0.00015116847, 0.0072160577, 0.008173639, -0.009521785, -0.012446221, 0.011471109, -0.0099388985, 0.0024098544, 0.008394381, -0.0021477435, -0.008910614, -0.0060414085, 0.0014799589, -0.005630015, -0.004673648, 0.0024314593, -0.009543402, 0.003394421, -0.0013403775, -0.0025102848, 0.003439642, 0.0040303133, 0.0072158743, -0.0034275749, 0.008643182, 0.014867404, 0.025689844, -0.01773355, 0.013454398, 0.0023766127, -0.006925014, 0.0036466415, 0.0060635027, -0.00091687724, 0.003646045, 0.011536055, 0.0063533816, 0.018873658, 0.0047420873, -0.016949568, 0.002722445, 0.0095773805, -0.0066942363, -0.0001100332, -0.010772876, -0.012238115, -0.005584939, 0.018533813, 0.0083128875, -0.017864307, -0.00358416, -0.003109801, -0.0025800231, 0.01806939, 0.014239135, 0.030202866, 0.0076701664, -0.012322938, 0.008919904, 0.0012420372, 0.0073560937, 0.0052632974, -0.007788256, 0.006249171, 0.0031807648, 0.0037008184, -0.00024529017, 0.0049945274, -0.0032755744, -0.00014820579, -0.008090504, 0.0035945342, 0.0061217905, -0.012279631, -0.019108353, 0.005073087, 0.0035956926, -0.00014330527, 0.0127117885, 0.015425339, 0.012376991, -0.004988234, -0.008053918, 0.0010940839, 0.008904858, 0.020601502, -0.0045576645, 0.0064976336, 0.0027749655, -0.005241912, -0.0005452196, 0.009309123, -0.009114589, -0.005014179, 0.006736184, 0.0040617497, -0.0030540808, 0.0029295161, -0.0047526057, 0.01499985, 0.009164848, -0.0016199844, 0.011718279, -0.008923013, -0.0018271919, 0.0015695604, 0.0017887007, 0.007736922, -0.0079220105, -0.010132681, 0.0070021683, 0.00055414723, 0.008706546, 0.013576412, 0.0008627934, 0.0043985783, -0.0030036392, 0.019699052, -0.0024333, 0.0038161227, -0.00909727, 0.010960616, -0.007041241, -0.013880975, 0.007342519, 0.00764752, 0.0024032157, 0.003295883, -0.1132105, -0.011450607, -0.0015795671, -0.007834052, 0.007941813, -0.00026587656, -0.005377929, -0.0058090766, -0.015295839, -0.00035174767, -0.0073247557, -0.0013905776, -0.0006907001, -0.020879809, -0.013205408, -0.0061502974, -0.0064749382, 0.0009251186, -0.0061035217, -0.008031335, 0.008557322, -0.0052812104, 0.00062276877, -0.008552796, -0.003550454, -0.011297866, -0.0032801195, 0.00069597573, 0.016288258, 0.0054334225, -0.0013349383, 0.014238313, 0.0054858634, -0.0056137643, 0.020840187, -0.002446988, -0.018050743, 0.008703075, -0.14649908, 0.00042352919, -0.0020464233, -0.0028620737, 0.0012261184, 0.018291548, -0.0026376355, -0.00024085189, -0.003993837, 0.0003153804, 0.006394464, 0.005152643, -0.0069652013, 0.0008521419, 0.003340518, -0.00037016073, -0.010796305, -0.0044556186, -0.00422371, 0.015100595, -0.0010091099, 0.017887052, 0.004043701, 0.017865576, -0.0029085472, -0.0052503534, 0.004866889, 0.003220592, 0.024293656, 0.0017740541, 0.004630815, 0.0040959143, -0.008144434, -0.0018518118, 0.0002630172, 0.021649733, 0.017208714, -0.00077797065, -0.001909069, -0.010039338, 0.008989066, -0.013269079, 0.013095848, 0.004325439, 0.014712833, -0.00026429168, -0.008672494, -0.0052497922, 3.619066e-05, 0.0028011175, -0.008326368, 0.009950339, -0.009297699, 0.010745094, -0.001405444, -0.015319651, -0.013453065, 0.0064118374, -0.01075331, -0.0050996817, 0.00050987443, 0.0014574162, -0.0042783245, 0.006809053, -0.0023012867, 0.020924456, -0.0016384242, -0.0032932886, -0.0030421452, 0.00076984946, 0.0027184295, 0.021099206, 0.0018594655, -0.008865333, -0.0003142777, 0.029581007, 0.00952983, 0.019412525, -0.00032140635, -0.008990414, 0.0011624207, -0.0132678505, -0.0026930706, 0.008921076, -0.0011496709, -0.0082167, -0.00518357, -0.008103689, -0.009153927, -0.026547961, -0.0020081322, 0.002500721, 0.004224613, 0.007483305, -0.0006708063, -0.0059270514, -0.0030505406, -0.013500392, -0.007452837, 0.007316393, 0.004696284, -0.019649375, 0.02284377, 0.0052881576, -0.010571614, -0.009887914, 0.0070875646, -0.0007994569, -0.018950835, -0.027336601, -0.00433105, -0.0036401364, 0.016323375, 0.011474691, -0.0034770274, 0.014324242, -0.011692526, 0.004739389, -0.022581602, -0.01399244, 0.012687459, -0.007679862, 0.014028497, -0.013099801, -0.024784628, 0.009663542, -0.00482986, 0.009359365, -0.015866669, 0.00726088, -0.009787866, -0.004512235, -0.005399301, -0.0022217408, 0.017473144, -0.010016775, 0.012551457, -0.013010758, 0.005185402, 0.0027136272, 0.0056194053, 0.0022764655, -0.012126467, 0.0018918565, -0.00815426, 0.0071802633, 0.00813588, -0.0008422576, -0.019213514, -0.0032058968, -0.017469218, 0.022292145, 0.0013000207, -0.0015674542, -0.004571937, 0.010469812, 0.011739173, -0.016218625, -0.013849837, -0.005416057, 0.0051296875, 0.0054684198, 0.001525902, 0.0073340377, -0.018034086, -0.0072691496, -0.03531057, -0.0004752263, 0.007740409, -0.0070495117, 0.0077596456, -0.00707552, -0.006462723, -0.0041585034, -0.019509748, -0.016965915, 0.005408287, -0.021205084, -0.011422741, 0.0023677547, -0.033482257, 0.0043269834, -0.0041974885, -0.01093284, -0.0029538283, 0.011952675, -0.012764986, -0.0018016396, 0.0062226057, -0.0038473238, 0.003907019, -0.022963474, -0.0041796686, 0.031773753, -0.0078426255, 0.011349774, -0.009472353, -0.00055456895, -0.0035060204, 0.014229991, -0.0060345307, 0.0030717603, 0.02052113, -0.14522687, -0.00484548, -0.0014720944, -0.014967958, 0.029121937, 0.028654315, -1.6728254e-05, -0.016293475, 0.009676138, -0.014651251, 0.025975022, 0.009128352, 0.0051015355, -0.014438089, 0.033098135, -0.012758477, 0.009364095, -0.012200427, -0.011671655, -0.0010366233, 0.0013689842, -0.0051388526, 0.0036119495, 0.0059600454, -0.008924195, -0.01017617, 0.009511373, -0.014401612, -0.0074841753, 0.016178543, 0.00025385205, 0.0030739882, -0.020986851, 0.021127269, -0.005223156, 0.0046878816, -0.0128641995, -0.0019380987, 0.0006732094, -0.003843154, -0.025439335, -0.0060423496, 0.028234133, 0.026077002, -0.0031660926, -0.004145903, -0.0012686977, 0.007476486, -0.005402293, 0.008249089, -0.0069594365, -0.007921583, -0.007643556, 0.012504293, 0.014243172, -0.01408587, -0.0064563407, -0.004097106, 0.0037107214, 0.015403958, -0.008217485, -0.02310671, -0.007745087, -0.0012526822, 0.02383939, -0.010456939, 0.004048509, 0.15960713, -0.006387762, 0.017105447, -0.008384319, -0.016810702, 0.0052262596, 0.0042364085, -0.0019450817, 0.0060789995, -0.017642338, -0.0051189405, 0.013874605, -0.0014120303, 0.008351726, 0.010983397, 0.00049827155, -0.015633188, 0.0042529367, 0.0029934791, 0.0013555249, -0.01716208, -0.013370146, -0.013716208, -0.026516747, 0.020736432, 0.013663255, 0.007019483, -0.006584795, 0.014985353, 0.0006613909, -0.0062306034, -0.00475118, -0.0075749555, 0.00091658824, -0.007121966, -0.010053001, 0.0029361388, -0.005997528, -0.009403506, 0.026797354, 0.0045511513, 0.03778204, -0.015482683, -0.00032370872, 0.0028499863, -0.001980733, -0.0014689262, 0.029153686, -0.013260484, -0.019481713, -0.025866715, 0.0013269652, -0.014184377, -0.001715898, 0.006084634, -0.028749112, -0.010886078, 0.0028124207, -0.0066801636, -0.00266881, 0.004605766, -0.013414164, -0.010543114, 0.0073078354, -0.008840308, 0.006084353, 0.0039019973, -0.00068117253, 0.005922451, -0.14533015, -0.016710341, -0.03263761, 0.012745239, 0.00027182544, -0.007785814, 0.012933303, 0.008224248, 0.002528524, -0.0055116187, 0.0018811785, 0.0048578447, 0.020274214, 0.016657565, 0.0009166257, 0.0043060496, -0.005186799, 0.009414867, 0.031042153, -0.0064592646, 0.00045539404, 0.010328221, 0.021219887, -0.012896841, 0.0017669579, 0.005786937, -0.019750223, -0.0007032727, -0.0019398744, -0.009655384, -0.021099534, 0.0051645674, -0.012254091, -0.0066547943, -0.0109128365, -0.014446938, -0.023842089, -0.013330547, -0.0052215774, -0.01944244, 0.0032077115, -0.008706346, 0.022036793, -0.0041054124, 0.004268658, -0.0014124791, -0.00054420566, 0.0008420199, 0.014483189, -0.02462611, 0.0022661232, 0.004238507, -0.02212584, -0.010940766, -0.009160378, 0.007392417, 0.006907548, -0.006978511, 0.015094545, -0.0017748147, 0.00083685335, 0.004573746, 0.009839016, 0.015530481, -0.008074673, 0.01016042, -0.003269624, 0.00047534695, -4.1046613e-05, 0.0076778354, 0.0050063883, 7.484576e-05, 0.004115339, -0.0074869883, -0.0034842205, -0.0047795093, -0.012687481, 0.0047620917, 0.0132305985, 0.0032890374, -0.016497603, -0.008910619, -0.00600853, -0.016717792, 0.052187182, -0.022252891, -0.015290374, -0.009754721, -0.0053847576, -0.007975858, 0.007915991, -0.00034954966, 0.010945096, 0.014887257, -0.0027807625, -0.0018843679, -0.0036073846, 0.010712413, 0.004702778, -0.013892268, 0.008858131, 0.009703941, -0.022199906, -0.0009294483, 0.0048781475, -0.014465032, -0.0065873885, 0.013620839, 0.008882532, -0.014797941, -0.02315264, 0.0035629757, -0.007944938, 0.0061624693, 0.0022328356, -0.0059400974, -0.0058145463, 0.02173992, 0.0029683954, -0.0029424026, 0.009977164, 0.0025317192, 0.017379722, -0.008098143, -0.00032959046, -0.00408963, -0.006147621, -0.013198372, 0.018536327, -0.016877646, 0.001418366, 0.005517868, 0.0145011, 0.013512288, 0.020143695, -0.0147362845, 0.012108253, 0.0063225594, 0.020634318, 0.0075556906, -0.014478951, 0.0078929765, -0.0045748064, 0.010434264, -0.005567757, -0.022164723, 0.005967128, 0.015245835, -0.0011556142, -0.0043237493, -0.009800061, -0.0027734388, -0.018720286, -0.009578812, 0.011342881, 0.013736288, -0.0040011015, 0.019140195, 0.019327367, 0.010034457, -0.008303761, -0.007098802, -0.008161295, -0.010975495, 0.0033590675, -0.014047115, -0.0018176135, -0.04712131, -0.00088557706, -0.022374447, -0.005804092, -0.008387622, 0.0030471643, 0.0074298875, -0.009514318, -0.0021364915, -0.0009373849, 0.015600231, 0.0064428323, -0.088082194, 0.0077370647, 0.0044905925, 0.0026597749, 0.019099534, 0.0030934701, -0.0048109656, 0.00034076726, -0.0068058665, -0.01314207, 0.019379111, -0.0025093483, -0.009431241, -0.026827272, -0.006836926, -0.018390696, -0.022000713, 0.005850584, -0.0025003187, 0.0069900723, 0.004442208, -0.004561449, 0.0010091072, 0.006481544, 0.009097732, -0.0075227334, 0.020895071, 0.011779466, 0.02547225, 0.016931256, 0.008913802, -0.013311803, 0.0034993289, 0.009009374, 0.003794047, 0.023439558, -0.003082917, -0.006014101, -0.0016905738, -0.04572624, 0.012048019, 0.0048483643, -0.10628315, -0.0044479542, 0.01705044, 0.009867319, -0.012906053, -0.011389124, -0.0071406467, -0.0028502862, 0.012096619, -0.0018303605, -0.01821742, 0.012867676, 0.013200852, 0.0031069757, 0.027581923, -0.0038204659, -0.0060192803, -0.0049840766, -0.010002556, -0.008087181, 0.0072070244, -0.009536937, 0.0032830157, 0.040829405, 0.001940352, -0.0043666475, -0.012020717, 0.01327645, -0.015163694, 0.00032472276, 0.023178954, -0.028413143, -0.0072811637, -0.01741921, 0.013301311, -0.009151481, -0.006386168, 0.006812658, 0.004663354, -0.010237075, 0.0002882566, 0.043926477, 0.006226564, -0.02459469, -0.008300967, -0.13445835, -0.011449537, -0.01360294, -0.002316698, -0.005207327, 0.011864133, 0.0072310423, 0.14047928, 0.019490905, -0.0010516671, -0.005449794, 0.010202811, 0.0072590327, 0.0067016687, 0.0033976466, 0.008367865, 0.014613922, 0.015929338, -0.010094719, -0.013335418, 0.016026458, -0.012445613, -0.026847914, 0.016913582, 0.024705071, -0.049494717, -0.016271038, -0.024964876, 0.0063772304, 0.0052512693, 0.0058465316, -0.020490052, 0.000777482, -0.01924561, -0.0013904006, 0.0012922605, -0.020259118, -0.005911742, -0.0020993229, -0.005922993, 0.030015573, 0.00027308526, 0.0141761955, -0.0073248823, -0.0014132215, 0.01396724, -0.0055637243, -0.008272773, 0.010122748, -0.01188212, 0.008838438, -0.012715397, 0.007858904, -0.018693028, 0.0041242586, -0.016856816, -0.008931039, -0.0110758785, 0.011936906, -0.006999994, -0.011008074, -0.010209765, -0.0107355155, 0.008387989, -0.007895002, -0.01196691, -0.012440982, -0.018573636, -0.013241796, 0.0037422045, -0.008178915, 0.005989262, 0.023841253, 0.0036754936, 0.012596429, -0.0069636935, -0.00498606, 0.017755086, -0.021056596, 0.010764985, 0.005069399, 0.001619101, -0.0037262696, 0.00092712586, -0.007830519, 0.0052648066, 0.0017562977, 0.0042572194, 0.018175093, 0.0075955577, 0.0015364984, -0.0030773284, 0.014604134, 0.019623194, 0.0050080796, -0.004324196, 0.009640022, 0.0015703059, 0.0077288854, -0.018546999, -0.015941022, -0.033479728, -0.017288776, -0.008899718, -0.0021211375, 0.017160803, 0.019212188, 0.010462251, -0.002413217, 0.0033199093, 0.02811794, -0.0028160687, -0.019162586, -0.016851647, -0.011368404, -0.016107105, 0.006870179, -0.0037541015, 0.0071148905, -0.0025381919, -0.027212702, -0.012119733, 0.006817047, 0.0031755096, -0.0013144377, 0.0045627262, -0.0053958693, -0.0026531613, -0.011630838, 0.012975877, -0.0062166387, 0.016715009, 0.0047254628, 0.014665407, 0.007746173, 0.0048498367, -0.029286366, 0.019708168, 0.01130379, -0.015988324, 0.011932356, -0.01364437, 0.016958512, 0.002848879, 0.005495166, -0.003852408, -0.0013992825, -0.0023857073, -0.025057014, -0.0073909033, -0.010666858, 0.018958876, -0.008346325, 0.00087307463, -0.029444428, 0.0061799693, 0.0022705588, 0.022751587, 0.0020925994, -0.0053833215, 0.00054199714, 0.0141721405, -0.011643909, -0.0055029294, -0.012303825, -0.0032252537, 0.0028755155, -0.021615002, 0.031269975, -0.003423346, 0.00078726123, -0.016600532, -0.0037122602, -0.010074338, -0.0028286704, -0.02013286, 0.0037055332, 0.0054761195, -0.014138022, 0.000116523435, 0.013965427, 0.003482211, 0.00429528, 0.005476304, -0.0060408474, -0.003498169, 0.013316207, -0.021057865, 0.008336313, 0.009208894, -0.01197013, -0.03616457, 0.015237974, -0.014636786, -0.01985011, 0.0030313914, -0.01421656, 0.005723166, -0.010730115, 0.023478916, -0.0048932056, -0.0121876355, -0.0029149556, -0.048710153, -0.0068258992, 0.0072727813, -0.030960208, -0.011758108, -0.016304262, -0.003436134, -0.0031892075, 0.012726658, 0.009504766, -0.010052709, -0.011957072, -0.006584682, -0.0034522503, 0.009905413, 0.011487814, 0.0022003262, 0.022734998, -0.00071194186, -0.0057513434, 0.009483147, 0.008598632, -0.01539975, -0.002152432, 0.0013794381, -0.007557987, 0.011098277, -0.004589748, 0.018996606, 0.012650006, -0.0016129671, -0.0059613828, 0.023516396, -0.009815685, 0.019145224, -0.0032616027, 0.0013568632, 0.007795837, 0.01260974, 0.01721024, 0.0069343285, -0.012441253, 0.001554053, 0.011315368, 0.0069068586, -0.0073361737, -9.677183e-06, 0.00297757, 0.023860851, -0.007811136, -0.021272115, 0.013476857, 1.1395192e-05, -0.020510208, 0.0016175065, 0.00785928, 0.01277782, -0.017133608, 0.0005873182, -0.0014663788, 0.0041075214, 0.0063971225, 0.008038818, 0.00846998, 0.0153711885, -0.0010689753, 0.0143194655, -0.014746734, -0.0015148757, 0.006768694, -0.026669635, -0.0006578941, 0.017775076, -0.02206163, -0.011127443, -0.007823693, 0.024030536, 0.00093143363, 0.009654119, 0.010152854, 0.0005243376, 0.005586514, 0.0039377874, -0.006389009, -0.014216872, 0.022365568, 0.004141276, -0.002781028, -0.022284307, 0.009734575, -0.0026268524, -0.0064771115, 0.014167697, -0.01550572, 0.017105957, -0.0067671384, 0.004923865, -0.012895308, 0.009042602, -0.015826924, -0.00779576, 0.0010488926, 0.010957331, 0.0073524807, -0.02282195, 0.004106338, 0.025811141, 0.011349862, 0.0014588543, -0.0068598203, 0.0035880394, -0.006502692, -0.012868245, 0.001650895, 0.0027910485, -0.020946512, 0.009907347, -0.008362807, -0.004338162, 0.016683644, 0.014336802, -0.001874066, 0.001186371, 0.024398634, -0.0013826477, 0.0061845775, 0.002375911, 0.024305705, -0.013229011, -0.011160459, -0.023852566, 0.0019705177, 0.010111284, 0.0043200757, 0.0019163844, 0.0070113693, -0.004515974, -0.011870334, 0.0064161485, 0.0027713953, -0.020177457, 0.010038708, -0.0049322164, 0.015048684, -0.0029381136, 0.016244605, 0.0033722252, -0.00882889, 0.024957446, 0.0008209427, 0.0049850447, 0.011737392, -0.0040210765, 0.017083142, -0.00073944405, -0.001867008, 0.01218501, 0.012221928, 0.008271406, -0.0012267416, 0.00012375855, -0.008276644, -0.0013751262, -0.015175438, -0.0069213174, -0.02945149, 0.012210977, -0.0015951259, -0.009034106, -0.00050614256, 0.007106431, -0.007722315, 0.0028266252, 0.010039843, -0.010925547, 0.0077098683, 0.01075167, -0.021315116, -0.0039546806, 0.015775606, -0.007617118, -0.015524474, -0.0033447822, 0.0031158554, 0.008858688, 0.005373683, 0.0024960765, 0.008065391, -0.007965391, 0.016389957, 0.010341606, 0.0015910169, 0.015342536, -0.0018835028, -0.009002117, -0.0024568285, 0.0021969546, 0.0020026618, -0.004966744, 0.010652918, 0.0052154986, 0.005139762, -0.0010811408, 0.003645874, -9.042359e-05, 0.0049565774, 0.027181568, -0.021136187, 0.00071422243, 0.0074189845, -0.015040298, -0.017143622, 0.040922724, 0.005855421, 0.003989484, -0.005613881, -0.0017215215, -0.0146218, -0.004294399, -0.0035653163, 0.018654216, -0.005274892, -0.009204611, -0.017974388, -0.00819635, -0.0074376855, 0.026305627, -0.0020794973, -0.0028996356, 0.005352652, 0.017622337, 0.003559277, 0.008572517, -0.010396407, 0.0035654702, 0.00084537914, 0.009824092, 0.01733092, -0.0062260865, 0.013496054, -0.009031774, -0.001732649, 0.004364489, -0.034788903, 0.010749989, 0.01674434, -0.0046223723, 0.025728418, -0.0093989875, -0.01249864, -0.0032321129, -0.002126882, -0.011155753, -0.013319794, -5.235248e-06, 0.012446302, -0.0067673638, -0.013845786, 0.0018489123, 0.0024204152, 0.019256733, -0.0057005454, -0.0033195273, 0.00034734452, 0.008552061, -0.00080887903, 0.009640652, -0.054371707, -0.030803077, -0.033809792, -0.016563827, -0.010440517, -0.017690243, 0.0006054471, 0.0014190288, 0.025501875, -0.06426982, 0.004000654, 0.0055703586, 0.017002594, 0.020159975, 0.0032946824, -6.027982e-05, -0.031284567, -0.001055516, 0.0060777417, -0.03425192, 0.0030769035, 0.0049611027, -0.006781435, -0.010356601, 0.0087594185, -0.0017387215, 0.0010839521, -0.00088999525, -0.00040464845, -0.0048094844, -0.0004972004, -0.012850471, -0.0088800825, -0.0042273942, 0.015416634, -0.010373433, -0.0003262102, 0.007764501, 0.009622124, -0.0075249346, -0.022998683, 0.0054241307, 0.012566848, -0.011910813, 0.014874878, 0.006361818, 0.0013773199, -0.0006054056, 0.01203687, 0.0058373, -0.0049579735, -0.002864954, -0.00325936, -0.0010066418, -0.0009514965, -0.010671118, -0.008445874, 0.0036903357, -0.0053944783, 0.0056899562, 0.006776567, -0.01227781, 0.00052676286, -0.0047505656, -0.006227996, -0.001115136, 0.00022409605, -0.008044816, 0.006951512, -0.022023497, -0.022229416, -0.011288558, -0.006184099, -0.015029054, 0.014801005, 0.011314399, -0.0074891397, 0.009818004, -0.018649856, 0.00072911324, -0.013885662, 0.013818244, -0.02180744, -0.013353122, 0.021373978, -0.0059972615, 0.005448512, -0.0052970657, 0.007612455, 0.009221534, 0.009555188, -0.010638828, -0.017210055, 4.84573e-05, 0.0012080629, 0.008101924, -0.013362096, -0.023488712, -0.010210713, 0.0074534314, -0.0063799717, -0.0064546335, -0.0045329514, -0.012306861, -0.0064557455, 0.0060713086, -0.0025031636, -0.013475726, 0.009609134, 0.0006591153, -0.004860469, -0.014601402, -0.020493554, -0.01085557, -0.00064204214, 0.010980381, 0.01410931, 0.016649239, 0.0054711476, 0.007670918, -0.0058583925, -0.011923359, 0.010591189, -0.0038499995, 0.0019101741, -0.008008082, -0.01749982, 0.01710305, 0.00815812, -0.019268826, -0.0030629658, 0.006844183, 0.008465403, -0.010428565, -0.003494307, -0.003394441, -0.0010091895, 0.016044335, 0.011388927, -0.011987382, 0.012984031, 0.056342963, 0.0058227843, -0.012853501, 0.007286408, -0.012223966, 0.00016795006, -0.0011186446, -0.0010553292, -0.0038754432, -0.0068216743, 0.0020234962, -0.012293278, 0.008857126, 0.022183672, 0.009875139, -0.008074708, 0.0007870311, -0.011765023, -0.024606727, 0.0058205966, 0.01616379, 0.0015480634, -0.004907547, -0.008772223, 0.011680951, 0.016595121, -0.010645394, -0.0010667917, -0.004752826, -0.0032701038, -0.007975834, -0.0034467054, 0.00075837784, -0.002492175, -0.007402926, 0.0024468831, 0.005423251, -0.008616214, -0.0005552259, -0.01133873, -0.0007028425, -0.001940935, -0.01889093, 0.009018843, 0.013127434, -0.017044704, -0.006047463, 0.02824177, -0.010825773, -0.007254411, 0.003013742, 0.01058577, 0.019377077, 0.005959982, 0.00064093823, 0.011839711, 0.0011543517, 0.009888654, -0.018364964, 0.008974388, -0.018522212, -0.011295154, -0.0039876266, 0.0005787272, 0.0053040218, -0.0027589865, -0.0028927408, 0.0083944835, 0.01861488, -0.012961627, 0.031753562, 0.0054571, -0.0041520167, -0.013899627, 0.0047222315, 0.20105131, 0.14114794, -0.0021858474, -0.0058011073, -0.003897722, 0.02266232, -0.033713415, 0.0064812973, 0.023584772, -0.014244101, -0.0038845309, 0.00025414626, -0.022628214, 0.00559132, 0.023854097, 0.0118129, -0.0054428065, -0.0058548735, -0.0059051993, 0.01382087, -0.030204201, 0.0065316465, 0.0094154505, 0.004275206, -0.01370133, 0.011075197, 0.012315199, 0.0033786588, 0.02662863, 0.01341472, -0.013936379, 0.01549693, 0.021633092, -0.0031420933, 0.002985069, 0.009052972, -0.020112783, -0.031582866, 0.002280578, -0.008938114, -0.0038872678, 0.00042054037, 0.0056333826, 0.0060769795, 0.008420596, -0.006831916, 0.00821843, 0.0019158379, 0.0034354583, 0.019172953, 0.008087249, 0.008876366, 0.0024738845, 0.0023638615, -0.0026852044, 0.010566188, 0.014128873, -0.014171861, -0.0061185095, 0.01835445, 0.014496192, 0.0077236085, 0.009071891, -0.0141876675, -0.006785183, 0.013628949, 0.0014895655, -0.0025842825, 0.0060816747, 0.014868103, 0.01163192, 0.0073308977, -0.0041814973, -0.0070791305, -0.00888739, 0.018025089, 0.0059721484, -0.01144105, -0.00073275185, 0.0066195442, -0.014715789, -0.010789897, 0.010847137, 0.011178025, -0.013706782, 0.024986595, 0.00020065396, 0.0037425368, 0.11481213, -0.0124746, 0.012197085, -0.02062861, 0.015491295, 0.010980024, -0.006300239, 0.044580292, 0.009714199, 0.0037064734, 0.025039447, 0.009450168, 0.002581927, -0.014266169, 0.014717255, -0.0025130939, 0.015688619, 0.06406228, -6.0117378e-05, 0.0069372673, 0.005929814, 0.02122869, -0.004108571, -0.0017605359, 0.008390221, 0.014164968, 0.021945398, 0.01620966, -0.010113699, 0.017883355, -0.11060174, -0.0066272607, -0.00032095084, -0.0060879784, -0.006824253, 0.00729865, -0.01973715, 0.004453611, 0.008387935, -0.0028899156, -0.0027218703, -0.0043668565, 0.021464821, -0.006902562, -0.0027815662, -0.0037703796, 0.0011186403, -0.0072240457, 0.008470168, -0.0034267406, 0.015766054, -0.023785695, -0.004295011, 0.017417401, 0.010351835, -0.0016573688, -0.0061396337, -0.0006208183, 0.007781284, 0.008316983, -0.02257763, 0.0061323917, 0.009441728, 0.01700396, -0.002872143, -0.0034479059, 0.018488724, 0.025289511, 0.008971589, -0.029335432, 0.0023372455, -0.0044543347, -0.0072710738, -0.018924443, 0.003098246, -0.006548448, -0.00061204913, -0.010908086, -0.008725028, 0.00139958, 0.024202101, 0.007873874, 0.007992913, 0.0014181244, 0.028740212, 0.023247875, -0.007500479, -0.022490583, 0.008353087, 0.0030266605, -0.0011331438, 0.031000689, -0.009425341, -0.0005774716, -0.0075489916, -0.01695577, -0.005887028, 0.011765027, -0.0036184434, -0.00571737, 0.00968151, 0.017296629, 0.010442931, -0.0012433701, -0.014075573, -0.0029407456, -0.007551232, 0.015183873, 0.0023393831, 0.004482581, 0.010503483, -0.02147486, -0.010252623, 0.12173035, 0.014511246, -0.0025130527, -0.030774297, -0.0056193373, -0.004798535, 0.0027115077, -0.017617362, -0.017303735, -0.008285705, 0.014860111, -0.004054103, -0.023307318, -0.009951344, -0.0021966342, 0.0010390191, 0.0020029885, 0.02837242, -0.0104331225, -0.0113101, 0.010416519, 0.0023020345, 0.017102243, 0.0114699975, -0.014828939, -0.013494741, -0.010739626, 0.0043730317, -0.0010920912, 0.00046784937, -0.0006695403, -0.009634277, -0.013501747, -0.03822457, 0.0048748977, 0.00022805895, -0.0064427815, 0.00451251, 0.0024360737, -0.010672249, 0.01822223, -0.02651216, 0.017312804, 0.01718677, -0.026609188, 0.21165107, -0.0102750445, 0.005174364, -0.0076223607, -0.0095482655, -0.020293519, -0.013716342, 0.010906324, 0.0091829, 0.010094447, 0.0038329717, -0.0020400768, 0.009561551, -0.019056031, -0.025151549, -0.010040018, -0.008487913, 0.0113330055, 0.0036873962, 0.02933136, -0.0017131909, -0.002054878, -0.02978478, -0.011551555, -0.03405481, 0.03251846, 0.012143056, 0.010693073, -0.0039312746, 0.013221611, 0.0016619945, -0.015084599, 0.004467559, 6.36541e-05, 0.019895786, 0.0073371623, 0.024303583, -0.0030595013, 0.009922201, -0.012400923, -0.003277554, 0.013591559, -0.015232653, 0.008238469, -0.010459796, -0.0029977583, -0.002057014, 0.0046332455, 0.0024339806, -0.009235617, -0.014453203, 0.00030405156, -0.017405966, -0.004528244, -0.0115094, -0.0037281648, -0.010716285, 0.0040489426, -0.0010268909, -0.0021147204, -0.015705127, -0.0007545687, -0.012657343, -0.01349598, 0.0013321086, -0.0021306544, -0.021677047]
        )

        ruta_imagen = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'ParroquiaSanGonzalo.jpg')
        
        if os.path.exists(ruta_imagen):
            with open(ruta_imagen, 'rb') as f:
                comunicado_1.imagen_portada.save('ParroquiaSanGonzalo.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Comunicado 1.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen}'))

        comunicado_1.save()

        comunicado_1.areas_interes.set([9])

        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Comunicado 1 asociado al área ID 9.'))


        # =========================================================================
        # POBLADO DE COMUNICADO 2
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Comunicado 2...")

        contenido_comunicado_2 = (
            "La junta de gobierno comunica a los hermanos que el traslado de los pasos a la Parroquia "
            "tendrá lugar en la mañana del jueves santo, 17 de abril de 2025 a las 08:00 horas de la mañana.\n\n"
            "TODOS los hermanos que deseen acompañar a nuestros sagrados titulares, deberán estar en la SMPI "
            "Catedral de Sevilla a las 07:00 horas de la mañana, accediendo por la Puerta del Perdón (Patio de los Naranjos).\n\n"
            "Los hermanos ocuparán su puesto en la cofradía y tendrán que presentar su papeleta de sitio de la "
            "estación de penitencia de 2025.\n\n"
            "Los hermanos penitentes y los hermanos que portaron bocinas, podrán incorporarse al cortejo portando cirio.\n\n"
            "Los hermanos que porten insignias deberán estar a las 06:45 horas de la mañana, accediendo por la "
            "Puerta del Perdón (Patio de los Naranjos).\n\n"
            "Hermanos mayores de 14 años: traje oscuro y corbata.\n"
            "Hermanas mayores de 14 años: traje oscuro."
        )

        comunicado_2 = Comunicado(
            titulo="Comunicado de la junta de gobierno",
            contenido=contenido_comunicado_2,
            fecha_emision=make_aware(datetime(2025, 4, 15, 10, 0)),
            tipo_comunicacion='GENERAL',
            autor_id=29,
            embedding=[-0.013441678, 0.007076689, 0.028392086, -0.04846377, -0.0059736236, 0.023486024, -0.007363567, 0.024129685, -0.0057368767, 0.004391209, -0.012576682, -0.024881437, -0.02424166, 0.0026685686, 0.1386111, -0.0008467496, -0.010511302, 0.016972445, 0.0023764006, -0.017054658, 0.024603484, -0.012846889, -0.006811523, -0.011571005, -0.023001814, 0.0148908, 0.015917048, 0.00043429545, 0.05109251, -0.018982539, -0.0105464775, 0.0041017486, -0.020419901, -0.0060416106, -0.011134309, 0.011494374, -0.019238656, 0.011195022, -0.0033849664, -0.0037158364, -0.008717413, 0.027704053, -0.020490173, -0.01101882, 0.010797119, -0.010515318, 0.0007017061, -0.04046342, -0.0038226333, 0.0077164136, -0.0024294287, 0.0026004352, -0.020537967, -0.18307126, -0.011104893, 0.009748299, 0.001493126, 0.005404223, -0.024984257, -0.010184733, -0.006941054, 0.028960483, -0.007536827, -0.004440308, 0.009799549, -0.014890002, -0.013879132, 0.026605448, -0.017206127, 0.0143583445, 0.021179952, -0.006881346, -0.008749662, 0.016046787, -0.0014558388, -0.02195432, -0.0018300521, 0.010581946, -0.024565134, 0.04419114, -0.0008778452, -0.01383496, -0.0058596274, -0.022986636, -0.02288364, -0.0016262493, 0.001975947, -0.017880213, -0.0033361271, 0.0023666692, -0.0065491195, 0.04583426, 0.0072920006, -0.018537251, 0.0054973345, 0.00906736, 0.013457647, -0.013958181, -0.00998318, -0.026864273, -0.019310063, -0.02322203, -0.015642848, -0.006875559, 0.030511092, -0.04002847, 0.014256594, -0.014539754, -0.007707915, -0.02701932, -0.013186103, -0.0019062033, -0.005218602, -0.0015054474, 0.014938478, -0.18626577, -0.022603158, 0.0065671722, -0.024022693, -0.033724405, 0.016959429, -0.012893025, -0.0051892763, 0.022093043, 0.0061340267, 0.0052045616, 0.00978969, 0.0017272644, -0.025509486, -0.018399898, 0.010501108, -0.0053353747, -0.0006934897, 0.009551519, -0.029700004, 0.014225088, -0.0143025685, -0.016368583, 0.007950987, 0.013317209, 0.009040221, 0.014633889, 0.0042793727, 0.01604579, -0.001292117, -0.0005377699, 0.023087857, 0.016879762, -0.0023676571, -0.004415473, -0.002850532, 0.0015900321, 0.01243852, -0.0023008431, -0.009708137, -0.038452838, 0.017768966, 0.022526504, -0.007210974, 0.018694256, -0.035134934, -0.0019315089, -0.015692394, 0.01132125, 0.0017221933, 0.0057004695, -0.009350263, -0.0036703115, -0.01837698, -0.0044059046, -0.015926102, -0.016588688, -0.024419926, -0.013627874, -0.01529934, -0.0049376003, -0.015836487, -0.024720278, 0.011835879, 0.0021051615, -0.0039461977, -0.006144996, -0.013975442, -0.0070593297, 0.0037334885, -0.0036152625, -0.0033240982, -0.008267342, -0.014681613, -0.0054568998, -0.0025272786, -0.0068589835, 0.005529195, -0.007983432, 0.013934149, 0.02932949, -0.0046676053, -0.010505445, 0.009131666, -0.014347511, 0.017175976, -0.0013736393, 0.01205619, -0.014399586, -0.009604573, -0.0014153878, -0.021701721, -0.0024108565, -0.0006355982, 0.02581201, -0.0031918825, -0.017480858, 0.009739433, -0.044306353, 0.007927658, -0.006558054, 0.0074831657, 0.012034908, -0.024650887, -0.022045031, 0.010537829, 0.002904822, -0.02022526, 0.019179044, -0.001933841, -0.0041894666, 0.0008280967, -0.006606956, -0.00031924425, 0.01288403, 0.021595787, 0.004773861, 0.016690727, 0.035917856, 0.01689726, -0.0029387404, -0.0036977907, 0.005417227, 0.025073335, 0.013114858, 0.00896171, -0.017714284, -0.01578666, 0.0008591828, 0.0087758545, 0.013643626, 0.005022876, -0.0018244563, -0.0033363877, -0.0045120143, 0.0047334223, 0.016747383, -0.0134939365, 0.013963314, -0.03827516, 0.0116349375, -0.014615041, 0.0057578166, -0.010139802, -0.032556392, -0.017340193, 0.0021774862, -0.0027029773, -0.0018496875, -0.003434343, 0.009353169, 0.0056718593, 0.016364675, -0.029567739, -0.00209442, 0.025858967, 0.01259824, -0.021654792, -0.0117315035, -0.00042508735, 0.0010307406, -0.13572906, 0.02360039, 0.00040031484, -0.026107704, 0.004607193, -0.0076911757, 0.00302294, -0.014948662, -0.002830668, -0.021752216, -0.009053864, -0.025366593, 0.0026093957, -0.01869329, 0.004077498, 0.0028889868, 0.030728752, 0.0063941474, 0.024618484, -0.035184998, 0.022629546, 0.009192804, -0.017049214, -0.010759685, 0.013498951, -0.0075128493, -0.0007897458, 0.045648333, 0.013263107, -0.011286272, 0.013696993, -4.270045e-05, -0.00081641297, 0.002028386, 0.0046059494, -0.0031530797, 0.014519057, -0.019804996, -0.01724001, 0.01949583, 0.02500822, -0.029060422, 0.00692786, 0.026811983, -0.021462146, -0.02075612, -0.013734543, 0.0013274481, -0.009533207, 0.017396528, -0.022320066, 0.0036112587, 0.005505536, 0.008182048, 0.012993893, 0.007792791, 0.013680982, 0.0017077219, -0.013859882, -0.0005366354, 0.00038302736, 0.01349456, -0.0022599997, 0.019295184, 0.00058425096, -0.0035344358, 0.00402916, -0.024830248, -0.01829412, 0.031524535, 0.00039653835, -0.0408244, 0.010600159, -0.038204633, 0.011115202, -0.014165751, -0.0020249588, 0.012978872, 0.0022071842, 0.00031776345, -0.022463912, -0.0057710703, -0.010880636, 0.030307349, 0.00920652, -0.013050527, -0.0073088645, 0.008661167, -0.006719345, -0.011547798, -0.017631333, 0.004926138, 0.007928596, 0.0015751771, -0.0048769745, 0.0019251028, -0.004419341, 0.0043930337, -0.004093938, 0.019384252, -0.017285492, 0.016283773, 0.009177545, 0.009842811, -0.010905952, 0.0171202, -0.014640788, 0.0073100217, -0.009811636, 0.018680707, -0.025999567, 0.0017331536, 0.027029729, -0.00405058, 0.00842277, -0.0020376977, -0.0068053207, -0.0051844367, -0.025233774, 0.010553032, 0.010839382, -0.025193304, -0.010374352, 0.009597198, -0.006972393, 0.009341218, -0.010978125, -0.01753404, 0.0010789395, -0.007907791, -0.014053364, 0.0062730107, 0.0067942385, -0.0008291929, 0.013584955, 0.0090648765, 0.0143215405, 0.017491346, 0.048959114, -0.011310785, 0.023208044, 0.0008050954, 0.026101716, 0.024430435, 0.010103294, 0.0056511965, -0.020577963, 0.0017973835, 0.0055458616, -0.023120804, -0.027020155, -0.010077182, -0.009222163, -0.0110075185, -0.00414024, -0.018533451, -0.016170884, -0.0072964034, -0.012933238, -0.024172027, -0.007549461, 0.0019541187, -0.010154717, 0.010427458, 0.0034432125, -0.0058835247, 0.0051981094, -0.0071733454, 0.015296753, 0.029000478, -0.007820295, -0.0017669294, 0.019635113, -0.000196555, 0.011803713, -0.01573753, 0.01528979, 0.0020991836, -0.004741807, 0.016005935, -0.013112713, -0.004097453, -9.794222e-05, 0.013316021, -0.001797054, -0.01860023, 0.015324013, 0.0018696996, -0.010290476, 0.010995324, -0.004869843, -0.0023730765, 0.015602097, 0.022607444, 0.0026405104, 0.0120513225, -0.011070418, 0.010825506, -0.0015111067, 0.0077324635, 0.0024635384, -0.013180462, 0.015964005, 0.0025891818, -0.0068984753, -0.003749011, -0.011712184, -0.01726948, -0.0176685, -0.0033399162, 0.01719795, 0.030044409, 0.004024318, 0.007388232, 0.042025752, 0.015050148, -0.019202966, 0.0088072205, -0.031338047, 0.010350226, -0.008002128, 0.009913024, 0.036231488, -9.3185074e-05, 0.018155748, 0.010344967, -0.0064738216, -0.007947055, -0.016996179, 0.0060828687, -0.011759246, 0.019672448, 0.001999004, -0.009509241, 0.011136196, -0.006780788, -0.0076850923, 0.0028828527, 0.012977179, 0.0018551315, 0.002875171, 0.0051654237, -0.012267667, 0.006216999, -0.0065777507, 0.013668836, 0.014162507, -0.0024956055, -0.028923128, 0.005518409, 0.0035098612, 0.00055538, -0.0034526058, -0.0016275956, -0.020126019, 0.023792436, -0.0022069947, -0.008381745, -0.0044293297, 0.009579902, 0.00011834545, -0.0029311732, 0.0005736948, 0.008962033, -0.007773634, -0.00865915, 0.003100906, -0.0018251262, 0.0033132737, -0.109698884, -0.011578196, 0.01084654, -0.0062278532, -0.019070892, 0.0019094204, 0.0069543007, -0.01051208, -0.009841349, 0.006109167, -0.018972237, -0.008855775, 0.0097338185, 0.012569188, -0.008091446, -0.021789493, -0.015427558, 0.011449739, 0.006331861, 0.00602654, -0.0127178645, 0.0139802415, -0.0048638973, 0.009110578, -0.002365485, 0.0065172394, 0.006953905, -0.0053188098, -0.0019860137, -0.011914857, 0.006051577, 0.0010820763, 0.0034053482, 0.021805417, 0.020368738, 0.029145982, 0.0015103628, -0.019739004, 0.0014451806, -0.0010466011, 0.0046770433, 0.0059191687, -0.013693177, 0.0057885214, 0.006017904, -0.029211855, 0.003830758, -0.008840184, 0.010238547, 0.00047885833, -0.016105592, 0.0060086492, 0.016476125, -0.006016128, -0.029687122, -0.013525618, 0.013702078, 0.026901225, -0.0054716584, 0.009065239, -0.008827149, -0.00045944317, 0.032795243, 0.010324898, -0.006828547, -0.011830565, -0.010940918, -0.0037023085, -0.023231145, 0.017624417, -0.0014417749, -0.019320572, -0.008412115, 0.015967349, -0.009982234, 0.0021797204, -0.00716579, 0.014657046, 0.015040877, 0.0079006, 0.017440433, 0.0208939, -0.08533372, -0.024751887, -0.0041964813, 0.013292089, 0.014329894, 0.0040791407, -0.018985838, -0.0057785814, 0.010866438, -0.009346847, -0.018209867, 0.022666, -0.008914858, 0.013660189, -0.0075263474, -0.0023961808, 0.01678239, -0.0075367987, -0.0011700041, 0.0021884996, 0.0018083327, -0.015087829, -0.0016040201, -0.0075600026, 0.0058382144, -0.0060810535, -0.011847566, 0.019060746, 0.019789997, -0.029676342, -0.0040902807, -0.12506895, 0.0058569466, -0.00078302034, 0.031651497, 0.01827906, -0.0039974973, 0.015203974, 0.00037581497, 0.002740149, -0.0008192191, -0.008190938, 0.005758373, -0.024901256, -0.00021515036, 0.002821615, 0.13316649, 0.0047747595, -0.0007701495, 0.020526035, -0.011994524, -0.013311296, -0.011488573, 0.02728476, -0.00036235256, -0.00023598979, -0.006703598, 0.011804015, -0.006598826, 0.010367912, 0.023692213, 0.010324327, 0.021602636, -0.0013112692, 0.0034876675, -0.009182722, 0.011665051, 0.018045288, -0.0025123823, -0.006851943, 0.007921913, -0.020710904, 0.03284287, -0.013820948, -0.02759299, -0.011376763, -0.0027361752, 0.0314079, 0.0028108943, 0.010741567, -0.00982777, -0.011584017, -0.053909775, 0.008840167, 0.00036286112, 0.015664905, 0.024824336, -0.017029436, 0.003250431, -0.0018966243, -0.007089126, 0.012706677, 0.0046617887, 0.01095725, 0.015771223, -0.0011369576, -0.00703642, -0.0052445373, 0.008904331, 0.014815839, 4.0312098e-06, -0.002344864, 0.0377162, -0.022200827, -0.034012172, -0.015492438, -0.0077224867, -0.010672548, 0.010434328, 0.019764418, -0.007056655, 0.021984773, 0.018041845, 0.005518651, -0.010549835, -0.054405853, -0.015192423, -0.008477343, 0.008639919, 0.008116721, -0.016668746, -0.00647653, -0.014670745, 0.0028809074, -0.009674942, 0.0051548085, -0.0031404481, 0.022472616, 0.016511127, -0.00388479, -0.0003812471, -0.005376252, 0.0041643665, -0.009813393, -0.014680317, -0.009476156, -0.007986832, -0.0051425584, -0.028527359, 0.00064527954, -0.02825513, 0.012073987, -0.0073153498, -0.012244067, 0.0275826, 0.017336905, 0.023538645, -0.0023538603, 0.0055215172, -0.0043437923, -0.012330598, -0.008193171, 0.004643277, -0.007696769, 0.0062308717, 0.014180084, -0.0050672106, -0.0112666655, -0.0053334716, -0.0053021554, -0.00222555, 0.011989625, -0.0056723845, -0.0039039727, 0.0066433987, 0.014189666, -0.014206238, -0.016634535, 0.003841135, -0.0043727336, -0.015816035, 0.01754381, -0.0019755447, -0.006409671, -0.0081179645, -0.005593937, -0.013057441, -0.008690549, 0.008299527, -0.00821031, -0.0090592075, 0.005884508, 0.005961746, -0.0034314173, 0.008439029, -0.008157639, 0.0015685573, 0.003994318, -0.009922368, 0.020300712, 0.009673917, 0.010841367, 0.0027215732, 0.0006891232, -0.0015436548, 0.0062657213, 0.005607569, -0.013024424, -0.022245876, 0.006292014, 0.018759146, -0.007232272, 0.0034395014, -0.011517953, -0.0018941064, 0.002706726, 0.00824189, -0.014167407, -0.0020966853, -0.00022089148, 0.022692155, 0.017105756, 0.011817303, 0.0021523873, 0.013263134, 0.023878446, 0.01033198, -0.009291463, -0.0017833448, -0.0051762844, -0.010726697, -0.0042091496, -0.010218609, 0.035759274, -0.0023053803, -0.016699139, 0.0042026658, -0.005660465, 0.00884921, -0.008629509, 0.0030536188, -0.0033800476, -0.0026420122, 0.006344486, 0.01831402, -0.0017296972, 0.01702712, 0.0024904076, 0.015611005, 0.0004499108, 0.012046673, 0.002549719, 0.01207972, 0.0035787034, -0.0046513025, 0.009044387, -0.01941455, -0.0038912375, -0.0018227306, -0.004497547, -0.005987776, 0.005712842, 0.0039868793, 0.008336918, -0.0065355888, -2.667981e-05, 0.011447001, 0.010139741, 0.017196689, -0.0065318374, 0.0050586467, 0.0029069565, 0.0011411856, 0.0058102827, 0.011761563, -0.007951998, -0.002875682, 0.0018452911, 0.0003920269, 0.010083796, -0.0026486518, 0.00822545, -0.0025518113, -0.006016743, 0.0017574695, -0.00014158415, -0.014029347, 0.005843643, 0.007125864, -0.0119594, -0.008718696, -0.002726079, 0.00531699, 0.005509819, -0.008176654, 0.017061302, -0.009847573, 0.0015526192, 0.023892596, 0.014501158, -0.010892247, -0.021133551, -0.0061855195, -0.005060589, -0.006953426, -0.005059537, -0.013496541, 0.005889607, -0.022951677, 0.004770626, 0.018390262, -0.00649985, -0.014966291, 0.009995113, -0.00020533464, 0.0030225755, 0.0015513375, -0.011525565, 0.0032730743, 0.0046434132, -0.017167479, 0.010154334, 0.02270455, 0.005835175, -0.0068714507, 0.002274998, -0.008600837, 0.006823721, 0.011550294, 0.011803049, -0.018278247, -0.0033649537, 0.0055966265, 0.0060871188, 0.016124185, -0.017613845, 0.011364278, 0.012122779, -0.0045444737, 0.0020867917, -0.0048320955, -0.0062145055, 0.00084392837, -0.005925631, -0.0004920229, 0.008927981, -0.029372524, 0.0031723848, 0.006797071, 0.016142843, -0.019380417, 0.1059316, -0.007134768, -0.0017885419, -0.0005360493, -0.009308954, 0.02257887, 0.005009657, -0.003594754, 0.017721621, 0.0009811722, 0.0047224863, 0.021765629, -0.0024301137, -0.003668655, 0.012081021, 0.004618417, -0.009283775, -0.0018006392, -0.0014547305, -0.013243002, 0.0038214133, -0.0060940385, 0.0075225495, -0.009079833, -0.0018687539, 0.0046937186, 0.005460495, 0.0071124514, 0.011189641, -0.0029498744, -0.011260407, 0.0023145417, -0.003360267, 0.010750935, -0.0142091615, -0.007911116, 0.0032602572, -0.0036203938, -0.011583047, 0.015499419, 0.010944726, -0.012535776, -0.012998671, 0.008482727, -0.010702421, -0.003956681, -0.010058566, 0.0056938655, 0.008352478, 0.010819502, -0.0012506095, -0.004989855, 0.006824311, -0.011776692, -0.0032593638, 0.005061646, 0.009582547, 0.0041293628, 0.020505419, -0.008300408, 0.001338848, -0.012338261, -0.005025505, -0.0049434532, -0.0043739523, -0.019817473, -0.001187615, 0.0068745855, -0.00794676, -0.010472449, 0.0030862559, 0.002467817, 0.016648406, 0.0007586438, 0.03452411, -0.005735916, -0.003444501, 0.003758697, -0.0056572934, -0.0008125088, 0.010847754, 0.011729839, -0.006327647, -0.0017957435, -0.016153751, 0.006028586, 0.00039062861, -0.015531178, 0.010653856, 0.014204958, 0.01677259, 0.0070234886, -0.00755414, 0.003788888, 0.005439819, 0.0032280427, 0.109480835, -0.008079197, -0.00473294, 0.013359042, -0.013255924, -0.0025868714, -0.010090264, -0.013439441, 0.004420236, -0.008104734, 0.022346912, 0.0064251386, 0.0009177456, -0.0076201614, -0.011438914, 0.007326714, 0.017964976, -0.015951717, -0.012565892, -0.004844988, 0.025204467, 0.0023844005, -0.0025352128, -0.00805406, 0.0027796854, 2.1286129e-05, 0.005027795, 0.011974861, -0.0128580285, 5.8289173e-05, -0.0077541866, 0.003942938, -0.007267551, 0.004451785, -0.013415071, 0.0039178, -0.00582618, 0.006804219, 0.00681557, 0.003147169, 0.0032581387, 0.004172527, 0.019214137, -0.0034582645, -0.009989871, -0.008104416, -0.016750498, 0.0015284333, -0.013331874, 0.0066363164, -0.0060876445, -0.010852128, 0.014842003, -0.0012164494, 0.006453883, -0.0029972454, -0.01265983, -0.015153793, 0.0051120203, 0.017269501, 0.01756396, 0.0040728813, 0.022026509, 0.0006549766, -0.0058776014, -0.00017916005, -1.6797036e-05, -0.00020400505, -0.006287998, 0.00674799, 0.012215518, 0.006637113, 0.0017330458, 0.0049301577, 0.010835593, -0.00051489286, -0.010019839, -0.0036168962, -0.0118460255, -0.0022933413, -0.0011544643, -0.02065788, 0.0057819025, -0.0131212035, -0.0019401044, 0.007707707, -0.009324473, -0.022972181, -0.0034290464, -0.0052891904, 0.0020084323, 0.014597667, 0.004790574, -0.0140656885, -0.00615858, -0.011724867, 0.010537227, -0.017100135, -0.00015478, 0.0059306305, -0.003304732, 0.013200462, 0.004770571, -0.0012142883, -0.0016420727, 0.016353184, 0.0064337566, -0.014526535, 0.012221518, -0.0026415666, 0.013032116, -0.0020724796, 0.0032916858, -0.006922408, 0.008879202, -0.026959492, 0.010999577, 0.00048609867, -0.01233641, 0.018618062, 0.014211263, -0.008442861, -0.0034569306, -0.012049283, -0.0038078586, -0.0013649398, -0.029780375, 0.00822487, 0.008709305, -0.008926396, -0.000425757, -0.015803652, 0.0013300609, -0.0047471044, -0.0017532199, 0.013009823, -0.017806375, -0.002348647, -0.027398402, -0.00626446, -0.009652075, -0.0021893734, -0.0029911923, -0.018138995, -0.00048087098, -0.0052565355, -0.0011368813, 0.0115697645, -0.005379478, -0.0011553864, 0.00044302826, 0.0062388936, -0.005359528, -0.0028695615, -0.0012541381, -0.0131207565, 0.011944056, -0.0085013015, 0.029468639, 0.0050135315, 0.009828712, -0.06324242, 0.004935232, 0.0054346044, 0.0064555686, 0.0017800032, 0.0052997833, 0.0019310518, -0.017909855, 0.007680814, 0.009965791, 0.012549503, 0.0032154892, 0.0076108556, 0.006166212, -0.0012188423, -0.014311489, 0.005702537, -0.013789188, -0.011192545, -0.004497786, -0.018057432, 0.006544333, 0.0010546241, 0.018369356, 0.0101006385, -0.0025861876, 0.0007202225, 0.0033358522, 0.00093738904, 0.003539452, 0.010667801, -0.010638096, -0.005171929, 0.0145933665, 0.010507592, 0.014137095, 0.014641465, -0.009217379, 0.005364763, -0.0041791163, 0.017686104, -0.009496549, 0.004921483, 0.013137144, -0.0008113434, -0.021721575, 0.015526774, 0.017641775, -0.007731, 0.00018305518, 0.020393806, 0.008813309, -0.027852844, 0.016856318, -0.0065631196, -0.0038178721, 0.021623287, -0.0031696977, 0.012780215, -0.0029505934, 0.0011117794, -0.0038595388, -0.010568917, 0.0037014228, -0.020667022, -0.0092753535, 0.005388678, -0.007445962, -0.013287682, -0.003246808, 0.0055677127, 0.010124445, -0.010266979, -0.00524452, 0.0041524814, -0.009679243, 0.0079605505, -0.0033093463, 0.0026616037, 0.011116453, -0.014930037, -0.00042665805, 0.0014734768, -0.012521542, -0.0025612095, -0.0005274403, 0.001620853, -0.0017249134, -0.023677606, -0.0065711904, -0.00469019, -0.0028944756, 0.0030760907, -0.0012164608, 0.001685171, 0.00035137823, 0.005495921, -0.0061772773, 0.006286183, 0.014550499, -0.008771651, 0.00451746, 0.009325771, 0.0082876105, -0.005369365, -0.0048946035, -0.01059919, -0.007532613, 0.012231166, 0.0015693513, -0.008178547, -0.0012520059, 0.012515395, 0.01346718, 0.025156671, 0.015567454, -0.011267366, -0.0127247535, 0.0026805454, 0.0026549217, -0.00521451, 0.0014946325, -0.01714978, -0.01663191, -0.002007931, 0.013099641, -0.012429517, -0.008398861, -0.0081566395, 0.0025277473, -0.0013729896, 0.019363511, 0.027963512, 0.0037237655, -0.013488201, 0.009800497, -1.2503521e-05, 0.000999075, -0.0041869055, -0.009779316, 0.01833783, -0.010857925, 0.0022457973, 0.01079847, 0.0061113965, 0.0037587297, 0.0021632307, 0.0043935385, 0.0044405833, 0.008795013, -0.0011419584, -0.010533435, 0.0011896611, 0.0037176977, 0.0059155156, 0.008341347, 0.004182635, 0.0039229468, -0.006645252, -0.0026511718, 0.006966292, 0.011113323, 0.007400125, 0.0062117884, 0.0031919475, 0.012522417, 0.0059480392, -0.0038567355, 0.0050216476, -0.0017919433, -0.0068080006, 0.0014414472, -0.0009224692, -0.0017809978, 0.0045513036, 0.008336371, 0.008382942, -0.0029326451, -0.00916217, -0.003593698, -0.012776231, 0.0182886, 0.0004779626, -0.0074651414, 0.0010058285, 0.0018659807, -0.0038178794, 0.0047047916, -0.0051432424, 0.017716441, 0.0067927865, 0.0061422237, -0.0011420801, -0.014179835, 0.014034082, -0.00040978048, 0.010984715, -0.0066581704, 0.009154658, -0.010791952, -0.009671176, 0.003742739, 0.011379271, -0.0032927275, -0.011845871, -0.11770746, -0.013126696, 0.0020945056, -0.0056862934, 0.011781782, 0.0017745809, 0.0007171819, -0.0042478107, -0.008204092, -0.00035797758, 0.0009603897, 0.00026123348, -0.01767594, -0.02301881, -0.011625851, -0.0022798216, -0.0002784621, -0.009999033, 0.0021904954, -0.0073693898, 0.0042488226, 0.0005075077, -0.0021169672, 0.0020915181, -0.0022566752, -0.00967333, -0.0097185755, -0.00030741343, 0.0051433635, -0.0026421272, -0.002073122, 0.0073664756, -0.005158291, -0.0013347719, 0.021364288, 0.0022443195, -0.0077144452, 0.0049142465, -0.14844006, 0.010363092, -0.005585926, -0.0055867517, -0.00354174, 0.009647314, 0.0032060272, 0.007827982, 0.0059437673, -0.0019375772, -3.6797115e-05, -0.004591525, -0.016323261, 3.8250473e-05, 0.011300554, -0.0005569752, -0.0007139616, -0.0069855293, -0.00935365, 0.016762882, 0.0046468624, 0.003217714, 0.007115578, 0.026454793, -0.010307862, -0.0100453375, 0.008950563, 0.0013238185, 0.021377567, 0.010941063, 0.0068531865, 0.010706139, -0.0070746415, 0.004032562, 0.013604011, 0.0070994557, 0.0053524184, -0.00052337314, 0.0027767182, -0.0073203514, 0.014663314, -0.0071464214, 0.012813454, -0.0013703905, -0.0012130085, -0.0024052016, -0.005535562, -0.0066486453, 0.005291809, 0.005341812, -0.015246108, 0.013769372, 0.0007036417, 0.0066358387, 0.012379829, -0.004895886, -0.0059112217, 0.0029802157, 0.0011428919, -0.010400563, -0.01247109, -0.0060575176, 0.0044202623, 0.0028723904, 0.007071939, -0.00022147805, -0.0013510863, 0.0048632566, -0.014613224, -0.006076272, -0.0064277817, 0.020983774, -0.009069641, -0.0075214524, 0.006889699, 0.034403753, 0.014667185, -0.0020721997, -0.0045848247, -0.0015110249, 0.015780505, -0.0074439873, -0.017198963, 0.011289535, -0.005334314, -0.014009325, -0.009353056, 0.002443971, 0.008365817, -0.03717464, -0.008598002, -0.012287938, -0.0021773817, -0.0018537871, 0.00346245, -0.0034431184, -0.009165178, -0.0025254255, 0.003352879, 0.006645482, 0.006239074, 0.009568264, 0.025829954, -0.012535218, 0.015491755, -0.007926338, 0.005435908, 0.003812901, -0.003820825, -0.035599113, -0.00809645, 0.0023813609, 0.014081604, 0.017152702, -0.01129372, 0.007257057, -0.010143684, 0.008006094, 0.0050722496, -0.0027643673, 0.009948161, -0.016655738, 0.032322608, -0.0055107917, 0.007937498, 0.001180932, -0.0051287552, 0.0021223195, -0.0058442177, 0.0017039701, 0.0037723898, -0.00659249, 0.004126628, -0.016715087, 0.015968751, -0.019438753, 0.01379415, -0.014815044, 0.013292328, -0.014089732, -0.003412502, -0.0034073207, 0.0047120266, 0.00903322, -0.02891634, 0.010971613, 0.0032503915, 0.004559357, 0.008670512, -0.007993892, -0.03178781, 0.009190864, -0.009190027, 0.008573471, 0.008759922, 0.0078288615, 0.0064271702, -0.0057470417, 0.0012508065, -0.0074064215, 0.00365758, 0.019507192, -0.005482956, -0.00096073875, -0.018590126, 0.005560257, -0.013438529, 0.015574805, -0.009333247, 0.00064149156, 0.006225696, -0.0016217217, 0.0027665324, -0.0007716854, -0.02000398, 0.0033668247, 0.008593954, -0.011608016, -0.0076541966, 0.007016424, -0.017146189, 0.0069575, 0.007863621, -0.01185902, -0.0066623515, 0.010218474, -0.011826482, -0.0010449748, 0.0076484624, -0.0049605663, 7.366934e-05, -0.007001868, -0.0057497066, 0.012553949, -0.0016056483, -0.004183971, -0.0053120228, -0.0028081345, -0.0036779894, 0.014058593, 0.017703997, 0.0058323727, 0.01418701, -0.15202215, 0.0008163967, -0.004397728, -0.013042664, -0.0015102101, 0.010595097, -0.0015965856, -0.0029033483, 0.012933793, -0.022557834, 0.015274779, 0.01474604, 0.0036407984, -0.012736656, 0.019788746, -0.007951109, 0.01063139, -0.0027518426, -0.0056357104, -0.0012126926, 8.352664e-05, 0.015083811, -0.0028996079, -0.0021900763, -0.007856769, -0.0026437526, 0.01892536, -0.011332182, -0.0104083195, 0.0018498828, 0.009887317, -0.0042666644, -0.015761798, 0.03196211, 0.0025531375, 0.0088133225, -0.0305467, -0.014819149, -0.006694996, 0.0035680379, -0.022481637, -0.024892794, 0.0065189353, 0.009007214, -0.0020034562, -0.0007551836, -0.02454989, -0.015811644, -0.0038499811, 0.012116088, -0.017650565, -0.01477193, -0.012856643, -0.0040164627, 0.0028160245, -0.016096912, 0.009657089, 0.0018844696, 0.013740161, 0.010014974, -0.0053161145, 0.00015642238, 0.012200709, 0.013851211, 0.017765427, -0.00020377988, 0.0030674497, 0.16878295, -0.0132477805, 0.01594084, 0.008980184, -0.008381784, 0.01733177, -0.0044711228, -0.0026949965, 0.011659594, -0.022425668, -0.01709412, 0.022036254, 0.003871142, -0.014761347, -0.010645342, 0.000114837865, 0.0052589313, 0.006625211, -0.0065661184, -0.00259521, -0.015026947, -0.011497099, -0.0016811098, -0.024413195, 0.000994332, -0.016126469, 0.017197283, -0.007813628, 0.019587992, -0.0032806385, 0.009268209, -0.003616893, -0.012190456, -0.0043659327, -0.0068115755, 0.01740844, 0.00077036663, 0.008652778, -0.0045201494, 0.028183473, 0.0069009904, 0.025207585, -0.0041561667, -0.005820443, 0.01429624, 0.00031296274, -0.0034639898, 0.016972743, -0.008563771, -0.009021519, -0.021891076, 0.014292338, -0.00600453, -0.0017001284, 0.0018328229, -0.034299552, 0.0009733458, -0.0003405708, 0.000826843, 0.0008902881, -0.00097151037, -0.015770558, -0.019760808, 0.0105281565, -0.0010231134, 0.0023856028, -0.020382592, -0.0060855015, 0.000492105, -0.14405224, -0.012557362, -0.017680392, -0.0033823394, -0.00065649586, -0.014837583, 0.0060640965, 0.0032706377, 0.008349147, -0.015391218, -0.0015957203, 0.0065684286, 0.017558701, 0.007326391, 0.00039364956, 0.020894341, 0.012039614, 0.012843752, 0.011546534, -0.004283396, 0.0065654134, 0.0032645033, 0.010927214, -0.021802215, -0.012054011, -0.0013658579, -0.0038501217, -0.010738358, -0.0027732973, 0.016905742, -0.016047131, 0.0057255635, -0.0068829185, 0.008038418, -0.026932634, -0.005148776, -0.027621683, -0.01596724, 0.003367292, -0.0015723368, -0.0014996034, -0.00606805, 0.0063212896, -0.018175153, 0.008110568, -0.0037859061, -0.017838012, 0.001537036, 0.015218136, -0.019691676, 0.00042337496, -0.0005078838, -0.013510377, -0.02863271, -0.013151126, 0.003672522, 0.004232416, -0.025038524, 0.01335072, -0.016454538, -0.0041418984, 0.015686693, -0.0008083287, 0.016561734, 0.004630454, -0.004544792, -0.0044075823, 0.006086702, 0.007494342, -0.007303684, -0.0077830628, 0.004611099, 0.000682276, -0.009507835, -0.0001299835, 0.008981375, -0.0073217205, -0.004588781, 0.0074720285, 0.00070639356, -0.01082513, -0.0019398227, -0.0061458033, -0.016194027, 0.04499077, -0.028943056, 0.002719207, 0.003046323, -0.011569696, -0.0017095606, 0.008074911, -0.00037845643, 0.004225412, 0.0060979426, 0.019863557, 0.008732906, -0.009504793, 0.023937862, -0.0060314653, -0.007070981, 0.0014432484, 0.015450881, -0.024368433, -0.009629758, 0.006956789, -0.007516841, 3.3731467e-05, 0.013288902, 0.0038237048, -0.0072758244, -0.012428245, 0.007860041, -0.015969498, 0.0063818987, 0.006334807, 0.0076015345, 0.0045978567, 0.01728661, 0.0010762005, -0.002736192, 0.0068655657, 0.016227756, 0.0043269605, -0.004072569, 0.003126959, -0.0021837503, -0.0035828145, -0.0034587956, 0.020384992, -0.011799068, 0.014135134, -0.0013619575, -0.008417931, 0.017593354, 0.014973428, 0.0016068612, 0.037036814, 0.01999493, 0.022876453, -0.003083133, -0.019724982, 0.006110036, -0.008209479, 0.008782264, 0.0014507443, -0.025917113, -0.002990646, 0.020614, 0.007872602, -0.012070585, 0.003495968, -0.00062459, -0.019960543, -0.012959165, 0.012904687, -0.0035710442, 0.0100631835, 0.02317638, 0.013988408, -0.0027384062, 0.0031941722, -0.0073502837, -0.0051388713, -0.010655521, 0.003743321, -0.012843976, -0.006080675, -0.031595226, -0.01618035, -0.013498496, 0.008007144, -0.011532034, -0.00067593134, -0.0008266642, -0.017234055, 0.018391088, 0.009337311, 0.0043202015, -0.0054412982, -0.08934503, 0.006454405, 0.0121726375, -0.0040919445, 0.010395827, -0.0034454144, -0.013763541, -0.0024487393, -0.0036506588, -0.0034376779, 0.01288837, 0.013713079, -0.011045287, -0.023856362, 0.003172059, -0.0068093007, -0.0068312865, 0.008090335, 0.010584141, -0.01271995, -0.003964057, -0.008343193, 0.0077450033, 0.008663141, -0.001956003, -0.021932587, 0.01594181, 0.017193273, 0.0288066, 0.014083428, -0.0005023997, -0.013623967, -0.0012609403, 0.013041584, -0.005776918, 0.011703005, -0.010017132, -0.020504596, 0.0076025026, -0.0593763, -0.0046259565, 0.0009203399, -0.10877584, 0.001031688, 0.024630316, 0.023463976, -0.0012989986, -0.01622928, -0.007717408, -0.01817938, 0.017152501, -0.007311347, -0.009356029, -0.0008809008, 0.012091383, -0.0040771724, 0.025924211, 0.0152029665, 0.0132284, -0.00059030176, -0.0040034684, -0.010193673, -0.004089682, -0.011823825, -0.002729419, 0.034637466, -0.0045018448, -0.0072744046, 0.005657161, 0.02468082, -0.0033004726, 0.0023181795, 0.025994113, -0.025632761, -0.008777137, -0.008969486, 0.019109022, -0.0064266226, -0.0020115108, 0.018753553, 0.0019178138, -0.029086463, -0.01120114, 0.04268655, 0.0032781162, -0.038098935, 0.0007616516, -0.126929, -0.015624373, -0.0020665533, 0.0016146809, 0.002849304, 0.018126579, 0.007514821, 0.14125934, 0.010062873, 0.0013091452, -0.009736117, 0.004511793, 0.008164233, -0.009297447, -0.001203482, 0.0037458905, 0.017312584, 0.01714016, -0.015446341, 0.012108912, -0.0023042, -0.00835688, -0.00595803, 0.0063047223, 0.0068025347, -0.048142564, -0.003300106, -0.016051311, 0.0069569265, 0.0028301314, 0.00032281692, -0.00257502, 0.0021866595, -0.014754227, 0.00016574372, -0.0057852473, -0.007043115, 0.008291693, 0.0016309755, -0.011720318, 0.0177943, 0.015489053, 0.017668182, -0.011559519, -0.0087964395, 0.0031599733, -0.0079638725, 0.001530655, 0.013780786, 0.017852465, -0.0010371589, -0.018712051, 0.009212497, -0.013640717, -0.009196564, -0.0032545517, -0.011767076, -0.0032413255, 0.0012607162, -0.0059620505, 0.0017666788, -0.020355893, -0.007417313, 0.011963721, 0.0059108553, -0.007174811, -0.011128809, -0.025804091, -0.02115292, 0.011447485, 0.0055560363, 0.0065693124, 0.022059247, -0.004934974, -0.006995124, -0.01938295, -0.00335925, 0.025385035, -0.019126529, 0.0015124193, 0.0110194, -0.005159681, 0.0005082414, 0.002926326, -0.014692279, -0.010215048, -0.0007880062, -0.003514574, 0.021977518, 0.012956782, -0.0071675354, 0.0018155689, 0.026137717, 0.013011897, 0.0038716143, 0.005016225, 0.006667992, 0.013445527, 0.020173844, -0.0070947306, -0.011730683, -0.023057956, -0.016771788, -0.02726666, -0.008114149, 0.012559054, -0.0003796825, 0.013927799, 0.008937216, 0.00847961, 0.018184466, 0.01121179, -0.009060421, -0.008531351, -0.029517747, -0.014889324, 0.0019714157, -0.004642489, -0.0018151726, -0.0030372294, -0.015070941, -0.007361294, -0.008027901, -0.009238117, -0.010092483, 0.006932853, -0.016510552, -0.007353865, 0.00036481395, 0.0008259912, 0.0002106616, 0.0022675192, -0.016396066, -0.016350098, 0.0076320698, -0.00049596187, -0.012284576, 0.013448192, -0.004749304, 0.0034240661, 0.0014189854, 0.0023173732, 0.019550668, -0.004222567, 0.004998029, -0.008107146, -0.00323238, 0.00397444, -0.020558676, 0.01234428, -0.002101968, -0.0007766705, -0.016553143, -0.010803417, -0.032686215, 0.007587724, 0.01088773, 0.0055258344, 0.0011835742, -0.008832495, -0.0012467485, 0.005542428, 0.0028294078, -0.0028750203, -0.0034429817, -0.011707506, 0.0012056027, -0.01963294, 0.03660115, 0.0055118543, -0.0027292597, -0.002441381, -0.0040931036, -0.0022150846, -0.009290489, -0.010736448, 0.0017377291, 0.010194744, 0.0067680473, -0.00998556, 0.012301032, 0.008379896, -0.013256777, 0.019110274, -0.004393857, -0.008813366, 0.013016171, -0.007968566, 0.008750768, 0.018720865, -0.0057345345, -0.043445006, 0.012056966, 0.006830206, -0.007952936, -0.009323333, -0.020857481, 0.014978255, 0.00215273, 0.013123404, 0.008007338, -0.01702051, -0.011950307, -0.04040456, -0.012294821, 0.0055592223, -0.04004036, 0.0038579234, -0.010994037, 0.0047738547, 0.0056174905, 0.014698227, -0.008449612, 0.005012881, -0.0082559055, 0.006863288, 0.0054892385, 0.006200354, 0.0059217275, 0.00078266195, 0.025036775, -0.010173627, 0.0019440419, 0.022279408, -0.0075536203, -0.00605199, -0.013750306, 0.02162383, -0.005114792, -0.0021615732, -0.017055474, 0.007567694, -0.0077138795, 0.011463188, -0.00072113884, 0.013032435, -0.004601109, 0.028357893, -3.495112e-05, -6.494836e-05, 0.0010072291, 0.011422205, 0.022539467, 0.004789605, -0.008295251, -0.017507209, 0.005076582, -0.010084857, -0.0018427673, 0.017569331, -0.007089613, 0.018389042, -0.007535071, -0.0012925073, 0.007979152, 0.006312828, -0.011153738, 0.01617295, 0.0074051665, 0.0017778262, -0.014864124, 0.022289539, 0.0027714132, 0.008890506, -0.006837025, 0.00057340733, 0.012073002, 0.011139057, -0.010847791, -0.006368396, 0.0019966902, -0.0068634874, -0.019561151, -0.02057755, -0.0025334184, 0.017820332, -0.010814594, 0.00087972404, -0.01119333, 0.019510334, 0.01772269, 0.0049886443, 0.0150531465, 0.005145718, 0.006547729, -0.008269349, -0.010436151, -0.009487839, 0.010638786, -0.0032230294, -0.0040577156, -0.00900562, 0.006887021, 6.29699e-05, -0.008281714, -0.012122985, -0.021575864, -0.005843337, -0.020455178, 0.005435107, -0.02626131, -0.0051564216, -0.006522045, -0.006020229, 0.004838036, 0.007998842, 0.024708927, -0.028520279, 0.008628832, 0.025691148, 0.0062528565, 0.014315798, -0.008527202, -0.0041581974, -0.010409291, -0.021724548, 0.008024209, 0.004453331, -0.010446626, 0.023265399, -0.008967875, -0.00042384173, 0.023857096, 0.016362622, 0.01667798, 0.005066065, 0.020210821, 0.0039841514, 0.013014006, 0.0033621625, 0.009508119, -0.01805061, -0.017122552, -0.019052297, -0.0043552946, 0.0029136487, 0.0014872254, -0.0066141943, -0.002012225, -0.0019561911, -0.0031912257, 0.0136609925, 0.011606207, -0.025532035, 0.003547403, 0.0010326181, 0.011082271, -0.016202174, 0.00541166, -0.00725935, -0.0102694975, 0.011402245, -0.0049078767, 0.014454843, 0.007348984, -0.013624677, 0.013899108, 0.00012910883, -0.0013278688, 0.012059475, 0.011935064, 0.015835596, -0.013262776, -0.00095808046, -0.0193062, 0.0027205984, -0.016076606, -0.006623611, -0.017484039, -0.007842387, -0.00021922003, -0.00016557805, 0.0026504502, 0.0039684507, 0.010407494, 0.0032263978, -0.0008573552, -0.0044389195, 0.0056605167, 0.002807124, -0.030387556, 0.008616295, 0.011375594, 0.000644334, -0.009737554, -0.006047584, 0.013530329, 0.013166346, 0.021099145, 0.0012720427, -0.0033332705, -0.0020370209, -0.0032998284, -0.0016949708, -0.009964262, 0.017731752, -0.0011529103, -0.004596378, 0.01644251, -0.0038595428, 0.010300542, -0.0027027195, 0.013556787, 0.0025973623, 0.0040661413, 0.0011065073, 0.00033257084, -0.009891027, -0.008442295, 0.009388694, -0.026832726, 0.009368069, 0.017190197, -0.0142257335, -0.019378444, 0.024749259, 0.0015912881, -0.012944776, 0.004338852, -0.009506879, -0.012157747, -0.00350336, -0.00556281, 0.017778186, 0.007179742, 0.00039938278, 0.01157869, -0.019715019, 0.0013136904, 0.0030226123, -0.009567739, -0.010010434, 0.0063173613, -0.0023568866, 0.006655948, 0.016247477, -0.011867474, 0.006586563, 0.019087246, 0.01213647, -0.0022932326, -0.0010716878, 0.0069258455, -0.008665314, 0.0042857574, -0.0013904108, -0.010668578, -0.00062115997, 0.01201316, -0.00652365, -0.0003198757, -0.021946523, -0.01510976, -0.004706844, 0.0061468026, -0.02544103, -0.006194714, -0.0051389034, 0.020418638, -0.0069043385, 0.00165975, 0.0010744288, -0.0018983526, 0.0047260527, -0.015817247, -0.0089731375, 0.00041826625, 0.016235488, -0.006435792, 0.004359467, -0.062470708, -0.016654441, -0.04676323, -0.0062524737, -0.004363955, -0.010945654, 0.0016477389, 0.0021272644, 0.024619143, -0.04364077, 0.012210429, -0.0018785436, 0.007131924, 0.022169253, 0.0023017374, -0.0062385034, -0.020578252, 0.007843147, 0.0014105802, -0.0126859695, -0.002177598, 0.03301395, 0.00093593093, -0.0077516856, 0.005807695, 0.0023818149, 0.001285175, 0.0079144165, 0.010470915, -0.012520274, 0.004652442, -0.0038401315, -0.0077962987, -0.008793136, 0.007740179, -0.0032910395, 0.0013585454, 0.008597452, -0.011567004, -0.024219992, -0.04348961, 0.0074848332, 0.013774697, 0.0026077777, 0.0018546208, 0.014748787, 0.0002737965, -0.006961081, 0.016983729, -0.00049724133, -0.019544724, 0.0013546123, -0.0051361937, -0.0074048527, 0.019699888, 0.0016742747, -0.0034764663, 0.0034177897, -8.0497644e-05, 0.00040503236, 0.001742462, -0.0010211286, -0.01676741, 0.0035622048, -0.013071915, 0.002849324, -0.0039477632, -0.008673519, 0.010206399, -0.018532028, 0.009529172, -0.007016941, -0.0013588148, -0.008695678, 0.026860736, 0.02100034, -0.011194293, 0.018255107, -0.011091717, -0.0076967645, -0.008796983, -0.00017026634, -0.02655255, -0.0057272497, 0.0136053525, 0.0011050656, -0.0033152206, -0.00261853, 0.0039540078, 0.0049298406, 0.0004949718, -0.0056159496, -0.008056718, 0.012558549, -0.0011607497, -0.001062299, -0.015956646, -0.014709428, 0.0031430284, 0.0052308906, -0.014571993, 0.00064768794, 0.0068166433, -0.015488112, -0.009632448, 0.0007137361, -0.0054031336, -0.018135333, 0.0051606516, 0.020109162, 0.0113746375, -0.03342055, -0.024169505, -0.011815736, -0.007883395, 0.006842756, 0.012051961, 0.017524632, -0.00867087, 0.018685749, 0.003754499, -0.012981849, 0.00394427, -0.003117313, -0.009848555, -0.0072457744, -0.004937272, 0.01110605, 0.010899959, -0.01412389, -0.005435478, 0.0049350387, 0.0068377783, -0.019344326, -0.0053436216, -0.011976459, 0.0023442293, 0.0009197832, -0.00044750748, -0.001409555, 0.022161745, 0.050522506, 0.0051212916, -0.023523439, 0.0009420635, -0.028391976, 0.0019374054, 0.010719264, 0.011500538, -0.006412441, 0.0053265216, 0.015884522, 6.75839e-05, -0.0018327329, -0.015943727, 0.0059396173, -0.013561422, 0.0015949801, -0.018306624, -0.021439333, -0.0028741143, 0.008678792, -0.011906801, -0.0028993797, -0.016365925, 0.006220999, 0.025266726, -0.008665623, 0.0034021852, -0.007613921, -0.01389001, -0.014115554, -0.0045346315, -0.0012169178, 0.0033395607, 0.00015618965, 0.0067779073, -0.0029352827, -0.010400511, -0.0042421645, 0.0075244186, 0.0043352386, 6.8623915e-05, -0.019700045, 0.004596694, 0.0130886445, -0.009139992, -0.006007094, 0.03342617, -0.013718501, 0.006151359, 0.021314789, -0.008232854, 0.015498698, 0.013825079, -0.0054084873, 0.008701536, 0.0035709036, 0.012111021, -0.020749247, -0.0002663274, -0.025738806, -0.0090481285, -0.0005016491, 0.016619379, 0.0013777231, -0.0046083434, 0.0048189186, -0.0064855334, -0.0036197032, -0.0389512, 0.023577157, -0.004260177, 0.009908715, -0.0047736755, 0.005107494, 0.19688839, 0.14121847, -0.006469101, -0.011833303, 0.006718441, 0.0030592065, -0.01965944, 0.0049842703, 0.019620012, -0.020616254, -0.017769143, 0.0104200225, -0.017524183, 0.013496206, -0.0056035155, -0.008774442, -0.012759905, -0.0040664175, -0.0056918496, 0.013234924, -0.02144658, 0.0063746073, -0.0005296519, -0.0072143623, -0.0298628, 0.007880133, 0.011342022, -0.0031851414, 0.029889949, -0.005750553, 4.422826e-05, 0.0038771455, 0.011604428, -0.010412497, 0.004550804, 0.019830985, -0.018573571, -0.01841962, -0.0016134661, -0.0051777074, -0.0065129334, 0.0068471516, 0.0036774392, 0.014234341, 0.017124595, 0.013255577, 0.0057687922, -0.002981478, 0.0013038679, 0.008503422, 0.0052263825, 0.003788723, 0.00692021, 0.005734935, 0.0096092345, 0.012997395, 0.010277094, -0.0043079867, 0.0043155393, 0.020575644, 0.010704993, 0.01349616, 0.007745748, 0.0031976134, -0.00727223, 0.0010357839, 0.007450108, -0.004876774, 0.013341814, -0.0038060665, 0.01153257, -8.796314e-05, -0.009329493, -0.006862034, -0.010483662, 0.006594217, 0.0002524614, -0.0068410286, 0.0025155745, -0.001593572, -0.006161628, -0.01513228, 0.017021123, 0.014763044, -0.0022922524, 0.0037101305, 0.0042040986, 0.00014290809, 0.13344346, -0.029759351, 0.014482105, -0.014693307, 0.013991698, 0.012233783, -0.005839931, 0.04513035, 0.0020241332, -0.010477726, 0.028906757, 0.003372463, 0.0063390154, -0.009592573, 0.010105838, -0.009813376, 0.009279822, 0.057482656, 0.0073359576, -0.012401676, 0.010453394, 0.020718599, -0.003399779, -0.011966553, 0.00961996, -0.003874751, 0.010464161, 0.0041465354, -0.008421661, -0.0072973664, -0.1092216, -0.010550851, -0.011075316, -0.016881073, 0.002245027, 0.018800592, -0.014403884, 0.0033823005, 0.012160339, 0.009873134, -0.0022765996, -0.012643086, 0.0040292246, -0.009448419, -0.012288881, -0.009793497, 0.009017252, -0.0064625544, -0.008200078, 0.0005538749, 0.01521722, -0.0035624013, 0.002556591, 0.029920673, 0.008070413, 0.0120054055, 0.008632174, -0.0031758351, 0.010205422, 0.011931518, -0.009437684, 0.0051203067, -0.004966023, 0.0056508183, -0.0034846764, -0.00017507099, 0.02238719, 0.021596096, 0.002717092, -0.023010379, -0.0065424056, -0.005956812, -0.014846652, -0.016661951, 0.021855576, -0.011376163, 0.016690267, -0.0032520462, -0.006151656, -0.012012659, 0.008698012, -0.008617864, 0.016143994, 0.009503883, 0.011818994, 0.01975389, 0.0039705285, -0.010544218, -0.00053587375, 0.011666857, 0.0028382628, 0.031928383, -0.015970454, -0.009287976, 0.0055048177, -0.019306, -0.0079599945, 0.011610893, -0.010579229, -0.011155596, -3.3894175e-05, 0.018514752, 0.016337277, -0.0058958163, 0.004047436, -0.0056084758, -0.002109158, 0.010189958, 0.018033631, -0.007577322, 9.717338e-05, -0.0035210906, -0.0068389946, 0.13047914, 0.014569934, 0.0065904027, -0.0023715491, 0.0005888544, -0.0026911437, -0.007545334, -0.019513272, 0.0002567965, -0.0042806542, 0.008524623, -0.0036573005, -0.014797519, -0.015341571, 0.004129225, 0.0016148873, 0.0089891935, 0.024856202, -0.0031641892, -0.004846863, 0.010619036, -0.0005390398, 0.015087491, 0.021736395, -0.021525906, -0.0011093387, -0.005297932, 0.01003288, 0.00031778318, -0.0072777006, 0.00084113353, -0.00547526, 0.006904974, -0.021971317, -0.0017821641, -0.018840646, 0.012091933, 0.010026849, 0.010739739, -0.019550499, 0.008430106, -0.036259186, 0.029014438, 0.0049989372, -0.04740853, 0.20419154, -0.017289346, 0.0029616887, -0.0009969029, -0.0069446033, -0.01583106, -0.0028393962, 0.0052565136, 0.006685163, -0.0025910607, -0.0013835661, -0.00014838953, 0.008591391, -0.002566316, -0.01555078, -0.00273608, -0.006618293, 0.011613636, 0.0062489547, 0.014280932, 0.0050978735, -0.0031623058, -0.027084917, -0.013261272, -0.017014815, 0.028735638, 0.009067015, 0.020288076, 0.0030741878, -0.012731925, 0.003935979, -0.0059344913, -0.007147056, 0.00977869, -0.006082229, -0.0131141255, 0.014056636, 0.011635573, 0.012178006, -0.010014409, -0.0062339567, 0.0078272335, -0.022022687, 0.002411944, 0.0011891118, -0.0011976627, -0.0004245514, 0.004200864, -0.00015128081, -0.008876931, 0.003191684, 0.009559989, -0.009365364, -0.012837858, -0.02196926, -0.0013132612, 0.0020008946, 0.008412886, -0.0014819927, 0.0095650405, -0.0080919145, 0.0014905644, -0.009304574, -0.0056427335, -0.0035890513, -0.012347147, -0.02429249]
        )

        ruta_imagen = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'SanGonzaloJuevesSanto2025.jpg')

        if os.path.exists(ruta_imagen):
            with open(ruta_imagen, 'rb') as f:
                comunicado_2.imagen_portada.save('SanGonzaloJuevesSanto2025.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Comunicado 2.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen}'))

        comunicado_2.save()

        comunicado_2.areas_interes.set([9])

        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Comunicado 2 asociado al área ID 9.'))
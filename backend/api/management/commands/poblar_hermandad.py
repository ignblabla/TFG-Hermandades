import random
import time

from google import genai

from ...models import Acto, Comunicado, CuerpoPertenencia, Cuota, DatosBancarios, Hermano, AreaInteres, PapeletaSitio, PreferenciaSolicitud, Puesto, TipoActo, TipoPuesto, Tramo
from datetime import date, datetime
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import make_aware
import os
from google.genai import types
from django.conf import settings
from django.core.files import File
import random
from django.contrib.auth.hashers import make_password

def generar_y_guardar_embedding_sync(comunicado_id):
    """Versión síncrona exclusiva para scripts de poblado (evita que el hilo muera prematuramente)"""
    try:
        comunicado = Comunicado.objects.get(pk=comunicado_id)
        texto = f"Título: {comunicado.titulo}\nContenido: {comunicado.contenido}"

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        resultado = client.models.embed_content(
            model='gemini-embedding-001',
            contents=texto,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )

        comunicado.embedding = resultado.embeddings[0].values
        comunicado.save(update_fields=['embedding'])
        print(f"✅ Embedding guardado para el comunicado {comunicado_id}")
        
    except Exception as e:
        print(f"⚠️ Error: {e}")



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

            # --- TRAMOS DE VIRGEN (8 Tramos) ---
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
        # POBLADO DE ACTO: ESTACIÓN DE PENITENCIA 2028 (ID=11)
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Acto: Estación de Penitencia 2028...")

        now = timezone.now()

        Acto.objects.filter(id=11).delete()

        descripcion_acto_2028 = (
            "La Estación de Penitencia a la Santa Iglesia Catedral es el acto central y culminante "
            "de la vida de nuestra Hermandad de San Gonzalo. En este año 2028, nos preparamos para vivir "
            "nuevamente este encuentro íntimo con nuestro Señor en su Soberano Poder ante Caifás y nuestra "
            "Madre y Señora de la Salud. Este solemne acto público de fe es la manifestación más genuina de nuestro "
            "compromiso cristiano, donde cada nazareno, costalero, acólito y hermano se convierte en un "
            "testimonio vivo del Evangelio por las calles de nuestro barrio de Triana y de toda Sevilla. "
            "Se invita a todos los hermanos a participar con recogimiento, orden y profundo sentido de "
            "pertenencia, haciendo de cada paso una oración y de cada cirio encendido una luz de esperanza."
        )

        acto_ep28 = Acto(
            id=11,
            nombre="Estación de Penitencia 2028",
            lugar="Parroquia de San Gonzalo",
            descripcion=descripcion_acto_2028,
            fecha=datetime(2028, 4, 10, 15, 0, 0, tzinfo=timezone.get_current_timezone()),
            modalidad="TRADICIONAL",
            tipo_acto_id=1,
            inicio_solicitud=now - timedelta(days=10),
            fin_solicitud=now + timedelta(days=10),
            inicio_solicitud_cirios=now + timedelta(days=15),
            fin_solicitud_cirios=now + timedelta(days=25),
            fecha_ejecucion_reparto=None,
            fecha_ejecucion_cirios=None
        )

        ruta_imagen = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'EstacionPenitencia2025.jpg')
        
        if os.path.exists(ruta_imagen):
            with open(ruta_imagen, 'rb') as f:
                acto_ep28.imagen_portada.save('EstacionPenitencia2028.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Acto 11.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen}'))

        acto_ep28.save()
        
        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Acto Estación de Penitencia 2028 con ID 11.'))



        # =========================================================================
        # POBLADO DE PUESTOS DEL ACTO 11 (EP 2028)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Puestos para el Acto 11...")

        start_id = 291

        puestos_data_ep28 = [
            {"id": start_id + 0, "nombre": "Bocina Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 8, "cortejo_cristo": True},
            {"id": start_id + 1, "nombre": "Cruz de Guía", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 12, "cortejo_cristo": True},
            {"id": start_id + 2, "nombre": "Farol Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 9, "cortejo_cristo": True},
            {"id": start_id + 3, "nombre": "Senatus (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id + 4, "nombre": "Varas Senatus (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id + 5, "nombre": "Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id + 6, "nombre": "Varas Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id + 7, "nombre": "Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id + 8, "nombre": "Varas Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id + 9, "nombre": "Banderín Sacramental (tramo 5)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id + 10, "nombre": "Varas Banderín Sacramental (tramo 5)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id + 11, "nombre": "Guión del Cincuentenario (tramo 6)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id + 12, "nombre": "Varas Guión del Cincuentenario (tramo 6)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id + 13, "nombre": "Banderín de la Juventud (tramo 7)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id + 14, "nombre": "Varas Banderín de la Juventud (tramo 7)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id + 15, "nombre": "Bandera Cruz de Jerusalén (tramo 8)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id + 16, "nombre": "Varas Bandera Cruz de Jerusalén (tramo 8)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id + 17, "nombre": "Guión de la Caridad (tramo 9)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id + 18, "nombre": "Varas Guión de la Caridad (tramo 9)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id + 19, "nombre": "Guión Sacramental (tramo 10)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id + 20, "nombre": "Varas Guión Sacramental (tramo 10)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id + 21, "nombre": "Estandarte Sacramental (tramo 11)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id + 22, "nombre": "Varas Estandarte Sacramental (tramo 11)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id + 23, "nombre": "Cirio Grande Cristo", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": start_id + 24, "nombre": "Cirio Mediano Cristo", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": start_id + 25, "nombre": "Cirio Pequeño Cristo", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 5, "cortejo_cristo": True},
        ]

        puestos_virgen_data_ep28 = [
            {"id": start_id + 26, "nombre": "Cirios apagados cruces (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 1, "cortejo_cristo": False},
            {"id": start_id + 27, "nombre": "Bocinas (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 8, "cortejo_cristo": False},
            {"id": start_id + 28, "nombre": "Simpecado (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": start_id + 29, "nombre": "Faroles Simpecado (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 9, "cortejo_cristo": False},
            {"id": start_id + 30, "nombre": "Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": start_id + 31, "nombre": "Varas Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": start_id + 32, "nombre": "Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": start_id + 33, "nombre": "Varas Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": start_id + 34, "nombre": "Bandera Concepcionista (tramo 5)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": start_id + 35, "nombre": "Varas Bandera Concepcionista (tramo 5)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": start_id + 36, "nombre": "Bandera Realeza de María (tramo 6)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": start_id + 37, "nombre": "Varas Bandera Realeza de María (tramo 6)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": start_id + 38, "nombre": "Guión de la Coronación (tramo 7)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": start_id + 39, "nombre": "Varas Guión de la Coronación (tramo 7)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": start_id + 40, "nombre": "Libro de Reglas (tramo 8)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": start_id + 41, "nombre": "Varas Libro de Reglas (tramo 8)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": start_id + 42, "nombre": "Estandarte (tramo 9)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": start_id + 43, "nombre": "Varas Estandarte (tramo 9)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": start_id + 44, "nombre": "Cirio Grande Virgen", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": start_id + 45, "nombre": "Cirio Mediano Virgen", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": start_id + 46, "nombre": "Cirio Pequeño Virgen", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 11, "tipo_puesto_id": 5, "cortejo_cristo": False},
        ]

        puestos_data_ep28.extend(puestos_virgen_data_ep28)

        puestos_a_crear = [Puesto(**data) for data in puestos_data_ep28]
        Puesto.objects.bulk_create(puestos_a_crear)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(puestos_a_crear)} puestos para el Acto 11 (ID inicial: {start_id}).'))



        # =========================================================================
        # POBLADO DE ACTO: ESTACIÓN DE PENITENCIA 2029 (ID=12)
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Acto: Estación de Penitencia 2029...")

        now = timezone.now()

        Acto.objects.filter(id=12).delete()

        descripcion_acto_2029 = (
            "La Estación de Penitencia a la Santa Iglesia Catedral es el acto central y culminante "
            "de la vida de nuestra Hermandad de San Gonzalo. En este año 2029, nos preparamos para vivir "
            "nuevamente este encuentro íntimo con nuestro Señor en su Soberano Poder ante Caifás y nuestra "
            "Madre y Señora de la Salud. Un testimonio vivo del Evangelio por las calles de nuestro barrio "
            "de Triana, renovando nuestra fe y fraternidad en cada paso del camino."
        )

        acto_ep29 = Acto(
            id=12,
            nombre="Estación de Penitencia 2029",
            lugar="Parroquia de San Gonzalo",
            descripcion=descripcion_acto_2029,
            fecha=datetime(2029, 3, 26, 15, 0, 0, tzinfo=timezone.get_current_timezone()),
            modalidad="TRADICIONAL",
            tipo_acto_id=1,
            inicio_solicitud=now - timedelta(days=20),
            fin_solicitud=now - timedelta(days=10),
            fecha_ejecucion_reparto=now - timedelta(days=9),
            inicio_solicitud_cirios=now - timedelta(days=8),
            fin_solicitud_cirios=now + timedelta(days=10),
            fecha_ejecucion_cirios=None
        )

        ruta_imagen = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'EstacionPenitencia2025.jpg')
        
        if os.path.exists(ruta_imagen):
            with open(ruta_imagen, 'rb') as f:
                acto_ep29.imagen_portada.save('EstacionPenitencia2029.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Acto 12.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen}'))

        acto_ep29.save()
        
        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Acto Estación de Penitencia 2029 con ID 12.'))



        # =========================================================================
        # POBLADO DE PUESTOS DEL ACTO 12 (EP 2029)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Puestos para el Acto 12...")

        start_id_29 = 338

        puestos_data_ep29 = [
            {"id": start_id_29 + 0, "nombre": "Bocina Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 8, "cortejo_cristo": True},
            {"id": start_id_29 + 1, "nombre": "Cruz de Guía", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 12, "cortejo_cristo": True},
            {"id": start_id_29 + 2, "nombre": "Farol Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 9, "cortejo_cristo": True},
            {"id": start_id_29 + 3, "nombre": "Senatus (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id_29 + 4, "nombre": "Varas Senatus (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id_29 + 5, "nombre": "Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id_29 + 6, "nombre": "Varas Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id_29 + 7, "nombre": "Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id_29 + 8, "nombre": "Varas Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id_29 + 9, "nombre": "Banderín Sacramental (tramo 5)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id_29 + 10, "nombre": "Varas Banderín Sacramental (tramo 5)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id_29 + 11, "nombre": "Guión del Cincuentenario (tramo 6)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id_29 + 12, "nombre": "Varas Guión del Cincuentenario (tramo 6)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id_29 + 13, "nombre": "Banderín de la Juventud (tramo 7)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id_29 + 14, "nombre": "Varas Banderín de la Juventud (tramo 7)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id_29 + 15, "nombre": "Bandera Cruz de Jerusalén (tramo 8)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id_29 + 16, "nombre": "Varas Bandera Cruz de Jerusalén (tramo 8)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id_29 + 17, "nombre": "Guión de la Caridad (tramo 9)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id_29 + 18, "nombre": "Varas Guión de la Caridad (tramo 9)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id_29 + 19, "nombre": "Guión Sacramental (tramo 10)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id_29 + 20, "nombre": "Varas Guión Sacramental (tramo 10)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id_29 + 21, "nombre": "Estandarte Sacramental (tramo 11)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": start_id_29 + 22, "nombre": "Varas Estandarte Sacramental (tramo 11)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": start_id_29 + 23, "nombre": "Cirio Grande Cristo", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": start_id_29 + 24, "nombre": "Cirio Mediano Cristo", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": start_id_29 + 25, "nombre": "Cirio Pequeño Cristo", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 5, "cortejo_cristo": True},
        ]

        puestos_virgen_data_ep29 = [
            {"id": start_id_29 + 26, "nombre": "Cirios apagados cruces (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 1, "cortejo_cristo": False},
            {"id": start_id_29 + 27, "nombre": "Bocinas (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 8, "cortejo_cristo": False},
            {"id": start_id_29 + 28, "nombre": "Simpecado (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": start_id_29 + 29, "nombre": "Faroles Simpecado (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 9, "cortejo_cristo": False},
            {"id": start_id_29 + 30, "nombre": "Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": start_id_29 + 31, "nombre": "Varas Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": start_id_29 + 32, "nombre": "Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": start_id_29 + 33, "nombre": "Varas Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": start_id_29 + 34, "nombre": "Bandera Concepcionista (tramo 5)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": start_id_29 + 35, "nombre": "Varas Bandera Concepcionista (tramo 5)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": start_id_29 + 36, "nombre": "Bandera Realeza de María (tramo 6)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": start_id_29 + 37, "nombre": "Varas Bandera Realeza de María (tramo 6)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": start_id_29 + 38, "nombre": "Guión de la Coronación (tramo 7)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": start_id_29 + 39, "nombre": "Varas Guión de la Coronación (tramo 7)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": start_id_29 + 40, "nombre": "Libro de Reglas (tramo 8)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": start_id_29 + 41, "nombre": "Varas Libro de Reglas (tramo 8)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": start_id_29 + 42, "nombre": "Estandarte (tramo 9)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": start_id_29 + 43, "nombre": "Varas Estandarte (tramo 9)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": start_id_29 + 44, "nombre": "Cirio Grande Virgen", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": start_id_29 + 45, "nombre": "Cirio Mediano Virgen", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 5, "cortejo_cristo": False},
            {"id": start_id_29 + 46, "nombre": "Cirio Pequeño Virgen", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 12, "tipo_puesto_id": 5, "cortejo_cristo": False},
        ]

        puestos_data_ep29.extend(puestos_virgen_data_ep29)

        puestos_a_crear = [Puesto(**data) for data in puestos_data_ep29]
        Puesto.objects.bulk_create(puestos_a_crear)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(puestos_a_crear)} puestos para el Acto 12 (ID inicial: {start_id_29}).'))



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



        # =========================================================================
        # POBLADO DE COMUNICADO 3
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Comunicado 3...")

        contenido_comunicado_3 = (
            "La junta de gobierno, y a proposición del diputado de juventud, aprobó en días pasados el nombramiento de quien realizará el cartel anunciador del mismo para este año 2025, recayendo esta designación sobre Pablo Vázquez Chaves, joven artista autodidacta de 21 años que comparte su visión de Sevilla a través de dibujos.\n\n"
            "El autor nació en esta ciudad el 30 de Agosto de 2003. Dió sus primeros pasos en el Colegio Santa Teresa de Jesús, en la localidad de San Juan de Aznalfarache, donde ganó varios premios de pintura. Posteriormente, estudió bachillerato y el TSEASD en Mairena del Aljarafe. Actualmente es estudiante de CAFYD en la Universidad Pablo de Olavide y amante de su tierra y el arte. Cada trazo que realiza captura la esencia de Sevilla, sus tradiciones y su belleza única.\n\n"
            "El acto del Pregón de la Juventud de nuestra Hermandad de San Gonzalo tendrá lugar en nuestro templo parroquial el próximo jueves 27 de marzo, tras la culminación de la misa vespertina de las 20 horas. La presentación del cartel acontecerá unos días antes en una fecha que se comunicará en tiempo y forma.\n\n"
            "Cabe recordar, que a propuesta del diputado de juventud, se aprobó el nombramiento de quien pronunciará el Pregón de la Juventud del año 2025, que alcazará su XX edición, recayendo esta designación sobre nuestra hermana Cristina del Pilar Montenegro Torres, quien será presentada por nuestra hermana Reyes de la Salud Baena Rueda.\n\n"
            "Cristina del Pilar Montenegro Torres, tiene 24 años, pertenece a nuestra hermandad desde el 27 de diciembre de 2000 y es, también, hermana de la Hermandad de la Esperanza de Triana y de la Hermandad del Rocío de Gines (Sevilla). Actualmente es miembro del grupo joven desde marzo de 2014 y participa en cuantas actividades organizan los difrentes colectivos de nuestra corporación.\n\n"
            "PREGONEROS DE LA JUVENTUD DE SAN GONZALO\n"
            "2004. Sebastián Ruiz Cabrera\n"
            "2005. Moisés Ruz Lorenzo\n"
            "2006. Juan Manuel Labrador Jiménez\n"
            "2007. Carlos Cabrera Díaz\n"
            "2008. Miguel Ángel Guera Maldonado\n"
            "2009. José Esmeralda de Tena\n"
            "2010. María Isabel Sol Bkhiti\n"
            "2011. Sara Segador Coronilla\n"
            "2012. Sara María González Ruiz\n"
            "2013. José Contreras Sarria\n"
            "2014. Alberto Jiménez Aguilar\n"
            "2015. No se celebró\n"
            "2016. Antonio Vázquez Bayón\n"
            "2017. Raúl Molina García\n"
            "2018. Alonso Seoane García\n"
            "2019. Juan Bueno Cazorla\n"
            "2020. Aplazado por la Covid-19\n"
            "2021. Javier Jesús Peña Rodríguez\n"
            "2022. Manuel Barcia Osuna\n"
            "2023. Alicia de los Ángeles Castro García\n"
            "2024. Pablo Sánchez Arias"
        )

        comunicado_3 = Comunicado(
            titulo="Nombramiento del cartelista del Pregón de la Juventud 2025",
            contenido=contenido_comunicado_3,
            fecha_emision=make_aware(datetime(2025, 3, 5, 12, 0)),
            tipo_comunicacion='GENERAL',
            autor_id=1353,
            embedding=None
        )

        ruta_imagen_3 = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'Pregon.jpg')
        
        if os.path.exists(ruta_imagen_3):
            with open(ruta_imagen_3, 'rb') as f:
                comunicado_3.imagen_portada.save('Pregon.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Comunicado 3.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen_3}'))

        comunicado_3.save()

        comunicado_3.areas_interes.set([3, 9])

        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Comunicado 2 asociado a las áreas ID 3 y 9.'))



        # =========================================================================
        # POBLADO DE COMUNICADO 4
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Comunicado 4...")

        contenido_comunicado_4 = (
            "Una vez que ha quedado atrás nuestra Semana Santa, la diputación de juventud prepara la tradicional procesión de la Cruz de Mayo, cuya salida está prevista para la tarde del próximo sábado 11 de mayo.\n\n"
            "Todos aquellos jóvenes que, teniendo cumplidos, al menos, los 14 años de edad, quieran participar como costaleros, habrán de acudir a nuestra casa de hermandad este viernes 5 de abril de 2024 a las 18 horas para la igualá en nuestra casa hermandad, sita en la Avenida de Coria número 13.\n\n"
            "Por último, se hace saber a todos aquellos jóvenes que quieran ser costaleros que habrán de usar calzado negro obligatoriamente."
        )

        comunicado_4 = Comunicado(
            titulo="Preparativos para la procesión de la Cruz de Mayo del grupo joven en 2024",
            contenido=contenido_comunicado_4,
            fecha_emision=make_aware(datetime(2024, 4, 2, 12, 0)),
            tipo_comunicacion='GENERAL',
            autor_id=1353
        )

        comunicado_4.save()

        ruta_imagen_4 = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'comunicados', 'CruzMayo.jpg')
        
        if os.path.exists(ruta_imagen_4):
            with open(ruta_imagen_4, 'rb') as f:
                comunicado_4.imagen_portada.save('CruzMayo.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Comunicado 4.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen_4}'))

        comunicado_4.save()

        comunicado_4.areas_interes.set([3, 9])

        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Comunicado 4 asociado a las áreas ID 3 y 9.'))



        # =========================================================================
        # POBLADO DE COMUNICADO 5
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Comunicado 5...")

        contenido_comunicado_5 = (
            "Nuestras imágenes titulares han sido revestidas para el resto del actual tiempo de Pascua de Resurrección que estamos viviendo, una vez que la Semana Santa forma ya parte de nuestros recuerdos, con la dicha de haber podido realizar la estación de penitencia en un año tan complejo debido a la situación meteorológica.\n\n"
            "Nuestro Padre Jesús en Su Soberano Poder, revestido por nuestro hermano Mateo Domingo González Gago, luce, como es habitual en estas fechas, una túnica blanca lisa en clara alusión al tiempo festivo y triunfante que vive la Iglesia en su calendario litúrgico.\n\n"
            "Nuestra Señora de la Salud ha sido revestida por Antonio Bejarano Ruiz, portando la saya blanca ejecutada en 2013 por Jesús Rosado Borja y luciendo el manto azul pavo bordado por Mariano Martín Santonja en 2014, sobre el que ostenta una toca de encaje de punto de España elaborada con la técnica de bolillo de oro. Así mismo, asido a su cintura, la Virgen porta el fajín bordado por José Librero Fernández en 2017 y que fue donado por la coronación por un grupo de cuatro jóvenes hermanos.\n\n"
            "Entre las piezas de su ajuar, en el pecho de la Señora aparece el broche de la Fuente de la Salud labrado por Fernando Marmolejo Hernández y donado por el cuerpo de acólitos de la coronación canónica, y junto a éste también luce el donado por la Hermandad de la Hiniesta, regalado por el acontecimiento ya citado en 2017, y que luce en esta ocasión por el próximo cincuentenario de la coronación de Santa María de la Hiniesta Gloriosa y el CCCLXXV aniversario del voto de la ciudad de Sevilla a esta efigie como acción de gracias tras la epidemia de peste que asoló nuestra urbe en 1649.\n\n"
            "San Juan Evangelista porta túnica blanca lisa y mantolín rojo, en clara alusión a la próxima solemnidad de Pentecostés, con la que culminan los cincuenta días de la Pascua de Resurrección."
        )

        comunicado_5 = Comunicado(
            titulo="Nuestros titulares, revestidos para el resto del tiempo pascual de Resurrección de 2024",
            contenido=contenido_comunicado_5,
            fecha_emision=make_aware(datetime(2025, 4, 10, 12, 0)),
            tipo_comunicacion='GENERAL',
            autor_id=1353
        )

        comunicado_5.save()

        ruta_imagen_5 = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'comunicados', 'Pascua2024.jpg')
        
        if os.path.exists(ruta_imagen_5):
            with open(ruta_imagen_5, 'rb') as f:
                comunicado_5.imagen_portada.save('Pascua2024.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Comunicado 5.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen_5}'))

        comunicado_5.save()

        comunicado_5.areas_interes.set([9])

        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Comunicado 5 asociado al área ID 9.'))



        # =========================================================================
        # POBLADO DE COMUNICADO 6
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Comunicado 6...")

        contenido_comunicado_6 = (
            "El pasado domingo 26 de mayo, festividad de la Santísima Trinidad y jornada en la que se desarrolla la procesión eucarística de nuestra corporación, tuvo lugar el estreno y bendición del nuevo ostensorio para Su Divina Majestad, que bajo diseño de Francisco Javier Sánchez de los Reyes ha labrado el taller de Jesús Domínguez, tal y como se aprobó en el cabildo general de hermanos del domingo 4 de febrero de 2024.\n\n"
            "Según el diseñador, Sánchez de los Reyes, el ostensorio para el Santísimo Sacramento «mantiene la estructura clásica de este tipo de piezas, de estilo renacimiento, con la inscripción alrededor del viril “EGO SUM PANIS VITAE”, entre espigas de trigo; posee una doble ráfaga, con objeto de destacar y focalizar la visión en la Sagrada Forma una vez colocado sobre la custodia procesional que ya posee la hermandad, rematándose en un pequeño Calvario». La pieza ha sido labrada en plata de ley en su color."
        )

        comunicado_6 = Comunicado(
            titulo="Estrenado el nuevo ostensorio para Su Divina Majestad",
            contenido=contenido_comunicado_6,
            fecha_emision=make_aware(datetime(2024, 5, 28, 12, 0)),
            tipo_comunicacion='GENERAL',
            autor_id=1353
        )

        comunicado_6.save()

        ruta_imagen_6 = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'comunicados', 'Ostensorio2024.jpg')
        
        if os.path.exists(ruta_imagen_6):
            with open(ruta_imagen_6, 'rb') as f:
                comunicado_6.imagen_portada.save('Ostensorio2024.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Comunicado 6.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen_6}'))

        comunicado_6.save()

        comunicado_6.areas_interes.set([4, 9])

        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Comunicado 6 asociado a las áreas ID 4 y 9.'))



        # =========================================================================
        # POBLADO DE COMUNICADO 7
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Comunicado 7...")

        contenido_comunicado_7 = (
            "La Junta de Gobierno, reunida en Cabildo Extraordinario de Oficiales el día 10 de junio de 2024, tomó el siguiente acuerdo:\n\n"
            "Aprobar, la apertura de un expediente para la separación o pérdida de la cualidad de hermano y regularización de la misma, "
            "a aquellos hermanos con cuotas pendientes, superiores al importe equivalente a más de dos años, de acuerdo con lo establecido "
            "en la Regla 13 Aptado. 5 de nuestra corporación."
        )

        comunicado_7 = Comunicado(
            titulo="Acuerdo adoptado por la junta de gobierno en cabildo extraordinario de oficiales de 11 de junio de 2024",
            contenido=contenido_comunicado_7,
            fecha_emision=make_aware(datetime(2024, 6, 12, 12, 0)),
            tipo_comunicacion='GENERAL',
            autor_id=1353
        )

        comunicado_7.save()

        comunicado_7.areas_interes.set([9])

        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Comunicado 7 asociado al área ID 9.'))



        # =========================================================================
        # POBLADO DE COMUNICADO 8
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Comunicado 8...")

        contenido_comunicado_8 = (
            "En la tarde del sábado 31 de agosto, Nuestra Señora de la Salud se halla presidiendo el presbiterio de la Parroquia de San Gonzalo con motivo de su misa solemne del domingo 1 de septiembre y besamano como conmemoración de su antigua festividad del pasado 26 de agosto. La Santísima Virgen, revestida por Antonio Bejarano Ruiz, luce la saya bordada en 2017 en el taller de Jesús Rosado Borja con diseño de Francisco Javier Sánchez de los Reyes y el manto de salida ejecutado y dibujado por los mismos artistas, respectivamente, en 2023, siendo la primera vez que nuestra titular mariana luce esta prenda en un besamano. Sobre sus sienes, la Señora porta la presea labrada en plata por Fernando Marmolejo Camargo en 1967 y remozada y enriquecida en 2017 con oro y piedras preciosas por su hijo, Fernando Marmolejo Hernández, para la coronación canónica. A la cintura se anuda un fajín bordado en el taller de José Librero Fernández y estrenado igualmente en el citado 2017 por la gozosa efemérides ya referida. El tocado es un encaje de punto de aguja, lucido por nuestra dolorosa aquel inolvidable sábado 14 de octubre de 2017. Entre las joyas cabe destacar la medalla de oro de la Asociación de la Medalla Milagrosa de nuestra parroquia, los broches de las hermandades de la Paz y de la Sanidad de Cádiz, así como las medallas de oro con los titulares de la Hermandad del Baratillo como guiño a la inminente coronación de Nuestra Señora de la Piedad. Y en el centro del pecho, la réplica de la Medalla de la Ciudad de Sevilla.\n\n"
            "El aparato de cultos se erige como un salón de trono en torno a un pabellón real, timbrado por una corona de la Hermandad de Valme, Protectora de Dos Hermanas, y que se completa con unas columnas de la Hermandad de la Soledad de San Lorenzo, cortinas de terciopelo burdeos y peanín de la Hermandad de la Estrella y trono de María Santísima del Refugio de la Hermandad de San Bernardo, todo ello cedido por cada una de estas corporaciones, al igual que la de las Siete Palabras ha prestado las consolas y la del Rocío de Triana sus jarras cerámicas, distribuyéndose entre las mismas el exorno floral, consistente en nardos y claveles bicolor (crema y rosa). En el presbiterio cuelgan lámparas de cristal de nuestro patrimonio, y Nuestra Señora de la Salud se ubica sobre la alfombra elaborada por Baldomero, de Castilleja de la Cuesta, en 2022. Finalmente, en el conjunto se disponen cuatro ángeles del escultor Augusto Morilla procedentes del patrimonio de la Asociación de María Auxiliadora de Triana, y otros dos más del escultor Manuel Ramos Corona procedentes de la Hermandad del Rosario del Barrio León.\n\n"
            "Recordamos que el besamano será este sábado 31 de agosto de 19 a 21 horas, con misa a las 20, y el domingo 1 de septiembre, de 9 a 14 y de 17 a 21 horas, con misas a las 10, 12 y 20 horas, siendo la de las 12 la dedicada a Nuestra Señora de la Salud, la cual se emitirá en directo en el canal de YouTube de nuestra Hermandad de San Gonzalo. El horario de fotógrafos y videógrafos con trípodes u otros elementos de apoyo será exclusivamente de 8:15 a 9 horas del domingo, antes de la apertura del templo parroquial por la mañana."
        )

        comunicado_8 = Comunicado(
            titulo="Nuestra Señora de la Salud, expuesta en besamano en conmemoración de su antigua festividad",
            contenido=contenido_comunicado_8,
            fecha_emision=make_aware(datetime(2024, 8, 31, 12, 0)),
            tipo_comunicacion='GENERAL',
            autor_id=1353
        )

        comunicado_8.save()

        ruta_imagen_8 = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'comunicados', 'BesamanosAgosto2024.jpg')
        
        if os.path.exists(ruta_imagen_8):
            with open(ruta_imagen_8, 'rb') as f:
                comunicado_8.imagen_portada.save('BesamanosAgosto2024.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Comunicado 8.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen_8}'))

        comunicado_8.save()

        comunicado_8.areas_interes.set([5, 9])

        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Comunicado 8 asociado a las áreas ID 5 y 9.'))



        # =========================================================================
        # POBLADO DE COMUNICADO 9
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Comunicado 9...")

        contenido_comunicado_9 = (
            "La Asociación Musical María Santísima de la Victoria ha tomado la decisión de que en este año 2024 "
            "le sea entregado su galardón Madre Cigarrera a nuestra Hermandad de San Gonzalo, una distinción que "
            "será recogida por nuestro hermano mayor, Manuel Lobo, el próximo sábado 23 de noviembre, a la "
            "finalización del concierto en honor a Santa Cecilia que dicha corporación penitencial organiza "
            "esa misma tarde a partir de las 19 horas.\n\n"
            
            "Este galardón se concede a nuestra hermandad, según se hace saber por el propio colectivo musical, "
            "“Por el vínculo mantenido y el apoyo mostrado durante los más de 45 años de historia de las "
            "formaciones musicales nacidas en el seno de nuestra asociación, habiéndose mantenido desde la "
            "fundación de la Banda Nuestra Señora de la Victoria, hasta la fecha actual, así como con la "
            "Banda Juvenil (hoy día Banda Columna y Azotes), lo que sin duda nos hace sentirla como nuestra "
            "y uno de los pilares donde se sustenta el espíritu musical de Las Cigarreras”.\n\n"
            
            "Este galardón alcanza ya su duodécima edición, habiéndosele entregado anteriormente a:\n"
            "■ Pedro Morales Muñoz (2010).\n"
            "■ Francisco Javier Gutiérrez Juan (2011).\n"
            "■ Francisco Javier González Ríos (2012).\n"
            "■ Bienvenido Puelles Oliver (2013).\n"
            "■ Hermandad de la Sagrada Cena (2014).\n"
            "■ Bartolomé Gómez Meliá (2015).\n"
            "■ Banda de Música del Maestro Tejera (2016).\n"
            "■ Círculo Mercantil e Industrial de Sevilla (2019).\n"
            "■ Antonio González Ríos (2021).\n"
            "■ Pedro Manuel Pacheco Palomo (2022).\n"
            "■ José Antonio Herrera Solís (2023)."
        )

        comunicado_9 = Comunicado(
            titulo="El Galardón Madre Cigarrera de 2024 es concedido a nuestra Hermandad de San Gonzalo",
            contenido=contenido_comunicado_9,
            fecha_emision=make_aware(datetime(2024, 10, 10, 12, 0)),
            tipo_comunicacion='GENERAL',
            autor_id=1353
        )

        comunicado_9.save()

        ruta_imagen_9 = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'comunicados', 'Galardon.jpg')
        
        if os.path.exists(ruta_imagen_9):
            with open(ruta_imagen_9, 'rb') as f:
                comunicado_9.imagen_portada.save('Galardon.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Comunicado 9.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen_9}'))

        comunicado_9.save()

        comunicado_9.areas_interes.set([9])

        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Comunicado 9 asociado al área 9.'))



        # =========================================================================
        # POBLADO DE COMUNICADO 10
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Comunicado 10...")

        contenido_comunicado_10 = (
            "La junta de gobierno, reunida en cabildo ordinario de oficiales el martes 8 de octubre de 2024, tomó los siguientes acuerdos:\n\n"
            "• Convocar cabildo general extraordinario de modificación de reglas para el sábado 30 de noviembre de 2024.\n"
            "• Aprobar el procedimiento para la presentación de enmiendas al proyecto de reforma de reglas.\n"
            "• Solicitar a la autoridad eclesiástica, con motivo del II Congreso Internacional de Hermandades y Piedad Popular, "
            "permiso para celebrar los días 5 y 6 de diciembre besamano extraordinario a Nuestro Padre Jesús en Su Soberano Poder ante Caifás."
        )

        comunicado_10 = Comunicado(
            titulo="Acuerdos adoptados por la junta de gobierno en cabildo ordinario de oficiales del martes 8 de octubre de 2024",
            contenido=contenido_comunicado_10,
            fecha_emision=make_aware(datetime(2024, 10, 11, 12, 0)),
            tipo_comunicacion='GENERAL',
            autor_id=1353
        )

        comunicado_10.save()

        comunicado_10.areas_interes.set([9])

        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Comunicado 10 asociado al área ID 9.'))



        # =========================================================================
        # POBLADO DE COMUNICADO 11
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Comunicado 11...")

        contenido_comunicado_11 = (
            "Con motivo del Jubileo Universal del Año Santo, declarado por el papa Pablo VI desde el 23 de mayo de 1974 -aunque no se inauguraría hasta la Nochebuena siguiente- y ganar las indulgencias del mismo en sus preparativos, la Hermandad de San Gonzalo decidió en cabildo de oficiales celebrado el 9 de agosto de 1974, y presidido por Antonio Garduño Navas como hermano mayor, llevar procesionalmente a Nuestra Señora de la Salud hasta la Real Parroquia de Señora Santa Ana, fijándose la salida el sábado 19 de octubre de aquel año.\n\n"
            "Salió a las seis de la tarde de su sede canónica, la Parroquia de San Gonzalo, y utilizó para este culto externo extraordinario el paso de la Divina Pastora de Triana, eliminándose su manto para que la Virgen fuese sobre la peana de salida de su paso de palio, si bien los candelabros no eran los de estas andas pastoreñas, siendo unos dorados -tal vez los de María Auxiliadora de Triana-, y además sería la primera vez que la cofradía saldría a la calle con hermanos costaleros comandados por el capataz Juan Vizcaya Vargas, a la sazón prioste primero de la hermandad en ese momento, si bien esta cuadrilla no participaría en la estación de penitencia hasta el Lunes Santo de 1976.\n\n"
            "La Virgen portaba la corona de plata sobredorada de Fernando Marmolejo Camargo, ofrendada a la Señora en 1967, y lucía la saya que Antonio Rincón Galicia confeccionase en 1965 sobre un traje nupcial con bordados de un traje de luces donado por el diestro Paco Camino, pieza que en aquellos años formaba parte del ajuar de salida de la dolorosa cada Lunes Santo, aunque no llevó manto blanco, sino uno burdeos liso.\n\n"
            "El recorrido parece ser que fue este: Nuestra Señora de la Salud, Giralda, San Martín de Porres, Asturias, Evangelista, Pagés del Corro, pasaje de Bernal Vidal -actual Santísimo Cristo de las Tres Caídas-, Pelay Correa, Plazuela de Santa Ana (se accede al interior del templo, saliendo nuevamente por la misma puerta), Vázquez de Leca -hoy Párroco Don Eugenio-, Pureza (estación en la capilla de los Marineros de la Hermandad de la Esperanza de Triana), Altozano, San Jacinto (parada ante la casa de hermandad de la Estrella, lugar donde hoy se alza su capilla), San Martín de Porres y Nuestra Señora de la Salud."
        )

        comunicado_11 = Comunicado(
            titulo="Cincuenta años de la salida extraordinaria a Santa Ana de Nuestra Señora de la Salud",
            contenido=contenido_comunicado_11,
            fecha_emision=make_aware(datetime(2024, 10, 19, 12, 0)),
            tipo_comunicacion='GENERAL',
            autor_id=1353
        )

        comunicado_11.save()

        ruta_imagen_11 = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'comunicados', 'ExtraordinariaSalud1974.jpg')
        
        if os.path.exists(ruta_imagen_11):
            with open(ruta_imagen_11, 'rb') as f:
                comunicado_11.imagen_portada.save('ExtraordinariaSalud1974.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Comunicado 11.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen_11}'))

        comunicado_11.save()

        comunicado_11.areas_interes.set([7, 9])

        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Comunicado 11 asociado a las áreas ID 7 y 9.'))



        # =========================================================================
        # POBLADO DE COMUNICADO 12
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Comunicado 12...")

        contenido_comunicado_12 = (
            "La Junta de Gobierno, reunida en cabildo de oficiales ordinario el miércoles 29 de enero de 2025, tomó los siguientes acuerdos:\n\n"
            "• Aprobar, el acta del cabildo de oficiales ordinario de fecha 2 de diciembre de 2024.\n"
            "• Aprobar, las cuentas presentadas por mayordomía a 31 de diciembre de 2024.\n"
            "• Aprobar, los presupuestos para 2025, presentados por mayordomía.\n"
            "• Solicitar, al Delgado Diocesano para asuntos jurídicos, dispensa, para poder proceder según lo establecido en la Regla 106, detallada en las nuevas reglas aprobadas por los hermanos en Cabildo Extraordinario de Reglas de fecha 30 de noviembre de 2024."
        )

        comunicado_12 = Comunicado(
            titulo="Acuerdos adoptados por la junta de gobierno en cabildo ordinario de oficiales.",
            contenido=contenido_comunicado_12,
            fecha_emision=make_aware(datetime(2025, 2, 6, 12, 0)),
            tipo_comunicacion='GENERAL',
            autor_id=1353
        )

        comunicado_12.save()

        comunicado_12.areas_interes.set([9])

        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Comunicado 12 asociado al área ID 9.'))



        # =========================================================================
        # POBLADO DE COMUNICADO 13
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Comunicado 13...")

        contenido_comunicado_13 = (
            "La sala capital baja del Excmo. Ayuntamiento de Sevilla, acogió hoy viernes 14 de febrero de 2025, la presentación de la nueva túnica para Nuestro Padre Jesús en Su Soberano Poder ante Caifás.\n\n"
            "Cabe recordar que los hermanos, reunidos en el cabildo general de hermanos celebrado el 4 de febrero de 2024 en los salones parroquiales de la Parroquia de San Gonzalo aprobaron la ejecución del diseño presentado por la junta de gobierno.\n\n"
            "El diseño fue presentado por D. Javier Sánchez de los Reyes, autor del mismo, quien explicó que se trataría de una túnica de estilo persa, bordada en oro, realizada en tela de tisú blanco de la misma tela con la que se confeccionó el manto bordado de Ntra. Sra. de la Salud presentado el 1 de marzo de 2023 en el patio de la sede social en Sierpes del Círculo Mercantil e Industrial de Sevilla y su ejecución se ha llevado a cabo por el taller de bordados de D. Joaquín Salcedo Canca.\n\n"
            "Esta túnica ha sido bordada casi en su totalidad a lo largo del año 2024 y principios de 2025, en pecho, dos mangas, espalda y falda tanto delantera como trasera, dejando libre el espacio para el cíngulo. Detallar que se han bordado las costuras laterales de la túnica, algo importante para que la túnica no quede de forma almendrada sino redondeada y al ponerla luzca mucho más. Ha sido bordada con un volumen discreto aunque por cercanía de éste taller de bordados al diseñador, éste ha seguido de cerca su ejecución asesorando al bordador ante las dudas que tuviera."
        )

        comunicado_13 = Comunicado(
            titulo="Presentación de la nueva túnica bordada para Ntro. Padre Jesús en Su Soberano Poder",
            contenido=contenido_comunicado_13,
            fecha_emision=make_aware(datetime(2025, 2, 14, 12, 0)),
            tipo_comunicacion='GENERAL',
            autor_id=1353
        )

        comunicado_13.save()

        ruta_imagen_13 = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'comunicados', 'Tunica.jpg')
        
        if os.path.exists(ruta_imagen_13):
            with open(ruta_imagen_13, 'rb') as f:
                comunicado_13.imagen_portada.save('Tunica.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Comunicado 13.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen_13}'))

        comunicado_13.save()

        comunicado_13.areas_interes.set([4, 9])

        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Comunicado 13 asociado a las áreas ID 4 y 9.'))



        # =========================================================================
        # POBLADO DE COMUNICADO 14
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Comunicado 14...")

        contenido_comunicado_14 = (
            "En el cabildo general ordinario celebrado el domingo 16 de febrero de 2025, se tomaron los siguientes acuerdos:\n\n"
            "• Aprobar el acta del cabildo general ordinario anterior.\n"
            "• Aprobar la memoria de actividades del año 2024 presentada por secretaría.\n"
            "• Aprobar las cuentas presentadas por mayordomía a sábado 31 de diciembre de 2024.\n"
            "• Aprobar los presupuestos para 2025, presentados por mayordomía."
        )

        comunicado_14 = Comunicado(
            titulo="Acuerdos adoptados en cabildo general ordinario del 16 de febrero de 2025",
            contenido=contenido_comunicado_14,
            fecha_emision=make_aware(datetime(2025, 2, 20, 12, 0)),
            tipo_comunicacion='GENERAL',
            autor_id=1353
        )

        comunicado_14.save()

        comunicado_14.areas_interes.set([9])

        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Comunicado 14 asociado al área ID 9.'))



        # =========================================================================
        # POBLADO DE COMUNICADO 15
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Comunicado 15...")

        contenido_comunicado_15 = (
            "Nuestra tradicional comida de hermandad se desarrollará el próximo domingo 9 de marzo, "
            "tras la función principal de instituto, en el Restaurante Muelle 21 (Avenida Santiago Montoto "
            "sin número, Edificio Acuario de Sevilla, pudiéndose acudir desde nuestra feligresía en la "
            "línea 6 de TUSSAM) a partir de las 14:45 horas.\n\n"
            "El precio por cubierto será de 48 euros para los adultos y 26 euros hasta los catorce años de edad. "
            "Se pueden retirar las invitaciones en mayordomía, siendo el último día para ello el Miércoles de "
            "Ceniza 5 de marzo, semana del quinario en honor a Nuestro Padre Jesús en Su Soberano Poder."
        )

        comunicado_15 = Comunicado(
            titulo="Comida de hermandad 2025",
            contenido=contenido_comunicado_15,
            fecha_emision=make_aware(datetime(2025, 2, 24, 12, 0)),
            tipo_comunicacion='GENERAL',
            autor_id=1353
        )

        comunicado_15.save()

        ruta_imagen_15 = os.path.join(settings.BASE_DIR, '..', 'frontend', 'src', 'assets', 'comunicados', 'Muelle.jpg')
        
        if os.path.exists(ruta_imagen_15):
            with open(ruta_imagen_15, 'rb') as f:
                comunicado_15.imagen_portada.save('Muelle.jpg', File(f), save=False)
            self.stdout.write(self.style.SUCCESS('Imagen adjuntada correctamente al Comunicado 15.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ No se encontró la imagen en: {ruta_imagen_15}'))

        comunicado_15.save()

        comunicado_15.areas_interes.set([9])

        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Comunicado 15 asociado al área ID 9.'))





















        comunicados_sin_vector = Comunicado.objects.filter(embedding__isnull=True)
        for comunicado in comunicados_sin_vector:
            generar_y_guardar_embedding_sync(comunicado.id)
            time.sleep(2)
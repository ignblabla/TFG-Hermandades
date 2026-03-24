from ...models import Acto, Comunicado, CuerpoPertenencia, Cuota, DatosBancarios, Hermano, AreaInteres, Puesto, TipoActo, TipoPuesto
from datetime import date
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Puebla la base de datos con hermanos de prueba y áreas de interés'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando el poblado de datos...")

        with transaction.atomic():

            # =========================================================================
            # LIMPIEZA PREVIA DE TABLAS
            # =========================================================================
            Acto.objects.all().delete()
            TipoActo.objects.all().delete()
            TipoPuesto.objects.all().delete()
            AreaInteres.objects.all().delete()
            CuerpoPertenencia.objects.all().delete()
            Comunicado.objects.all().delete()
            Cuota.objects.all().delete()
            Hermano.objects.all().delete()

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
            ]

            tipos_acto_a_crear = [TipoActo(**data) for data in tipos_acto_data]
            TipoActo.objects.bulk_create(tipos_acto_a_crear)
            
            self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(tipos_acto_a_crear)} tipos de acto.'))

            # =========================================================================
            # POBLADO DE ÁREAS DE INTERÉS
            # =========================================================================
            self.stdout.write("Iniciando el poblado de Áreas de Interés...")
            
            areas_data = [
                {"nombre_area": "CARIDAD", "telegram_channel_id": "-1003771492735", "telegram_invite_link": "https://t.me/+6COuAR98wTg4ZTg0"},
                {"nombre_area": "CULTOS_FORMACION", "telegram_channel_id": "-1003810636379", "telegram_invite_link": "https://t.me/+y6RU6E-56GlwZjk0"},
                {"nombre_area": "JUVENTUD", "telegram_channel_id": "-1003712795257", "telegram_invite_link": "https://t.me/+YLUtzvpqJ0UwNzdk"},
                {"nombre_area": "PATRIMONIO", "telegram_channel_id": "-1003845246574", "telegram_invite_link": "https://t.me/+0pt8qkh_swYwZjY0"},
                {"nombre_area": "PRIOSTIA", "telegram_channel_id": "-1003827691615", "telegram_invite_link": "https://t.me/+kBu6wbNcxyU4MTFk"},
                {"nombre_area": "DIPUTACION_MAYOR_GOBIERNO", "telegram_channel_id": "-1003752302067", "telegram_invite_link": "https://t.me/+RSbb2civhvsyYjk8"},
                {"nombre_area": "COSTALEROS", "telegram_channel_id": "-1003754745133", "telegram_invite_link": "https://t.me/+W-HAa5nMjLNINTc0"},
                {"nombre_area": "ACOLITOS", "telegram_channel_id": "-1003681055153", "telegram_invite_link": "https://t.me/+sVPhJF3zi3wyNjI0"},
                {"nombre_area": "TODOS_HERMANOS", "telegram_channel_id": "-1003835565597", "telegram_invite_link": "https://t.me/+gs2wua73Y003N2M0"},
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
                
                self.stdout.write(self.style.SUCCESS('Hermano número 1 creado'))


            if not Hermano.objects.filter(dni="11111111B").exists():
                Hermano.objects.create_user(id=2, nombre="Francisco", primer_apellido="Barrio", segundo_apellido="Muñoz",
                    dni="11111111B", username="11111111B", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="pacobarrio@gmail.com", telefono="649146786", estado_civil="CASADO",
                    fecha_nacimiento="1968-05-07",genero="MASCULINO",
                    direccion="Calle Cristo del SOberano Poder, 16", localidad="Sevilla", codigo_postal = "41010",
                    provincia="Sevilla",comunidad_autonoma="Andalucía",
                    fecha_bautismo="1968-10-25", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Gonzalo",
                    estado_hermano = "ALTA", numero_registro="2", fecha_ingreso_corporacion="1973-03-02")
                
                self.stdout.write(self.style.SUCCESS('Hermano número 2 creado'))

            if not Hermano.objects.filter(dni="11111111C").exists():
                Hermano.objects.create_user(id=3, nombre="Antonio", primer_apellido="García", segundo_apellido="López",
                    dni="11111111C", username="11111111C", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="antoniogarcia@gmail.com", telefono="646172203", estado_civil="SOLTERO",
                    fecha_nacimiento="1958-02-14", genero="MASCULINO",
                    direccion="Calle Pureza, 10", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1958-03-20", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de Santa Ana",
                    estado_hermano="ALTA", numero_registro="3", fecha_ingreso_corporacion="1974-05-15")
                
                self.stdout.write(self.style.SUCCESS('Hermano número 3 creado'))

            # --- HERMANO 4 (1975) ---
            if not Hermano.objects.filter(dni="11111111D").exists():
                Hermano.objects.create_user(id=4, nombre="Manuel", primer_apellido="Rodríguez", segundo_apellido="Sánchez",
                    dni="11111111D", username="11111111D", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="manuelrodriguez@hotmail.com", telefono="646172204", estado_civil="CASADO",
                    fecha_nacimiento="1960-11-05", genero="MASCULINO",
                    direccion="Avda. de Coria, 22", localidad="Triana", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1960-12-01", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Jacinto",
                    estado_hermano="ALTA", numero_registro="4", fecha_ingreso_corporacion="1975-09-20")

                self.stdout.write(self.style.SUCCESS('Hermano número 4 creado'))

            # --- HERMANO 5 (1977) ---
            if not Hermano.objects.filter(dni="11111111E").exists():
                Hermano.objects.create_user(id=5, nombre="José María", primer_apellido="Pérez", segundo_apellido="Gómez",
                    dni="11111111E", username="11111111E", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="jmperez@yahoo.es", telefono="646172205", estado_civil="SEPARADO",
                    fecha_nacimiento="1962-07-22", genero="MASCULINO",
                    direccion="Calle Betis, 5", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1962-08-15", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de Santa Ana",
                    estado_hermano="ALTA", numero_registro="5", fecha_ingreso_corporacion="1977-02-10")

                self.stdout.write(self.style.SUCCESS('Hermano número 5 creado'))

            # --- HERMANO 6 (1979) ---
            if not Hermano.objects.filter(dni="11111111F").exists():
                Hermano.objects.create_user(id=6, nombre="David", primer_apellido="Sánchez", segundo_apellido="Ruiz",
                    dni="11111111F", username="11111111F", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="davidsanchez@gmail.com", telefono="646172206", estado_civil="SOLTERO",
                    fecha_nacimiento="1970-01-30", genero="MASCULINO",
                    direccion="Plaza del Altozano, 2", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1970-03-15", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Gonzalo",
                    estado_hermano="ALTA", numero_registro="6", fecha_ingreso_corporacion="1979-06-05")

                self.stdout.write(self.style.SUCCESS('Hermano número 6 creado'))

            # --- HERMANO 7 (1981) ---
            if not Hermano.objects.filter(dni="11111111G").exists():
                Hermano.objects.create_user(id=7, nombre="Juan", primer_apellido="González", segundo_apellido="Torres",
                    dni="11111111G", username="11111111G", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="juangonzalez@outlook.com", telefono="646172207", estado_civil="CASADO",
                    fecha_nacimiento="1965-09-12", genero="MASCULINO",
                    direccion="Calle San Jacinto, 45", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1965-10-10", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Jacinto",
                    estado_hermano="ALTA", numero_registro="7", fecha_ingreso_corporacion="1981-11-30")

                self.stdout.write(self.style.SUCCESS('Hermano número 7 creado'))

            # --- HERMANO 8 (1983) ---
            if not Hermano.objects.filter(dni="11111111H").exists():
                Hermano.objects.create_user(id=8, nombre="Miguel Ángel", primer_apellido="Fernández", segundo_apellido="Martín",
                    dni="11111111H", username="11111111H", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="miguelangel@us.es", telefono="646172208", estado_civil="VIUDO",
                    fecha_nacimiento="1955-04-04", genero="MASCULINO",
                    direccion="Calle Pagés del Corro, 80", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1955-05-05", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Gonzalo",
                    estado_hermano="ALTA", numero_registro="8", fecha_ingreso_corporacion="1983-05-22")

                self.stdout.write(self.style.SUCCESS('Hermano número 8 creado'))

            # --- HERMANO 9 (1985) ---
            if not Hermano.objects.filter(dni="11111111I").exists():
                Hermano.objects.create_user(id=9, nombre="Javier", primer_apellido="López", segundo_apellido="Díaz",
                    dni="11111111I", username="11111111I", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="javierlopez@gmail.com", telefono="646172209", estado_civil="SOLTERO",
                    fecha_nacimiento="1975-12-24", genero="MASCULINO",
                    direccion="Calle Alfarería, 12", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1976-02-02", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de Santa Ana",
                    estado_hermano="ALTA", numero_registro="9", fecha_ingreso_corporacion="1985-01-14")

                self.stdout.write(self.style.SUCCESS('Hermano número 9 creado'))

            # --- HERMANO 10 (1986) ---
            if not Hermano.objects.filter(dni="11111111J").exists():
                Hermano.objects.create_user(id=10, nombre="Carlos", primer_apellido="Martínez", segundo_apellido="Romero",
                    dni="11111111J", username="11111111J", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="carlosmartinez@empresa.com", telefono="646172210", estado_civil="CASADO",
                    fecha_nacimiento="1969-08-18", genero="MASCULINO",
                    direccion="Calle Castilla, 33", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1969-09-20", lugar_bautismo="Sevilla", parroquia_bautismo="Basílica del Cachorro",
                    estado_hermano="ALTA", numero_registro="10", fecha_ingreso_corporacion="1986-08-09")

                self.stdout.write(self.style.SUCCESS('Hermano número 10 creado'))

            # --- HERMANO 11 (1988) ---
            if not Hermano.objects.filter(dni="11111111K").exists():
                Hermano.objects.create_user(id=11, nombre="Alejandro", primer_apellido="Ruiz", segundo_apellido="Navarro",
                    dni="11111111K", username="11111111K", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="alejandroruiz@gmail.com", telefono="646172211", estado_civil="SOLTERO",
                    fecha_nacimiento="1980-03-03", genero="MASCULINO",
                    direccion="Calle Febo, 9", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1980-04-10", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Gonzalo",
                    estado_hermano="ALTA", numero_registro="11", fecha_ingreso_corporacion="1988-03-27")

                self.stdout.write(self.style.SUCCESS('Hermano número 11 creado'))

            # --- HERMANO 12 (1989) ---
            if not Hermano.objects.filter(dni="11111111L").exists():
                Hermano.objects.create_user(id=12, nombre="Sergio", primer_apellido="Jiménez", segundo_apellido="Castillo",
                    dni="11111111L", username="11111111L", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="sergiojimenez@gmail.com", telefono="646172212", estado_civil="CASADO",
                    fecha_nacimiento="1972-11-11", genero="MASCULINO",
                    direccion="Calle Esperanza de Triana, 55", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1973-01-01", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de Santa Ana",
                    estado_hermano="ALTA", numero_registro="12", fecha_ingreso_corporacion="1989-12-15")

                self.stdout.write(self.style.SUCCESS('Hermano número 12 creado'))

            if not Hermano.objects.filter(dni="11111111M").exists():
                Hermano.objects.create_user(id=13, nombre="Juan Carlos", primer_apellido="Molina", segundo_apellido="Vázquez",
                    dni="11111111M", username="11111111M", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="jcmolina@gmail.com", telefono="646172213", estado_civil="CASADO",
                    fecha_nacimiento="1978-01-15", genero="MASCULINO",
                    direccion="Calle San Vicente de Paúl, 4", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1978-02-20", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Gonzalo",
                    estado_hermano="ALTA", numero_registro="13", fecha_ingreso_corporacion="1990-02-15")

                self.stdout.write(self.style.SUCCESS('Hermano número 13 creado'))

            # --- HERMANO 14 (1991) ---
            if not Hermano.objects.filter(dni="11111111N").exists():
                Hermano.objects.create_user(id=14, nombre="Fernando", primer_apellido="Ortiz", segundo_apellido="Garrido",
                    dni="11111111N", username="11111111N", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="fernandoortiz@hotmail.com", telefono="646172214", estado_civil="SOLTERO",
                    fecha_nacimiento="1982-05-10", genero="MASCULINO",
                    direccion="Calle Evangelista, 23", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1982-06-15", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de Santa Ana",
                    estado_hermano="ALTA", numero_registro="14", fecha_ingreso_corporacion="1991-06-20")

                self.stdout.write(self.style.SUCCESS('Hermano número 14 creado'))

            # --- HERMANO 15 (1992) ---
            if not Hermano.objects.filter(dni="11111111O").exists():
                Hermano.objects.create_user(id=15, nombre="Alberto", primer_apellido="Domínguez", segundo_apellido="Serrano",
                    dni="11111111O", username="11111111O", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="albertods@yahoo.es", telefono="646172215", estado_civil="CASADO",
                    fecha_nacimiento="1970-12-05", genero="MASCULINO",
                    direccion="Calle Trabajo, 8", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1971-01-10", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Jacinto",
                    estado_hermano="ALTA", numero_registro="15", fecha_ingreso_corporacion="1992-04-10")

                self.stdout.write(self.style.SUCCESS('Hermano número 15 creado'))

            # --- HERMANO 16 (1993) ---
            if not Hermano.objects.filter(dni="11111111P").exists():
                Hermano.objects.create_user(id=16, nombre="Ignacio", primer_apellido="Ramos", segundo_apellido="Gil",
                    dni="11111111P", username="11111111P", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="ignacioramos@gmail.com", telefono="646172216", estado_civil="SEPARADO",
                    fecha_nacimiento="1965-08-22", genero="MASCULINO",
                    direccion="Calle Condes de Bustillo, 15", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1965-09-30", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Gonzalo",
                    estado_hermano="ALTA", numero_registro="16", fecha_ingreso_corporacion="1993-09-08")

                self.stdout.write(self.style.SUCCESS('Hermano número 16 creado'))

            # --- HERMANO 17 (1994) ---
            if not Hermano.objects.filter(dni="11111111Q").exists():
                Hermano.objects.create_user(id=17, nombre="Pablo", primer_apellido="Ibáñez", segundo_apellido="Vega",
                    dni="11111111Q", username="11111111Q", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="pabloibanez@outlook.com", telefono="646172217", estado_civil="SOLTERO",
                    fecha_nacimiento="1985-03-14", genero="MASCULINO",
                    direccion="Calle Voluntad, 2", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1985-04-20", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de Santa Ana",
                    estado_hermano="ALTA", numero_registro="17", fecha_ingreso_corporacion="1994-11-25")

                self.stdout.write(self.style.SUCCESS('Hermano número 17 creado'))

            # --- HERMANO 18 (1995) ---
            if not Hermano.objects.filter(dni="11111111R").exists():
                Hermano.objects.create_user(id=18, nombre="Ricardo", primer_apellido="Gil", segundo_apellido="Márquez",
                    dni="11111111R", username="11111111R", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="ricardogil@gmail.com", telefono="646172218", estado_civil="CASADO",
                    fecha_nacimiento="1975-07-07", genero="MASCULINO",
                    direccion="Calle Turruñuelo, 10", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1975-08-08", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Jacinto",
                    estado_hermano="ALTA", numero_registro="18", fecha_ingreso_corporacion="1995-03-30")

                self.stdout.write(self.style.SUCCESS('Hermano número 18 creado'))

            # --- HERMANO 19 (1996) ---
            if not Hermano.objects.filter(dni="11111111S").exists():
                Hermano.objects.create_user(id=19, nombre="Jorge", primer_apellido="Román", segundo_apellido="Cano",
                    dni="11111111S", username="11111111S", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="jorgeroman@us.es", telefono="646172219", estado_civil="SOLTERO",
                    fecha_nacimiento="1988-11-01", genero="MASCULINO",
                    direccion="Calle López de Gomara, 40", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1989-01-15", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Gonzalo",
                    estado_hermano="ALTA", numero_registro="19", fecha_ingreso_corporacion="1996-07-14")

                self.stdout.write(self.style.SUCCESS('Hermano número 19 creado'))

            # --- HERMANO 20 (1997) ---
            if not Hermano.objects.filter(dni="11111111T").exists():
                Hermano.objects.create_user(id=20, nombre="Luis", primer_apellido="Marín", segundo_apellido="Perea",
                    dni="11111111T", username="11111111T", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="luismarin@gmail.com", telefono="646172220", estado_civil="CASADO",
                    fecha_nacimiento="1972-02-28", genero="MASCULINO",
                    direccion="Calle Justino Matute, 5", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1972-03-25", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de Santa Ana",
                    estado_hermano="ALTA", numero_registro="20", fecha_ingreso_corporacion="1997-01-22")

                self.stdout.write(self.style.SUCCESS('Hermano número 20 creado'))

            # --- HERMANO 21 (1998) ---
            if not Hermano.objects.filter(dni="11111111U").exists():
                Hermano.objects.create_user(id=21, nombre="Víctor", primer_apellido="Rubio", segundo_apellido="Sanz",
                    dni="11111111U", username="11111111U", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="victorrubio@hotmail.com", telefono="646172221", estado_civil="SOLTERO",
                    fecha_nacimiento="1990-09-09", genero="MASCULINO",
                    direccion="Plaza de San Martín de Porres, 1", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1990-10-12", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Jacinto",
                    estado_hermano="ALTA", numero_registro="21", fecha_ingreso_corporacion="1998-10-05")

                self.stdout.write(self.style.SUCCESS('Hermano número 21 creado'))

            # --- HERMANO 22 (1999) ---
            if not Hermano.objects.filter(dni="11111111V").exists():
                Hermano.objects.create_user(id=22, nombre="Raúl", primer_apellido="Sáez", segundo_apellido="Lozano",
                    dni="11111111V", username="11111111V", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="raulsaez@gmail.com", telefono="646172222", estado_civil="CASADO",
                    fecha_nacimiento="1976-06-16", genero="MASCULINO",
                    direccion="Calle Santa Cecilia, 14", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1976-07-20", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Gonzalo",
                    estado_hermano="ALTA", numero_registro="22", fecha_ingreso_corporacion="1999-12-12")

                self.stdout.write(self.style.SUCCESS('Hermano número 22 creado'))

            # --- HERMANO 23 (2000) ---
            if not Hermano.objects.filter(dni="11111111W").exists():
                Hermano.objects.create_user(id=23, nombre="Andrés", primer_apellido="Vargas", segundo_apellido="Reyes",
                    dni="11111111W", username="11111111W", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="andresvargas@gmail.com", telefono="646172223", estado_civil="SOLTERO",
                    fecha_nacimiento="1992-02-14", genero="MASCULINO",
                    direccion="Calle Rosario Vega, 3", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1992-03-20", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Gonzalo",
                    estado_hermano="ALTA", numero_registro="23", fecha_ingreso_corporacion="2000-05-15")

                self.stdout.write(self.style.SUCCESS('Hermano número 23 creado'))

            # --- HERMANO 24 (2001) ---
            if not Hermano.objects.filter(dni="11111111X").exists():
                Hermano.objects.create_user(id=24, nombre="Beatriz", primer_apellido="Castro", segundo_apellido="Mora",
                    dni="11111111X", username="11111111X", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="beatrizcastro@hotmail.com", telefono="646172224", estado_civil="CASADO",
                    fecha_nacimiento="1980-11-30", genero="FEMENINO",
                    direccion="Calle Rodrigo de Triana, 12", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1981-01-10", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de Santa Ana",
                    estado_hermano="ALTA", numero_registro="24", fecha_ingreso_corporacion="2001-11-20")

                self.stdout.write(self.style.SUCCESS('Hermano número 24 creado'))

            # --- HERMANO 25 (2002) ---
            if not Hermano.objects.filter(dni="11111111Y").exists():
                Hermano.objects.create_user(id=25, nombre="Camilo", primer_apellido="Nuñez", segundo_apellido="Iglesias",
                    dni="11111111Y", username="11111111Y", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="camilonunez@yahoo.es", telefono="646172225", estado_civil="SOLTERO",
                    fecha_nacimiento="1995-07-07", genero="MASCULINO",
                    direccion="Calle Paraíso, 8", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1995-08-15", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Jacinto",
                    estado_hermano="ALTA", numero_registro="25", fecha_ingreso_corporacion="2002-03-10")

                self.stdout.write(self.style.SUCCESS('Hermano número 25 creado'))

            # --- HERMANO 26 (2003) ---
            if not Hermano.objects.filter(dni="11111111Z").exists():
                Hermano.objects.create_user(id=26, nombre="Dolores", primer_apellido="Fuentes", segundo_apellido="Cano",
                    dni="11111111Z", username="11111111Z", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="lola@gmail.com", telefono="646172226", estado_civil="VIUDO",
                    fecha_nacimiento="1950-01-01", genero="FEMENINO",
                    direccion="Avda. República Argentina, 20", localidad="Sevilla", codigo_postal="41011",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1950-02-02", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de los Remedios",
                    estado_hermano="ALTA", numero_registro="26", fecha_ingreso_corporacion="2003-09-08")

                self.stdout.write(self.style.SUCCESS('Hermano número 26 creado'))

            # --- HERMANO 27 (2004) ---
            if not Hermano.objects.filter(dni="22222222A").exists():
                Hermano.objects.create_user(id=27, nombre="Enrique", primer_apellido="Solís", segundo_apellido="León",
                    dni="22222222A", username="22222222A", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="enriquesolis@gmail.com", telefono="646172227", estado_civil="CASADO",
                    fecha_nacimiento="1975-05-05", genero="MASCULINO",
                    direccion="Calle Salado, 4", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1975-06-06", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Gonzalo",
                    estado_hermano="ALTA", numero_registro="27", fecha_ingreso_corporacion="2004-02-14")

                self.stdout.write(self.style.SUCCESS('Hermano número 27 creado'))

            # --- HERMANO 28 (2005) ---
            if not Hermano.objects.filter(dni="22222222B").exists():
                Hermano.objects.create_user(id=28, nombre="Fátima", primer_apellido="Méndez", segundo_apellido="Cruz",
                    dni="22222222B", username="22222222B", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="fatimamendez@outlook.com", telefono="646172228", estado_civil="SOLTERO",
                    fecha_nacimiento="1998-09-12", genero="FEMENINO",
                    direccion="Calle Arcos, 11", localidad="Sevilla", codigo_postal="41011",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1998-10-20", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Jacinto",
                    estado_hermano="ALTA", numero_registro="28", fecha_ingreso_corporacion="2005-06-30")

                self.stdout.write(self.style.SUCCESS('Hermano número 28 creado'))

            # --- HERMANO 29 (2006) ---
            if not Hermano.objects.filter(dni="53962686V").exists():
                Hermano.objects.create_superuser(id=29, nombre="Ignacio", primer_apellido="Blanquero", segundo_apellido="Blanco",
                    dni="53962686V", username="53962686V", password="1234", is_superuser=True, is_staff=True, is_active=True,
                    esAdmin=True, email="ignacio.blanquero@gmail.com", telefono="644169492", estado_civil="SOLTERO",
                    fecha_nacimiento="2003-01-24",genero="MASCULINO",
                    direccion="Calle Pensamiento, 50", localidad="Mairena del Aljarafe", codigo_postal = "41927",
                    provincia="Sevilla",comunidad_autonoma="Andalucía",
                    fecha_bautismo="2003-04-26", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Gonzalo",
                    estado_hermano = "ALTA", numero_registro="29", fecha_ingreso_corporacion="2006-03-01")
                
                self.stdout.write(self.style.SUCCESS('Hermano número 29 creado'))

            # --- HERMANO 30 (2006) ---
            if not Hermano.objects.filter(dni="22222222C").exists():
                Hermano.objects.create_user(id=30, nombre="Gabriel", primer_apellido="Pascual", segundo_apellido="Guerra",
                    dni="22222222C", username="22222222C", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="gabrielpascual@us.es", telefono="646172229", estado_civil="SEPARADO",
                    fecha_nacimiento="1968-04-15", genero="MASCULINO",
                    direccion="Calle Niebla, 33", localidad="Sevilla", codigo_postal="41011",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1968-05-20", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de Santa Ana",
                    estado_hermano="ALTA", numero_registro="30", fecha_ingreso_corporacion="2006-12-12")

                self.stdout.write(self.style.SUCCESS('Hermano número 30 creado'))

            # --- HERMANO 31 (2007) ---
            if not Hermano.objects.filter(dni="22222222D").exists():
                Hermano.objects.create_user(id=31, nombre="Hugo", primer_apellido="Benítez", segundo_apellido="Roldán",
                    dni="22222222D", username="22222222D", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="hugobenitez@gmail.com", telefono="646172230", estado_civil="SOLTERO",
                    fecha_nacimiento="2000-01-01", genero="MASCULINO",
                    direccion="Calle Farmacéutico Murillo, 5", localidad="Sevilla", codigo_postal="41010",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="2000-02-15", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Gonzalo",
                    estado_hermano="ALTA", numero_registro="31", fecha_ingreso_corporacion="2007-04-05")

                self.stdout.write(self.style.SUCCESS('Hermano número 31 creado'))

            # --- HERMANO 32 (2008) ---
            if not Hermano.objects.filter(dni="22222222E").exists():
                Hermano.objects.create_user(id=32, nombre="Inés", primer_apellido="Carmona", segundo_apellido="Vidal",
                    dni="22222222E", username="22222222E", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="inescarmona@hotmail.com", telefono="646172231", estado_civil="SOLTERO",
                    fecha_nacimiento="1990-08-25", genero="FEMENINO",
                    direccion="Calle Virgen de Luján, 40", localidad="Sevilla", codigo_postal="41011",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1990-10-01", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de los Remedios",
                    estado_hermano="ALTA", numero_registro="32", fecha_ingreso_corporacion="2008-10-20")

                self.stdout.write(self.style.SUCCESS('Hermano número 32 creado'))

            # --- HERMANO 33 (2010) ---
            if not Hermano.objects.filter(dni="22222222F").exists():
                Hermano.objects.create_user(id=33, nombre="Julián", primer_apellido="Herrera", segundo_apellido="Prieto",
                    dni="22222222F", username="22222222F", password="1234", is_superuser=False, is_staff=True, is_active=True,
                    esAdmin=False, email="julianherrera@gmail.com", telefono="646172232", estado_civil="CASADO",
                    fecha_nacimiento="1983-12-10", genero="MASCULINO",
                    direccion="Calle Asunción, 15", localidad="Sevilla", codigo_postal="41011",
                    provincia="Sevilla", comunidad_autonoma="Andalucía",
                    fecha_bautismo="1984-01-20", lugar_bautismo="Sevilla", parroquia_bautismo="Parroquia de San Jacinto",
                    estado_hermano="ALTA", numero_registro="33", fecha_ingreso_corporacion="2010-01-15")

                self.stdout.write(self.style.SUCCESS('Hermano número 33 creado'))

        self.stdout.write(self.style.SUCCESS('¡Proceso de Áreas y Hermanos finalizado con éxito!'))


        # =========================================================================
        # POBLADO DE CUOTAS
        # =========================================================================
        self.stdout.write("Iniciando el poblado masivo de Cuotas...")
        
        Cuota.objects.all().delete()

        with connection.cursor() as cursor:
            # En bases de datos que no lo soporten (como sqlite por defecto) puedes añadir un try/except aquí si da fallo.
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
            fecha=now + timedelta(days=30),
            modalidad="TRADICIONAL",
            tipo_acto_id=1,
            inicio_solicitud=now + timedelta(days=7),
            fin_solicitud=now + timedelta(days=12),
            inicio_solicitud_cirios=now + timedelta(days=13),
            fin_solicitud_cirios=now + timedelta(days=24),
            fecha_ejecucion_reparto=None,
            imagen_portada=None
        )
        
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
        ]

        puestos_virgen_data = [
            {"id": 24, "nombre": "Cirios apagados cruces (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 1, "cortejo_cristo": False},
            {"id": 25, "nombre": "Bocinas (tramo 1)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 8, "cortejo_cristo": False},
            {"id": 26, "nombre": "Simpecado (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 27, "nombre": "Faroles Simpecado (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 9, "cortejo_cristo": False},
            {"id": 28, "nombre": "Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 29, "nombre": "Varas Bandera Blanca y Celeste (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 30, "nombre": "Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 31, "nombre": "Varas Bandera Asuncionista (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 32, "nombre": "Bandera Concepcionista (tramo 5)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 33, "nombre": "Varas Bandera Concepcionista (tramo 5)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 34, "nombre": "Bandera Realeza de María (tramo 6)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 35, "nombre": "Varas Bandera Realeza de María (tramo 6)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 36, "nombre": "Guión de la Coronación (tramo 7)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 37, "nombre": "Varas Guión de la Coronación (tramo 7)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 38, "nombre": "Libro de Reglas (tramo 8)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 39, "nombre": "Varas Libro de Reglas (tramo 8)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": False},
            {"id": 40, "nombre": "Estandarte (tramo 9)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 7, "cortejo_cristo": False},
            {"id": 41, "nombre": "Varas Estandarte (tramo 9)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 1, "tipo_puesto_id": 6, "cortejo_cristo": False},
        ]

        puestos_data.extend(puestos_virgen_data)

        puestos_a_crear = [Puesto(**data) for data in puestos_data]
        Puesto.objects.bulk_create(puestos_a_crear)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(puestos_a_crear)} puestos para el Acto 1 en total.'))


        # =========================================================================
        # POBLADO DE ACTO: VIA CRUCIS (ID=2)
        # =========================================================================
        self.stdout.write("Iniciando el poblado del Acto: Viacrucis...")

        fecha_acto_vc = now + timedelta(days=60)
        
        inicio_solicitud_vc = now - timedelta(days=10)
        fin_solicitud_vc = now - timedelta(days=2)
        inicio_solicitud_cirios_vc = now - timedelta(days=1)
        fin_solicitud_cirios_vc = now + timedelta(days=10)

        descripcion_viacrucis = (
            "El solemne Viacrucis en honor a Nuestro Padre Jesús en Su Soberano Poder ante Caifás constituye "
            "uno de los momentos de mayor recogimiento, devoción y espiritualidad en el calendario de nuestra "
            "Hermandad de San Gonzalo. Este piadoso acto nos invita a acompañar a nuestra Venerada Imagen titular "
            "por las calles de nuestro querido barrio de Triana, meditando sobre los misterios de la Pasión, "
            "Muerte y Resurrección de Cristo a través de las catorce estaciones. A diferencia de la Estación "
            "de Penitencia, el Viacrucis se distingue por su carácter íntimo y austero, donde el rezo pausado "
            "y el silencio de los hermanos marcan el discurrir del Señor, acercándolo a los enfermos y a los "
            "hogares de nuestros feligreses. La junta de gobierno ruega a todos los hermanos que deseen participar "
            "portando cirio que lo hagan con el máximo respeto y compostura, vistiendo traje oscuro y portando "
            "la medalla de la corporación. Que este ejercicio de piedad sirva para preparar nuestros corazones "
            "de cara a los días santos, reforzando nuestro compromiso cristiano, la fraternidad entre todos los "
            "miembros de la cofradía y nuestra incondicional fe en el Soberano Poder de Dios."
        )

        Acto.objects.filter(id=2).delete()

        acto_viacrucis = Acto(
            id=2,
            nombre="Viacrucis en honor a Nuestro Padre Jesús en Su Soberano Poder ante Caifás",
            lugar="Parroquia de San Gonzalo",
            descripcion=descripcion_viacrucis,
            fecha=fecha_acto_vc,
            modalidad="TRADICIONAL",
            tipo_acto_id=4,
            inicio_solicitud=inicio_solicitud_vc,
            fin_solicitud=fin_solicitud_vc,
            inicio_solicitud_cirios=inicio_solicitud_cirios_vc,
            fin_solicitud_cirios=fin_solicitud_cirios_vc,
            fecha_ejecucion_reparto=None,
            imagen_portada=None
        )
        
        acto_viacrucis.save()
        
        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Acto Viacrucis con ID 2.'))

        # =========================================================================
        # POBLADO DE PUESTOS DEL ACTO 2 (VIACRUCIS)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de Puestos para el Acto 2 (Viacrucis)...")

        puestos_viacrucis_data = [
            {"id": 42, "nombre": "Cruz de Guía", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 12, "cortejo_cristo": True},
            {"id": 43, "nombre": "Farol Cruz de Guía", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 9, "cortejo_cristo": True},
            {"id": 44, "nombre": "Senatus (tramo 2)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 45, "nombre": "Varas Senatus (tramo 2)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 46, "nombre": "Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 47, "nombre": "Varas Bandera Morada (tramo 3)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 48, "nombre": "Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 1, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 7, "cortejo_cristo": True},
            {"id": 49, "nombre": "Varas Bandera Pontificia (tramo 4)", "numero_maximo_asignaciones": 4, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 6, "cortejo_cristo": True},
            {"id": 50, "nombre": "Cirio Grande Cristo", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 51, "nombre": "Cirio Mediano Cristo", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 5, "cortejo_cristo": True},
            {"id": 52, "nombre": "Cirio Pequeño Cristo", "numero_maximo_asignaciones": 4000, "disponible": True, "lugar_citacion": "Parroquia de San Gonzalo", "hora_citacion": "13:30", "acto_id": 2, "tipo_puesto_id": 5, "cortejo_cristo": True},
        ]

        puestos_viacrucis_a_crear = [Puesto(**data) for data in puestos_viacrucis_data]
        Puesto.objects.bulk_create(puestos_viacrucis_a_crear)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado {len(puestos_viacrucis_a_crear)} puestos para el Acto 2.'))
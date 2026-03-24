from ...models import Acto, Comunicado, CuerpoPertenencia, Cuota, DatosBancarios, Hermano, AreaInteres, Puesto, TipoActo, TipoPuesto
from datetime import date, datetime
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import make_aware

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


        # =========================================================================
        # POBLADO DE ACTOS: MISAS DE HERMANDAD (RECURRENTE)
        # =========================================================================
        self.stdout.write("Iniciando el poblado de 10 Misas de Hermandad...")

        fecha_primera_misa = make_aware(datetime(2026, 4, 12, 12, 30))

        id_inicial_misa = 3

        for i in range(10):
            fecha_misa = fecha_primera_misa + timedelta(weeks=i)
            id_actual = id_inicial_misa + i

            Acto.objects.filter(id=id_actual).delete()
            
            misa = Acto(
                id=id_actual,
                nombre=f"Misa de Hermandad - {fecha_misa.strftime('%d/%m/%Y')}",
                lugar="Parroquia de San Gonzalo",
                descripcion=(
                    "Solemne Eucaristía semanal de la Hermandad de San Gonzalo. "
                    "Un encuentro de fe y fraternidad para todos los hermanos y devotos en nuestra sede canónica, "
                    "donde compartimos la palabra de Dios y fortalecemos nuestros lazos comunitarios ante "
                    "nuestros Sagrados Titulares."
                ),
                fecha=fecha_misa,
                modalidad=None,
                tipo_acto_id=11,
                inicio_solicitud=None,
                fin_solicitud=None,
                inicio_solicitud_cirios=None,
                fin_solicitud_cirios=None,
                fecha_ejecucion_reparto=None,
                imagen_portada=None
            )
            misa.save()

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se han creado 10 Misas de Hermandad (IDs {id_inicial_misa} al {id_inicial_misa + 9}).'))


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
            imagen_portada=None,
            fecha_emision=make_aware(datetime(2025, 4, 7, 10, 0)),
            tipo_comunicacion='GENERAL',
            autor_id=29,
            embedding = [-0.0036156958, 0.02633657, 0.030822897, -0.043637194, -0.012035134, 0.01675095, -0.0075424784, 0.0074111256, -0.0175064, -0.0065236855, -0.021755844, -0.0034895914, -0.016520964, -0.00015666753, 0.112815745, 0.006178681, 0.0045511783, 0.009115889, -0.008990799, 0.00936294, 0.031208172, -0.026618084, -0.008469969, -0.013791753, -0.016179493, 0.017803516, 0.017535213, -0.003849115, 0.055034682, -0.024611106, -0.008974789, 0.009950784, -0.015855465, -0.015974166, -0.0032992577, 0.012744429, -0.02257757, 0.00066067744, -0.013712919, 0.006990629, -0.018510016, 0.008027872, -0.0071479813, -0.008364593, -0.0033012973, -0.0038218226, -0.009127707, -0.033630766, 0.0068855505, 0.0008659034, 0.011403227, -0.0029171722, -0.03199255, -0.1883819, -0.014823372, 0.0061421874, -0.014318994, -0.01015957, 0.006551342, -0.00023322784, -0.014163183, 0.012352222, -0.015743047, -0.006742478, 0.00640012, -0.012633438, -0.0068382355, 0.05978841, -0.024363197, 0.007046703, -0.0017447683, -0.006473108, 0.00026440242, -0.0032597033, -0.010327979, -0.020821914, 0.0068883873, 0.0062220837, -0.016774097, 0.03210548, -0.012900659, 4.1897805e-05, -0.0030768292, -0.015735464, -0.0061611263, -0.014981842, 0.026689647, -0.016128952, -0.0022656443, 0.0078894, 0.008050368, 0.02856563, -0.010878026, -0.016755868, 0.019610513, 0.002120529, 0.021376781, 0.00028382236, -0.016866371, -0.017232541, -0.012233178, -0.003617589, -0.0014269918, 1.36348735e-05, 0.0022383225, -0.030889878, 0.018091286, 0.01123449, 0.001811767, 0.00018536186, -0.010197252, 0.0005386618, -0.0022831988, 0.009585391, -0.0004168875, -0.1822966, 0.008722838, -0.00054338505, -0.010551849, -0.024722595, 0.019673213, 0.0013622401, -0.008624067, 0.035809703, 0.0017431647, -0.004661212, 0.021419406, -0.0135479085, -0.019798925, -0.013026004, 0.016147178, -0.01283361, 0.018426044, 0.016597275, -0.028725488, 0.027759196, -0.024844524, -0.013716245, 0.011365834, 0.00025309154, 0.020433044, 0.022212828, -0.0007541929, 0.0035435, -0.00040259224, 0.0060875695, 0.010734586, -0.0064346683, -0.021169923, -0.006799743, 0.023219008, 0.009308992, -0.017075447, -0.0015595193, -0.0038960085, -0.020247797, 0.012102003, 0.0040730615, 0.012177488, 0.006871818, -0.0050898, -0.007065076, -0.0066562095, 0.0059614466, 0.008324015, 0.00795466, -0.027933879, -0.013889138, -0.01809094, 0.0008987773, -0.02039869, -0.01388883, -0.014992886, -0.009330984, -0.018762281, -0.0044576963, -0.0005348025, -0.042958856, 0.02259564, -0.008562872, 0.004896835, -0.009114849, -0.017226098, 0.0078559695, 0.012827215, -0.02506158, -0.0031533006, 0.0060327016, 0.0019206268, -0.0062799393, -0.009668376, -0.0239618, 0.009870289, -0.012129658, -0.007265261, -0.0052291225, -0.0035426957, -0.016061202, 0.017749911, -0.014542, 0.020296074, -0.006982402, 0.002810885, -0.00077748316, 0.003427771, 0.010127315, -0.020301085, -0.004568646, -0.0155821955, 0.012385444, -0.0024876597, -0.009193806, 0.014510464, -0.029498046, 0.012469921, -0.008211285, -0.024976961, 0.010188084, -0.018775016, -0.025342489, -0.010843463, -0.002329142, -0.015831416, 0.043953385, -0.0015468119, -0.006615777, 0.0017983416, -0.022387292, 0.023468977, 0.023026403, 0.00339078, 0.005321417, 0.024648111, 0.019034619, 0.034023654, -0.00046209514, 0.012433214, -0.0072441297, 0.0397325, 0.01835212, 0.0017883442, -0.016444463, -0.009586719, -0.01533544, 0.007960454, 0.011326132, 0.008032181, -0.014757766, -0.0002817785, -0.027623408, 0.00069938716, 0.013962856, 0.0060953307, -0.0021261666, -0.021558924, 0.013638511, -0.010827649, 0.012624781, -0.023730846, -0.020206869, -0.015531261, -0.008730007, -0.011316279, -0.013544834, -0.0005389264, -7.510544e-05, 0.009947514, 0.034005307, -0.016267803, -0.0013274899, 0.014934804, 0.003314801, -0.0008572649, -0.013236187, 0.002424477, 0.0035588066, -0.14258224, 0.03592168, -0.029791614, -0.009842101, -0.0045555364, -0.017434083, -0.011653919, 0.010443277, -0.01921199, -0.0061313175, 0.00097220106, -0.02894477, -0.009325464, -0.021888738, -0.0024349384, 0.019661086, 0.003779664, 0.013046364, 0.0051592495, -0.04495696, 0.032336056, -0.009830727, -0.024566362, -0.014240311, 0.014778733, -0.0029625061, -0.024289805, 0.025523948, 0.023741033, -0.0007929502, 0.006023514, -0.0058214935, -0.0027839309, 0.0020700134, 0.01951366, 0.006686814, 0.027413383, -0.02387804, -0.006621398, 0.010945592, 0.035040826, 0.00054875185, 0.024058469, 0.03890555, -0.028186226, -0.013865644, -0.01316106, -0.010647755, -0.0008742605, 0.025067206, -0.024032084, -0.0019476138, 0.01860584, -0.0041596307, -0.010718697, -0.01697574, 0.017247628, 0.0055902707, -0.01755229, -0.0045020115, -0.021126058, 0.0012013525, 0.0048880163, 0.0060669845, -0.001465217, 0.014560503, 0.0083548715, -0.0044358885, -0.013988121, 0.034320705, 0.0038944813, -0.038729724, 0.026223006, -0.039793175, 0.005188171, -0.008496979, -0.0021582248, -0.0039132573, -0.00020559075, 0.0059150904, -0.022327255, -0.0010950209, 0.008087291, 0.041035477, 0.025451507, -0.014619377, -0.014878291, -0.0050453423, -0.001151988, -0.0074841636, -0.010180396, 0.0019375484, -0.0008368217, 0.0051048244, -0.026711155, -0.013364184, -0.01180464, -0.0036040507, -0.0021790154, 0.038436968, -0.018396845, 0.002669943, 0.009064444, 0.0011740302, -0.004189649, 0.016934669, -0.015697854, 0.0104891835, 0.0067608906, -0.0055443565, -0.0089633865, 0.00203811, 0.015916133, 0.016691042, 0.0034184384, -0.00323118, -0.0037128099, -0.0065113585, 0.0032561063, 0.008548812, -0.009306453, -0.03615672, -0.016510786, 0.0023232007, -0.011240636, 0.0072148987, 0.0005707918, -0.0052682986, 0.0056280154, -0.017134003, -0.0056957533, -0.0037405624, -0.015952721, -0.022923404, 0.017757485, 0.019301862, 0.0026941744, 0.00040313206, 0.04386225, -0.03091487, 0.015616982, 0.003511045, 0.001691058, 0.009789919, 0.01214607, 0.0063012424, -0.031066928, 0.0011296493, 0.019772522, -0.028835231, -0.015365752, -0.026693009, 0.00059953006, 0.0007245435, -0.0032312963, -0.020193323, -0.034837734, 0.002870414, -0.025182616, -0.025464075, -0.001731918, -0.021830529, -0.0061888555, 0.0066181645, 0.0072158696, -0.005348271, -0.008340618, 0.007438262, 0.02231706, -0.0019985088, 0.0063968557, 0.010916341, 0.022186814, 0.0037962825, 0.007363209, -0.0232954, 0.0073416145, -0.0036246642, -0.0024585451, -0.0019920876, -0.0055801086, -0.00029093478, 0.0034475394, 0.013761468, -0.005692742, -0.0030853206, 0.00612777, 0.0032972603, -0.015080878, 0.0017006646, -0.0061202506, 0.00013773935, 0.018132053, 0.016314723, 0.0041234754, -0.015682647, -0.021421775, 0.0120381545, -0.008594913, 0.007497993, -0.0067143207, 0.008033784, 0.001775782, -0.008405061, -0.016088786, 0.008753853, -0.015354987, 0.0049432176, -0.02598525, 0.015752092, 0.021020688, 0.011421999, 0.022020645, 0.0075051263, 0.049051125, 0.0035805004, -0.0061123124, 0.018319711, -0.012020176, 0.0029124145, -0.0028229936, 0.010967183, 0.010667237, 0.007827427, 0.008363846, 0.010068946, -0.014925452, 0.00430917, 0.0065069394, 0.0113984635, -0.009560526, 0.004765054, 0.004671902, 0.011480984, -0.011343658, -0.0057688747, -0.007994485, 0.0007175724, 0.009075692, 0.0154369995, -0.004350429, 0.0009881894, -0.008520464, 0.0045196987, -0.01342208, 0.0062933797, 0.008350494, 0.010178063, -0.023628524, 4.87355e-05, 0.0025079937, -4.025639e-05, -0.008166507, 0.006232893, -0.0122316, 0.014209186, -0.011529982, -0.018471, -0.009312681, 0.007961669, -0.010611472, 0.023762573, 0.010223139, -0.0035481115, -0.0062642726, -0.030307956, 0.008145388, 0.010079205, 0.006687945, -0.08712773, -0.0028502347, 0.0069753104, -0.01870846, 0.003796099, 0.010507038, 0.0053498396, -0.012269242, -0.007228268, 0.0062224627, -0.024833811, 0.00027818698, 0.011264603, 0.010926246, -0.009468022, -0.03522096, -0.0019375657, 0.022093136, -0.010612997, 0.008763774, -0.0022377907, 0.005137645, 0.007415309, 0.01312898, -0.013061098, -0.007125873, 0.009752871, -0.026193341, 0.006272659, -0.024071673, 0.0029320717, -0.00037828216, -0.01034524, 0.01930575, 0.0054372633, 0.02484385, 0.005796539, -0.036052477, 0.019487977, -0.017355489, 0.0011895809, 0.017593836, -0.0028100298, 0.005608813, -0.00013984225, -0.00894533, 0.016930645, -0.017239999, 0.02253727, 0.00598017, 0.0032578106, 0.012059607, 0.02371072, 0.005902832, -0.03307631, -0.008769796, 0.023726158, 0.0072071, -0.00088661193, -0.0004816407, 0.0012797917, -0.012329408, 0.042134643, -0.01423445, -0.0034784582, -0.008850483, 0.00671358, 0.0068423287, -0.009733268, 0.0029235608, -0.016772522, 0.008063955, -0.0020948972, 0.0050684395, -0.005408622, 0.022288581, 0.019006217, 0.035994623, 0.00056832307, 0.006124456, 0.0034317044, -0.00031408595, -0.08205662, -0.0228214, -0.012135657, 0.0062672747, 0.0011646862, -0.0073520094, -0.00192844, -0.006560737, -0.013897629, -0.0175093, -0.020113694, 0.017346375, -0.011151523, 0.0029785912, 0.020660143, 0.011367556, 0.0149946315, -0.022766467, -0.001300709, 0.00681642, 0.0013383903, -0.0008574972, 0.008140434, -0.011846749, 0.004191367, 0.005381891, -0.010484118, 0.024182094, -0.0044480423, -0.04162026, -0.010078379, -0.13238992, -0.0069658863, -0.01078328, 0.014640216, 0.0013649227, 0.0109033035, 0.010133985, 0.01537956, -0.0058249426, 0.009381451, 0.00028919152, -0.014058839, -0.018418508, -0.0017307985, 0.016354246, 0.12624672, 0.036166973, 0.0024385941, -0.011388976, -0.0070835887, -0.010326213, 0.0046509407, 0.012548867, -0.010831778, -0.021668095, -0.013773086, 0.001512631, 0.0021108035, 0.009561544, 0.023911783, -0.00023988147, 0.040638022, -0.0076122936, -0.0068538757, -5.8344e-05, -0.0029914798, 0.0064152987, 0.00083410664, 0.0048183617, 0.0046366616, 0.0007333187, 0.018892463, -0.003925981, -0.015042726, -0.02576336, -0.01294749, 0.0072655845, 0.005917501, 0.014512151, -0.0011896329, -0.009615698, -0.06868029, 0.010396184, 0.0028004232, 0.0064894874, 0.023880698, 0.00081235863, 0.018622963, -0.005800167, -0.017870737, 0.017947437, -0.0018278814, 0.0058996305, 0.0063928706, -0.0018749828, -0.006899958, -0.015333906, 0.017519824, 0.005998971, 0.006900513, 0.025379721, 0.024292175, -0.009370025, -0.020049945, 0.0029453505, -0.0055768765, -0.0068252124, -0.00046151443, 0.014368704, -0.015032733, 0.027543973, 0.012202177, 8.112975e-05, -0.032249775, -0.01963905, -0.02763385, -0.00095096324, 0.018334638, 0.022604996, -0.013157599, -0.00013941317, -0.007545059, 0.020868879, -0.029709186, -0.00066751573, -0.021096075, 0.01953953, -0.0047509647, -0.0038997475, 0.020509697, -0.013544403, -0.0036160238, 0.009738365, -0.020118548, -0.0010394221, -0.014670881, 0.005229354, 0.006066527, 0.008084831, -0.0041294484, 0.011329096, 0.005528614, -0.00047189, 0.007680145, 0.018701136, 0.024363201, -0.019034158, -0.0033964983, -0.012220702, -0.004692431, -0.0031972642, 0.0030308175, -0.00759384, 0.009279597, 0.012163897, -0.009809034, -0.0011883343, 0.0036338132, -0.0045436574, -0.0007384655, 0.010034143, -0.005342959, 0.0031585349, 0.002062261, 0.010856623, -0.012445937, -0.006163345, 0.008120285, 0.0012018739, -0.0007820175, 0.021578554, 0.0060571004, -0.014478986, -0.008974449, 0.0055922884, 0.00999658, -0.00460166, 0.0059380597, -0.008355459, 0.0006281168, 0.0047479994, 0.016644245, 0.0033882426, 0.014357825, -0.013444373, 0.004095969, -0.0059455894, -0.011568431, -0.0020476433, 0.004541057, 0.013857669, -0.0012997568, -0.012971506, 0.0015980955, 0.013499513, 0.005999631, -0.0084555, -0.01893152, 0.0041656336, 0.012545623, -0.0024167318, 0.014525117, 0.005515964, 0.0059595117, -0.010445103, 0.008263836, -0.005988959, 0.0068738493, 0.008112628, 0.0064613717, 0.024423389, 0.008291158, -0.015822237, 0.0030098273, 0.017653782, 0.016566603, -0.0056718085, -0.010250613, -0.017238779, -0.007054495, -0.008777307, -0.0085037295, 0.028174661, -0.002468169, 0.0018171747, 0.002757995, -0.013327688, 0.0008214922, 0.00071955816, -0.012110491, -0.0053303293, 0.0016083649, -0.0049143406, 0.0051389206, 0.001383269, 0.010053701, -0.0025331655, 0.0026290992, 0.0070170984, -0.006084164, 0.0077355406, 0.011905113, 0.009857063, -0.0013914491, 0.007991947, -0.0139019545, -0.013181827, 0.002951569, -0.010112294, 0.0017155824, 0.0029040286, 0.004438166, -0.008337886, 0.0024966851, -0.0038797248, 0.008536254, 0.013044139, 0.008551773, -0.005144869, -0.0019640017, -0.003446623, -0.0077462057, 0.0067786193, 0.018276371, -0.008343949, 0.0048730425, 0.015197243, -0.013768551, 0.015842263, -0.003956814, 0.010993323, -0.0054062386, -0.0115796, -0.025894472, 0.0019192874, -0.000401557, 0.0076317075, 0.010981334, -0.004184219, -0.007030261, 0.003676071, 0.0025720538, 0.0071895546, -0.0060441005, -0.013784146, -0.02596189, -0.0052443896, 0.011641076, -0.00089476747, -0.01655537, -0.016873235, -0.0014442638, -0.00040137247, -0.004217634, -0.009697004, -0.00048009402, 0.0015191616, -0.023256656, -0.0030822232, 0.01085395, -0.00023653227, -0.012395064, 0.0016938732, -4.389102e-05, -0.00081943016, 0.007031691, -0.016901195, -0.004048985, 0.0024570343, -0.022843326, 0.004562482, 0.019286906, -0.0085546365, -0.00077583577, 0.009145555, -0.019386247, -0.0026722318, -0.0101649305, -0.003862607, -0.02365942, -0.0053834384, 0.004551403, -0.010095757, 0.013045509, -0.0063127317, 0.03293238, 0.0062471195, -0.012513304, 0.009210856, 0.006063965, -0.0006953556, 0.0050541745, -0.0050376193, -0.005929078, 0.012386655, -0.018966103, 0.00032265263, 0.0017686868, 0.015228381, -0.0011273695, 0.10852235, -0.0065970393, 0.0073920214, 0.004204872, -0.005263982, 0.008841461, -0.004627653, -0.011297399, 0.0077111083, -0.003009532, 0.009530434, 0.02112055, 0.015701728, -0.0076933005, -0.0008795012, -0.0054722046, -0.014620998, 0.0057921703, 0.005960419, -0.01247406, -0.011595418, -0.011267436, 0.014258352, 0.004173568, 0.014630598, 0.00711212, 0.006379664, 0.0032110333, 0.02318947, -0.002524867, -0.0040543703, -0.0011587173, -0.013931901, 0.008400058, -0.022227013, 0.0048927264, 0.012512936, -0.007698991, -0.022937823, 0.010584379, 0.0065709264, -0.00073321833, -0.011566502, 0.0077773887, 0.0033480923, 0.0009809361, -0.007956807, 0.004912196, 0.014993306, 0.017557764, -0.0046632634, -0.0055724564, -0.008056567, -0.009947596, -0.0020952038, -0.00095217925, 0.010177807, 0.0054083453, 0.022363791, -0.00044358542, 0.012616112, -0.0052690078, 0.010454391, 0.0030086255, -0.0012878132, -0.0057290616, -0.0064162505, 0.0016606266, -0.0034322361, -0.0073603685, 0.00024029319, 0.0047326535, 0.013751025, -0.00023234673, 0.03709236, -0.005709207, -0.0005906554, 0.010135407, 0.00051015324, 0.0051531508, 0.006371246, 0.007148423, -0.0017032846, -0.0023674548, -0.030211208, 0.010333344, -0.0088067185, 0.007022057, 0.002764102, 0.021384696, 0.013395947, 0.0023664378, 0.007921582, 0.013052141, -0.013316017, 0.0021915527, 0.10333421, -0.007954378, -0.0071756523, 0.010110315, -0.009651805, -0.008712299, -0.008482758, -0.0072924457, 0.010453034, -0.011283, 0.027568841, -0.010341531, -0.0033094774, -0.0063687195, -0.009451377, -0.006870854, 0.021524899, -0.016808962, -0.01638216, -0.0119770635, 0.022368696, 0.004457902, 0.008026203, -0.0087813875, 0.010257499, -0.006823848, 0.0016767124, 0.020323176, 0.005595511, 0.0056834198, -0.005964765, -0.00021391205, 0.0020696733, 0.00772878, 0.010456447, -0.004394156, -0.0041437745, 0.012609904, -0.004082262, -0.011483591, -8.164101e-05, 0.0023857316, 0.016830573, -0.0049618045, -0.0027947775, -0.0044281674, -0.018423522, 0.0029117512, -0.0057858387, 0.012516971, 0.0032372135, -0.0109623475, -0.008179108, -0.0016345913, 0.008910404, 0.0006604793, -0.003064225, -0.006692611, -0.0005381949, 0.005891861, 0.012744653, 0.00870492, 0.01825226, 0.0023934299, 0.00068898726, -0.007627998, 0.0019366189, 0.0028806957, -0.0037005274, 0.011248742, 0.02696407, 0.00025755158, 0.008156117, 0.008721509, 0.005205186, 0.0013676769, 0.00700197, 0.00772223, -0.012734992, -0.0054255947, -0.0041869436, -0.029672805, 0.01069181, -0.0030627025, 0.0023678567, 0.0051676277, -0.0078079505, -0.02546413, -0.0049537965, -0.0053096055, 0.0057912106, 0.0029976065, 0.011159227, -0.009654128, -0.008303385, -0.0018620272, 0.0083874, -0.018839324, 0.015303553, 0.00902299, 0.0022967455, 0.0020651487, -0.00043992637, 0.005186473, -0.0035196478, 0.015305424, 0.0061481763, -0.010022043, 0.0071187126, -0.015609182, 0.00046875275, -0.0039218157, 0.01402368, 0.0059707426, 0.0049578724, -0.015808217, 0.02167538, 0.0010149787, -0.002607015, 0.010702729, 0.014613712, 0.00053870503, 0.0046918388, -0.0085753715, -0.00038197034, -0.001656972, -0.024010498, 0.016342595, -0.0032591596, -0.009049655, -0.0021047955, -0.027321484, -0.0070576067, -0.012985411, 0.0068026385, 0.0041048, -0.020113561, -0.0027782384, -0.03128514, -0.0031556843, -0.013736272, 0.00031341804, -0.008606425, -0.0064825504, -0.007230583, 0.0012880217, -0.011050278, 0.0067930417, -0.011466948, 0.008468649, 0.0041709444, 0.012615288, -0.004087428, 0.007283637, 0.0009949321, -0.006613796, 0.0030791382, -0.006838211, 0.0150257535, 0.0003506833, -0.008295854, -0.06323289, 0.0026637388, 0.009025295, 0.013004877, 0.0010267422, -0.0060502184, 0.010719734, 0.002052032, 0.008551328, 0.0027486056, 0.010096999, -0.0029415335, 0.0042365645, -0.0032576772, -0.0033764062, -0.010914759, -0.0037251853, 0.0028052346, -0.004664509, -0.006986074, -0.009086746, 0.0009321903, 0.00048499406, 0.010118416, 0.0032304937, -0.0054482818, 0.002723442, 0.0074695847, -0.0033046864, -0.004508095, -0.0033472795, -0.010065984, -0.01242648, 0.0057880473, -0.0015392486, 0.0190329, 0.008038351, -0.00620283, -0.0011357702, -0.008860333, -0.0021623208, -0.01844456, 0.0002212421, 0.011063334, -0.007332712, -0.02772567, 0.011803094, 0.013217541, 0.009097858, -0.0074506607, 0.01897315, -0.011539794, -0.015780995, 0.020802261, -0.021303872, -0.011031279, 0.003998141, 0.011277643, 0.01166203, -0.009929448, 0.012784043, -0.0037053043, 0.0010882635, 0.011477638, -0.0015533139, -0.0061552264, -0.008291905, -0.01304713, 0.00101053, 0.009094819, 0.0002000662, 0.018528843, -0.0094852075, -0.0011434495, -0.001441344, -0.009119995, 0.017975533, -0.00015116847, 0.0072160577, 0.008173639, -0.009521785, -0.012446221, 0.011471109, -0.0099388985, 0.0024098544, 0.008394381, -0.0021477435, -0.008910614, -0.0060414085, 0.0014799589, -0.005630015, -0.004673648, 0.0024314593, -0.009543402, 0.003394421, -0.0013403775, -0.0025102848, 0.003439642, 0.0040303133, 0.0072158743, -0.0034275749, 0.008643182, 0.014867404, 0.025689844, -0.01773355, 0.013454398, 0.0023766127, -0.006925014, 0.0036466415, 0.0060635027, -0.00091687724, 0.003646045, 0.011536055, 0.0063533816, 0.018873658, 0.0047420873, -0.016949568, 0.002722445, 0.0095773805, -0.0066942363, -0.0001100332, -0.010772876, -0.012238115, -0.005584939, 0.018533813, 0.0083128875, -0.017864307, -0.00358416, -0.003109801, -0.0025800231, 0.01806939, 0.014239135, 0.030202866, 0.0076701664, -0.012322938, 0.008919904, 0.0012420372, 0.0073560937, 0.0052632974, -0.007788256, 0.006249171, 0.0031807648, 0.0037008184, -0.00024529017, 0.0049945274, -0.0032755744, -0.00014820579, -0.008090504, 0.0035945342, 0.0061217905, -0.012279631, -0.019108353, 0.005073087, 0.0035956926, -0.00014330527, 0.0127117885, 0.015425339, 0.012376991, -0.004988234, -0.008053918, 0.0010940839, 0.008904858, 0.020601502, -0.0045576645, 0.0064976336, 0.0027749655, -0.005241912, -0.0005452196, 0.009309123, -0.009114589, -0.005014179, 0.006736184, 0.0040617497, -0.0030540808, 0.0029295161, -0.0047526057, 0.01499985, 0.009164848, -0.0016199844, 0.011718279, -0.008923013, -0.0018271919, 0.0015695604, 0.0017887007, 0.007736922, -0.0079220105, -0.010132681, 0.0070021683, 0.00055414723, 0.008706546, 0.013576412, 0.0008627934, 0.0043985783, -0.0030036392, 0.019699052, -0.0024333, 0.0038161227, -0.00909727, 0.010960616, -0.007041241, -0.013880975, 0.007342519, 0.00764752, 0.0024032157, 0.003295883, -0.1132105, -0.011450607, -0.0015795671, -0.007834052, 0.007941813, -0.00026587656, -0.005377929, -0.0058090766, -0.015295839, -0.00035174767, -0.0073247557, -0.0013905776, -0.0006907001, -0.020879809, -0.013205408, -0.0061502974, -0.0064749382, 0.0009251186, -0.0061035217, -0.008031335, 0.008557322, -0.0052812104, 0.00062276877, -0.008552796, -0.003550454, -0.011297866, -0.0032801195, 0.00069597573, 0.016288258, 0.0054334225, -0.0013349383, 0.014238313, 0.0054858634, -0.0056137643, 0.020840187, -0.002446988, -0.018050743, 0.008703075, -0.14649908, 0.00042352919, -0.0020464233, -0.0028620737, 0.0012261184, 0.018291548, -0.0026376355, -0.00024085189, -0.003993837, 0.0003153804, 0.006394464, 0.005152643, -0.0069652013, 0.0008521419, 0.003340518, -0.00037016073, -0.010796305, -0.0044556186, -0.00422371, 0.015100595, -0.0010091099, 0.017887052, 0.004043701, 0.017865576, -0.0029085472, -0.0052503534, 0.004866889, 0.003220592, 0.024293656, 0.0017740541, 0.004630815, 0.0040959143, -0.008144434, -0.0018518118, 0.0002630172, 0.021649733, 0.017208714, -0.00077797065, -0.001909069, -0.010039338, 0.008989066, -0.013269079, 0.013095848, 0.004325439, 0.014712833, -0.00026429168, -0.008672494, -0.0052497922, 3.619066e-05, 0.0028011175, -0.008326368, 0.009950339, -0.009297699, 0.010745094, -0.001405444, -0.015319651, -0.013453065, 0.0064118374, -0.01075331, -0.0050996817, 0.00050987443, 0.0014574162, -0.0042783245, 0.006809053, -0.0023012867, 0.020924456, -0.0016384242, -0.0032932886, -0.0030421452, 0.00076984946, 0.0027184295, 0.021099206, 0.0018594655, -0.008865333, -0.0003142777, 0.029581007, 0.00952983, 0.019412525, -0.00032140635, -0.008990414, 0.0011624207, -0.0132678505, -0.0026930706, 0.008921076, -0.0011496709, -0.0082167, -0.00518357, -0.008103689, -0.009153927, -0.026547961, -0.0020081322, 0.002500721, 0.004224613, 0.007483305, -0.0006708063, -0.0059270514, -0.0030505406, -0.013500392, -0.007452837, 0.007316393, 0.004696284, -0.019649375, 0.02284377, 0.0052881576, -0.010571614, -0.009887914, 0.0070875646, -0.0007994569, -0.018950835, -0.027336601, -0.00433105, -0.0036401364, 0.016323375, 0.011474691, -0.0034770274, 0.014324242, -0.011692526, 0.004739389, -0.022581602, -0.01399244, 0.012687459, -0.007679862, 0.014028497, -0.013099801, -0.024784628, 0.009663542, -0.00482986, 0.009359365, -0.015866669, 0.00726088, -0.009787866, -0.004512235, -0.005399301, -0.0022217408, 0.017473144, -0.010016775, 0.012551457, -0.013010758, 0.005185402, 0.0027136272, 0.0056194053, 0.0022764655, -0.012126467, 0.0018918565, -0.00815426, 0.0071802633, 0.00813588, -0.0008422576, -0.019213514, -0.0032058968, -0.017469218, 0.022292145, 0.0013000207, -0.0015674542, -0.004571937, 0.010469812, 0.011739173, -0.016218625, -0.013849837, -0.005416057, 0.0051296875, 0.0054684198, 0.001525902, 0.0073340377, -0.018034086, -0.0072691496, -0.03531057, -0.0004752263, 0.007740409, -0.0070495117, 0.0077596456, -0.00707552, -0.006462723, -0.0041585034, -0.019509748, -0.016965915, 0.005408287, -0.021205084, -0.011422741, 0.0023677547, -0.033482257, 0.0043269834, -0.0041974885, -0.01093284, -0.0029538283, 0.011952675, -0.012764986, -0.0018016396, 0.0062226057, -0.0038473238, 0.003907019, -0.022963474, -0.0041796686, 0.031773753, -0.0078426255, 0.011349774, -0.009472353, -0.00055456895, -0.0035060204, 0.014229991, -0.0060345307, 0.0030717603, 0.02052113, -0.14522687, -0.00484548, -0.0014720944, -0.014967958, 0.029121937, 0.028654315, -1.6728254e-05, -0.016293475, 0.009676138, -0.014651251, 0.025975022, 0.009128352, 0.0051015355, -0.014438089, 0.033098135, -0.012758477, 0.009364095, -0.012200427, -0.011671655, -0.0010366233, 0.0013689842, -0.0051388526, 0.0036119495, 0.0059600454, -0.008924195, -0.01017617, 0.009511373, -0.014401612, -0.0074841753, 0.016178543, 0.00025385205, 0.0030739882, -0.020986851, 0.021127269, -0.005223156, 0.0046878816, -0.0128641995, -0.0019380987, 0.0006732094, -0.003843154, -0.025439335, -0.0060423496, 0.028234133, 0.026077002, -0.0031660926, -0.004145903, -0.0012686977, 0.007476486, -0.005402293, 0.008249089, -0.0069594365, -0.007921583, -0.007643556, 0.012504293, 0.014243172, -0.01408587, -0.0064563407, -0.004097106, 0.0037107214, 0.015403958, -0.008217485, -0.02310671, -0.007745087, -0.0012526822, 0.02383939, -0.010456939, 0.004048509, 0.15960713, -0.006387762, 0.017105447, -0.008384319, -0.016810702, 0.0052262596, 0.0042364085, -0.0019450817, 0.0060789995, -0.017642338, -0.0051189405, 0.013874605, -0.0014120303, 0.008351726, 0.010983397, 0.00049827155, -0.015633188, 0.0042529367, 0.0029934791, 0.0013555249, -0.01716208, -0.013370146, -0.013716208, -0.026516747, 0.020736432, 0.013663255, 0.007019483, -0.006584795, 0.014985353, 0.0006613909, -0.0062306034, -0.00475118, -0.0075749555, 0.00091658824, -0.007121966, -0.010053001, 0.0029361388, -0.005997528, -0.009403506, 0.026797354, 0.0045511513, 0.03778204, -0.015482683, -0.00032370872, 0.0028499863, -0.001980733, -0.0014689262, 0.029153686, -0.013260484, -0.019481713, -0.025866715, 0.0013269652, -0.014184377, -0.001715898, 0.006084634, -0.028749112, -0.010886078, 0.0028124207, -0.0066801636, -0.00266881, 0.004605766, -0.013414164, -0.010543114, 0.0073078354, -0.008840308, 0.006084353, 0.0039019973, -0.00068117253, 0.005922451, -0.14533015, -0.016710341, -0.03263761, 0.012745239, 0.00027182544, -0.007785814, 0.012933303, 0.008224248, 0.002528524, -0.0055116187, 0.0018811785, 0.0048578447, 0.020274214, 0.016657565, 0.0009166257, 0.0043060496, -0.005186799, 0.009414867, 0.031042153, -0.0064592646, 0.00045539404, 0.010328221, 0.021219887, -0.012896841, 0.0017669579, 0.005786937, -0.019750223, -0.0007032727, -0.0019398744, -0.009655384, -0.021099534, 0.0051645674, -0.012254091, -0.0066547943, -0.0109128365, -0.014446938, -0.023842089, -0.013330547, -0.0052215774, -0.01944244, 0.0032077115, -0.008706346, 0.022036793, -0.0041054124, 0.004268658, -0.0014124791, -0.00054420566, 0.0008420199, 0.014483189, -0.02462611, 0.0022661232, 0.004238507, -0.02212584, -0.010940766, -0.009160378, 0.007392417, 0.006907548, -0.006978511, 0.015094545, -0.0017748147, 0.00083685335, 0.004573746, 0.009839016, 0.015530481, -0.008074673, 0.01016042, -0.003269624, 0.00047534695, -4.1046613e-05, 0.0076778354, 0.0050063883, 7.484576e-05, 0.004115339, -0.0074869883, -0.0034842205, -0.0047795093, -0.012687481, 0.0047620917, 0.0132305985, 0.0032890374, -0.016497603, -0.008910619, -0.00600853, -0.016717792, 0.052187182, -0.022252891, -0.015290374, -0.009754721, -0.0053847576, -0.007975858, 0.007915991, -0.00034954966, 0.010945096, 0.014887257, -0.0027807625, -0.0018843679, -0.0036073846, 0.010712413, 0.004702778, -0.013892268, 0.008858131, 0.009703941, -0.022199906, -0.0009294483, 0.0048781475, -0.014465032, -0.0065873885, 0.013620839, 0.008882532, -0.014797941, -0.02315264, 0.0035629757, -0.007944938, 0.0061624693, 0.0022328356, -0.0059400974, -0.0058145463, 0.02173992, 0.0029683954, -0.0029424026, 0.009977164, 0.0025317192, 0.017379722, -0.008098143, -0.00032959046, -0.00408963, -0.006147621, -0.013198372, 0.018536327, -0.016877646, 0.001418366, 0.005517868, 0.0145011, 0.013512288, 0.020143695, -0.0147362845, 0.012108253, 0.0063225594, 0.020634318, 0.0075556906, -0.014478951, 0.0078929765, -0.0045748064, 0.010434264, -0.005567757, -0.022164723, 0.005967128, 0.015245835, -0.0011556142, -0.0043237493, -0.009800061, -0.0027734388, -0.018720286, -0.009578812, 0.011342881, 0.013736288, -0.0040011015, 0.019140195, 0.019327367, 0.010034457, -0.008303761, -0.007098802, -0.008161295, -0.010975495, 0.0033590675, -0.014047115, -0.0018176135, -0.04712131, -0.00088557706, -0.022374447, -0.005804092, -0.008387622, 0.0030471643, 0.0074298875, -0.009514318, -0.0021364915, -0.0009373849, 0.015600231, 0.0064428323, -0.088082194, 0.0077370647, 0.0044905925, 0.0026597749, 0.019099534, 0.0030934701, -0.0048109656, 0.00034076726, -0.0068058665, -0.01314207, 0.019379111, -0.0025093483, -0.009431241, -0.026827272, -0.006836926, -0.018390696, -0.022000713, 0.005850584, -0.0025003187, 0.0069900723, 0.004442208, -0.004561449, 0.0010091072, 0.006481544, 0.009097732, -0.0075227334, 0.020895071, 0.011779466, 0.02547225, 0.016931256, 0.008913802, -0.013311803, 0.0034993289, 0.009009374, 0.003794047, 0.023439558, -0.003082917, -0.006014101, -0.0016905738, -0.04572624, 0.012048019, 0.0048483643, -0.10628315, -0.0044479542, 0.01705044, 0.009867319, -0.012906053, -0.011389124, -0.0071406467, -0.0028502862, 0.012096619, -0.0018303605, -0.01821742, 0.012867676, 0.013200852, 0.0031069757, 0.027581923, -0.0038204659, -0.0060192803, -0.0049840766, -0.010002556, -0.008087181, 0.0072070244, -0.009536937, 0.0032830157, 0.040829405, 0.001940352, -0.0043666475, -0.012020717, 0.01327645, -0.015163694, 0.00032472276, 0.023178954, -0.028413143, -0.0072811637, -0.01741921, 0.013301311, -0.009151481, -0.006386168, 0.006812658, 0.004663354, -0.010237075, 0.0002882566, 0.043926477, 0.006226564, -0.02459469, -0.008300967, -0.13445835, -0.011449537, -0.01360294, -0.002316698, -0.005207327, 0.011864133, 0.0072310423, 0.14047928, 0.019490905, -0.0010516671, -0.005449794, 0.010202811, 0.0072590327, 0.0067016687, 0.0033976466, 0.008367865, 0.014613922, 0.015929338, -0.010094719, -0.013335418, 0.016026458, -0.012445613, -0.026847914, 0.016913582, 0.024705071, -0.049494717, -0.016271038, -0.024964876, 0.0063772304, 0.0052512693, 0.0058465316, -0.020490052, 0.000777482, -0.01924561, -0.0013904006, 0.0012922605, -0.020259118, -0.005911742, -0.0020993229, -0.005922993, 0.030015573, 0.00027308526, 0.0141761955, -0.0073248823, -0.0014132215, 0.01396724, -0.0055637243, -0.008272773, 0.010122748, -0.01188212, 0.008838438, -0.012715397, 0.007858904, -0.018693028, 0.0041242586, -0.016856816, -0.008931039, -0.0110758785, 0.011936906, -0.006999994, -0.011008074, -0.010209765, -0.0107355155, 0.008387989, -0.007895002, -0.01196691, -0.012440982, -0.018573636, -0.013241796, 0.0037422045, -0.008178915, 0.005989262, 0.023841253, 0.0036754936, 0.012596429, -0.0069636935, -0.00498606, 0.017755086, -0.021056596, 0.010764985, 0.005069399, 0.001619101, -0.0037262696, 0.00092712586, -0.007830519, 0.0052648066, 0.0017562977, 0.0042572194, 0.018175093, 0.0075955577, 0.0015364984, -0.0030773284, 0.014604134, 0.019623194, 0.0050080796, -0.004324196, 0.009640022, 0.0015703059, 0.0077288854, -0.018546999, -0.015941022, -0.033479728, -0.017288776, -0.008899718, -0.0021211375, 0.017160803, 0.019212188, 0.010462251, -0.002413217, 0.0033199093, 0.02811794, -0.0028160687, -0.019162586, -0.016851647, -0.011368404, -0.016107105, 0.006870179, -0.0037541015, 0.0071148905, -0.0025381919, -0.027212702, -0.012119733, 0.006817047, 0.0031755096, -0.0013144377, 0.0045627262, -0.0053958693, -0.0026531613, -0.011630838, 0.012975877, -0.0062166387, 0.016715009, 0.0047254628, 0.014665407, 0.007746173, 0.0048498367, -0.029286366, 0.019708168, 0.01130379, -0.015988324, 0.011932356, -0.01364437, 0.016958512, 0.002848879, 0.005495166, -0.003852408, -0.0013992825, -0.0023857073, -0.025057014, -0.0073909033, -0.010666858, 0.018958876, -0.008346325, 0.00087307463, -0.029444428, 0.0061799693, 0.0022705588, 0.022751587, 0.0020925994, -0.0053833215, 0.00054199714, 0.0141721405, -0.011643909, -0.0055029294, -0.012303825, -0.0032252537, 0.0028755155, -0.021615002, 0.031269975, -0.003423346, 0.00078726123, -0.016600532, -0.0037122602, -0.010074338, -0.0028286704, -0.02013286, 0.0037055332, 0.0054761195, -0.014138022, 0.000116523435, 0.013965427, 0.003482211, 0.00429528, 0.005476304, -0.0060408474, -0.003498169, 0.013316207, -0.021057865, 0.008336313, 0.009208894, -0.01197013, -0.03616457, 0.015237974, -0.014636786, -0.01985011, 0.0030313914, -0.01421656, 0.005723166, -0.010730115, 0.023478916, -0.0048932056, -0.0121876355, -0.0029149556, -0.048710153, -0.0068258992, 0.0072727813, -0.030960208, -0.011758108, -0.016304262, -0.003436134, -0.0031892075, 0.012726658, 0.009504766, -0.010052709, -0.011957072, -0.006584682, -0.0034522503, 0.009905413, 0.011487814, 0.0022003262, 0.022734998, -0.00071194186, -0.0057513434, 0.009483147, 0.008598632, -0.01539975, -0.002152432, 0.0013794381, -0.007557987, 0.011098277, -0.004589748, 0.018996606, 0.012650006, -0.0016129671, -0.0059613828, 0.023516396, -0.009815685, 0.019145224, -0.0032616027, 0.0013568632, 0.007795837, 0.01260974, 0.01721024, 0.0069343285, -0.012441253, 0.001554053, 0.011315368, 0.0069068586, -0.0073361737, -9.677183e-06, 0.00297757, 0.023860851, -0.007811136, -0.021272115, 0.013476857, 1.1395192e-05, -0.020510208, 0.0016175065, 0.00785928, 0.01277782, -0.017133608, 0.0005873182, -0.0014663788, 0.0041075214, 0.0063971225, 0.008038818, 0.00846998, 0.0153711885, -0.0010689753, 0.0143194655, -0.014746734, -0.0015148757, 0.006768694, -0.026669635, -0.0006578941, 0.017775076, -0.02206163, -0.011127443, -0.007823693, 0.024030536, 0.00093143363, 0.009654119, 0.010152854, 0.0005243376, 0.005586514, 0.0039377874, -0.006389009, -0.014216872, 0.022365568, 0.004141276, -0.002781028, -0.022284307, 0.009734575, -0.0026268524, -0.0064771115, 0.014167697, -0.01550572, 0.017105957, -0.0067671384, 0.004923865, -0.012895308, 0.009042602, -0.015826924, -0.00779576, 0.0010488926, 0.010957331, 0.0073524807, -0.02282195, 0.004106338, 0.025811141, 0.011349862, 0.0014588543, -0.0068598203, 0.0035880394, -0.006502692, -0.012868245, 0.001650895, 0.0027910485, -0.020946512, 0.009907347, -0.008362807, -0.004338162, 0.016683644, 0.014336802, -0.001874066, 0.001186371, 0.024398634, -0.0013826477, 0.0061845775, 0.002375911, 0.024305705, -0.013229011, -0.011160459, -0.023852566, 0.0019705177, 0.010111284, 0.0043200757, 0.0019163844, 0.0070113693, -0.004515974, -0.011870334, 0.0064161485, 0.0027713953, -0.020177457, 0.010038708, -0.0049322164, 0.015048684, -0.0029381136, 0.016244605, 0.0033722252, -0.00882889, 0.024957446, 0.0008209427, 0.0049850447, 0.011737392, -0.0040210765, 0.017083142, -0.00073944405, -0.001867008, 0.01218501, 0.012221928, 0.008271406, -0.0012267416, 0.00012375855, -0.008276644, -0.0013751262, -0.015175438, -0.0069213174, -0.02945149, 0.012210977, -0.0015951259, -0.009034106, -0.00050614256, 0.007106431, -0.007722315, 0.0028266252, 0.010039843, -0.010925547, 0.0077098683, 0.01075167, -0.021315116, -0.0039546806, 0.015775606, -0.007617118, -0.015524474, -0.0033447822, 0.0031158554, 0.008858688, 0.005373683, 0.0024960765, 0.008065391, -0.007965391, 0.016389957, 0.010341606, 0.0015910169, 0.015342536, -0.0018835028, -0.009002117, -0.0024568285, 0.0021969546, 0.0020026618, -0.004966744, 0.010652918, 0.0052154986, 0.005139762, -0.0010811408, 0.003645874, -9.042359e-05, 0.0049565774, 0.027181568, -0.021136187, 0.00071422243, 0.0074189845, -0.015040298, -0.017143622, 0.040922724, 0.005855421, 0.003989484, -0.005613881, -0.0017215215, -0.0146218, -0.004294399, -0.0035653163, 0.018654216, -0.005274892, -0.009204611, -0.017974388, -0.00819635, -0.0074376855, 0.026305627, -0.0020794973, -0.0028996356, 0.005352652, 0.017622337, 0.003559277, 0.008572517, -0.010396407, 0.0035654702, 0.00084537914, 0.009824092, 0.01733092, -0.0062260865, 0.013496054, -0.009031774, -0.001732649, 0.004364489, -0.034788903, 0.010749989, 0.01674434, -0.0046223723, 0.025728418, -0.0093989875, -0.01249864, -0.0032321129, -0.002126882, -0.011155753, -0.013319794, -5.235248e-06, 0.012446302, -0.0067673638, -0.013845786, 0.0018489123, 0.0024204152, 0.019256733, -0.0057005454, -0.0033195273, 0.00034734452, 0.008552061, -0.00080887903, 0.009640652, -0.054371707, -0.030803077, -0.033809792, -0.016563827, -0.010440517, -0.017690243, 0.0006054471, 0.0014190288, 0.025501875, -0.06426982, 0.004000654, 0.0055703586, 0.017002594, 0.020159975, 0.0032946824, -6.027982e-05, -0.031284567, -0.001055516, 0.0060777417, -0.03425192, 0.0030769035, 0.0049611027, -0.006781435, -0.010356601, 0.0087594185, -0.0017387215, 0.0010839521, -0.00088999525, -0.00040464845, -0.0048094844, -0.0004972004, -0.012850471, -0.0088800825, -0.0042273942, 0.015416634, -0.010373433, -0.0003262102, 0.007764501, 0.009622124, -0.0075249346, -0.022998683, 0.0054241307, 0.012566848, -0.011910813, 0.014874878, 0.006361818, 0.0013773199, -0.0006054056, 0.01203687, 0.0058373, -0.0049579735, -0.002864954, -0.00325936, -0.0010066418, -0.0009514965, -0.010671118, -0.008445874, 0.0036903357, -0.0053944783, 0.0056899562, 0.006776567, -0.01227781, 0.00052676286, -0.0047505656, -0.006227996, -0.001115136, 0.00022409605, -0.008044816, 0.006951512, -0.022023497, -0.022229416, -0.011288558, -0.006184099, -0.015029054, 0.014801005, 0.011314399, -0.0074891397, 0.009818004, -0.018649856, 0.00072911324, -0.013885662, 0.013818244, -0.02180744, -0.013353122, 0.021373978, -0.0059972615, 0.005448512, -0.0052970657, 0.007612455, 0.009221534, 0.009555188, -0.010638828, -0.017210055, 4.84573e-05, 0.0012080629, 0.008101924, -0.013362096, -0.023488712, -0.010210713, 0.0074534314, -0.0063799717, -0.0064546335, -0.0045329514, -0.012306861, -0.0064557455, 0.0060713086, -0.0025031636, -0.013475726, 0.009609134, 0.0006591153, -0.004860469, -0.014601402, -0.020493554, -0.01085557, -0.00064204214, 0.010980381, 0.01410931, 0.016649239, 0.0054711476, 0.007670918, -0.0058583925, -0.011923359, 0.010591189, -0.0038499995, 0.0019101741, -0.008008082, -0.01749982, 0.01710305, 0.00815812, -0.019268826, -0.0030629658, 0.006844183, 0.008465403, -0.010428565, -0.003494307, -0.003394441, -0.0010091895, 0.016044335, 0.011388927, -0.011987382, 0.012984031, 0.056342963, 0.0058227843, -0.012853501, 0.007286408, -0.012223966, 0.00016795006, -0.0011186446, -0.0010553292, -0.0038754432, -0.0068216743, 0.0020234962, -0.012293278, 0.008857126, 0.022183672, 0.009875139, -0.008074708, 0.0007870311, -0.011765023, -0.024606727, 0.0058205966, 0.01616379, 0.0015480634, -0.004907547, -0.008772223, 0.011680951, 0.016595121, -0.010645394, -0.0010667917, -0.004752826, -0.0032701038, -0.007975834, -0.0034467054, 0.00075837784, -0.002492175, -0.007402926, 0.0024468831, 0.005423251, -0.008616214, -0.0005552259, -0.01133873, -0.0007028425, -0.001940935, -0.01889093, 0.009018843, 0.013127434, -0.017044704, -0.006047463, 0.02824177, -0.010825773, -0.007254411, 0.003013742, 0.01058577, 0.019377077, 0.005959982, 0.00064093823, 0.011839711, 0.0011543517, 0.009888654, -0.018364964, 0.008974388, -0.018522212, -0.011295154, -0.0039876266, 0.0005787272, 0.0053040218, -0.0027589865, -0.0028927408, 0.0083944835, 0.01861488, -0.012961627, 0.031753562, 0.0054571, -0.0041520167, -0.013899627, 0.0047222315, 0.20105131, 0.14114794, -0.0021858474, -0.0058011073, -0.003897722, 0.02266232, -0.033713415, 0.0064812973, 0.023584772, -0.014244101, -0.0038845309, 0.00025414626, -0.022628214, 0.00559132, 0.023854097, 0.0118129, -0.0054428065, -0.0058548735, -0.0059051993, 0.01382087, -0.030204201, 0.0065316465, 0.0094154505, 0.004275206, -0.01370133, 0.011075197, 0.012315199, 0.0033786588, 0.02662863, 0.01341472, -0.013936379, 0.01549693, 0.021633092, -0.0031420933, 0.002985069, 0.009052972, -0.020112783, -0.031582866, 0.002280578, -0.008938114, -0.0038872678, 0.00042054037, 0.0056333826, 0.0060769795, 0.008420596, -0.006831916, 0.00821843, 0.0019158379, 0.0034354583, 0.019172953, 0.008087249, 0.008876366, 0.0024738845, 0.0023638615, -0.0026852044, 0.010566188, 0.014128873, -0.014171861, -0.0061185095, 0.01835445, 0.014496192, 0.0077236085, 0.009071891, -0.0141876675, -0.006785183, 0.013628949, 0.0014895655, -0.0025842825, 0.0060816747, 0.014868103, 0.01163192, 0.0073308977, -0.0041814973, -0.0070791305, -0.00888739, 0.018025089, 0.0059721484, -0.01144105, -0.00073275185, 0.0066195442, -0.014715789, -0.010789897, 0.010847137, 0.011178025, -0.013706782, 0.024986595, 0.00020065396, 0.0037425368, 0.11481213, -0.0124746, 0.012197085, -0.02062861, 0.015491295, 0.010980024, -0.006300239, 0.044580292, 0.009714199, 0.0037064734, 0.025039447, 0.009450168, 0.002581927, -0.014266169, 0.014717255, -0.0025130939, 0.015688619, 0.06406228, -6.0117378e-05, 0.0069372673, 0.005929814, 0.02122869, -0.004108571, -0.0017605359, 0.008390221, 0.014164968, 0.021945398, 0.01620966, -0.010113699, 0.017883355, -0.11060174, -0.0066272607, -0.00032095084, -0.0060879784, -0.006824253, 0.00729865, -0.01973715, 0.004453611, 0.008387935, -0.0028899156, -0.0027218703, -0.0043668565, 0.021464821, -0.006902562, -0.0027815662, -0.0037703796, 0.0011186403, -0.0072240457, 0.008470168, -0.0034267406, 0.015766054, -0.023785695, -0.004295011, 0.017417401, 0.010351835, -0.0016573688, -0.0061396337, -0.0006208183, 0.007781284, 0.008316983, -0.02257763, 0.0061323917, 0.009441728, 0.01700396, -0.002872143, -0.0034479059, 0.018488724, 0.025289511, 0.008971589, -0.029335432, 0.0023372455, -0.0044543347, -0.0072710738, -0.018924443, 0.003098246, -0.006548448, -0.00061204913, -0.010908086, -0.008725028, 0.00139958, 0.024202101, 0.007873874, 0.007992913, 0.0014181244, 0.028740212, 0.023247875, -0.007500479, -0.022490583, 0.008353087, 0.0030266605, -0.0011331438, 0.031000689, -0.009425341, -0.0005774716, -0.0075489916, -0.01695577, -0.005887028, 0.011765027, -0.0036184434, -0.00571737, 0.00968151, 0.017296629, 0.010442931, -0.0012433701, -0.014075573, -0.0029407456, -0.007551232, 0.015183873, 0.0023393831, 0.004482581, 0.010503483, -0.02147486, -0.010252623, 0.12173035, 0.014511246, -0.0025130527, -0.030774297, -0.0056193373, -0.004798535, 0.0027115077, -0.017617362, -0.017303735, -0.008285705, 0.014860111, -0.004054103, -0.023307318, -0.009951344, -0.0021966342, 0.0010390191, 0.0020029885, 0.02837242, -0.0104331225, -0.0113101, 0.010416519, 0.0023020345, 0.017102243, 0.0114699975, -0.014828939, -0.013494741, -0.010739626, 0.0043730317, -0.0010920912, 0.00046784937, -0.0006695403, -0.009634277, -0.013501747, -0.03822457, 0.0048748977, 0.00022805895, -0.0064427815, 0.00451251, 0.0024360737, -0.010672249, 0.01822223, -0.02651216, 0.017312804, 0.01718677, -0.026609188, 0.21165107, -0.0102750445, 0.005174364, -0.0076223607, -0.0095482655, -0.020293519, -0.013716342, 0.010906324, 0.0091829, 0.010094447, 0.0038329717, -0.0020400768, 0.009561551, -0.019056031, -0.025151549, -0.010040018, -0.008487913, 0.0113330055, 0.0036873962, 0.02933136, -0.0017131909, -0.002054878, -0.02978478, -0.011551555, -0.03405481, 0.03251846, 0.012143056, 0.010693073, -0.0039312746, 0.013221611, 0.0016619945, -0.015084599, 0.004467559, 6.36541e-05, 0.019895786, 0.0073371623, 0.024303583, -0.0030595013, 0.009922201, -0.012400923, -0.003277554, 0.013591559, -0.015232653, 0.008238469, -0.010459796, -0.0029977583, -0.002057014, 0.0046332455, 0.0024339806, -0.009235617, -0.014453203, 0.00030405156, -0.017405966, -0.004528244, -0.0115094, -0.0037281648, -0.010716285, 0.0040489426, -0.0010268909, -0.0021147204, -0.015705127, -0.0007545687, -0.012657343, -0.01349598, 0.0013321086, -0.0021306544, -0.021677047]
        )
        comunicado_1.save()

        comunicado_1.areas_interes.set([9])

        self.stdout.write(self.style.SUCCESS('¡Éxito! Se ha creado el Comunicado 1 asociado al área ID 9.'))
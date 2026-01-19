from ...models import DatosBancarios, Hermano
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction

class Command(BaseCommand):
    help = 'Puebla la base de datos con hermanos de prueba'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando el poblado de datos...")

        with transaction.atomic():
            
            Hermano.objects.all().delete()

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

        self.stdout.write(self.style.SUCCESS('¡Proceso finalizado con éxito!'))

    


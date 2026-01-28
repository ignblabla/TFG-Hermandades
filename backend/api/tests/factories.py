import factory
from factory.django import DjangoModelFactory
from api.models import Hermano

class HermanoFactory(DjangoModelFactory):
    class Meta:
        model = Hermano

    dni = factory.Sequence(lambda n: f"{10000000+n}Z")
    username = factory.LazyAttribute(lambda o: o.dni)
    password="password",
    nombre = factory.Faker('first_name', locale='es_ES')
    primer_apellido = factory.Faker('last_name', locale='es_ES')
    segundo_apellido = factory.Faker('last_name', locale='es_ES')
    email = factory.Faker('email')
    telefono = "600123456"
    estado_civil = "SOLTERO"
    fecha_nacimiento = "1990-01-01"
    codigo_postal = "41001"
    direccion = "Calle Feria"  
    esAdmin = False
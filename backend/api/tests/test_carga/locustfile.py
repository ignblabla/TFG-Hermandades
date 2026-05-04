import random
import time

from locust import HttpUser, task, between

class CofradiaLoadTest(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        """
        Bloque de Autenticación.
        Apuntamos al endpoint real que genera los tokens JWT.
        """
        response = self.client.post("/api/token/", json={
            "dni": "53962686V",
            "password": "1234"
        })
        
        if response.status_code == 200:
            token = response.json().get("access")
            self.client.headers.update({"Authorization": f"Bearer {token}"})
        else:
            print(f"Error al autenticar: {response.status_code} - {response.text}")


    @task(3)
    def ver_proxima_estacion(self):
        """
        Testea el endpoint destacado de la próxima Estación de Penitencia.
        """
        self.client.get("/api/actos/proxima-estacion/", name="Próxima Estación de Penitencia")


    @task(1)
    def ver_detalle_acto(self):
        acto_id = 1
        self.client.get(f"/api/actos/{acto_id}/", name="Detalle de Acto")


    @task(2)
    def ver_proximos_actos(self):
        """
        Testea el endpoint de listado de próximos actos.
        """
        self.client.get("/api/actos/proximos/", name="Próximos Actos")


    @task(2)
    def ver_listado_historico_actos(self):
        """
        Testea el endpoint de listado general/histórico de actos.
        """
        self.client.get("/api/actos/", name="Listado General de Actos")


    @task(1)
    def ver_asistentes_leidos(self):
        """
        Testea el listado de asistentes que ya han sido confirmados/leídos para un acto.
        """
        acto_id = 1
        self.client.get(f"/api/actos/{acto_id}/asistentes-leidos/", name="Asistentes Leídos")


    @task(1)
    def ver_estadisticas_asistencia(self):
        """
        Testea el cálculo de estadísticas de asistencia (asistentes vs total esperado).
        """
        acto_id = 1
        self.client.get(f"/api/actos/{acto_id}/estadisticas-asistencia/", name="Estadísticas Asistencia")


    @task(1)
    def crear_acto(self):
        """
        Testea el endpoint de creación de nuevos actos.
        """
        identificador = f"{int(time.time() * 1000)}_{random.randint(1,999)}"
        
        payload = {
            "nombre": f"Nuevo Acto de Prueba {identificador}",
            "lugar": "Sede de la Hermandad",
            "fecha": "2026-05-15T19:00:00Z",
            "tipo_acto": "CABILDO_GENERAL",
            "descripcion": "Descripción generada para el test de carga"
        }

        with self.client.post("/api/actos/crear/", json=payload, name="Crear Acto", catch_response=True) as response:
            if response.status_code == 201 or response.status_code == 200:
                response.success()
            elif response.status_code == 400:
                response.failure(f"Error 400: {response.text}")
            else:
                response.failure(f"Fallo inesperado: {response.status_code}")
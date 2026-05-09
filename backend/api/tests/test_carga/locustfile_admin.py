import random
import time

from locust import HttpUser, task, between

class CofradiaLoadTest(HttpUser):
    wait_time = between(1, 5)
    host = "http://127.0.0.1:8000"

    def on_start(self):
        """
        Bloque de Autenticación.
        Apuntamos al endpoint real que genera los tokens JWT.
        """
        self.comunicados_creados = []

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
    def test_get_comunicados(self):
        """
        Bloque de Lectura de Comunicados.
        Apuntamos al endpoint real que obtiene y pagina los comunicados.
        """
        page = random.randint(1, 3)
        
        with self.client.get(f"/api/comunicados/?page={page}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()
            else:
                response.failure(f"Error GET comunicados: {response.status_code} - {response.text}")



    @task(2)
    def test_post_comunicado(self):
        """
        Bloque de Creación de Comunicados.
        Apuntamos al endpoint real que registra un nuevo comunicado en el sistema.
        """
        payload = {
            "titulo": f"Comunicado de prueba {random.randint(1000, 9999)}",
            "contenido": "Cuerpo del comunicado generado por Locust.",
            "tipo_comunicacion": "GENERAL",
            "areas_interes": [1]
        }

        with self.client.post("/api/comunicados/", json=payload, catch_response=True) as response:
            if response.status_code == 201:
                response.success()
                nuevo_id = response.json().get("id")
                if nuevo_id:
                    self.comunicados_creados.append(nuevo_id)
            elif response.status_code == 403:
                response.failure("Falló POST: El usuario autenticado en on_start no es Administrador")
            else:
                response.failure(f"Falló POST comunicados: {response.status_code} - {response.text}")



    @task(1)
    def test_patch_comunicado(self):
        """
        Bloque de Actualización de Comunicados.
        Apuntamos al endpoint real que actualiza parcialmente un comunicado existente.
        """
        if not self.comunicados_creados:
            return

        comunicado_id = random.choice(self.comunicados_creados)
        payload = {
            "titulo": f"Título actualizado por PATCH {random.randint(1000, 9999)}"
        }

        with self.client.patch(f"/api/comunicados/{comunicado_id}/", json=payload, name="/api/comunicados/[id]/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code in [403, 404]:
                response.success()
            else:
                response.failure(f"Falló PATCH comunicado: {response.status_code} - {response.text}")



    @task(1)
    def test_delete_comunicado(self):
        """
        Bloque de Eliminación de Comunicados.
        Apuntamos al endpoint real que elimina un comunicado del sistema.
        """
        if not self.comunicados_creados:
            return

        comunicado_id = self.comunicados_creados.pop(0)

        with self.client.delete(f"/api/comunicados/{comunicado_id}/", name="/api/comunicados/[id]/", catch_response=True) as response:
            if response.status_code == 204:
                response.success()
            elif response.status_code in [403, 404]:
                response.success()
            else:
                response.failure(f"Falló DELETE comunicado: {response.status_code} - {response.text}")
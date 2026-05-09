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
        response = self.client.post("/api/token/", json={
            "dni": "53962686V",
            "password": "1234"
        })
        
        if response.status_code == 200:
            token = response.json().get("access")
            self.client.headers.update({"Authorization": f"Bearer {token}"})
        else:
            print(f"Error al autenticar: {response.status_code} - {response.text}")



    # @task(3)
    # def test_get_comunicados(self):
    #     """
    #     Bloque de Lectura de Comunicados.
    #     Apuntamos al endpoint real que obtiene y pagina los comunicados.
    #     """
    #     page = random.randint(1, 3)
        
    #     with self.client.get(f"/api/comunicados/?page={page}", catch_response=True) as response:
    #         if response.status_code == 200:
    #             response.success()
    #         elif response.status_code == 404:
    #             response.success()
    #         else:
    #             response.failure(f"Error GET comunicados: {response.status_code} - {response.text}")



    # @task(2)
    # def test_get_detalle_comunicado(self):
    #     """
    #     Bloque de Lectura de Detalle de Comunicado.
    #     Apuntamos al endpoint real que obtiene la información de un comunicado específico.
    #     """
    #     comunicado_id = random.randint(1, 15)

    #     with self.client.get(f"/api/comunicados/{comunicado_id}/", name="/api/comunicados/[id]/", catch_response=True) as response:
    #         if response.status_code == 200:
    #             response.success()
    #         elif response.status_code == 404:
    #             response.success()
    #         else:
    #             response.failure(f"Error GET detalle comunicado: {response.status_code} - {response.text}")



    # @task(3)
    # def test_get_mis_noticias(self):
    #     """
    #     Bloque de Lectura de Mis Noticias.
    #     Apuntamos al endpoint real que obtiene los comunicados filtrados por áreas de interés del usuario logueado.
    #     """
    #     page = random.randint(1, 2)
        
    #     with self.client.get(f"/api/comunicados/mis-noticias/?page={page}", catch_response=True) as response:
    #         if response.status_code == 200:
    #             response.success()
    #         elif response.status_code == 404:
    #             response.success()
    #         else:
    #             response.failure(f"Error GET mis noticias: {response.status_code} - {response.text}")



    # @task(2)
    # def test_get_ultimos_area_interes(self):
    #     """
    #     Bloque de Lectura de Últimos Comunicados por Área de Interés.
    #     Apuntamos al endpoint real que obtiene los comunicados más recientes según las áreas del usuario.
    #     """
    #     with self.client.get("/api/comunicados/ultimos-area-interes/", catch_response=True) as response:
    #         if response.status_code == 200:
    #             response.success()
    #         elif response.status_code == 404:
    #             response.success()
    #         else:
    #             response.failure(f"Error GET últimos comunicados áreas: {response.status_code} - {response.text}")



    # @task(1)
    # def test_get_areas_interes(self):
    #     """
    #     Bloque de Lectura de Áreas de Interés.
    #     Apuntamos al endpoint real que devuelve la lista de áreas disponibles para poblar selectores.
    #     """
    #     with self.client.get("/api/areas-interes/", catch_response=True) as response:
    #         if response.status_code == 200:
    #             response.success()
    #         else:
    #             response.failure(f"Error GET áreas de interés: {response.status_code} - {response.text}")



    # @task(2)
    # def test_get_proximos_actos(self):
    #     """
    #     Bloque de Lectura de Próximos Actos.
    #     Apuntamos al endpoint real que devuelve los 3 actos más próximos para el Dashboard.
    #     """
    #     with self.client.get("/api/actos/proximos/", catch_response=True) as response:
    #         if response.status_code == 200:
    #             response.success()
    #         else:
    #             response.failure(f"Error GET próximos actos: {response.status_code} - {response.text}")



    # @task(2)
    # def test_get_total_cuotas_pendientes(self):
    #     """
    #     Bloque de Lectura de Cuotas Pendientes.
    #     Apuntamos al endpoint real que devuelve el número total de cuotas pendientes o devueltas del usuario autenticado.
    #     """
    #     with self.client.get("/api/mis-cuotas-pendientes/total/", catch_response=True) as response:
    #         if response.status_code == 200:
    #             response.success()
    #         else:
    #             response.failure(f"Error GET total cuotas pendientes: {response.status_code} - {response.text}")



    # @task(2)
    # def test_get_mis_cuotas(self):
    #     """
    #     Bloque de Lectura de Mis Cuotas.
    #     Apuntamos al endpoint real que lista y pagina las cuotas del hermano autenticado.
    #     """
    #     page = random.randint(1, 3)
        
    #     with self.client.get(f"/api/mis-cuotas/?page={page}", catch_response=True) as response:
    #         if response.status_code == 200:
    #             response.success()
    #         elif response.status_code == 404:
    #             response.success()
    #         else:
    #             response.failure(f"Error GET mis cuotas: {response.status_code} - {response.text}")



    # @task(1)
    # def test_get_tipos_acto(self):
    #     """
    #     Bloque de Lectura de Tipos de Acto.
    #     Apuntamos al endpoint real que devuelve la lista de tipos de acto para poblar selectores.
    #     """
    #     with self.client.get("/api/tipos-acto/", catch_response=True) as response:
    #         if response.status_code == 200:
    #             response.success()
    #         else:
    #             response.failure(f"Error GET tipos acto: {response.status_code} - {response.text}")



    # @task(1)
    # def test_get_tipos_puesto(self):
    #     """
    #     Bloque de Lectura de Tipos de Puesto.
    #     Apuntamos al endpoint real que devuelve la lista de tipos de puesto disponibles.
    #     """
    #     with self.client.get("/api/tipos-puesto/", catch_response=True) as response:
    #         if response.status_code == 200:
    #             response.success()
    #         else:
    #             response.failure(f"Error GET tipos puesto: {response.status_code} - {response.text}")



# --------------------------------------------------------------------------------
# ACTOS
# --------------------------------------------------------------------------------

    @task(2)
    def test_get_detalle_acto(self):
        """
        Bloque de Lectura de Detalle de Acto.
        Apuntamos al endpoint real que obtiene la información detallada de un acto específico.
        """
        acto_id = random.randint(1, 12)

        with self.client.get(f"/api/actos/{acto_id}/", name="/api/actos/[id]/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()
            else:
                response.failure(f"Error GET detalle acto: {response.status_code} - {response.text}")
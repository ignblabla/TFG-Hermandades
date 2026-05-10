import csv
import os
import random
import time

from locust import HttpUser, task, between

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "usuarios.csv")

with open(CSV_PATH, encoding='utf-8') as f:
    USUARIOS = list(csv.DictReader(f))

    PREGUNTAS_CHAT = [
        "¿Cuándo es la próxima estación de penitencia?",
        "¿Qué comunicados hay sobre cuotas?",
        "¿Cuál es el horario de los cultos?",
        "¿Hay algún comunicado sobre el besamanos?",
        "¿Cuándo es el cabildo de elecciones?",
        "¿Qué actividades hay programadas este mes?",
        "¿Hay novedades sobre la banda de música?",
        "¿Cuándo se reúne la junta de gobierno?",
    ]


class CofradiaLoadTest(HttpUser):
    wait_time = between(1, 5)
    host = "http://127.0.0.1:8000"

    ACTO_IDS = [1, 2, 3]
    PAPELETA_IDS = [1, 2, 3]
    PUESTO_IDS = [1, 2, 3, 4, 5]

    ACTOS_CON_PUESTOS = {
        11: [291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313],
    }

    ACTOS_CON_CIRIOS = {
        12: [361, 362, 363, 382, 383, 384],
    }

    def on_start(self):
        credenciales = random.choice(USUARIOS)
        response = self.client.post("/api/token/", json={
            "dni": credenciales["dni"],
            "password": credenciales["password"],
        })
        if response.status_code == 200:
            token = response.json().get("access")
            self.client.headers.update({"Authorization": f"Bearer {token}"})
            self._ya_solicito_insignia = False
            self._ya_solicito_cirio = False
            self._ya_solicito_baja = False

            mis_papeletas = self.client.get("/api/papeletas/mis-papeletas/")
            if mis_papeletas.status_code == 200:
                data = mis_papeletas.json().get("results", [])
                self._papeletas_descargables = [
                    p["id"] for p in data
                    if p.get("estado_papeleta") in ("EMITIDA", "RECOGIDA", "LEIDA")
                ]
                self._papeletas_qr = [
                    {"id": p["id"], "codigo": p["codigo_verificacion"]}
                    for p in data
                    if p.get("codigo_verificacion")
                ]
            else:
                self._papeletas_descargables = []
                self._papeletas_qr = []

            comunicados = self.client.get("/api/comunicados/")
            if comunicados.status_code == 200:
                data = comunicados.json().get("results", [])
                self._comunicado_ids = [c["id"] for c in data]
            else:
                self._comunicado_ids = []

        else:
            print(f"Error al autenticar: {response.status_code} - {response.text}")



    # -------------------------------------------------------------------------
    # Consulta de papeletas propias
    # -------------------------------------------------------------------------

    @task(5)
    def mis_papeletas(self):
        """GET /papeletas/mis-papeletas/ — el endpoint más consultado por usuarios."""
        self.client.get("/api/papeletas/mis-papeletas/", name="/papeletas/mis-papeletas/")



    @task(3)
    def ultima_papeleta(self):
        with self.client.get(
            "/api/papeletas/ultima/",
            name="/papeletas/ultima/",
            catch_response=True
        ) as response:
            if response.status_code in (200, 404):
                response.success()
            else:
                response.failure(f"Error inesperado: {response.status_code}")



    # -------------------------------------------------------------------------
    # Solicitud de insignia
    # -------------------------------------------------------------------------

    @task(4)
    def solicitar_insignia(self):
        if getattr(self, "_ya_solicito_insignia", False):
            return

        acto_id, puesto_ids = random.choice(list(self.ACTOS_CON_PUESTOS.items()))
        puestos = random.sample(puesto_ids, k=min(3, len(puesto_ids)))
        preferencias = [
            {"puesto_solicitado": puesto_id, "orden_prioridad": orden}
            for orden, puesto_id in enumerate(puestos, start=1)
        ]
        response = self.client.post(
            "/api/papeletas/solicitar-insignia/",
            json={"acto_id": acto_id, "preferencias": preferencias},
            name="/papeletas/solicitar-insignia/",
            catch_response=True,
        )
        with response:
            if response.status_code in (200, 201):
                self._ya_solicito_insignia = True
            elif response.status_code == 400:
                detail = response.json().get("detail", "")
                EXPECTED_ERRORS = (
                    "Ya existe una solicitud",
                    "mayor de 18 años",
                )
                if any(msg in detail for msg in EXPECTED_ERRORS):
                    self._ya_solicito_insignia = True
                    response.success()
                else:
                    response.failure(f"400 inesperado: {detail}")



    # -------------------------------------------------------------------------
    # Solicitud de insignia
    # -------------------------------------------------------------------------

    @task(4)
    def solicitar_cirio(self):
        if getattr(self, "_ya_solicito_cirio", False):
            return

        acto_id, puesto_ids = random.choice(list(self.ACTOS_CON_CIRIOS.items()))
        puesto_id = random.choice(puesto_ids)

        response = self.client.post(
            "/api/papeletas/solicitar-cirio/",
            json={
                "acto": acto_id,
                "puesto": puesto_id,
            },
            name="/papeletas/solicitar-cirio/",
            catch_response=True,
        )
        with response:
            if response.status_code in (200, 201):
                self._ya_solicito_cirio = True
            elif response.status_code == 400:
                detail = response.json().get("detail", "")
                EXPECTED_ERRORS = (
                    "Ya existe una solicitud",
                    "Ya tienes una solicitud activa",
                    "mayor de 18 años",
                    "no está disponible",
                    "plazo",
                )
                if any(msg in detail for msg in EXPECTED_ERRORS):
                    self._ya_solicito_cirio = True
                    response.success()
                else:
                    response.failure(f"400 inesperado: {detail}")



    # -------------------------------------------------------------------------
    # Descargar papeleta de sitio
    # -------------------------------------------------------------------------

    @task(2)
    def descargar_papeleta_pdf(self):
        if not getattr(self, "_papeletas_descargables", []):
            return

        pk = random.choice(self._papeletas_descargables)
        with self.client.get(
            f"/api/papeletas/{pk}/descargar/",
            name="/papeletas/[pk]/descargar/",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 403):
                response.success()
            else:
                response.failure(f"Error inesperado: {response.status_code}")



    # -------------------------------------------------------------------------
    # Endpoint /me
    # -------------------------------------------------------------------------

    @task(5)
    def usuario_logueado(self):
        with self.client.get(
            "/api/me/",
            name="/me/",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Error inesperado: {response.status_code}")



    # -------------------------------------------------------------------------
    # Listado de cuotas
    # -------------------------------------------------------------------------

    @task(3)
    def mis_cuotas(self):
        with self.client.get(
            "/api/mis-cuotas/",
            name="/mis-cuotas/",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Error inesperado: {response.status_code}")



    # -------------------------------------------------------------------------
    # Listado de comunicados
    # -------------------------------------------------------------------------

    @task(4)
    def lista_comunicados(self):
        with self.client.get(
            "/api/comunicados/",
            name="/comunicados/",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Error inesperado: {response.status_code}")



    # -------------------------------------------------------------------------
    # Consulta comunicado concreto
    # -------------------------------------------------------------------------

    @task(3)
    def detalle_comunicado(self):
        if not getattr(self, "_comunicado_ids", []):
            return

        pk = random.choice(self._comunicado_ids)
        with self.client.get(
            f"/api/comunicados/{pk}/",
            name="/comunicados/[pk]/",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 404):
                response.success()
            else:
                response.failure(f"Error inesperado: {response.status_code}")



    # -------------------------------------------------------------------------
    # Consulta comunicado concreto
    # -------------------------------------------------------------------------

    @task(2)
    def chat_comunicados(self):
        pregunta = random.choice(PREGUNTAS_CHAT)
        with self.client.post(
            "/api/comunicados/chat/",
            json={"pregunta": pregunta},
            name="/comunicados/chat/",
            catch_response=True,
            timeout=60,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()
            elif response.status_code == 500:
                error = response.json().get("error", "")
                if "api_key" in error or "Google" in error:
                    response.success()
                else:
                    response.failure(f"500 inesperado: {error}")
            else:
                response.failure(f"Error inesperado {response.status_code}: {response.text}")



    # -------------------------------------------------------------------------
    # Áreas de interés
    # -------------------------------------------------------------------------

    @task(1)
    def lista_areas_interes(self):
        with self.client.get(
            "/api/areas-interes/",
            name="/areas-interes/",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Error inesperado: {response.status_code}")



    # -------------------------------------------------------------------------
    # Solicitud de baja
    # -------------------------------------------------------------------------

    @task(1)
    def solicitar_baja(self):
        if getattr(self, "_ya_solicito_baja", False):
            return

        with self.client.post(
            "/api/solicitudes-baja/",
            json={"motivo": "Solicitud generada en test de carga."},
            name="/solicitudes-baja/",
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                self._ya_solicito_baja = True
                response.success()
            elif response.status_code == 400:
                error = str(response.json().get("error", ""))
                EXPECTED_ERRORS = (
                    "ya tiene una solicitud",
                    "pendiente",
                    "baja",
                )
                if any(msg in error.lower() for msg in EXPECTED_ERRORS):
                    self._ya_solicito_baja = True
                    response.success()
                else:
                    response.failure(f"400 inesperado: {error}")
            else:
                response.failure(f"Error inesperado: {response.status_code}")



    # -------------------------------------------------------------------------
    # Validar acceso QR
    # -------------------------------------------------------------------------

    @task(3)
    def validar_acceso_qr(self):
        if not getattr(self, "_papeletas_qr", []):
            return

        papeleta = random.choice(self._papeletas_qr)
        with self.client.post(
            "/api/control-acceso/validar/",
            json={
                "id": papeleta["id"],
                "codigo": papeleta["codigo"],
            },
            name="/control-acceso/validar/",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 400:
                error = str(response.json().get("error", ""))
                EXPECTED_ERRORS = (
                    "ya ha sido leída",
                    "no válida",
                    "expirada",
                )
                if any(msg in error.lower() for msg in EXPECTED_ERRORS):
                    response.success()
                else:
                    response.failure(f"400 inesperado: {error}")
            else:
                response.failure(f"Error inesperado: {response.status_code}")
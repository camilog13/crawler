# backend/dataforseo_client.py
import time
import requests
from typing import List, Dict, Any
from .config import DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD, DATAFORSEO_ENDPOINT, DATAFORSEO_TASK_GET_ENDPOINT


class DataForSEOClient:
    def __init__(self):
        if not DATAFORSEO_LOGIN or not DATAFORSEO_PASSWORD:
            raise RuntimeError("Configura DATAFORSEO_LOGIN y DATAFORSEO_PASSWORD en el .env")

        self.auth = (DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD)

    def create_onpage_task(self, domain: str, max_pages: int = 500) -> str:
        """
        Crea tarea de rastreo on_page.
        Devuelve ID de tarea.
        """
        payload = [
            {
                "target": domain,
                "max_crawl_pages": max_pages,
                "load_resources": True,
                "enable_javascript": True,
                "custom_js": "",
            }
        ]

        resp = requests.post(DATAFORSEO_ENDPOINT, auth=self.auth, json=payload)
        resp.raise_for_status()
        data = resp.json()

        # DataForSEO suele devolver results con tasks. Ajusta según tu contrato exacto.
        task_id = data["tasks"][0]["id"]
        return task_id

    def wait_for_task_and_get_results(self, task_id: str, sleep_seconds: int = 10, max_attempts: int = 30) -> List[Dict[str, Any]]:
        """
        Polling simple para esperar a que la tarea termine y obtener resultados.
        Devuelve lista de URLs con sus datos on-page.
        """
        for _ in range(max_attempts):
            ready_resp = requests.get(DATAFORSEO_TASK_GET_ENDPOINT, auth=self.auth)
            ready_resp.raise_for_status()
            ready_data = ready_resp.json()

            tasks = ready_data.get("tasks", [])
            for t in tasks:
                if t.get("id") == task_id:
                    # Aquí se suelen devolver resultados en results
                    result = t.get("result", [])
                    # Debes adaptar la estructura a tu contrato concreto
                    # Supongamos que viene como lista de URLs con onpage_score, meta, etc.
                    return result

            time.sleep(sleep_seconds)

        raise TimeoutError("La tarea de DataForSEO no se completó a tiempo")

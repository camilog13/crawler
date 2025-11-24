# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# IMPORTANTE:
# Pon tus credenciales reales en un archivo .env:
# DATAFORSEO_LOGIN=tu_login
# DATAFORSEO_PASSWORD=tu_password_o_api_key
# PAGESPEED_API_KEY=tu_key

DATAFORSEO_LOGIN = os.getenv("DATAFORSEO_LOGIN")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")
DATAFORSEO_ENDPOINT = os.getenv(
    "DATAFORSEO_ENDPOINT",
    "https://api.dataforseo.com/v3/on_page/task_post"
)
DATAFORSEO_TASK_GET_ENDPOINT = os.getenv(
    "DATAFORSEO_TASK_GET_ENDPOINT",
    "https://api.dataforseo.com/v3/on_page/tasks_ready"
)

PAGESPEED_API_KEY = os.getenv("PAGESPEED_API_KEY")
PAGESPEED_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./seo_auditor.db")

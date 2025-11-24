# backend/pagespeed_client.py
import requests
from typing import Dict, Any
from .config import PAGESPEED_API_KEY, PAGESPEED_ENDPOINT


def fetch_pagespeed(url: str, strategy: str = "mobile") -> Dict[str, Any]:
    """
    Llama a PageSpeed Insights y devuelve los datos brutos.
    """
    if not PAGESPEED_API_KEY:
        raise RuntimeError("Configura PAGESPEED_API_KEY en el .env")

    params = {
        "url": url,
        "key": PAGESPEED_API_KEY,
        "strategy": strategy
    }
    resp = requests.get(PAGESPEED_ENDPOINT, params=params)
    resp.raise_for_status()
    return resp.json()


def extract_performance_metrics(psi_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Extrae performance_score, LCP, CLS, TBT desde la respuesta de PSI.
    """
    lighthouse = psi_data.get("lighthouseResult", {})
    categories = lighthouse.get("categories", {})
    perf_score = categories.get("performance", {}).get("score")
    perf_score_scaled = perf_score * 100 if perf_score is not None else None

    audits = lighthouse.get("audits", {})
    def metric_value(id_: str):
        audit = audits.get(id_, {})
        return audit.get("numericValue")

    lcp = metric_value("largest-contentful-paint")
    cls = metric_value("cumulative-layout-shift")
    tbt = metric_value("total-blocking-time")

    return {
        "performance_score": perf_score_scaled,
        "lcp": lcp,
        "cls": cls,
        "tbt": tbt,
    }

"""
ARBOR - Connecteur NVD (National Vulnerability Database).
Utilise l'API NVD v2 avec gestion du rate limiting.
"""

import time
from datetime import datetime, timedelta, timezone

import httpx

from app.core.config import get_settings
from app.feeds.base import FeedConnector
from app.models.enums import Severity, VulnSource

NVD_API_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"

# Rate limits NVD :
# Sans clé API : 5 requêtes / 30 secondes
# Avec clé API : 50 requêtes / 30 secondes
RATE_LIMIT_DELAY_NO_KEY = 6.5  # secondes entre requêtes (safe)
RATE_LIMIT_DELAY_WITH_KEY = 0.7


class NVDConnector(FeedConnector):
    """Connecteur pour l'API NVD v2."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.nvd_api_key or None
        self.delay = RATE_LIMIT_DELAY_WITH_KEY if self.api_key else RATE_LIMIT_DELAY_NO_KEY

    def fetch(self, since: str | None = None) -> list[dict]:
        """
        Récupère les CVE depuis NVD.
        `since` : date ISO pour les deltas (lastModStartDate).
        Gère la pagination et le rate limiting.
        """
        params: dict = {"resultsPerPage": 200}

        if since:
            params["lastModStartDate"] = since
            # NVD requiert une date de fin à max 120 jours
            end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000")
            params["lastModEndDate"] = end
        else:
            # Premier sync : derniers 30 jours
            start = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S.000")
            end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000")
            params["lastModStartDate"] = start
            params["lastModEndDate"] = end

        headers = {}
        if self.api_key:
            headers["apiKey"] = self.api_key

        all_items = []
        start_index = 0

        while True:
            params["startIndex"] = start_index

            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.get(NVD_API_BASE, params=params, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
            except httpx.HTTPError as e:
                print(f"[NVD] Erreur HTTP : {e}")
                break

            vulns = data.get("vulnerabilities", [])
            all_items.extend(vulns)

            total_results = data.get("totalResults", 0)
            start_index += len(vulns)

            if start_index >= total_results or not vulns:
                break

            # Rate limiting
            time.sleep(self.delay)

        print(f"[NVD] {len(all_items)} CVE récupérées")
        return all_items

    def normalize(self, raw_items: list[dict]) -> list[dict]:
        """Normalise les CVE NVD vers le format ARBOR."""
        normalized = []

        for item in raw_items:
            cve_data = item.get("cve", {})
            cve_id = cve_data.get("id")
            if not cve_id:
                continue

            # Extraire les scores CVSS
            cvss_v3_score, cvss_v3_vector, cvss_v2_score = _extract_cvss(cve_data)

            # Déterminer la sévérité
            severity = _score_to_severity(cvss_v3_score or cvss_v2_score)

            # Description (préférer l'anglais)
            descriptions = cve_data.get("descriptions", [])
            desc = next((d["value"] for d in descriptions if d.get("lang") == "en"), None)
            if not desc and descriptions:
                desc = descriptions[0].get("value", "")

            # Références
            refs = [
                {"url": r.get("url"), "source": r.get("source")}
                for r in cve_data.get("references", [])
            ]

            # CPE et PURL affectés
            affected_cpes = _extract_affected_cpes(cve_data)
            affected_purls = []  # NVD ne fournit pas de PURL, mais des CPE

            # Dates
            published = cve_data.get("published")
            modified = cve_data.get("lastModified")

            normalized.append({
                "cve_id": cve_id,
                "source": VulnSource.NVD,
                "title": cve_id,  # NVD n'a pas de titre séparé
                "description": desc or "",
                "cvss_v3_score": cvss_v3_score,
                "cvss_v3_vector": cvss_v3_vector,
                "cvss_v2_score": cvss_v2_score,
                "severity": severity,
                "published_at": published,
                "modified_at": modified,
                "references": refs,
                "affected_cpes": affected_cpes,
                "affected_purls": affected_purls,
            })

        return normalized


def _extract_cvss(cve_data: dict) -> tuple:
    """Extrait les scores CVSS v3 et v2 depuis les métriques NVD."""
    metrics = cve_data.get("metrics", {})

    v3_score = None
    v3_vector = None
    v2_score = None

    # CVSS v3.1 ou v3.0
    for key in ["cvssMetricV31", "cvssMetricV30"]:
        v3_list = metrics.get(key, [])
        if v3_list:
            v3_data = v3_list[0].get("cvssData", {})
            v3_score = v3_data.get("baseScore")
            v3_vector = v3_data.get("vectorString")
            break

    # CVSS v2
    v2_list = metrics.get("cvssMetricV2", [])
    if v2_list:
        v2_data = v2_list[0].get("cvssData", {})
        v2_score = v2_data.get("baseScore")

    return v3_score, v3_vector, v2_score


def _score_to_severity(score: float | None) -> Severity:
    """Convertit un score CVSS en niveau de sévérité."""
    if score is None:
        return Severity.INFO
    if score >= 9.0:
        return Severity.CRITICAL
    if score >= 7.0:
        return Severity.HIGH
    if score >= 4.0:
        return Severity.MEDIUM
    if score > 0:
        return Severity.LOW
    return Severity.INFO


def _extract_affected_cpes(cve_data: dict) -> list[dict]:
    """Extrait les CPE affectés avec les ranges de versions."""
    affected = []
    configurations = cve_data.get("configurations", [])

    for config in configurations:
        for node in config.get("nodes", []):
            for match in node.get("cpeMatch", []):
                if match.get("vulnerable"):
                    entry = {"cpe": match.get("criteria")}
                    if "versionStartIncluding" in match:
                        entry["version_start"] = match["versionStartIncluding"]
                        entry["version_start_type"] = "including"
                    if "versionStartExcluding" in match:
                        entry["version_start"] = match["versionStartExcluding"]
                        entry["version_start_type"] = "excluding"
                    if "versionEndIncluding" in match:
                        entry["version_end"] = match["versionEndIncluding"]
                        entry["version_end_type"] = "including"
                    if "versionEndExcluding" in match:
                        entry["version_end"] = match["versionEndExcluding"]
                        entry["version_end_type"] = "excluding"
                    affected.append(entry)

    return affected

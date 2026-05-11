"""
ARBOR - Connecteur OSV (Open Source Vulnerabilities - Google).
Utilise l'API OSV pour récupérer les vulnérabilités open source.
"""

import httpx

from app.feeds.base import FeedConnector
from app.models.enums import Severity, VulnSource

OSV_API_BASE = "https://api.osv.dev/v1"


class OSVConnector(FeedConnector):
    """Connecteur pour l'API OSV (Google)."""

    # Écosystèmes à synchroniser
    ECOSYSTEMS = [
        "npm", "PyPI", "Maven", "Go", "NuGet",
        "crates.io", "RubyGems", "Packagist", "Hex",
    ]

    def fetch(self, since: str | None = None) -> list[dict]:
        """
        Récupère les vulnérabilités OSV.
        Utilise l'endpoint de query par écosystème.
        """
        all_items = []

        for ecosystem in self.ECOSYSTEMS:
            try:
                items = self._fetch_ecosystem(ecosystem)
                all_items.extend(items)
            except Exception as e:
                print(f"[OSV] Erreur pour {ecosystem}: {e}")
                continue

        print(f"[OSV] {len(all_items)} vulnérabilités récupérées")
        return all_items

    def _fetch_ecosystem(self, ecosystem: str) -> list[dict]:
        """Récupère les vulnérabilités pour un écosystème donné."""
        items = []
        page_token = None

        while True:
            body: dict = {"ecosystem": ecosystem}
            if page_token:
                body["page_token"] = page_token

            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{OSV_API_BASE}/querybatch",
                    json={"queries": [body]},
                )
                resp.raise_for_status()
                data = resp.json()

            results = data.get("results", [{}])
            if results:
                vulns = results[0].get("vulns", [])
                items.extend(vulns)
                page_token = results[0].get("next_page_token")
                if not page_token:
                    break
            else:
                break

        return items

    def normalize(self, raw_items: list[dict]) -> list[dict]:
        """Normalise les vulnérabilités OSV vers le format ARBOR."""
        normalized = []

        for item in raw_items:
            vuln_id = item.get("id")
            if not vuln_id:
                continue

            # Extraire les aliases (souvent un CVE)
            aliases = item.get("aliases", [])
            cve_id = next((a for a in aliases if a.startswith("CVE-")), vuln_id)

            # Score CVSS (si disponible dans severity)
            cvss_v3_score = None
            cvss_v3_vector = None
            severity_data = item.get("severity", [])
            for sev in severity_data:
                if sev.get("type") == "CVSS_V3":
                    cvss_v3_vector = sev.get("score")
                    # Extraire le score depuis le vecteur
                    cvss_v3_score = _parse_cvss_from_vector(cvss_v3_vector)
                    break

            # Sévérité depuis le score ou le champ database_specific
            severity = _osv_severity(cvss_v3_score, item)

            # Affected PURLs avec version ranges
            affected_purls = _extract_osv_affected(item)

            # Références
            refs = [
                {"url": r.get("url"), "type": r.get("type")}
                for r in item.get("references", [])
            ]

            normalized.append({
                "cve_id": cve_id,
                "source": VulnSource.OSV,
                "title": item.get("summary", cve_id),
                "description": item.get("details", ""),
                "cvss_v3_score": cvss_v3_score,
                "cvss_v3_vector": cvss_v3_vector,
                "cvss_v2_score": None,
                "severity": severity,
                "published_at": item.get("published"),
                "modified_at": item.get("modified"),
                "references": refs,
                "affected_cpes": [],
                "affected_purls": affected_purls,
            })

        return normalized


def _extract_osv_affected(item: dict) -> list[dict]:
    """Extrait les packages affectés avec leurs version ranges."""
    result = []
    for affected in item.get("affected", []):
        pkg = affected.get("package", {})
        ecosystem = pkg.get("ecosystem", "")
        name = pkg.get("name", "")
        purl = pkg.get("purl", "")

        if not purl and name:
            # Générer un PURL approximatif
            eco_map = {
                "npm": "npm", "PyPI": "pypi", "Maven": "maven",
                "Go": "golang", "NuGet": "nuget", "crates.io": "cargo",
                "RubyGems": "gem", "Packagist": "composer", "Hex": "hex",
            }
            purl_type = eco_map.get(ecosystem, "generic")
            purl = f"pkg:{purl_type}/{name}"

        for r in affected.get("ranges", []):
            range_type = r.get("type", "")
            events = r.get("events", [])

            entry = {"purl_pattern": purl}

            for event in events:
                if "introduced" in event:
                    entry["version_start"] = event["introduced"]
                if "fixed" in event:
                    entry["version_end"] = event["fixed"]
                    entry["version_end_type"] = "excluding"
                if "last_affected" in event:
                    entry["version_end"] = event["last_affected"]
                    entry["version_end_type"] = "including"

            result.append(entry)

    return result


def _parse_cvss_from_vector(vector: str | None) -> float | None:
    """Tente d'extraire le score de base d'un vecteur CVSS v3."""
    if not vector:
        return None
    # Le score n'est pas dans le vecteur lui-même
    # Il faudrait un calculateur CVSS complet — pour le MVP on renvoie None
    return None


def _osv_severity(score: float | None, item: dict) -> Severity:
    """Détermine la sévérité depuis le score CVSS ou les métadonnées OSV."""
    if score is not None:
        if score >= 9.0:
            return Severity.CRITICAL
        if score >= 7.0:
            return Severity.HIGH
        if score >= 4.0:
            return Severity.MEDIUM
        if score > 0:
            return Severity.LOW

    # Fallback : regarder database_specific
    db_specific = item.get("database_specific", {})
    sev_str = db_specific.get("severity", "").upper()
    mapping = {
        "CRITICAL": Severity.CRITICAL,
        "HIGH": Severity.HIGH,
        "MODERATE": Severity.MEDIUM,
        "MEDIUM": Severity.MEDIUM,
        "LOW": Severity.LOW,
    }
    return mapping.get(sev_str, Severity.INFO)

"""
ARBOR - Tâches Celery pour les feeds de vulnérabilités.
"""

from datetime import datetime, timezone

from app.workers.celery_app import celery_app
from app.core.config import get_settings
from app.core.database import get_session_factory
from app.models.vulnerability import Vulnerability
from app.services.matching_service import match_vulnerability_against_components


@celery_app.task(name="app.workers.feed_tasks.sync_nvd", bind=True, max_retries=3)
def sync_nvd(self):
    """
    Tâche planifiée : synchronise les vulnérabilités depuis NVD.
    Fréquence : configurable (défaut : toutes les heures).
    """
    settings = get_settings()
    if not settings.online_mode:
        print("[NVD] Mode offline — synchronisation ignorée")
        return {"status": "skipped", "reason": "offline_mode"}

    from app.feeds.nvd_connector import NVDConnector

    try:
        connector = NVDConnector()
        session_factory = get_session_factory()
        db = session_factory()

        try:
            # Déterminer la date de dernière sync
            last_vuln = (
                db.query(Vulnerability.modified_at)
                .filter(Vulnerability.source == "nvd")
                .order_by(Vulnerability.modified_at.desc())
                .first()
            )
            since = last_vuln[0].isoformat() if last_vuln and last_vuln[0] else None

            # Fetch + normalize
            normalized = connector.sync(since=since)

            # Upsert en base
            created, updated = _upsert_vulnerabilities(db, normalized)

            # Matching contre les composants existants
            total_alerts = 0
            for vuln_data in normalized:
                vuln = (
                    db.query(Vulnerability)
                    .filter(Vulnerability.cve_id == vuln_data["cve_id"])
                    .first()
                )
                if vuln:
                    alerts = match_vulnerability_against_components(db, vuln)
                    total_alerts += len(alerts)

            db.commit()

            result = {
                "source": "nvd",
                "fetched": len(normalized),
                "created": created,
                "updated": updated,
                "alerts_generated": total_alerts,
            }
            print(f"[NVD] Sync terminée : {result}")
            return result

        finally:
            db.close()

    except Exception as exc:
        print(f"[NVD] Erreur : {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(name="app.workers.feed_tasks.sync_osv", bind=True, max_retries=3)
def sync_osv(self):
    """
    Tâche planifiée : synchronise les vulnérabilités depuis OSV.
    Fréquence : configurable (défaut : toutes les 6 heures).
    """
    settings = get_settings()
    if not settings.online_mode:
        print("[OSV] Mode offline — synchronisation ignorée")
        return {"status": "skipped", "reason": "offline_mode"}

    from app.feeds.osv_connector import OSVConnector

    try:
        connector = OSVConnector()
        session_factory = get_session_factory()
        db = session_factory()

        try:
            normalized = connector.sync()
            created, updated = _upsert_vulnerabilities(db, normalized)

            total_alerts = 0
            for vuln_data in normalized:
                vuln = (
                    db.query(Vulnerability)
                    .filter(Vulnerability.cve_id == vuln_data["cve_id"])
                    .first()
                )
                if vuln:
                    alerts = match_vulnerability_against_components(db, vuln)
                    total_alerts += len(alerts)

            db.commit()

            result = {
                "source": "osv",
                "fetched": len(normalized),
                "created": created,
                "updated": updated,
                "alerts_generated": total_alerts,
            }
            print(f"[OSV] Sync terminée : {result}")
            return result

        finally:
            db.close()

    except Exception as exc:
        print(f"[OSV] Erreur : {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


def _upsert_vulnerabilities(db, normalized: list[dict]) -> tuple[int, int]:
    """
    Insère ou met à jour les vulnérabilités en base.
    Retourne (created_count, updated_count).
    """
    created = 0
    updated = 0

    for data in normalized:
        existing = (
            db.query(Vulnerability)
            .filter(Vulnerability.cve_id == data["cve_id"])
            .first()
        )

        if existing is None:
            vuln = Vulnerability(
                cve_id=data["cve_id"],
                source=data["source"],
                title=data["title"],
                description=data.get("description", ""),
                cvss_v3_score=data.get("cvss_v3_score"),
                cvss_v3_vector=data.get("cvss_v3_vector"),
                cvss_v2_score=data.get("cvss_v2_score"),
                severity=data["severity"],
                published_at=data.get("published_at"),
                modified_at=data.get("modified_at"),
                references=data.get("references", []),
                affected_cpes=data.get("affected_cpes", []),
                affected_purls=data.get("affected_purls", []),
            )
            db.add(vuln)
            created += 1
        else:
            # Mettre à jour si modifié
            existing.title = data["title"]
            existing.description = data.get("description", existing.description)
            existing.cvss_v3_score = data.get("cvss_v3_score", existing.cvss_v3_score)
            existing.cvss_v3_vector = data.get("cvss_v3_vector", existing.cvss_v3_vector)
            existing.severity = data["severity"]
            existing.modified_at = data.get("modified_at", existing.modified_at)
            existing.references = data.get("references", existing.references)
            existing.affected_cpes = data.get("affected_cpes", existing.affected_cpes)
            existing.affected_purls = data.get("affected_purls", existing.affected_purls)
            updated += 1

    db.flush()
    return created, updated

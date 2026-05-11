"""
ARBOR - Routes API pour les alertes.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, RequireProjectMember, RequireProjectReader
from app.models.alert import Alert
from app.models.bom import Component
from app.models.enums import AlertStatus, Severity
from app.models.project import ProjectMember
from app.models.vulnerability import Vulnerability
from app.schemas.alert import AlertResponse, AlertUpdateRequest

router = APIRouter()


@router.get("/{project_id}/alerts", response_model=list[AlertResponse])
def list_alerts(
    project_id: uuid.UUID,
    status: str | None = Query(default=None, description="Filtrer par statut"),
    severity: str | None = Query(default=None, description="Filtrer par sévérité minimum"),
    _membership: ProjectMember = RequireProjectReader,
    db: Session = Depends(get_db),
):
    """Liste les alertes d'un projet avec filtres optionnels."""
    query = db.query(Alert).filter(Alert.project_id == project_id)

    if status:
        try:
            alert_status = AlertStatus(status)
            query = query.filter(Alert.status == alert_status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Statut invalide : {status}")

    alerts = query.order_by(Alert.created_at.desc()).all()

    # Enrichir avec les données de vulnérabilité et composant
    result = []
    for alert in alerts:
        vuln = db.query(Vulnerability).filter(Vulnerability.id == alert.vulnerability_id).first()
        comp = db.query(Component).filter(Component.id == alert.component_id).first()

        data = AlertResponse(
            id=alert.id,
            project_id=alert.project_id,
            vulnerability_id=alert.vulnerability_id,
            component_id=alert.component_id,
            bom_version_id=alert.bom_version_id,
            status=alert.status.value,
            notified_at=alert.notified_at,
            resolved_at=alert.resolved_at,
            created_at=alert.created_at,
            cve_id=vuln.cve_id if vuln else "",
            severity=vuln.severity.value if vuln else "",
            cvss_score=vuln.cvss_v3_score if vuln else None,
            component_name=comp.name if comp else "",
            component_version=comp.version if comp else "",
        )
        result.append(data)

    # Filtrer par sévérité si demandé
    if severity:
        sev_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
        min_level = sev_order.get(severity.lower(), 0)
        result = [a for a in result if sev_order.get(a.severity, 0) >= min_level]

    return result


@router.patch("/{project_id}/alerts/{alert_id}", response_model=AlertResponse)
def update_alert_status(
    project_id: uuid.UUID,
    alert_id: uuid.UUID,
    body: AlertUpdateRequest,
    current_user: CurrentUser,
    _membership: ProjectMember = RequireProjectMember,
    db: Session = Depends(get_db),
):
    """Met à jour le statut d'une alerte (member+ only)."""
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.project_id == project_id).first()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")

    try:
        new_status = AlertStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Statut invalide : {body.status}")

    alert.status = new_status

    if new_status in (AlertStatus.RESOLVED, AlertStatus.NOT_APPLICABLE):
        from datetime import datetime, timezone
        alert.resolved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(alert)

    vuln = db.query(Vulnerability).filter(Vulnerability.id == alert.vulnerability_id).first()
    comp = db.query(Component).filter(Component.id == alert.component_id).first()

    return AlertResponse(
        id=alert.id,
        project_id=alert.project_id,
        vulnerability_id=alert.vulnerability_id,
        component_id=alert.component_id,
        bom_version_id=alert.bom_version_id,
        status=alert.status.value,
        notified_at=alert.notified_at,
        resolved_at=alert.resolved_at,
        created_at=alert.created_at,
        cve_id=vuln.cve_id if vuln else "",
        severity=vuln.severity.value if vuln else "",
        cvss_score=vuln.cvss_v3_score if vuln else None,
        component_name=comp.name if comp else "",
        component_version=comp.version if comp else "",
    )

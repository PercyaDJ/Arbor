"""
ARBOR - Service d'audit.
Enregistrement immutable des actions sensibles.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.enums import AuditAction


def log_action(
    db: Session,
    *,
    action: AuditAction,
    entity_type: str,
    entity_id: str,
    user_id: uuid.UUID | None = None,
    ip_address: str | None = None,
    details: dict | None = None,
) -> AuditLog:
    """
    Crée une entrée dans le log d'audit.
    Appelé par les services métier pour tracer les actions sensibles.
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        details=details or {},
        ip_address=ip_address,
    )
    db.add(entry)
    db.flush()
    return entry

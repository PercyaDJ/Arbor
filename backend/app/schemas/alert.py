"""
ARBOR - Schémas Pydantic pour les alertes.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class AlertResponse(BaseModel):
    """Réponse pour une alerte."""
    id: uuid.UUID
    project_id: uuid.UUID
    vulnerability_id: uuid.UUID
    component_id: uuid.UUID
    bom_version_id: uuid.UUID | None
    status: str
    notified_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime

    # Données enrichies
    cve_id: str = ""
    severity: str = ""
    cvss_score: float | None = None
    component_name: str = ""
    component_version: str = ""

    model_config = {"from_attributes": True}


class AlertUpdateRequest(BaseModel):
    """Mise à jour du statut d'une alerte."""
    status: str

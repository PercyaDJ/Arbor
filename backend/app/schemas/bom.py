"""
ARBOR - Schémas Pydantic pour les BOM.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class BOMResponse(BaseModel):
    """Réponse pour une version de BOM déposée."""
    id: uuid.UUID
    project_id: uuid.UUID
    version_label: str
    format: str
    type: str
    sha256_hash: str
    component_count: int
    parsed_at: datetime | None
    created_by: uuid.UUID | None
    bom_metadata: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class BOMBriefResponse(BaseModel):
    """BOM abrégée pour les listes."""
    id: uuid.UUID
    version_label: str
    format: str
    type: str
    component_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BOMUploadResponse(BaseModel):
    """Réponse après dépôt d'une BOM."""
    bom: BOMResponse
    components_added: int
    components_existing: int
    alerts_generated: int


class ComponentResponse(BaseModel):
    """Réponse pour un composant."""
    id: uuid.UUID
    purl: str
    name: str
    version: str
    type: str
    cpe: str | None
    supplier: str | None
    license: str | None

    model_config = {"from_attributes": True}

"""
ARBOR - Schémas Pydantic pour les projets.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# --- Projet ---
class ProjectCreateRequest(BaseModel):
    """Création d'un projet."""
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    settings: dict | None = None


class ProjectUpdateRequest(BaseModel):
    """Mise à jour d'un projet."""
    name: str | None = None
    description: str | None = None
    settings: dict | None = None


class ProjectResponse(BaseModel):
    """Réponse projet complète."""
    id: uuid.UUID
    name: str
    description: str | None
    organisation_id: uuid.UUID
    settings: dict
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    # Stats calculées (renseignées par le service)
    alert_count: int = 0
    critical_alert_count: int = 0
    last_bom_date: datetime | None = None
    member_count: int = 0

    model_config = {"from_attributes": True}


class ProjectBriefResponse(BaseModel):
    """Projet abrégé (pour les listes)."""
    id: uuid.UUID
    name: str
    description: str | None
    archived_at: datetime | None
    created_at: datetime
    alert_count: int = 0
    critical_alert_count: int = 0
    last_bom_date: datetime | None = None

    model_config = {"from_attributes": True}


# --- Membres ---
class MemberAddRequest(BaseModel):
    """Ajout d'un membre à un projet."""
    user_id: uuid.UUID
    role: str = Field(default="member", pattern="^(owner|member|reader)$")


class MemberUpdateRequest(BaseModel):
    """Changement de rôle d'un membre."""
    role: str = Field(..., pattern="^(owner|member|reader)$")


class MemberResponse(BaseModel):
    """Réponse membre de projet."""
    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    user_email: str = ""
    user_display_name: str = ""
    created_at: datetime

    model_config = {"from_attributes": True}

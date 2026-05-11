"""
ARBOR - Schémas Pydantic pour les utilisateurs.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    """Représentation publique d'un utilisateur."""
    id: uuid.UUID
    email: EmailStr
    display_name: str
    is_active: bool
    is_superuser: bool
    organisation_id: uuid.UUID
    notification_preferences: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    """Mise à jour du profil utilisateur."""
    display_name: str | None = None
    notification_preferences: dict | None = None


class UserBriefResponse(BaseModel):
    """Représentation abrégée (pour les listes)."""
    id: uuid.UUID
    email: str
    display_name: str

    model_config = {"from_attributes": True}

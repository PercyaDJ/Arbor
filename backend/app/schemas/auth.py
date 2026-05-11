"""
ARBOR - Schémas Pydantic pour l'authentification.
"""

from pydantic import BaseModel, EmailStr, Field


# --- Login ---
class LoginRequest(BaseModel):
    """Requête de connexion."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    """Réponse contenant les tokens JWT."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Requête de renouvellement de token."""
    refresh_token: str


# --- Inscription (par invitation) ---
class RegisterRequest(BaseModel):
    """Requête d'inscription via token d'invitation."""
    invitation_token: str
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=2, max_length=255)


# --- Invitation ---
class InvitationCreateRequest(BaseModel):
    """Requête de création d'invitation (owner/admin only)."""
    email: EmailStr
    project_id: str | None = None
    project_role: str | None = None


class InvitationResponse(BaseModel):
    """Réponse après création d'une invitation."""
    id: str
    email: str
    invitation_url: str
    created_at: str


# --- Changement de mot de passe ---
class ChangePasswordRequest(BaseModel):
    """Requête de changement de mot de passe."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

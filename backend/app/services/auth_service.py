"""
ARBOR - Service d'authentification.
Logique métier pour login, inscription par invitation et gestion des tokens.
"""

import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.enums import AuditAction, OrgPlan, ProjectRole
from app.models.organisation import Organisation
from app.models.project import ProjectMember
from app.models.user import Invitation, User
from app.services.audit_service import log_action


class AuthError(Exception):
    """Erreur métier liée à l'authentification."""

    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Authentifie un utilisateur par email + mot de passe.
    Lève AuthError si les identifiants sont invalides.
    """
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(password, user.hashed_password):
        raise AuthError("Email ou mot de passe incorrect", 401)

    if not user.is_active:
        raise AuthError("Compte désactivé. Contactez un administrateur.", 403)

    return user


def create_tokens(user: User) -> dict:
    """Crée les tokens JWT (access + refresh) pour un utilisateur."""
    extra = {"is_superuser": user.is_superuser}
    access_token = create_access_token(subject=str(user.id), extra_claims=extra)
    refresh_token = create_refresh_token(subject=str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def refresh_access_token(db: Session, refresh_token: str) -> dict:
    """
    Renouvelle l'access token à partir d'un refresh token valide.
    Lève AuthError si le refresh token est invalide.
    """
    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise AuthError("Refresh token invalide ou expiré", 401)

    user_id = payload.get("sub")
    if user_id is None:
        raise AuthError("Token invalide", 401)

    user = db.query(User).filter(User.id == uuid.UUID(user_id), User.is_active.is_(True)).first()
    if user is None:
        raise AuthError("Utilisateur non trouvé ou désactivé", 401)

    return create_tokens(user)


def create_invitation(
    db: Session,
    *,
    email: str,
    invited_by: User,
    project_id: uuid.UUID | None = None,
    project_role: str | None = None,
    ip_address: str | None = None,
) -> Invitation:
    """
    Crée une invitation pour un nouvel utilisateur.
    Seuls les owners et superusers peuvent inviter.
    """
    # Vérifier que l'email n'est pas déjà inscrit
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise AuthError(f"Un utilisateur avec l'email {email} existe déjà", 409)

    # Vérifier qu'il n'y a pas déjà une invitation active
    existing_inv = (
        db.query(Invitation)
        .filter(Invitation.email == email, Invitation.is_consumed.is_(False))
        .first()
    )
    if existing_inv is not None:
        raise AuthError(f"Une invitation pour {email} est déjà en attente", 409)

    # Générer le token d'invitation
    token = secrets.token_urlsafe(48)

    invitation = Invitation(
        email=email,
        token=token,
        invited_by=invited_by.id,
        organisation_id=invited_by.organisation_id,
        project_id=project_id,
        project_role=project_role,
    )
    db.add(invitation)

    log_action(
        db,
        action=AuditAction.USER_INVITED,
        entity_type="invitation",
        entity_id=str(invitation.id),
        user_id=invited_by.id,
        ip_address=ip_address,
        details={"invited_email": email},
    )

    db.commit()
    db.refresh(invitation)
    return invitation


def register_with_invitation(
    db: Session,
    *,
    invitation_token: str,
    password: str,
    display_name: str,
) -> User:
    """
    Inscrit un utilisateur à partir d'un token d'invitation.
    L'invitation est consommée et le user est créé.
    """
    invitation = (
        db.query(Invitation)
        .filter(Invitation.token == invitation_token, Invitation.is_consumed.is_(False))
        .first()
    )
    if invitation is None:
        raise AuthError("Invitation invalide ou déjà utilisée", 400)

    # Vérifier que l'email n'est pas pris entre-temps
    existing = db.query(User).filter(User.email == invitation.email).first()
    if existing is not None:
        raise AuthError(f"Un utilisateur avec cet email existe déjà", 409)

    # Créer l'utilisateur
    user = User(
        email=invitation.email,
        hashed_password=hash_password(password),
        display_name=display_name,
        organisation_id=invitation.organisation_id,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()

    # Si un projet est pré-assigné, ajouter le membership
    if invitation.project_id is not None:
        role = ProjectRole(invitation.project_role) if invitation.project_role else ProjectRole.MEMBER
        membership = ProjectMember(
            project_id=invitation.project_id,
            user_id=user.id,
            role=role,
        )
        db.add(membership)

    # Consommer l'invitation
    invitation.is_consumed = True

    db.commit()
    db.refresh(user)
    return user


def init_default_org_and_admin(db: Session) -> tuple[Organisation, User]:
    """
    Initialise l'organisation par défaut et le compte admin au premier démarrage.
    Idempotent : ne fait rien si l'admin existe déjà.
    Retourne (organisation, admin_user).
    """
    settings = get_settings()

    # Vérifier si l'admin existe déjà
    admin = db.query(User).filter(User.email == settings.admin_email).first()
    if admin is not None:
        org = db.query(Organisation).filter(Organisation.id == admin.organisation_id).first()
        return org, admin

    # Créer l'organisation par défaut
    org_slug = settings.default_org_name.lower().replace(" ", "-").replace("'", "")
    org = Organisation(
        name=settings.default_org_name,
        slug=org_slug,
        plan=OrgPlan.FREE,
        settings={
            "default_cvss_threshold": settings.default_cvss_threshold,
            "active_cert_sources": ["nvd", "osv"],
            "online_mode": settings.online_mode,
        },
    )
    db.add(org)
    db.flush()

    # Créer l'utilisateur admin
    admin = User(
        email=settings.admin_email,
        hashed_password=hash_password(settings.admin_password),
        display_name="Administrateur",
        organisation_id=org.id,
        is_active=True,
        is_superuser=True,
        notification_preferences={"cvss_min_threshold": 0.0, "digest_mode": "realtime"},
    )
    db.add(admin)
    db.commit()
    db.refresh(org)
    db.refresh(admin)

    return org, admin


def change_password(
    db: Session,
    *,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    """Change le mot de passe de l'utilisateur."""
    if not verify_password(current_password, user.hashed_password):
        raise AuthError("Mot de passe actuel incorrect", 400)

    user.hashed_password = hash_password(new_password)
    db.commit()

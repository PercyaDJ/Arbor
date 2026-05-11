"""
ARBOR - Routes API d'authentification.
Login, inscription par invitation, refresh token, profil utilisateur.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, SuperUser
from app.schemas.auth import (
    ChangePasswordRequest,
    InvitationCreateRequest,
    InvitationResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.auth_service import (
    AuthError,
    authenticate_user,
    change_password,
    create_invitation,
    create_tokens,
    refresh_access_token,
    register_with_invitation,
)
from app.services.audit_service import log_action
from app.models.enums import AuditAction

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authentification par email + mot de passe. Retourne un access et refresh token."""
    try:
        user = authenticate_user(db, body.email, body.password)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    log_action(
        db,
        action=AuditAction.USER_LOGIN,
        entity_type="user",
        entity_id=str(user.id),
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()

    return create_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """Renouvelle l'access token à partir d'un refresh token valide."""
    try:
        tokens = refresh_access_token(db, body.refresh_token)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return tokens


@router.post("/register", response_model=UserResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Inscription via un token d'invitation. Crée le compte utilisateur."""
    try:
        user = register_with_invitation(
            db,
            invitation_token=body.invitation_token,
            password=body.password,
            display_name=body.display_name,
        )
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return user


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentUser):
    """Retourne le profil de l'utilisateur connecté."""
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    body: UserUpdateRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """Met à jour le profil de l'utilisateur connecté."""
    if body.display_name is not None:
        current_user.display_name = body.display_name
    if body.notification_preferences is not None:
        current_user.notification_preferences = body.notification_preferences
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/password")
def update_password(
    body: ChangePasswordRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """Change le mot de passe de l'utilisateur connecté."""
    try:
        change_password(
            db,
            user=current_user,
            current_password=body.current_password,
            new_password=body.new_password,
        )
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return {"message": "Mot de passe modifié avec succès"}


# --- Invitations (owner / superuser) ---

@router.post("/invitations", response_model=InvitationResponse)
def create_invite(
    body: InvitationCreateRequest,
    request: Request,
    current_user: SuperUser,
    db: Session = Depends(get_db),
):
    """
    Crée une invitation pour un nouvel utilisateur.
    Réservé aux superusers (gestion globale).
    """
    import uuid as uuid_mod

    project_uuid = uuid_mod.UUID(body.project_id) if body.project_id else None

    try:
        invitation = create_invitation(
            db,
            email=body.email,
            invited_by=current_user,
            project_id=project_uuid,
            project_role=body.project_role,
            ip_address=request.client.host if request.client else None,
        )
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    return InvitationResponse(
        id=str(invitation.id),
        email=invitation.email,
        invitation_url=f"/register?token={invitation.token}",
        created_at=invitation.created_at.isoformat(),
    )

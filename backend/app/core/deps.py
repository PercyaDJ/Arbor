"""
ARBOR - Dépendances FastAPI (injection).
Authentification, autorisation et utilitaires communs.
"""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import decode_token, hash_api_key
from app.models.enums import ProjectRole
from app.models.project import ProjectApiKey, ProjectMember
from app.models.user import User

# Schéma d'authentification Bearer
security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """
    Dépendance : extrait et valide l'utilisateur courant depuis le JWT.
    Lève 401 si le token est absent, invalide ou expiré.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification requis",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide : sujet manquant",
        )

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide : identifiant utilisateur malformé",
        )

    user = db.query(User).filter(User.id == uid, User.is_active.is_(True)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur non trouvé ou désactivé",
        )

    return user


# Alias typé pour l'injection
CurrentUser = Annotated[User, Depends(get_current_user)]


def require_superuser(current_user: CurrentUser) -> User:
    """Dépendance : vérifie que l'utilisateur est superadmin."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Droits d'administration requis",
        )
    return current_user


SuperUser = Annotated[User, Depends(require_superuser)]


def get_project_role_checker(min_role: ProjectRole):
    """
    Factory de dépendance : vérifie que l'utilisateur a au moins le rôle
    spécifié sur le projet cible (extrait de l'URL path).

    Hiérarchie : owner > member > reader
    """
    role_hierarchy = {
        ProjectRole.READER: 0,
        ProjectRole.MEMBER: 1,
        ProjectRole.OWNER: 2,
    }

    def checker(
        project_id: uuid.UUID,
        current_user: CurrentUser,
        db: Session = Depends(get_db),
    ) -> ProjectMember:
        # Les superusers passent tous les checks
        if current_user.is_superuser:
            # Créer un pseudo-membership pour cohérence
            membership = (
                db.query(ProjectMember)
                .filter(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == current_user.id,
                )
                .first()
            )
            if membership is None:
                # Superuser sans membership : accès autorisé mais on simule owner
                mock = ProjectMember(
                    project_id=project_id,
                    user_id=current_user.id,
                    role=ProjectRole.OWNER,
                )
                return mock
            return membership

        membership = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == current_user.id,
            )
            .first()
        )

        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas membre de ce projet",
            )

        if role_hierarchy.get(membership.role, -1) < role_hierarchy.get(min_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle '{min_role.value}' minimum requis pour cette action",
            )

        return membership

    return checker


# Dépendances pré-configurées pour les rôles projet courants
RequireProjectReader = Depends(get_project_role_checker(ProjectRole.READER))
RequireProjectMember = Depends(get_project_role_checker(ProjectRole.MEMBER))
RequireProjectOwner = Depends(get_project_role_checker(ProjectRole.OWNER))


def get_current_user_or_api_key(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: Session = Depends(get_db),
) -> User | ProjectApiKey:
    """
    Dépendance : accepte soit un JWT utilisateur, soit une API key projet.
    Utilisé pour l'endpoint de dépôt BOM (CI/CD).
    Format API key dans le header : Bearer arbor_ak_<key>
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise (JWT ou API key)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Détecter si c'est une API key (préfixe arbor_ak_)
    if token.startswith("arbor_ak_"):
        key_hash = hash_api_key(token)
        api_key = (
            db.query(ProjectApiKey)
            .filter(ProjectApiKey.key_hash == key_hash, ProjectApiKey.is_active.is_(True))
            .first()
        )
        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key invalide ou révoquée",
            )
        return api_key

    # Sinon, traiter comme un JWT
    return get_current_user(credentials, db)

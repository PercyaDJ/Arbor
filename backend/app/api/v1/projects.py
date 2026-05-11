"""
ARBOR - Routes API pour les projets et les membres.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, RequireProjectMember, RequireProjectOwner, RequireProjectReader
from app.models.enums import ProjectRole
from app.models.project import ProjectMember
from app.schemas.project import (
    MemberAddRequest,
    MemberResponse,
    MemberUpdateRequest,
    ProjectBriefResponse,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.services.project_service import (
    ProjectError,
    add_member,
    archive_project,
    create_project,
    get_project_detail,
    get_project_members,
    get_user_projects,
    remove_member,
    update_member_role,
    update_project,
)

router = APIRouter()


# --- Projets ---

@router.post("/", response_model=ProjectResponse, status_code=201)
def create(
    body: ProjectCreateRequest,
    request: Request,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """Crée un nouveau projet. L'utilisateur devient automatiquement owner."""
    try:
        project = create_project(
            db,
            name=body.name,
            description=body.description,
            settings=body.settings,
            user=current_user,
            ip_address=request.client.host if request.client else None,
        )
        return get_project_detail(db, project.id)
    except ProjectError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/", response_model=list[ProjectBriefResponse])
def list_projects(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Liste tous les projets accessibles par l'utilisateur connecté."""
    return get_user_projects(db, current_user)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    _membership: ProjectMember = RequireProjectReader,
    db: Session = Depends(get_db),
):
    """Détail d'un projet avec ses statistiques."""
    try:
        return get_project_detail(db, project_id)
    except ProjectError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.patch("/{project_id}", response_model=ProjectResponse)
def patch_project(
    project_id: uuid.UUID,
    body: ProjectUpdateRequest,
    _membership: ProjectMember = RequireProjectOwner,
    db: Session = Depends(get_db),
):
    """Met à jour un projet (owner only)."""
    try:
        update_project(
            db,
            project_id=project_id,
            name=body.name,
            description=body.description,
            settings=body.settings,
        )
        return get_project_detail(db, project_id)
    except ProjectError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{project_id}/archive", response_model=ProjectResponse)
def archive(
    project_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    _membership: ProjectMember = RequireProjectOwner,
    db: Session = Depends(get_db),
):
    """Archive un projet (owner only). Action irréversible."""
    try:
        archive_project(
            db,
            project_id=project_id,
            user=current_user,
            ip_address=request.client.host if request.client else None,
        )
        return get_project_detail(db, project_id)
    except ProjectError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


# --- Membres ---

@router.get("/{project_id}/members", response_model=list[MemberResponse])
def list_members(
    project_id: uuid.UUID,
    _membership: ProjectMember = RequireProjectReader,
    db: Session = Depends(get_db),
):
    """Liste les membres d'un projet."""
    return get_project_members(db, project_id)


@router.post("/{project_id}/members", response_model=MemberResponse, status_code=201)
def add_project_member(
    project_id: uuid.UUID,
    body: MemberAddRequest,
    request: Request,
    current_user: CurrentUser,
    _membership: ProjectMember = RequireProjectOwner,
    db: Session = Depends(get_db),
):
    """Ajoute un membre au projet (owner only)."""
    try:
        member = add_member(
            db,
            project_id=project_id,
            user_id=body.user_id,
            role=ProjectRole(body.role),
            added_by=current_user,
            ip_address=request.client.host if request.client else None,
        )
        # Enrichir avec les infos user
        members = get_project_members(db, project_id)
        return next(m for m in members if m["id"] == member.id)
    except ProjectError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.patch("/{project_id}/members/{member_id}", response_model=MemberResponse)
def update_member(
    project_id: uuid.UUID,
    member_id: uuid.UUID,
    body: MemberUpdateRequest,
    request: Request,
    current_user: CurrentUser,
    _membership: ProjectMember = RequireProjectOwner,
    db: Session = Depends(get_db),
):
    """Change le rôle d'un membre (owner only)."""
    try:
        update_member_role(
            db,
            member_id=member_id,
            role=ProjectRole(body.role),
            updated_by=current_user,
            ip_address=request.client.host if request.client else None,
        )
        members = get_project_members(db, project_id)
        return next(m for m in members if m["id"] == member_id)
    except ProjectError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.delete("/{project_id}/members/{member_id}", status_code=204)
def delete_member(
    project_id: uuid.UUID,
    member_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    _membership: ProjectMember = RequireProjectOwner,
    db: Session = Depends(get_db),
):
    """Retire un membre du projet (owner only)."""
    try:
        remove_member(
            db,
            member_id=member_id,
            removed_by=current_user,
            ip_address=request.client.host if request.client else None,
        )
    except ProjectError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

"""
ARBOR - Routes API pour le dépôt et la gestion des BOM.
"""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, RequireProjectMember, RequireProjectOwner, RequireProjectReader
from app.models.project import ProjectMember
from app.schemas.bom import BOMBriefResponse, BOMResponse, BOMUploadResponse, ComponentResponse
from app.services.bom_service import (
    BOMError,
    deposit_bom,
    get_bom_components,
    get_bom_detail,
    get_bom_history,
    purge_bom_history,
)

router = APIRouter()


@router.post(
    "/{project_id}/bom",
    response_model=BOMUploadResponse,
    status_code=201,
)
async def upload_bom(
    project_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    version_label: str | None = Query(default=None, description="Label de version (auto-généré si absent)"),
    _membership: ProjectMember = RequireProjectMember,
    db: Session = Depends(get_db),
):
    """
    Dépose une BOM pour un projet.
    Formats supportés : CycloneDX (JSON/XML), SPDX (JSON/XML).
    """
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Fichier vide")
    if len(content) > 50 * 1024 * 1024:  # 50 MB max
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 50 MB)")

    try:
        result = deposit_bom(
            db,
            project_id=project_id,
            filename=file.filename or "unknown",
            content=content,
            version_label=version_label,
            user_id=current_user.id,
            ip_address=request.client.host if request.client else None,
        )
        return result
    except BOMError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/{project_id}/bom", response_model=list[BOMBriefResponse])
def list_bom_versions(
    project_id: uuid.UUID,
    _membership: ProjectMember = RequireProjectReader,
    db: Session = Depends(get_db),
):
    """Historique des versions de BOM d'un projet."""
    return get_bom_history(db, project_id)


@router.get("/{project_id}/bom/{bom_id}", response_model=BOMResponse)
def get_bom(
    project_id: uuid.UUID,
    bom_id: uuid.UUID,
    _membership: ProjectMember = RequireProjectReader,
    db: Session = Depends(get_db),
):
    """Détail d'une version de BOM."""
    try:
        bom = get_bom_detail(db, bom_id)
        if bom.project_id != project_id:
            raise HTTPException(status_code=404, detail="BOM non trouvée pour ce projet")
        return bom
    except BOMError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/{project_id}/bom/{bom_id}/components", response_model=list[ComponentResponse])
def list_bom_components(
    project_id: uuid.UUID,
    bom_id: uuid.UUID,
    _membership: ProjectMember = RequireProjectReader,
    db: Session = Depends(get_db),
):
    """Liste les composants d'une BOM."""
    return get_bom_components(db, bom_id)


@router.post("/{project_id}/bom/purge")
def purge_bom(
    project_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    keep_last: int = Query(default=3, ge=1, le=100, description="Nombre de BOM à conserver"),
    _membership: ProjectMember = RequireProjectOwner,
    db: Session = Depends(get_db),
):
    """Purge les anciennes BOM, en gardant les N dernières (owner only)."""
    deleted = purge_bom_history(
        db,
        project_id=project_id,
        keep_last=keep_last,
        user=current_user,
        ip_address=request.client.host if request.client else None,
    )
    return {"deleted_count": deleted, "kept": keep_last}

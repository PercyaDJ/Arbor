"""
ARBOR - Service de gestion des projets.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.bom import BOM
from app.models.enums import AlertStatus, AuditAction, ProjectRole, Severity
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.services.audit_service import log_action


class ProjectError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def create_project(
    db: Session,
    *,
    name: str,
    description: str | None,
    settings: dict | None,
    user: User,
    ip_address: str | None = None,
) -> Project:
    """Crée un projet et assigne l'utilisateur comme owner."""
    project = Project(
        name=name,
        description=description,
        organisation_id=user.organisation_id,
        settings=settings or {},
    )
    db.add(project)
    db.flush()

    membership = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=ProjectRole.OWNER,
    )
    db.add(membership)

    log_action(
        db,
        action=AuditAction.PROJECT_CREATED,
        entity_type="project",
        entity_id=str(project.id),
        user_id=user.id,
        ip_address=ip_address,
        details={"name": name},
    )

    db.commit()
    db.refresh(project)
    return project


def get_user_projects(db: Session, user: User) -> list[dict]:
    """Retourne tous les projets accessibles par l'utilisateur avec stats."""
    if user.is_superuser:
        projects = (
            db.query(Project)
            .filter(Project.organisation_id == user.organisation_id)
            .order_by(Project.created_at.desc())
            .all()
        )
    else:
        project_ids = (
            db.query(ProjectMember.project_id)
            .filter(ProjectMember.user_id == user.id)
            .subquery()
        )
        projects = (
            db.query(Project)
            .filter(Project.id.in_(project_ids))
            .order_by(Project.created_at.desc())
            .all()
        )

    result = []
    for project in projects:
        stats = _get_project_stats(db, project.id)
        data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "organisation_id": project.organisation_id,
            "settings": project.settings,
            "archived_at": project.archived_at,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            **stats,
        }
        result.append(data)
    return result


def get_project_detail(db: Session, project_id: uuid.UUID) -> dict:
    """Retourne le détail d'un projet avec ses stats."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise ProjectError("Projet non trouvé", 404)

    stats = _get_project_stats(db, project.id)
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "organisation_id": project.organisation_id,
        "settings": project.settings,
        "archived_at": project.archived_at,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        **stats,
    }


def update_project(
    db: Session,
    *,
    project_id: uuid.UUID,
    name: str | None = None,
    description: str | None = None,
    settings: dict | None = None,
) -> Project:
    """Met à jour un projet (owner only — vérifié par la dépendance)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise ProjectError("Projet non trouvé", 404)

    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    if settings is not None:
        project.settings = settings

    db.commit()
    db.refresh(project)
    return project


def archive_project(
    db: Session,
    *,
    project_id: uuid.UUID,
    user: User,
    ip_address: str | None = None,
) -> Project:
    """Archive un projet (owner only)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise ProjectError("Projet non trouvé", 404)
    if project.archived_at is not None:
        raise ProjectError("Le projet est déjà archivé", 400)

    project.archived_at = datetime.now(timezone.utc)

    log_action(
        db,
        action=AuditAction.PROJECT_ARCHIVED,
        entity_type="project",
        entity_id=str(project.id),
        user_id=user.id,
        ip_address=ip_address,
    )

    db.commit()
    db.refresh(project)
    return project


# --- Membres ---

def add_member(
    db: Session,
    *,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    role: ProjectRole,
    added_by: User,
    ip_address: str | None = None,
) -> ProjectMember:
    """Ajoute un membre au projet."""
    # Vérifier que l'utilisateur existe
    target_user = db.query(User).filter(User.id == user_id).first()
    if target_user is None:
        raise ProjectError("Utilisateur non trouvé", 404)

    existing = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        .first()
    )
    if existing is not None:
        raise ProjectError("L'utilisateur est déjà membre de ce projet", 409)

    membership = ProjectMember(project_id=project_id, user_id=user_id, role=role)
    db.add(membership)

    log_action(
        db,
        action=AuditAction.MEMBER_ADDED,
        entity_type="project_member",
        entity_id=str(project_id),
        user_id=added_by.id,
        ip_address=ip_address,
        details={"target_user_id": str(user_id), "role": role.value},
    )

    db.commit()
    db.refresh(membership)
    return membership


def update_member_role(
    db: Session,
    *,
    member_id: uuid.UUID,
    role: ProjectRole,
    updated_by: User,
    ip_address: str | None = None,
) -> ProjectMember:
    """Change le rôle d'un membre."""
    membership = db.query(ProjectMember).filter(ProjectMember.id == member_id).first()
    if membership is None:
        raise ProjectError("Membre non trouvé", 404)

    old_role = membership.role.value
    membership.role = role

    log_action(
        db,
        action=AuditAction.MEMBER_ROLE_CHANGED,
        entity_type="project_member",
        entity_id=str(member_id),
        user_id=updated_by.id,
        ip_address=ip_address,
        details={"old_role": old_role, "new_role": role.value},
    )

    db.commit()
    db.refresh(membership)
    return membership


def remove_member(
    db: Session,
    *,
    member_id: uuid.UUID,
    removed_by: User,
    ip_address: str | None = None,
) -> None:
    """Retire un membre du projet."""
    membership = db.query(ProjectMember).filter(ProjectMember.id == member_id).first()
    if membership is None:
        raise ProjectError("Membre non trouvé", 404)

    # Empêcher de retirer le dernier owner
    if membership.role == ProjectRole.OWNER:
        owner_count = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == membership.project_id,
                ProjectMember.role == ProjectRole.OWNER,
            )
            .count()
        )
        if owner_count <= 1:
            raise ProjectError("Impossible de retirer le dernier owner du projet", 400)

    log_action(
        db,
        action=AuditAction.MEMBER_REMOVED,
        entity_type="project_member",
        entity_id=str(member_id),
        user_id=removed_by.id,
        ip_address=ip_address,
        details={"target_user_id": str(membership.user_id)},
    )

    db.delete(membership)
    db.commit()


def get_project_members(db: Session, project_id: uuid.UUID) -> list[dict]:
    """Retourne les membres d'un projet avec les infos utilisateur."""
    members = (
        db.query(ProjectMember, User)
        .join(User, ProjectMember.user_id == User.id)
        .filter(ProjectMember.project_id == project_id)
        .all()
    )

    return [
        {
            "id": m.id,
            "project_id": m.project_id,
            "user_id": m.user_id,
            "role": m.role.value,
            "user_email": u.email,
            "user_display_name": u.display_name,
            "created_at": m.created_at,
        }
        for m, u in members
    ]


# --- Helpers internes ---

def _get_project_stats(db: Session, project_id: uuid.UUID) -> dict:
    """Calcule les stats d'un projet (alertes, dernière BOM, membres)."""
    alert_count = (
        db.query(func.count(Alert.id))
        .filter(
            Alert.project_id == project_id,
            Alert.status.in_([AlertStatus.NEW, AlertStatus.ACKNOWLEDGED, AlertStatus.IN_PROGRESS]),
        )
        .scalar() or 0
    )

    critical_count = (
        db.query(func.count(Alert.id))
        .filter(Alert.project_id == project_id, Alert.status == AlertStatus.NEW)
        .join(Alert.vulnerability)
        .filter(Alert.vulnerability.has(severity=Severity.CRITICAL))
        .scalar() or 0
    )

    last_bom = (
        db.query(BOM.created_at)
        .filter(BOM.project_id == project_id)
        .order_by(BOM.created_at.desc())
        .first()
    )

    member_count = (
        db.query(func.count(ProjectMember.id))
        .filter(ProjectMember.project_id == project_id)
        .scalar() or 0
    )

    return {
        "alert_count": alert_count,
        "critical_alert_count": critical_count,
        "last_bom_date": last_bom[0] if last_bom else None,
        "member_count": member_count,
    }

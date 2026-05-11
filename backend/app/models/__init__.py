"""
ARBOR - Import centralisé de tous les modèles SQLAlchemy.
Ce fichier est importé par Alembic (env.py) pour que l'autogenerate
détecte toutes les tables.
"""

from app.models.organisation import Organisation
from app.models.user import User, Invitation
from app.models.project import Project, ProjectMember, ProjectApiKey
from app.models.bom import BOM, Component, BOMComponent
from app.models.vulnerability import Vulnerability
from app.models.alert import Alert
from app.models.vex import VEXStatement
from app.models.audit import AuditLog

__all__ = [
    "Organisation",
    "User",
    "Invitation",
    "Project",
    "ProjectMember",
    "ProjectApiKey",
    "BOM",
    "Component",
    "BOMComponent",
    "Vulnerability",
    "Alert",
    "VEXStatement",
    "AuditLog",
]

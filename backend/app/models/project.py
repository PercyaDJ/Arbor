"""
ARBOR - Modèles Project et ProjectMember.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ProjectRole


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Unité centrale d'ARBOR.
    Un projet correspond à une application, un système, un produit
    ou tout périmètre logiciel cohérent.
    """

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Settings propres au projet (JSONB)
    # Surcharge les settings de l'organisation si définis
    # Exemple : {"cvss_threshold": 7.0, "cert_sources": ["nvd", "osv"], "notifications_enabled": true}
    settings: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )

    # --- Relations ---
    organisation = relationship("Organisation", back_populates="projects")
    members = relationship(
        "ProjectMember", back_populates="project", lazy="select", cascade="all, delete-orphan"
    )
    boms = relationship("BOM", back_populates="project", lazy="select", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="project", lazy="select", cascade="all, delete-orphan")
    vex_statements = relationship(
        "VEXStatement", back_populates="project", lazy="select", cascade="all, delete-orphan"
    )
    api_keys = relationship(
        "ProjectApiKey", back_populates="project", lazy="select", cascade="all, delete-orphan"
    )

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None

    def __repr__(self) -> str:
        status = "archived" if self.is_archived else "active"
        return f"<Project {self.name} ({status})>"


class ProjectMember(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Liaison entre un utilisateur et un projet avec un rôle.
    Un projet peut avoir plusieurs owners.
    L'utilisateur créateur est owner par défaut.
    """

    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_member"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[ProjectRole] = mapped_column(
        Enum(ProjectRole, name="project_role"),
        default=ProjectRole.MEMBER,
        nullable=False,
    )

    # --- Relations ---
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")

    def __repr__(self) -> str:
        return f"<ProjectMember user={self.user_id} role={self.role.value}>"


class ProjectApiKey(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Clé API par projet pour l'ingestion CI/CD.
    Le hash SHA256 de la clé est stocké en base (jamais en clair).
    """

    __tablename__ = "project_api_keys"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # SHA256
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # --- Relations ---
    project = relationship("Project", back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<ProjectApiKey {self.name} active={self.is_active}>"

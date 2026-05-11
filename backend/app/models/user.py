"""
ARBOR - Modèle User.
Authentification locale uniquement en v0.1 (invitation only, pas de 2FA).
"""

import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Utilisateur ARBOR.
    Lié à une organisation unique (mono-org en v0.1).
    L'inscription se fait par invitation d'un owner/admin.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Organisation (mono-org MVP)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Préférences de notification (JSONB)
    # Exemple : {"cvss_min_threshold": 7.0, "digest_mode": "realtime"|"daily"|"weekly"}
    notification_preferences: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )

    # --- Relations ---
    organisation = relationship("Organisation", back_populates="users")
    project_memberships = relationship(
        "ProjectMember", back_populates="user", lazy="select", cascade="all, delete-orphan"
    )
    created_boms = relationship("BOM", back_populates="created_by_user", lazy="select")

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Invitation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Invitation à rejoindre ARBOR.
    Créée par un owner ou admin, consommée lors de l'inscription.
    """

    __tablename__ = "invitations"

    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    invited_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_consumed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Rôle et projet optionnels pré-assignés
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    project_role: Mapped[str | None] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<Invitation {self.email} consumed={self.is_consumed}>"

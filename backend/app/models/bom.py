"""
ARBOR - Modèles BOM, Component et BOMComponent (table de liaison).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import BOMFormat, BOMType, ComponentType


class BOM(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Bill of Materials déposé pour un projet.
    Chaque dépôt crée une version indépendante et immuable.
    L'historique complet est conservé (purge manuelle possible, garder les 3 dernières).
    """

    __tablename__ = "boms"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_label: Mapped[str] = mapped_column(String(100), nullable=False)
    format: Mapped[BOMFormat] = mapped_column(
        Enum(BOMFormat, name="bom_format"),
        nullable=False,
    )
    type: Mapped[BOMType] = mapped_column(
        Enum(BOMType, name="bom_type"),
        default=BOMType.SBOM,
        nullable=False,
    )

    # Stockage du fichier original (chemin filesystem)
    raw_file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Parsing
    parsed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    component_count: Mapped[int] = mapped_column(default=0, nullable=False)

    # Auteur du dépôt
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Métadonnées extraites du BOM (JSONB)
    # Exemple : {"tool": "syft", "timestamp": "...", "serial_number": "..."}
    bom_metadata: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )

    # --- Relations ---
    project = relationship("Project", back_populates="boms")
    created_by_user = relationship("User", back_populates="created_boms")
    bom_components = relationship(
        "BOMComponent", back_populates="bom", lazy="select", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<BOM {self.version_label} ({self.format.value})>"


class Component(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Composant logiciel dédupliqué.
    Un composant apparaissant dans 10 projets n'existe qu'une fois dans cette table.
    La déduplication se fait sur le PURL (Package URL).
    """

    __tablename__ = "components"

    purl: Mapped[str] = mapped_column(
        String(1024), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[ComponentType] = mapped_column(
        Enum(ComponentType, name="component_type"),
        default=ComponentType.LIBRARY,
        nullable=False,
    )
    cpe: Mapped[str | None] = mapped_column(String(1024), nullable=True, index=True)
    supplier: Mapped[str | None] = mapped_column(String(512), nullable=True)
    license: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # --- Relations ---
    bom_components = relationship("BOMComponent", back_populates="component", lazy="select")
    alerts = relationship("Alert", back_populates="component", lazy="select")

    def __repr__(self) -> str:
        return f"<Component {self.name}@{self.version}>"


class BOMComponent(Base, TimestampMixin):
    """
    Table de liaison entre BOM et Component.
    Permet de savoir quels composants sont présents dans quelle BOM.
    """

    __tablename__ = "bom_components"
    __table_args__ = (
        UniqueConstraint("bom_id", "component_id", name="uq_bom_component"),
    )

    # Clé primaire composite
    bom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("boms.id", ondelete="CASCADE"),
        primary_key=True,
    )
    component_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("components.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # --- Relations ---
    bom = relationship("BOM", back_populates="bom_components")
    component = relationship("Component", back_populates="bom_components")

    def __repr__(self) -> str:
        return f"<BOMComponent bom={self.bom_id} component={self.component_id}>"

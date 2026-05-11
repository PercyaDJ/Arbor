"""
ARBOR - Modèle VEXStatement.
Structure posée en v0.1, workflow complet en v0.2.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import VEXJustification, VEXStatus


class VEXStatement(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Statement VEX : décision d'arbitrage humaine pour une alerte.
    Immuable en écriture : toute modification crée une nouvelle révision.
    """

    __tablename__ = "vex_statements"

    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    vulnerability_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vulnerabilities.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[VEXStatus] = mapped_column(
        Enum(VEXStatus, name="vex_status"), nullable=False,
    )
    justification: Mapped[VEXJustification | None] = mapped_column(
        Enum(VEXJustification, name="vex_justification"), nullable=True,
    )
    justification_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact_statement: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit trail
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    closed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Révision (pour l'immuabilité)
    revision: Mapped[int] = mapped_column(default=1, nullable=False)
    previous_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vex_statements.id", ondelete="SET NULL"), nullable=True,
    )

    alert = relationship("Alert", back_populates="vex_statements")
    project = relationship("Project", back_populates="vex_statements")

    def __repr__(self) -> str:
        return f"<VEXStatement {self.status.value} rev={self.revision}>"

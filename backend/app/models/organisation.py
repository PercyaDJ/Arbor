"""
ARBOR - Modèle Organisation.
En v0.1 MVP, une seule organisation est créée à l'initialisation (mono-org).
"""

from sqlalchemy import Enum, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import OrgPlan


class Organisation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Conteneur de plus haut niveau.
    Regroupe des projets et des utilisateurs.
    En mode self-hosted mono-instance, correspond à l'entité qui déploie ARBOR.
    """

    __tablename__ = "organisations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    plan: Mapped[OrgPlan] = mapped_column(
        Enum(OrgPlan, name="org_plan"),
        default=OrgPlan.FREE,
        nullable=False,
    )

    # Settings JSONB : seuil CVSS par défaut, sources CERT actives, mode online/offline
    settings: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )

    # --- Relations ---
    users = relationship("User", back_populates="organisation", lazy="select")
    projects = relationship("Project", back_populates="organisation", lazy="select")

    def __repr__(self) -> str:
        return f"<Organisation {self.slug} ({self.plan.value})>"

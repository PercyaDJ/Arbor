"""
ARBOR - Service de gestion des BOM.
Dépôt, parsing, stockage, historique et purge.
"""

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.bom import BOM, BOMComponent, Component
from app.models.enums import AuditAction, BOMFormat, BOMType, ComponentType
from app.models.user import User
from app.parsers.cyclonedx_parser import parse_cyclonedx_json, parse_cyclonedx_xml
from app.parsers.spdx_parser import parse_spdx_json, parse_spdx_xml
from app.services.audit_service import log_action


class BOMError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def detect_bom_format(filename: str, content: bytes) -> BOMFormat:
    """Détecte le format d'un fichier BOM (CycloneDX ou SPDX, JSON ou XML)."""
    fname = filename.lower()
    content_start = content[:500].decode("utf-8", errors="ignore").lower()

    # Détection par contenu
    if "cyclonedx" in content_start or '"bomformat"' in content_start:
        if content.strip().startswith(b"{"):
            return BOMFormat.CYCLONEDX_JSON
        return BOMFormat.CYCLONEDX_XML

    if "spdxversion" in content_start or "spdx" in content_start:
        if content.strip().startswith(b"{"):
            return BOMFormat.SPDX_JSON
        return BOMFormat.SPDX_XML

    # Fallback par extension
    if fname.endswith(".json"):
        if "cdx" in fname or "cyclone" in fname:
            return BOMFormat.CYCLONEDX_JSON
        return BOMFormat.SPDX_JSON
    if fname.endswith(".xml"):
        if "cdx" in fname or "cyclone" in fname:
            return BOMFormat.CYCLONEDX_XML
        return BOMFormat.SPDX_XML

    raise BOMError("Format de fichier BOM non reconnu. Formats supportés : CycloneDX, SPDX (JSON/XML)")


def deposit_bom(
    db: Session,
    *,
    project_id: uuid.UUID,
    filename: str,
    content: bytes,
    version_label: str | None = None,
    user_id: uuid.UUID | None = None,
    ip_address: str | None = None,
) -> dict:
    """
    Dépose une BOM pour un projet.
    Parse le fichier, déduplique les composants, crée les alertes.
    Retourne un résumé du dépôt.
    """
    settings = get_settings()

    # Détection du format
    bom_format = detect_bom_format(filename, content)

    # Hash SHA256
    sha256 = hashlib.sha256(content).hexdigest()

    # Générer le label de version si absent
    if not version_label:
        existing_count = (
            db.query(func.count(BOM.id))
            .filter(BOM.project_id == project_id)
            .scalar() or 0
        )
        version_label = f"v{existing_count + 1}"

    # Stocker le fichier brut
    storage_path = Path(settings.bom_storage_path)
    project_dir = storage_path / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)

    bom_id = uuid.uuid4()
    file_ext = "json" if "json" in bom_format.value else "xml"
    file_path = project_dir / f"{bom_id}.{file_ext}"
    file_path.write_bytes(content)

    # Parser le BOM
    parse_result = _parse_bom(bom_format, content)
    parsed_components = parse_result["components"]
    bom_metadata = parse_result["metadata"]

    # Créer l'entrée BOM en base
    bom = BOM(
        id=bom_id,
        project_id=project_id,
        version_label=version_label,
        format=bom_format,
        type=BOMType.SBOM,
        raw_file_path=str(file_path),
        sha256_hash=sha256,
        parsed_at=datetime.now(timezone.utc),
        component_count=len(parsed_components),
        created_by=user_id,
        bom_metadata=bom_metadata,
    )
    db.add(bom)
    db.flush()

    # Dédupliquer et insérer les composants
    components_added = 0
    components_existing = 0

    for comp_data in parsed_components:
        component = db.query(Component).filter(Component.purl == comp_data["purl"]).first()

        if component is None:
            component = Component(
                purl=comp_data["purl"],
                name=comp_data["name"],
                version=comp_data["version"],
                type=comp_data["type"] if isinstance(comp_data["type"], ComponentType) else ComponentType.LIBRARY,
                cpe=comp_data.get("cpe"),
                supplier=comp_data.get("supplier"),
                license=comp_data.get("license"),
            )
            db.add(component)
            db.flush()
            components_added += 1
        else:
            components_existing += 1

        # Liaison BOM ↔ Component
        link = BOMComponent(bom_id=bom.id, component_id=component.id)
        db.add(link)

    # Audit log
    log_action(
        db,
        action=AuditAction.BOM_DEPOSITED,
        entity_type="bom",
        entity_id=str(bom.id),
        user_id=user_id,
        ip_address=ip_address,
        details={
            "project_id": str(project_id),
            "format": bom_format.value,
            "component_count": len(parsed_components),
            "version_label": version_label,
        },
    )

    db.commit()
    db.refresh(bom)

    return {
        "bom": bom,
        "components_added": components_added,
        "components_existing": components_existing,
        "alerts_generated": 0,  # Le matching sera déclenché en Phase 5
    }


def get_bom_history(db: Session, project_id: uuid.UUID) -> list[BOM]:
    """Retourne l'historique des BOM d'un projet, de la plus récente à la plus ancienne."""
    return (
        db.query(BOM)
        .filter(BOM.project_id == project_id)
        .order_by(BOM.created_at.desc())
        .all()
    )


def get_bom_detail(db: Session, bom_id: uuid.UUID) -> BOM:
    """Retourne le détail d'une BOM."""
    bom = db.query(BOM).filter(BOM.id == bom_id).first()
    if bom is None:
        raise BOMError("BOM non trouvée", 404)
    return bom


def get_bom_components(db: Session, bom_id: uuid.UUID) -> list[Component]:
    """Retourne les composants d'une BOM."""
    return (
        db.query(Component)
        .join(BOMComponent, BOMComponent.component_id == Component.id)
        .filter(BOMComponent.bom_id == bom_id)
        .all()
    )


def purge_bom_history(
    db: Session,
    *,
    project_id: uuid.UUID,
    keep_last: int = 3,
    user: User,
    ip_address: str | None = None,
) -> int:
    """
    Purge les anciennes BOM d'un projet, en gardant les N dernières.
    Retourne le nombre de BOM supprimées.
    """
    all_boms = (
        db.query(BOM)
        .filter(BOM.project_id == project_id)
        .order_by(BOM.created_at.desc())
        .all()
    )

    if len(all_boms) <= keep_last:
        return 0

    boms_to_delete = all_boms[keep_last:]
    deleted_count = 0

    for bom in boms_to_delete:
        # Supprimer le fichier physique
        try:
            Path(bom.raw_file_path).unlink(missing_ok=True)
        except OSError:
            pass

        db.delete(bom)
        deleted_count += 1

    log_action(
        db,
        action=AuditAction.BOM_PURGED,
        entity_type="project",
        entity_id=str(project_id),
        user_id=user.id,
        ip_address=ip_address,
        details={"deleted_count": deleted_count, "kept": keep_last},
    )

    db.commit()
    return deleted_count


def _parse_bom(bom_format: BOMFormat, content: bytes) -> dict:
    """Dispatch le parsing vers le bon parser selon le format."""
    parsers = {
        BOMFormat.CYCLONEDX_JSON: parse_cyclonedx_json,
        BOMFormat.CYCLONEDX_XML: parse_cyclonedx_xml,
        BOMFormat.SPDX_JSON: parse_spdx_json,
        BOMFormat.SPDX_XML: parse_spdx_xml,
    }
    parser = parsers.get(bom_format)
    if parser is None:
        raise BOMError(f"Parser non disponible pour le format {bom_format.value}")
    return parser(content)

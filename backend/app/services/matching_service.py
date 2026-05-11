"""
ARBOR - Service de matching vulnérabilités ↔ composants.
Matching par PURL avec support des version ranges.
"""

import re
import uuid
from datetime import datetime, timezone

from packaging.version import Version, InvalidVersion
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.bom import BOM, BOMComponent, Component
from app.models.enums import AlertStatus, Severity
from app.models.project import Project
from app.models.vulnerability import Vulnerability


def match_vulnerability_against_components(
    db: Session, vulnerability: Vulnerability
) -> list[Alert]:
    """
    Pour une vulnérabilité donnée, trouve tous les composants affectés
    dans les projets actifs et crée les alertes correspondantes.
    """
    new_alerts = []

    # Matching par PURL (affected_purls)
    for affected in vulnerability.affected_purls or []:
        purl_pattern = affected.get("purl_pattern", "")
        if not purl_pattern:
            continue

        # Extraire le nom du package du PURL (sans la version)
        base_purl = _strip_version_from_purl(purl_pattern)

        # Trouver les composants dont le PURL correspond
        matching_components = (
            db.query(Component)
            .filter(Component.purl.like(f"{base_purl}@%"))
            .all()
        )

        for component in matching_components:
            if _is_version_affected(component.version, affected):
                alerts = _create_alerts_for_component(db, vulnerability, component)
                new_alerts.extend(alerts)

    # Matching par CPE (affected_cpes)
    for affected in vulnerability.affected_cpes or []:
        cpe = affected.get("cpe", "")
        if not cpe:
            continue

        # Chercher les composants avec un CPE correspondant
        matching = db.query(Component).filter(Component.cpe.isnot(None))

        # Matching basique sur le préfixe CPE (vendor:product)
        cpe_prefix = _extract_cpe_prefix(cpe)
        if cpe_prefix:
            matching = matching.filter(Component.cpe.like(f"%{cpe_prefix}%"))

        for component in matching.all():
            if _is_cpe_version_affected(component, affected):
                alerts = _create_alerts_for_component(db, vulnerability, component)
                new_alerts.extend(alerts)

    return new_alerts


def match_bom_against_vulnerabilities(
    db: Session, bom: BOM
) -> list[Alert]:
    """
    Pour une BOM nouvellement déposée, matche ses composants
    contre les vulnérabilités existantes en base.
    """
    new_alerts = []

    # Récupérer les composants de cette BOM
    components = (
        db.query(Component)
        .join(BOMComponent, BOMComponent.component_id == Component.id)
        .filter(BOMComponent.bom_id == bom.id)
        .all()
    )

    # Pour chaque composant, chercher les vulnérabilités qui le concernent
    for component in components:
        vulnerabilities = _find_vulnerabilities_for_component(db, component)
        for vuln in vulnerabilities:
            alert = _create_alert_if_not_exists(
                db,
                project_id=bom.project_id,
                vulnerability=vuln,
                component=component,
                bom_version_id=bom.id,
            )
            if alert:
                new_alerts.append(alert)

    return new_alerts


def _find_vulnerabilities_for_component(
    db: Session, component: Component
) -> list[Vulnerability]:
    """Trouve les vulnérabilités affectant un composant donné."""
    base_purl = _strip_version_from_purl(component.purl)

    # Recherche dans affected_purls (JSONB) avec LIKE
    # On cherche les vulnérabilités dont affected_purls contient le pattern PURL
    vulns = (
        db.query(Vulnerability)
        .filter(
            Vulnerability.affected_purls.cast(db.bind.dialect.type_descriptor(type(None)))
            .isnot(None)
            if False
            else Vulnerability.affected_purls != []
        )
        .all()
    )

    matching = []
    for vuln in vulns:
        for affected in vuln.affected_purls or []:
            pattern = affected.get("purl_pattern", "")
            if not pattern:
                continue
            vuln_base = _strip_version_from_purl(pattern)
            if vuln_base == base_purl and _is_version_affected(component.version, affected):
                matching.append(vuln)
                break

    return matching


def _create_alerts_for_component(
    db: Session, vulnerability: Vulnerability, component: Component
) -> list[Alert]:
    """Crée des alertes pour un composant affecté dans tous les projets actifs."""
    alerts = []

    # Trouver les projets actifs contenant ce composant (via la dernière BOM)
    project_boms = (
        db.query(BOM.project_id, func.max(BOM.id).label("latest_bom_id"))
        .join(BOMComponent, BOMComponent.bom_id == BOM.id)
        .filter(BOMComponent.component_id == component.id)
        .join(Project, Project.id == BOM.project_id)
        .filter(Project.archived_at.is_(None))
        .group_by(BOM.project_id)
        .all()
    )

    for project_id, latest_bom_id in project_boms:
        alert = _create_alert_if_not_exists(
            db,
            project_id=project_id,
            vulnerability=vulnerability,
            component=component,
            bom_version_id=latest_bom_id,
        )
        if alert:
            alerts.append(alert)

    return alerts


def _create_alert_if_not_exists(
    db: Session,
    *,
    project_id: uuid.UUID,
    vulnerability: Vulnerability,
    component: Component,
    bom_version_id: uuid.UUID | None = None,
) -> Alert | None:
    """Crée une alerte si elle n'existe pas déjà pour ce triplet."""
    existing = (
        db.query(Alert)
        .filter(
            Alert.project_id == project_id,
            Alert.vulnerability_id == vulnerability.id,
            Alert.component_id == component.id,
        )
        .first()
    )

    if existing is not None:
        return None

    alert = Alert(
        project_id=project_id,
        vulnerability_id=vulnerability.id,
        component_id=component.id,
        bom_version_id=bom_version_id,
        status=AlertStatus.NEW,
    )
    db.add(alert)
    db.flush()
    return alert


# --- Utilitaires de version ---

def _strip_version_from_purl(purl: str) -> str:
    """Retire la version d'un PURL (pkg:npm/lodash@4.17.20 → pkg:npm/lodash)."""
    at_idx = purl.rfind("@")
    if at_idx > 0 and "/" in purl[:at_idx]:
        return purl[:at_idx]
    return purl


def _is_version_affected(component_version: str, affected: dict) -> bool:
    """
    Vérifie si une version de composant est dans le range affecté.
    Support : version_start, version_end, version_exact, vulnerable_range.
    """
    # Version exacte
    if "version_exact" in affected:
        return component_version == affected["version_exact"]

    # Range avec opérateur textuel (ex: "< 4.17.21")
    vuln_range = affected.get("vulnerable_range")
    if vuln_range:
        return _check_semver_range(component_version, vuln_range)

    # Range avec bornes start/end
    version_start = affected.get("version_start")
    version_end = affected.get("version_end")

    if not version_start and not version_end:
        return True  # Pas de range = toutes les versions affectées

    try:
        comp_ver = _parse_version(component_version)
    except InvalidVersion:
        return False  # Version non parsable, on ne matche pas

    if version_start:
        try:
            start_ver = _parse_version(version_start)
            start_type = affected.get("version_start_type", "including")
            if start_type == "including" and comp_ver < start_ver:
                return False
            if start_type == "excluding" and comp_ver <= start_ver:
                return False
        except InvalidVersion:
            pass

    if version_end:
        try:
            end_ver = _parse_version(version_end)
            end_type = affected.get("version_end_type", "excluding")
            if end_type == "excluding" and comp_ver >= end_ver:
                return False
            if end_type == "including" and comp_ver > end_ver:
                return False
        except InvalidVersion:
            pass

    return True


def _check_semver_range(version: str, range_spec: str) -> bool:
    """Vérifie un range textuel simple (ex: '< 4.17.21', '>= 1.0.0, < 2.0.0')."""
    try:
        comp_ver = _parse_version(version)
    except InvalidVersion:
        return False

    # Séparer les contraintes (ex: ">= 1.0, < 2.0")
    constraints = [c.strip() for c in range_spec.split(",")]

    for constraint in constraints:
        match = re.match(r"^([<>=!]+)\s*(.+)$", constraint)
        if not match:
            continue

        op, ver_str = match.groups()
        try:
            target = _parse_version(ver_str.strip())
        except InvalidVersion:
            continue

        if op == "<" and not (comp_ver < target):
            return False
        elif op == "<=" and not (comp_ver <= target):
            return False
        elif op == ">" and not (comp_ver > target):
            return False
        elif op == ">=" and not (comp_ver >= target):
            return False
        elif op == "==" and not (comp_ver == target):
            return False
        elif op == "!=" and not (comp_ver != target):
            return False

    return True


def _parse_version(version_str: str) -> Version:
    """Parse une version avec le module packaging, avec fallback."""
    # Nettoyer les préfixes courants
    cleaned = version_str.lstrip("v").strip()
    return Version(cleaned)


def _extract_cpe_prefix(cpe: str) -> str | None:
    """Extrait le vendor:product d'un CPE 2.3."""
    # Format : cpe:2.3:a:vendor:product:version:...
    parts = cpe.split(":")
    if len(parts) >= 5:
        return f"{parts[3]}:{parts[4]}"
    return None


def _is_cpe_version_affected(component: Component, affected: dict) -> bool:
    """Vérifie si un composant est affecté via son CPE et les version ranges."""
    if not component.cpe:
        return False
    # Réutiliser la logique de version range
    return _is_version_affected(component.version, affected)

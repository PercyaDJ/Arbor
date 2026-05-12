"""
ARBOR - Énumérations partagées pour les modèles.
Définies en Python (str, Enum) pour être utilisées à la fois
dans SQLAlchemy et Pydantic.
"""

import enum


# --- Organisation ---
class OrgPlan(str, enum.Enum):
    """Plan de l'organisation."""
    FREE = "free"
    COMMERCIAL = "commercial"


# --- Rôles projet ---
class ProjectRole(str, enum.Enum):
    """Rôle d'un membre dans un projet."""
    OWNER = "owner"
    MEMBER = "member"
    READER = "reader"


# --- Format BOM ---
class BOMFormat(str, enum.Enum):
    """Format du fichier BOM déposé."""
    CYCLONEDX_JSON = "cyclonedx_json"
    CYCLONEDX_XML = "cyclonedx_xml"
    SPDX_JSON = "spdx_json"
    SPDX_XML = "spdx_xml"
    CSV = "csv"


# --- Type BOM ---
class BOMType(str, enum.Enum):
    """Type de Bill of Materials."""
    SBOM = "sbom"
    CBOM_CLOUD = "cbom_cloud"
    CBOM_CRYPTO = "cbom_crypto"
    MIXED = "mixed"


# --- Type de composant ---
class ComponentType(str, enum.Enum):
    """Type de composant logiciel."""
    LIBRARY = "library"
    FRAMEWORK = "framework"
    CONTAINER = "container"
    DEVICE = "device"
    FIRMWARE = "firmware"
    SERVICE = "service"
    CLOUD_SERVICE = "cloud_service"
    CRYPTO_ALGORITHM = "crypto_algorithm"
    APPLICATION = "application"
    OS = "os"
    OTHER = "other"


# --- Source de vulnérabilité ---
class VulnSource(str, enum.Enum):
    """Source d'alimentation des vulnérabilités."""
    NVD = "nvd"
    OSV = "osv"
    CERT_FR = "cert_fr"
    CERT_IST = "cert_ist"
    CISA_KEV = "cisa_kev"
    ENISA = "enisa"
    GITHUB_ADVISORY = "github_advisory"


# --- Sévérité ---
class Severity(str, enum.Enum):
    """Niveau de sévérité d'une vulnérabilité."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# --- Statut d'alerte ---
class AlertStatus(str, enum.Enum):
    """Statut de traitement d'une alerte."""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    NOT_APPLICABLE = "not_applicable"


# --- Statut VEX ---
class VEXStatus(str, enum.Enum):
    """Statut d'un statement VEX (NTIA-compatible)."""
    AFFECTED = "affected"
    NOT_AFFECTED = "not_affected"
    FIXED = "fixed"
    UNDER_INVESTIGATION = "under_investigation"


# --- Justification VEX ---
class VEXJustification(str, enum.Enum):
    """Justification structurée d'un statement VEX (enum NTIA-compatible)."""
    COMPONENT_NOT_PRESENT = "component_not_present"
    VULNERABLE_CODE_NOT_PRESENT = "vulnerable_code_not_present"
    VULNERABLE_CODE_NOT_IN_EXECUTE_PATH = "vulnerable_code_not_in_execute_path"
    VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY = "vulnerable_code_cannot_be_controlled_by_adversary"
    INLINE_MITIGATIONS_ALREADY_EXIST = "inline_mitigations_already_exist"
    OTHER = "other"


# --- Actions d'audit ---
class AuditAction(str, enum.Enum):
    """Types d'actions traçées dans le log d'audit."""
    USER_LOGIN = "user_login"
    USER_INVITED = "user_invited"
    PROJECT_CREATED = "project_created"
    PROJECT_ARCHIVED = "project_archived"
    BOM_DEPOSITED = "bom_deposited"
    BOM_PURGED = "bom_purged"
    ALERT_CREATED = "alert_created"
    ALERT_STATUS_CHANGED = "alert_status_changed"
    VEX_CREATED = "vex_created"
    VEX_UPDATED = "vex_updated"
    VEX_CLOSED = "vex_closed"
    MEMBER_ADDED = "member_added"
    MEMBER_REMOVED = "member_removed"
    MEMBER_ROLE_CHANGED = "member_role_changed"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    SETTINGS_CHANGED = "settings_changed"

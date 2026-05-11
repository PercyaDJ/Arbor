"""
ARBOR - Configuration centralisée.
Toutes les variables d'environnement sont lues ici via Pydantic Settings.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration principale d'ARBOR, alimentée par les variables d'environnement."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="ARBOR_",
        case_sensitive=False,
    )

    # --- Application ---
    app_name: str = "ARBOR"
    app_version: str = "0.1.0"
    debug: bool = False
    secret_key: str = "CHANGE-ME-IN-PRODUCTION"
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # --- Base de données ---
    database_url: str = "postgresql://arbor:arbor@localhost:5432/arbor"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- JWT ---
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # --- Stockage BOM ---
    bom_storage_path: Path = Path("/data/bom_storage")

    # --- SMTP (Notifications email) ---
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "arbor@localhost"
    smtp_tls: bool = True

    # --- Feeds de vulnérabilités ---
    online_mode: bool = True
    nvd_api_key: str = ""  # Optionnel, améliore le rate limit
    nvd_sync_interval_hours: int = 1
    osv_sync_interval_hours: int = 6

    # --- Organisation (mono-org MVP) ---
    default_org_name: str = "Organisation par défaut"
    default_cvss_threshold: float = 0.0  # 0 = toutes les alertes

    # --- Admin initial ---
    admin_email: str = "admin@arbor.local"
    admin_password: str = "CHANGE-ME"

    # --- Rate limiting ---
    rate_limit_per_minute: int = 60


@lru_cache
def get_settings() -> Settings:
    """Retourne l'instance de configuration (singleton via cache)."""
    return Settings()

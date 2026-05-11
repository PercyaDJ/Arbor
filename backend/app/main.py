"""
ARBOR - Point d'entrée de l'application FastAPI.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

settings = get_settings()


def create_app() -> FastAPI:
    """Factory de l'application FastAPI."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "ARBOR — Registre centralisé de SBOM/CBOM connecté aux sources de vulnérabilités. "
            "API REST pour la gestion des projets, le dépôt de BOM et le suivi des alertes."
        ),
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routes ---
    # Les routeurs seront ajoutés ici au fur et à mesure des phases
    # from app.api.v1 import auth, projects, bom, alerts
    # app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentification"])
    # app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projets"])

    @app.get("/api/health", tags=["Système"])
    def health_check():
        """Vérification de santé de l'API."""
        return {
            "status": "ok",
            "app": settings.app_name,
            "version": settings.app_version,
        }

    return app


app = create_app()

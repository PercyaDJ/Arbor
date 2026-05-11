"""
ARBOR - Point d'entrée de l'application FastAPI.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Événements de cycle de vie de l'application.
    - Au démarrage : initialise l'org par défaut + admin.
    - À l'arrêt : nettoyage si nécessaire.
    """
    # --- Startup ---
    from app.core.database import get_session_factory
    from app.services.auth_service import init_default_org_and_admin

    session_factory = get_session_factory()
    db = session_factory()
    try:
        org, admin = init_default_org_and_admin(db)
        print(f"[ARBOR] Organisation : {org.name} (slug: {org.slug})")
        print(f"[ARBOR] Admin : {admin.email}")
    except Exception as e:
        print(f"[ARBOR] Erreur à l'initialisation : {e}")
    finally:
        db.close()

    yield  # L'application tourne

    # --- Shutdown ---
    print("[ARBOR] Arrêt de l'application.")


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
        lifespan=lifespan,
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Middleware : headers de sécurité HTTP ---
    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # --- Routes ---
    from app.api.v1 import auth, projects, bom, alerts

    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentification"])
    app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projets"])
    app.include_router(bom.router, prefix="/api/v1/projects", tags=["BOM"])
    app.include_router(alerts.router, prefix="/api/v1/projects", tags=["Alertes"])

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

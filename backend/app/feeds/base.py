"""
ARBOR - Classe abstraite FeedConnector.
Interface commune pour tous les connecteurs de feeds de vulnérabilités.
"""

from abc import ABC, abstractmethod


class FeedConnector(ABC):
    """
    Interface commune pour les connecteurs de feeds.
    Chaque source de vulnérabilités (NVD, OSV, CERT-FR, etc.)
    implémente cette interface.
    """

    @abstractmethod
    def fetch(self, since: str | None = None) -> list[dict]:
        """
        Récupère les vulnérabilités depuis la source.
        `since` : date ISO pour ne récupérer que les deltas.
        Retourne une liste de dicts bruts spécifiques à la source.
        """
        ...

    @abstractmethod
    def normalize(self, raw_items: list[dict]) -> list[dict]:
        """
        Normalise les données brutes vers le format ARBOR standard.
        Retourne une liste de dicts compatibles avec le modèle Vulnerability :
        {
            "cve_id": str,
            "source": VulnSource,
            "title": str,
            "description": str,
            "cvss_v3_score": float | None,
            "cvss_v3_vector": str | None,
            "cvss_v2_score": float | None,
            "severity": Severity,
            "published_at": datetime | None,
            "modified_at": datetime | None,
            "references": list[dict],
            "affected_cpes": list[dict],
            "affected_purls": list[dict],
        }
        """
        ...

    def sync(self, since: str | None = None) -> list[dict]:
        """Fetch + normalize en une opération."""
        raw = self.fetch(since=since)
        return self.normalize(raw)

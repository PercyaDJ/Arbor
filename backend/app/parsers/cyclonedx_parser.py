"""
ARBOR - Parser CycloneDX (JSON et XML).
Extrait les composants d'un fichier BOM au format CycloneDX.
"""

import json
from xml.etree import ElementTree as ET

from app.models.enums import ComponentType

# Namespace CycloneDX XML
CDX_NS = "http://cyclonedx.org/schema/bom/1.6"
CDX_NS_FALLBACKS = [
    "http://cyclonedx.org/schema/bom/1.5",
    "http://cyclonedx.org/schema/bom/1.4",
    "http://cyclonedx.org/schema/bom/1.3",
]


def _map_component_type(cdx_type: str | None) -> ComponentType:
    """Mappe un type CycloneDX vers le type ARBOR."""
    mapping = {
        "library": ComponentType.LIBRARY,
        "framework": ComponentType.FRAMEWORK,
        "application": ComponentType.APPLICATION,
        "container": ComponentType.CONTAINER,
        "device": ComponentType.DEVICE,
        "firmware": ComponentType.FIRMWARE,
        "operating-system": ComponentType.OS,
        "service": ComponentType.SERVICE,
    }
    return mapping.get(cdx_type or "", ComponentType.LIBRARY)


def parse_cyclonedx_json(content: bytes) -> dict:
    """
    Parse un fichier CycloneDX JSON.
    Retourne : {"metadata": {...}, "components": [{purl, name, version, type, cpe, ...}]}
    """
    data = json.loads(content)

    # Extraire les métadonnées
    meta_raw = data.get("metadata", {})
    metadata = {
        "tool": _extract_tool_name(meta_raw),
        "timestamp": meta_raw.get("timestamp"),
        "serial_number": data.get("serialNumber"),
        "spec_version": data.get("specVersion"),
    }

    # Extraire les composants
    components = []
    for comp in data.get("components", []):
        parsed = _parse_cdx_component(comp)
        if parsed:
            components.append(parsed)

    return {"metadata": metadata, "components": components}


def parse_cyclonedx_xml(content: bytes) -> dict:
    """
    Parse un fichier CycloneDX XML.
    Retourne : {"metadata": {...}, "components": [{purl, name, version, type, cpe, ...}]}
    """
    root = ET.fromstring(content)

    # Détecter le namespace
    ns = ""
    for candidate in [CDX_NS] + CDX_NS_FALLBACKS:
        if root.tag.startswith(f"{{{candidate}}}"):
            ns = f"{{{candidate}}}"
            break

    # Métadonnées
    meta_el = root.find(f"{ns}metadata")
    metadata = {}
    if meta_el is not None:
        tool_el = meta_el.find(f"{ns}tools/{ns}tool/{ns}name")
        ts_el = meta_el.find(f"{ns}timestamp")
        metadata = {
            "tool": tool_el.text if tool_el is not None else None,
            "timestamp": ts_el.text if ts_el is not None else None,
            "serial_number": root.get("serialNumber"),
            "spec_version": root.get("version"),
        }

    # Composants
    components = []
    for comp_el in root.findall(f".//{ns}component"):
        parsed = _parse_cdx_xml_component(comp_el, ns)
        if parsed:
            components.append(parsed)

    return {"metadata": metadata, "components": components}


def _parse_cdx_component(comp: dict) -> dict | None:
    """Parse un composant CycloneDX JSON."""
    name = comp.get("name")
    version = comp.get("version", "unknown")
    if not name:
        return None

    purl = comp.get("purl")
    if not purl:
        # Générer un pseudo-PURL si absent
        purl = f"pkg:generic/{name}@{version}"

    return {
        "purl": purl,
        "name": name,
        "version": version,
        "type": _map_component_type(comp.get("type")),
        "cpe": comp.get("cpe"),
        "supplier": _extract_supplier(comp),
        "license": _extract_license(comp),
    }


def _parse_cdx_xml_component(el: ET.Element, ns: str) -> dict | None:
    """Parse un composant CycloneDX XML."""
    name_el = el.find(f"{ns}name")
    version_el = el.find(f"{ns}version")
    purl_el = el.find(f"{ns}purl")
    cpe_el = el.find(f"{ns}cpe")

    name = name_el.text if name_el is not None else None
    if not name:
        return None

    version = version_el.text if version_el is not None else "unknown"
    purl = purl_el.text if purl_el is not None else f"pkg:generic/{name}@{version}"

    return {
        "purl": purl,
        "name": name,
        "version": version,
        "type": _map_component_type(el.get("type")),
        "cpe": cpe_el.text if cpe_el is not None else None,
        "supplier": None,
        "license": None,
    }


def _extract_tool_name(meta: dict) -> str | None:
    """Extrait le nom de l'outil depuis les métadonnées CycloneDX."""
    tools = meta.get("tools")
    if isinstance(tools, list) and tools:
        return tools[0].get("name")
    if isinstance(tools, dict):
        components = tools.get("components", [])
        if components:
            return components[0].get("name")
    return None


def _extract_supplier(comp: dict) -> str | None:
    """Extrait le fournisseur d'un composant."""
    supplier = comp.get("supplier")
    if isinstance(supplier, dict):
        return supplier.get("name")
    return None


def _extract_license(comp: dict) -> str | None:
    """Extrait la licence d'un composant."""
    licenses = comp.get("licenses", [])
    if licenses:
        lic = licenses[0]
        if isinstance(lic, dict):
            license_obj = lic.get("license", {})
            return license_obj.get("id") or license_obj.get("name")
    return None

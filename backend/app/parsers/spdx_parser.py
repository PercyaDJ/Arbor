"""
ARBOR - Parser SPDX (JSON et XML).
Extrait les composants d'un fichier BOM au format SPDX.
"""

import json
from xml.etree import ElementTree as ET

from app.models.enums import ComponentType

# Namespace SPDX XML (RDF)
SPDX_NS = "http://spdx.org/rdf/terms#"


def parse_spdx_json(content: bytes) -> dict:
    """
    Parse un fichier SPDX JSON.
    Retourne : {"metadata": {...}, "components": [{purl, name, version, type, ...}]}
    """
    data = json.loads(content)

    # Métadonnées
    creation_info = data.get("creationInfo", {})
    metadata = {
        "tool": _extract_spdx_tool(creation_info),
        "timestamp": creation_info.get("created"),
        "serial_number": data.get("SPDXID"),
        "spec_version": data.get("spdxVersion"),
    }

    # Packages → composants
    components = []
    for pkg in data.get("packages", []):
        parsed = _parse_spdx_package(pkg)
        if parsed:
            components.append(parsed)

    return {"metadata": metadata, "components": components}


def parse_spdx_xml(content: bytes) -> dict:
    """
    Parse un fichier SPDX XML (tag-value format encapsulé en XML).
    Support basique — le format principal de SPDX est le JSON.
    """
    root = ET.fromstring(content)

    # Détecter le namespace
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    metadata = {
        "tool": None,
        "timestamp": None,
        "serial_number": None,
        "spec_version": None,
    }

    components = []
    for pkg_el in root.findall(f".//{ns}Package") + root.findall(".//Package"):
        parsed = _parse_spdx_xml_package(pkg_el, ns)
        if parsed:
            components.append(parsed)

    return {"metadata": metadata, "components": components}


def _parse_spdx_package(pkg: dict) -> dict | None:
    """Parse un package SPDX JSON vers un composant ARBOR."""
    name = pkg.get("name")
    if not name:
        return None

    # Ignorer le package racine du document
    spdx_id = pkg.get("SPDXID", "")
    if spdx_id == "SPDXRef-DOCUMENT":
        return None

    version = pkg.get("versionInfo", "unknown")

    # Chercher le PURL dans les external refs
    purl = None
    for ref in pkg.get("externalRefs", []):
        if ref.get("referenceType") == "purl":
            purl = ref.get("referenceLocator")
            break

    if not purl:
        purl = f"pkg:generic/{name}@{version}"

    # Licence
    license_info = pkg.get("licenseConcluded") or pkg.get("licenseDeclared")
    if license_info == "NOASSERTION":
        license_info = None

    return {
        "purl": purl,
        "name": name,
        "version": version,
        "type": ComponentType.LIBRARY,
        "cpe": None,
        "supplier": pkg.get("supplier"),
        "license": license_info,
    }


def _parse_spdx_xml_package(el: ET.Element, ns: str) -> dict | None:
    """Parse un package SPDX XML."""
    name_el = el.find(f"{ns}name") or el.find("name")
    if name_el is None or not name_el.text:
        return None

    version_el = el.find(f"{ns}versionInfo") or el.find("versionInfo")
    version = version_el.text if version_el is not None else "unknown"

    return {
        "purl": f"pkg:generic/{name_el.text}@{version}",
        "name": name_el.text,
        "version": version,
        "type": ComponentType.LIBRARY,
        "cpe": None,
        "supplier": None,
        "license": None,
    }


def _extract_spdx_tool(creation_info: dict) -> str | None:
    """Extrait le nom de l'outil depuis les métadonnées SPDX."""
    creators = creation_info.get("creators", [])
    for creator in creators:
        if isinstance(creator, str) and creator.startswith("Tool:"):
            return creator.replace("Tool:", "").strip()
    return None

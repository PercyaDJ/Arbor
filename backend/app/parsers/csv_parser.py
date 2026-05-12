import csv
from io import StringIO
from typing import Any, Dict

from app.models.enums import ComponentType

def parse_csv(content: bytes) -> Dict[str, Any]:
    text_content = content.decode("utf-8")
    reader = csv.DictReader(StringIO(text_content))
    
    if not reader.fieldnames or "name" not in reader.fieldnames or "version" not in reader.fieldnames:
        raise ValueError("Le fichier CSV doit au moins contenir les colonnes 'name' et 'version'.")

    components = []
    for row in reader:
        name = row.get("name", "").strip()
        version = row.get("version", "").strip()
        if not name or not version:
            continue
            
        type_str = row.get("type", "").strip()
        group = row.get("group", "").strip()
        purl = row.get("purl", "").strip()
        license_str = row.get("license", "").strip()
        
        # Determine component type
        try:
            comp_type = ComponentType(type_str.lower())
        except ValueError:
            comp_type = ComponentType.LIBRARY
            
        # Generate generic purl if missing
        if not purl:
            purl = f"pkg:generic/{group+'/' if group else ''}{name}@{version}"

        components.append({
            "purl": purl,
            "name": name,
            "version": version,
            "type": comp_type,
            "cpe": None,
            "supplier": None,
            "license": license_str if license_str else None,
            "group": group if group else None,
        })

    return {
        "metadata": {
            "format": "csv",
            "component_count": len(components),
        },
        "components": components,
    }

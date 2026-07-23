"""Human-readable developer reports built from structured project intelligence."""
from __future__ import annotations


def chaquopy_report(profile: dict) -> str:
    lines = [
        "Integración Android–Python con Chaquopy",
        "",
        f"• Plugin: {profile['plugin']}",
        f"• Python embebido: {profile['python_version']}",
        f"• ABI soportadas: {', '.join(profile['abis']) or 'no detectadas'}",
        f"• Entrada Android: {profile['android_entry']}",
        f"• Entrada Python: {profile['python_entry']}",
        f"• Flask local: {profile['flask_binding']}",
        "",
        "Flujo de arranque",
    ]
    lines.extend(f"  {index}. {step}" for index, step in enumerate(profile["startup_flow"], 1))
    lines.extend(["", "Puentes de datos"])
    lines.extend(f"  • {name}: {description}" for name, description in profile["data_bridge"].items())
    lines.extend(["", "Ventajas"])
    lines.extend(f"  ✓ {item}" for item in profile["advantages"])
    lines.extend(["", "Limitaciones"])
    lines.extend(f"  ! {item}" for item in profile["limitations"])
    lines.extend(["", "Dependencias Python", "  " + ", ".join(profile["pip_packages"])])
    return "\n".join(lines)


def diagrams_report(inventory: dict) -> str:
    lines = [
        "Catálogo de diagramas del proyecto",
        f"Total: {inventory['total']} diagramas | Grupos: {', '.join(inventory['groups'])}",
        f"Formatos: {inventory['formats']}",
    ]
    current_group = None
    for index, diagram in enumerate(inventory["diagrams"], 1):
        group = diagram["name"].split("/")[0]
        if group != current_group:
            current_group = group
            lines.extend(["", group.upper()])
        title = diagram.get("title") or diagram["name"].split("/")[-1].replace("_", " ")
        formats = ", ".join(source.rsplit(".", 1)[-1].upper() for source in diagram["sources"])
        lines.append(f"  {index:02d}. {title} [{formats}]")
        lines.append(f"      {diagram['name']}")
    lines.extend(["", "Para la defensa, relaciona cada figura con la hipótesis, el flujo y sus limitaciones."])
    return "\n".join(lines)


def state_of_art_report(state: dict) -> str:
    lines = [
        "Estado del arte y posicionamiento técnico",
        "",
        f"Alcance: {state['scope']}",
        f"Brecha: {state['research_gap']}",
        "",
        "Comparación",
    ]
    for item in state["approaches"]:
        lines.append(f"• {item['approach']}")
        lines.append(f"  Fortaleza: {item['strength']}")
        lines.append(f"  Brecha: {item['gap']}")
        lines.append(f"  Respuesta TPV: {item['project_response']}")
    lines.extend(["", "Diferenciadores"])
    lines.extend(f"  ✓ {item}" for item in state["differentiators"])
    lines.extend(["", "Evidencia"])
    lines.extend(f"  • {item}" for item in state["evidence"])
    lines.extend(["", "Nota académica", state["caveat"]])
    return "\n".join(lines)


def layers_report(architecture: list[dict], osi: list[dict]) -> str:
    lines = ["Capas del sistema", ""]
    for index, layer in enumerate(architecture, 1):
        lines.append(f"{index}. {layer['layer']}: {layer['responsibility']}")
        lines.append(f"   Rutas: {', '.join(layer['paths'])}")
    lines.extend(["", "Modelo OSI aplicado"])
    for layer in osi:
        lines.append(f"Capa {layer['layer']} — {layer['name']}")
        lines.append(f"  Proyecto: {layer['project']}")
        lines.append(f"  Medición: {layer['measurements']}")
        lines.append(f"  Límite: {layer['limitation']}")
    return "\n".join(lines)

#!/usr/bin/env python3
"""Autogenera docs/API_REFERENCE.md a partir de los decoradores @bp.route del código.
Uso:  python3 scripts/gen_api_reference.py
"""
import re, glob, datetime, os
from collections import defaultdict

BASE = os.path.join(os.path.dirname(__file__), "..", "app", "src", "main", "python")
BASE = os.path.abspath(BASE)
OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "API_REFERENCE.md")

ruta_re = re.compile(r'@(\w+)\.route\(\s*[\'"]([^\'"]+)[\'"]\s*(?:,\s*methods\s*=\s*(\[[^\]]*\]))?')
data = defaultdict(list)
total = 0
for f in sorted(glob.glob(os.path.join(BASE, "**", "*.py"), recursive=True)):
    rel = os.path.relpath(f, BASE)
    try:
        lines = open(f, encoding="utf-8").read().splitlines()
    except Exception:
        continue
    for i, ln in enumerate(lines):
        m = ruta_re.search(ln)
        if m:
            methods = m.group(3)
            ms = re.findall(r"[A-Z]+", methods) if methods else ["GET"]
            fn, doc = "", ""
            for j in range(i+1, min(i+5, len(lines))):
                dm = re.search(r'def\s+(\w+)', lines[j])
                if dm:
                    fn = dm.group(1)
                    for k in range(j+1, min(j+3, len(lines))):
                        ds = re.search(r'"""(.+?)"""', lines[k]) or re.search(r'"""(.+)', lines[k])
                        if ds:
                            doc = ds.group(1).strip().strip('"').strip()
                            break
                    break
            data[rel].append((", ".join(ms), m.group(2), fn, doc))
            total += 1

out = []
out.append("# 📡 Referencia de API — TPV Ultra Smart v8.0")
out.append("")
out.append("> **Documento autogenerado** a partir del código fuente.  ")
out.append(f"> Total de endpoints: **{total}** en **{len(data)}** módulos.  ")
out.append(f"> Generado: {datetime.date.today().isoformat()}")
out.append("")
out.append("> ⚠️ Las rutas se extraen de los decoradores `@bp.route(...)`. Los permisos por")
out.append("> rol dependen de `@login_required` / `@requiere_rol` de cada función.")
out.append("")
out.append("## Índice de módulos")
out.append("")
for f in sorted(data.keys()):
    nombre = f.replace("modules/", "").replace(".py", "")
    ancla = nombre.lower().replace("/", "").replace("_", "-").replace(".", "")
    out.append(f"- [`{f}`](#{ancla}) — {len(data[f])} endpoints")
out.append("")
out.append("---")
out.append("")
for f in sorted(data.keys()):
    nombre = f.replace("modules/", "").replace(".py", "")
    ancla = nombre.lower().replace("/", "").replace("_", "-").replace(".", "")
    out.append(f"## {nombre}")
    out.append(f'<a name="{ancla}"></a>')
    out.append(f"Archivo: `app/src/main/python/{f}`")
    out.append("")
    out.append("| Método | Ruta | Función | Descripción |")
    out.append("|--------|------|---------|-------------|")
    for ms, path, fn, doc in data[f]:
        doc = (doc or "").replace("|", "\\|")[:80]
        out.append(f"| {ms} | `{path}` | `{fn}` | {doc} |")
    out.append("")
open(OUT, "w", encoding="utf-8").write("\n".join(out))
print(f"OK: {total} endpoints -> docs/API_REFERENCE.md")

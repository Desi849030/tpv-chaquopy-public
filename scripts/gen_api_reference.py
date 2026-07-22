#!/usr/bin/env python3
"""Generate docs/API_REFERENCE.md from Flask route decorators."""
from __future__ import annotations

import datetime
import glob
import os
import re
from collections import defaultdict

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "src", "main", "python"))
OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "API_REFERENCE.md")

ROUTE_RE = re.compile(
    r'@(\w+)\.(route|get|post|put|delete|patch)\(\s*[\'"]([^\'"]+)[\'"]'
    r'\s*(?:,\s*methods\s*=\s*(\[[^\]]*\]))?'
)
data = defaultdict(list)
total = 0
for filename in sorted(glob.glob(os.path.join(BASE, "**", "*.py"), recursive=True)):
    relative = os.path.relpath(filename, BASE)
    try:
        lines = open(filename, encoding="utf-8").read().splitlines()
    except OSError:
        continue
    for index, line in enumerate(lines):
        match = ROUTE_RE.search(line)
        if not match:
            continue
        shortcut = match.group(2)
        methods_literal = match.group(4)
        methods = re.findall(r"[A-Z]+", methods_literal) if methods_literal else [
            "GET" if shortcut == "route" else shortcut.upper()
        ]
        function, docstring = "", ""
        for next_index in range(index + 1, min(index + 7, len(lines))):
            definition = re.search(r"def\s+(\w+)", lines[next_index])
            if not definition:
                continue
            function = definition.group(1)
            for doc_index in range(next_index + 1, min(next_index + 4, len(lines))):
                doc = re.search(r'"""(.+?)"""', lines[doc_index]) or re.search(r'"""(.+)', lines[doc_index])
                if doc:
                    docstring = doc.group(1).strip().strip('"').strip()
                    break
            break
        data[relative].append((", ".join(methods), match.group(3), function, docstring))
        total += 1

output = [
    "# Referencia de API — TPV Ultra Smart v6.13.1",
    "",
    "> Documento autogenerado a partir de decoradores Flask `route/get/post/put/delete/patch`.",
    f"> Total de endpoints declarados: **{total}** en **{len(data)}** módulos.",
    f"> Generado: {datetime.date.today().isoformat()}",
    "",
    "> Los permisos dependen de los decoradores y controles de sesión de cada función.",
    "",
    "## Índice de módulos",
    "",
]
for relative in sorted(data):
    name = relative.replace("modules/", "").replace(".py", "")
    anchor = name.lower().replace("/", "").replace("_", "-").replace(".", "")
    output.append(f"- [`{relative}`](#{anchor}) — {len(data[relative])} endpoints")
output.extend(["", "---", ""])
for relative in sorted(data):
    name = relative.replace("modules/", "").replace(".py", "")
    anchor = name.lower().replace("/", "").replace("_", "-").replace(".", "")
    output.extend([
        f"## {name}", f'<a name="{anchor}"></a>',
        f"Archivo: `app/src/main/python/{relative}`", "",
        "| Método | Ruta | Función | Descripción |",
        "|---|---|---|---|",
    ])
    for methods, path, function, docstring in data[relative]:
        description = (docstring or "").replace("|", "\\|")[:100]
        output.append(f"| {methods} | `{path}` | `{function}` | {description} |")
    output.append("")

with open(OUT, "w", encoding="utf-8") as stream:
    stream.write("\n".join(output))
print(f"OK: {total} endpoints -> docs/API_REFERENCE.md")

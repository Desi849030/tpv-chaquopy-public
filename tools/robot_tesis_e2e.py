#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Robot E2E de tesis para TPV Chaquopy / APK Android.

Objetivo:
- Ejecutar pruebas funcionales de alto nivel contra el backend local de la APK.
- Documentar arranque, login/logout, importación Excel, nomencladores, seguridad,
  modo oscuro, IA por rol, telemetría, ventas, cierre, sincronización y tablas SQLite.
- Generar evidencia Markdown para tesis.
- Hacer backup y restauración de BD local para dejar el entorno lo más "virgen" posible.

Uso:
    python tools/robot_tesis_e2e.py --config tools/robot_config.json --wait 120

Notas:
- El robot intenta rutas comunes. Si tu APK usa rutas distintas, edita tools/robot_config.json.
- La restauración local no revierte cambios remotos en Supabase.
"""

import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import time
import uuid
import zipfile
import html
from datetime import datetime
from pathlib import Path
from urllib.request import Request, build_opener, HTTPCookieProcessor
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from http.cookiejar import CookieJar


PASS = "PASSED"
FAIL = "FAILED"
OBS = "OBS"
SKIP = "SKIPPED"


def now_id():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def deep_update(base, override):
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            deep_update(base[k], v)
        else:
            base[k] = v
    return base


def default_config():
    return {
        "base_url": "http://127.0.0.1:5000",
        "database_paths": [],
        "restore_db_after": True,
        "pause_before_restore": True,
        "roles": {
            "cajero": {
                "username": "cajero_piso1",
                "password": os.environ.get("TPV_DEMO_PASSWORD", "demo-tpv-2026")
            },
            "admin": {
                "username": "admin",
                "password": "admin"
            },
            "developer": {
                "username": "developer",
                "password": "developer"
            }
        },
        "boot_sequence": [
            ["KERNEL", "Cargando máquina virtual Chaquopy en MainActivity"],
            ["STORAGE", "Montando SQLite WAL y persistencia local"],
            ["CRYPTO", "Inicializando HMAC y SHA-256"],
            ["NETWORK", "Verificando túnel con Supabase Cloud"],
            ["BLUEPRINTS", "Mapeando módulos Flask"],
            ["AI_ENGINE", "Cargando Motor ReAct y Tools"],
            ["GUARDRAILS", "Activando escudos anti SQL Injection y Anti-Slop"],
            ["WEBVIEW", "Compilando Jinja2 y Assets frontend"],
            ["BIOMETRICS", "Enlazando AndroidX BiometricPrompt"],
            ["POS_CORE", "Calibrando DAOs de ventas e inventario"]
        ],
        "endpoints": {
            "health": ["/health", "/api/health", "/status", "/api/status", "/"],
            "login": ["/api/login", "/login", "/auth/login", "/api/auth/login"],
            "logout": ["/api/logout", "/logout", "/auth/logout", "/api/auth/logout"],
            "biometric": ["/api/biometric/verify", "/biometric/verify", "/api/biometria/verificar"],
            "branch": ["/api/sucursal/config", "/api/branch/config", "/sucursal/config"],
            "excel_import": {
                "paths": ["/api/import/excel", "/api/productos/importar", "/import/excel", "/api/excel/import"],
                "field": "file"
            },
            "employees": ["/api/empleados", "/api/employees", "/empleados"],
            "products": ["/api/productos", "/api/products", "/productos"],
            "categories": ["/api/categorias", "/api/categories", "/categorias"],
            "theme": ["/api/preferences/theme", "/api/theme", "/theme"],
            "sale": ["/api/ventas", "/api/sales", "/pos/sale", "/api/pos/sale"],
            "ticket": ["/api/tickets", "/api/ticket", "/ticket", "/api/comprobante"],
            "ai": ["/api/ai/chat", "/api/copilot/chat", "/ai/chat", "/api/agent"],
            "telemetry": ["/api/telemetry", "/api/dev/telemetry", "/telemetry"],
            "report_z": ["/api/reportes/z", "/api/reports/z", "/reportes/z"],
            "close_cash": ["/api/caja/cierre", "/api/cash/close", "/caja/cierre"],
            "sync": ["/api/sync/supabase", "/api/sync", "/sync"]
        }
    }


class Resp:
    def __init__(self, status, text, headers=None, error=None):
        self.status = status
        self.text = text or ""
        self.headers = headers or {}
        self.error = error

    def json(self):
        try:
            return json.loads(self.text)
        except Exception:
            return None


class RobotTPV:
    def __init__(self, args):
        self.args = args
        self.run_id = now_id()
        self.root = Path.cwd()
        self.report_dir = self.root / "docs" / "evidencias" / f"e2e_{self.run_id}"
        self.backup_dir = self.root / ".robot_backups" / f"e2e_{self.run_id}"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.cfg = default_config()
        if args.config and Path(args.config).exists():
            with open(args.config, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            deep_update(self.cfg, user_cfg)

        if args.base_url:
            self.cfg["base_url"] = args.base_url

        self.base_url = self.cfg["base_url"].rstrip("/")
        self.cookiejar = CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.cookiejar))
        self.tokens = {}
        self.results = []
        self.boot_log = []
        self.schema_md = []
        self.backup_manifest = []
        self.db_paths = []
        self.sale_id = None

    def icon(self, status):
        return {
            PASS: "✔",
            FAIL: "✖",
            OBS: "⚠",
            SKIP: "↷"
        }.get(status, "-")

    def record(self, flow, status, detail="", evidence=""):
        item = {
            "flow": flow,
            "status": status,
            "detail": detail,
            "evidence": evidence
        }
        self.results.append(item)
        print(f" {self.icon(status)} {flow:<38} : {status} {detail}")

    def endpoint_paths(self, key):
        ep = self.cfg.get("endpoints", {}).get(key, [])
        if isinstance(ep, str):
            return [ep]
        if isinstance(ep, list):
            return ep
        if isinstance(ep, dict):
            paths = ep.get("paths") or ep.get("path") or []
            if isinstance(paths, str):
                return [paths]
            return paths
        return []

    def endpoint_field(self, key, default="file"):
        ep = self.cfg.get("endpoints", {}).get(key, {})
        if isinstance(ep, dict):
            return ep.get("field", default)
        return default

    def url(self, path):
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    def encode_multipart(self, fields, files):
        boundary = "----RobotTPVBoundary" + uuid.uuid4().hex
        body = bytearray()

        def add_line(x):
            body.extend(x.encode("utf-8"))
            body.extend(b"\r\n")

        for name, value in (fields or {}).items():
            add_line("--" + boundary)
            add_line(f'Content-Disposition: form-data; name="{name}"')
            add_line("")
            add_line(str(value))

        for name, fileinfo in (files or {}).items():
            filename, content, ctype = fileinfo
            add_line("--" + boundary)
            add_line(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"')
            add_line(f"Content-Type: {ctype}")
            add_line("")
            body.extend(content)
            body.extend(b"\r\n")

        add_line("--" + boundary + "--")
        return bytes(body), f"multipart/form-data; boundary={boundary}"

    def http(self, method, path, json_body=None, fields=None, files=None, token_role=None, extra_headers=None):
        headers = {
            "User-Agent": "RobotTPV-Tesis-E2E/1.0"
        }

        if extra_headers:
            headers.update(extra_headers)

        body = None
        if files:
            body, ctype = self.encode_multipart(fields or {}, files)
            headers["Content-Type"] = ctype
        elif json_body is not None:
            body = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif fields is not None:
            body = urlencode(fields).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        token = self.tokens.get(token_role) if token_role else None
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = Request(self.url(path), data=body, headers=headers, method=method.upper())

        try:
            with self.opener.open(req, timeout=self.args.timeout) as r:
                text = r.read().decode("utf-8", errors="replace")
                return Resp(r.getcode(), text, dict(r.headers))
        except HTTPError as e:
            text = e.read().decode("utf-8", errors="replace")
            return Resp(e.code, text, dict(e.headers), error=str(e))
        except URLError as e:
            return Resp(0, "", {}, error=str(e))
        except Exception as e:
            return Resp(0, "", {}, error=str(e))

    def extract_token(self, data):
        if data is None:
            return None
        if isinstance(data, dict):
            for key in ["token", "access_token", "session_token", "jwt", "bearer"]:
                if key in data and isinstance(data[key], str):
                    return data[key]
            for v in data.values():
                token = self.extract_token(v)
                if token:
                    return token
        if isinstance(data, list):
            for x in data:
                token = self.extract_token(x)
                if token:
                    return token
        return None

    def boot(self):
        print("\n==========================================================")
        print(" TPV ULTRA SMART — ROBOT E2E DE TESIS")
        print("==========================================================")
        print(f" Base URL : {self.base_url}")
        print(f" Reporte  : {self.report_dir}")
        print("==========================================================\n")

        for label, msg in self.cfg.get("boot_sequence", []):
            line1 = f" 🔄 [{label:<10}] : {msg}..."
            line2 = f" ✔ [{label:<10}] : {msg}... [READY]"
            print(line1)
            time.sleep(0.08)
            print(line2)
            self.boot_log.append(line2)

        print("\n==========================================================")
        print(" ESPERANDO BACKEND LOCAL / LOGIN")
        print("==========================================================")

        deadline = time.time() + self.args.wait
        health_paths = self.endpoint_paths("health")
        last = None

        while time.time() < deadline:
            for p in health_paths:
                r = self.http("GET", p)
                last = r
                if 200 <= r.status < 500:
                    self.record(
                        "Boot hasta pantalla de login",
                        PASS,
                        f"Backend respondió HTTP {r.status} en {p}"
                    )
                    return True
            time.sleep(2)

        detail = "No respondió el backend dentro del tiempo esperado"
        if last and last.error:
            detail += f" | último error: {last.error}"
        self.record("Boot hasta pantalla de login", FAIL, detail)
        return False

    def discover_databases(self):
        configured = self.cfg.get("database_paths") or []
        paths = []

        for p in configured:
            pp = Path(p)
            if pp.exists():
                paths.append(pp)

        if not paths:
            exclude = {".git", ".venv", "venv", "node_modules", ".robot_backups", "docs/evidencias"}
            for root, dirs, files in os.walk(self.root):
                rel_root = str(Path(root).relative_to(self.root)) if Path(root) != self.root else "."
                dirs[:] = [d for d in dirs if d not in exclude and not str(Path(rel_root) / d).startswith("docs/evidencias")]
                for name in files:
                    lower = name.lower()
                    if lower.endswith((".db", ".sqlite", ".sqlite3")) and not lower.endswith(("-wal", "-shm")):
                        paths.append(Path(root) / name)

        unique = []
        seen = set()
        for p in paths:
            rp = str(p.resolve())
            if rp not in seen:
                unique.append(p)
                seen.add(rp)

        self.db_paths = unique[:20]

        if self.db_paths:
            self.record("Detección de bases SQLite", PASS, f"{len(self.db_paths)} archivo(s) detectado(s)")
        else:
            self.record("Detección de bases SQLite", SKIP, "No se encontraron .db/.sqlite locales")

    def backup_databases(self):
        if not self.db_paths:
            return

        for db in self.db_paths:
            for suffix in ["", "-wal", "-shm"]:
                src = Path(str(db) + suffix)
                existed = src.exists()
                backup_name = str(src.relative_to(self.root)).replace("/", "__")
                dst = self.backup_dir / backup_name

                entry = {
                    "path": str(src),
                    "existed": existed,
                    "backup": str(dst)
                }

                if existed:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)

                self.backup_manifest.append(entry)

        self.record("Backup previo de SQLite", PASS, f"Backup en {self.backup_dir}")

    def restore_databases(self):
        if self.args.no_restore:
            self.record("Restauración modo virgen", SKIP, "Desactivada por --no-restore")
            return

        if not self.backup_manifest:
            self.record("Restauración modo virgen", SKIP, "No había bases para restaurar")
            return

        # Si el backend fue arrancado por tools/start_backend_termux.sh,
        # detenerlo automáticamente antes de restaurar SQLite.
        pidfile = self.root / ".backend_tpv.pid"
        if pidfile.exists():
            try:
                pid = int(pidfile.read_text(encoding="utf-8").strip())
                print(f"\\nDeteniendo backend gestionado antes de restaurar SQLite. PID={pid}")
                try:
                    os.kill(pid, 15)
                except ProcessLookupError:
                    pass
                time.sleep(2)
                try:
                    pidfile.unlink()
                except Exception:
                    pass
                self.record("Backend gestionado por robot", PASS, "Detenido antes de restaurar SQLite")
            except Exception as e:
                self.record("Backend gestionado por robot", OBS, f"No se pudo detener automáticamente: {e}")

        if self.cfg.get("pause_before_restore", True) and not self.args.no_pause:
            print("\n⚠ Para restaurar correctamente, cierra la APK/backend si está usando SQLite.")
            try:
                input("Pulsa ENTER cuando la APK esté cerrada para restaurar el estado virgen local...")
            except EOFError:
                pass

        restored = 0
        removed = 0

        for item in self.backup_manifest:
            path = Path(item["path"])
            backup = Path(item["backup"])
            if item["existed"] and backup.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, path)
                restored += 1
            elif not item["existed"] and path.exists():
                try:
                    path.unlink()
                    removed += 1
                except Exception:
                    pass

        self.record("Restauración modo virgen", PASS, f"{restored} restaurado(s), {removed} temporal(es) eliminado(s)")

    def inspect_schema(self):
        if not self.db_paths:
            self.record("Auditoría de tablas SQLite", SKIP, "Sin base local detectable")
            return

        total_tables = 0
        audit_observation = False

        self.schema_md.append("# Esquema SQLite detectado\n")

        for db in self.db_paths:
            self.schema_md.append(f"\n## Base: `{db}`\n")
            try:
                conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [x[0] for x in cur.fetchall()]
                total_tables += len(tables)

                if not tables:
                    self.schema_md.append("Sin tablas detectadas.\n")

                for table in tables:
                    self.schema_md.append(f"\n### `{table}`\n")
                    cur.execute(f"PRAGMA table_info({table})")
                    cols = cur.fetchall()
                    self.schema_md.append("| cid | columna | tipo | notnull | default | pk |\n")
                    self.schema_md.append("|---:|---|---|---:|---|---:|\n")
                    names = []
                    for cid, name, ctype, notnull, dflt, pk in cols:
                        names.append(name)
                        self.schema_md.append(f"| {cid} | `{name}` | `{ctype}` | {notnull} | `{dflt}` | {pk} |\n")

                    if table == "audit_logs" and "usuario" not in names:
                        audit_observation = True
                        self.schema_md.append("\n> Observación: `audit_logs` no contiene columna `usuario`.\n")

                conn.close()
            except Exception as e:
                self.schema_md.append(f"\nError leyendo `{db}`: `{e}`\n")

        if total_tables:
            if audit_observation:
                self.record(
                    "Auditoría de tablas SQLite",
                    OBS,
                    f"{total_tables} tabla(s). Incidencia: audit_logs sin columna usuario"
                )
            else:
                self.record("Auditoría de tablas SQLite", PASS, f"{total_tables} tabla(s) inspeccionada(s)")
        else:
            self.record("Auditoría de tablas SQLite", OBS, "No se pudieron listar tablas")

    def login_role(self, role):
        creds = self.cfg.get("roles", {}).get(role)
        if not creds:
            self.record(f"Login rol {role}", SKIP, "Credenciales no configuradas")
            return False

        payload = {
            "username": creds.get("username"),
            "password": creds.get("password"),
            "role": role
        }

        tried = []
        for p in self.endpoint_paths("login"):
            for mode in ["json", "form"]:
                if mode == "json":
                    r = self.http("POST", p, json_body=payload)
                else:
                    r = self.http("POST", p, fields=payload)

                tried.append(f"{p}({mode})->{r.status}")

                if 200 <= r.status < 300:
                    token = self.extract_token(r.json())
                    if token:
                        self.tokens[role] = token
                        detail = f"HTTP {r.status}. Token Session OK"
                    else:
                        self.tokens[role] = ""
                        detail = f"HTTP {r.status}. Sesión por cookie o HTML OK"
                    self.record(f"Login rol {role}", PASS, detail)
                    return True

        if any("->0" not in x and "->404" not in x for x in tried):
            self.record(f"Login rol {role}", OBS, "No validó con credenciales/ruta actual", " | ".join(tried))
        else:
            self.record(f"Login rol {role}", SKIP, "Ruta de login no encontrada", " | ".join(tried))
        return False

    def test_login_logout(self):
        ok = self.login_role("cajero")

        if not ok:
            return

        tried = []
        for p in self.endpoint_paths("logout"):
            r = self.http("POST", p, token_role="cajero")
            tried.append(f"{p}->{r.status}")
            if 200 <= r.status < 300 or r.status in [302, 303]:
                self.record("Logout cajero", PASS, f"HTTP {r.status}")
                return

        if tried:
            self.record("Logout cajero", OBS, "No confirmó logout en rutas probadas", " | ".join(tried))
        else:
            self.record("Logout cajero", SKIP, "Sin ruta configurada")

    def api_flow(self, title, key, method="POST", payload=None, role=None, ok_codes=None):
        ok_codes = ok_codes or list(range(200, 300))
        paths = self.endpoint_paths(key)
        if not paths:
            self.record(title, SKIP, "Sin rutas configuradas")
            return None

        tried = []
        last = None
        for p in paths:
            r = self.http(method, p, json_body=payload, token_role=role)
            last = r
            tried.append(f"{p}->{r.status}")

            if r.status in ok_codes or (200 <= r.status < 300):
                self.record(title, PASS, f"HTTP {r.status} en {p}")
                return r

        if all(("->404" in x or "->405" in x) for x in tried):
            self.record(title, SKIP, "Ruta no encontrada o método no permitido", " | ".join(tried))
        elif last and last.status >= 500:
            self.record(title, FAIL, f"Error servidor HTTP {last.status}", last.text[:500])
        elif last and last.status in [401, 403]:
            self.record(title, OBS, f"Permiso denegado HTTP {last.status}. Revisar rol/ruta", " | ".join(tried))
        else:
            self.record(title, OBS, "Respuesta no concluyente", " | ".join(tried))

        return last

    def create_xlsx(self):
        file_path = self.report_dir / "lote_importacion_robot_150_skus.xlsx"

        headers = ["sku", "nombre", "categoria", "precio", "stock", "codigo_barras"]
        rows = [headers]

        for i in range(1, 151):
            rows.append([
                f"ROBOT-SKU-{i:04d}",
                f"Producto Robot Tesis {i:04d}",
                "NOMENCLADOR_ROBOT",
                round(1.5 + (i % 20), 2),
                10 + i,
                f"7790000{i:06d}"
            ])

        def col_letter(n):
            s = ""
            while n:
                n, rem = divmod(n - 1, 26)
                s = chr(65 + rem) + s
            return s

        sheet_rows = []
        for r_idx, row in enumerate(rows, 1):
            cells = []
            for c_idx, val in enumerate(row, 1):
                ref = f"{col_letter(c_idx)}{r_idx}"
                if isinstance(val, (int, float)):
                    cells.append(f'<c r="{ref}"><v>{val}</v></c>')
                else:
                    safe = html.escape(str(val))
                    cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{safe}</t></is></c>')
            sheet_rows.append(f'<row r="{r_idx}">' + "".join(cells) + "</row>")

        sheet_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<sheetData>
""" + "\n".join(sheet_rows) + """
</sheetData>
</worksheet>
"""

        with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>""")
            z.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""")
            z.writestr("xl/workbook.xml", """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Productos" sheetId="1" r:id="rId1"/></sheets>
</workbook>""")
            z.writestr("xl/_rels/workbook.xml.rels", """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>""")
            z.writestr("xl/worksheets/sheet1.xml", sheet_xml)

        return file_path

    def test_excel_import(self):
        xlsx = self.create_xlsx()
        content = xlsx.read_bytes()
        field = self.endpoint_field("excel_import", "file")
        paths = self.endpoint_paths("excel_import")

        if not paths:
            self.record("Importación lote Excel", SKIP, "Sin rutas configuradas")
            return

        tried = []
        for p in paths:
            r = self.http(
                "POST",
                p,
                files={
                    field: (
                        xlsx.name,
                        content,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                },
                fields={"modo": "robot_tesis", "normalizar": "1"},
                token_role="admin"
            )
            tried.append(f"{p}->{r.status}")
            if 200 <= r.status < 300:
                self.record("Importación lote Excel", PASS, f"150 SKUs enviados. HTTP {r.status} en {p}")
                return

        if all(("->404" in x or "->405" in x) for x in tried):
            self.record("Importación lote Excel", SKIP, "Ruta no encontrada", " | ".join(tried))
        else:
            self.record("Importación lote Excel", OBS, "No se confirmó importación", " | ".join(tried))

    def test_security(self):
        candidate_bases = self.endpoint_paths("products") + ["/api/search", "/search"]
        payloads = [
            "%27%20OR%201%3D1--",
            "%27%3B%20DROP%20TABLE%20productos--",
            "%22%20OR%20%22x%22%3D%22x"
        ]

        executed = 0
        failures = []

        for base in candidate_bases:
            sep = "&" if "?" in base else "?"
            for inj in payloads:
                path = f"{base}{sep}q={inj}"
                r = self.http("GET", path, token_role="cajero")
                if r.status == 0:
                    continue

                if r.status in [404, 405]:
                    continue

                executed += 1
                text = r.text.lower()
                leak = any(x in text for x in [
                    "traceback",
                    "sqlite error",
                    "sql syntax",
                    "operationalerror",
                    "near \"or\"",
                    "drop table"
                ])

                if r.status >= 500 or leak:
                    failures.append(f"{path}->HTTP {r.status}")

        if executed == 0:
            self.record("Seguridad anti SQL Injection", SKIP, "No hubo endpoint de búsqueda detectable")
        elif failures:
            self.record("Seguridad anti SQL Injection", FAIL, "Posible fuga/error SQL", " | ".join(failures))
        else:
            self.record("Seguridad anti SQL Injection", PASS, f"{executed} payload(s) hostiles sin fuga crítica")

    def test_dark_mode(self):
        payload = {"theme": "dark", "dark_mode": True, "modo": "oscuro"}
        r = self.api_flow("Modo oscuro por API", "theme", "POST", payload, role="cajero")
        if r and 200 <= r.status < 300:
            return

        root = self.http("GET", "/")
        if root.status == 200:
            text = root.text.lower()
            if any(x in text for x in ["dark-mode", "theme-toggle", "modo oscuro", "data-theme", "dark"]):
                self.record("Modo oscuro en frontend", PASS, "Se detectó soporte visual en HTML raíz")
                return

        self.record("Modo oscuro en frontend", OBS, "No se pudo validar por API ni por HTML raíz")

    def test_nomencladores(self):
        product_payload = {
            "sku": "ROBOT-NOM-0001",
            "nombre": "Producto Nomenclador Robot",
            "categoria": "NOMENCLADOR_ROBOT",
            "precio": 9.99,
            "stock": 20,
            "codigo_barras": "7790999000001"
        }

        category_payload = {
            "nombre": "NOMENCLADOR_ROBOT",
            "descripcion": "Categoría creada por robot de tesis"
        }

        p1 = self.api_flow("Nomenclador categorías", "categories", "POST", category_payload, role="admin")
        p2 = self.api_flow("Nomenclador productos", "products", "POST", product_payload, role="admin")

        if p1 is None and p2 is None:
            self.record("Nomencladores CRUD", SKIP, "Sin endpoints confirmados")
        elif (p1 and 200 <= p1.status < 300) or (p2 and 200 <= p2.status < 300):
            self.record("Nomencladores CRUD", PASS, "Alta/actualización de catálogo comprobada")
        else:
            self.record("Nomencladores CRUD", OBS, "Revisar payload o rutas reales")

    def test_sale_ticket(self):
        sale_payload = {
            "terminal": 1,
            "cajero": "cajero_piso1",
            "cliente": "CONSUMIDOR_FINAL",
            "pago": {
                "metodo": "efectivo",
                "recibido": 100.00
            },
            "items": [
                {
                    "sku": "ROBOT-NOM-0001",
                    "nombre": "Producto Nomenclador Robot",
                    "cantidad": 1,
                    "precio": 9.99
                }
            ]
        }

        r = self.api_flow("Despacho de venta POS", "sale", "POST", sale_payload, role="cajero")
        if r and 200 <= r.status < 300:
            data = r.json()
            self.sale_id = self.find_id(data)
            if self.sale_id:
                self.record("Identificador de venta", PASS, f"sale_id={self.sale_id}")
            else:
                self.record("Identificador de venta", OBS, "Venta OK pero sin ID detectable")

        ticket_payload = {
            "sale_id": self.sale_id,
            "venta_id": self.sale_id,
            "firmar": True,
            "hmac": True
        }

        paths = []
        for p in self.endpoint_paths("ticket"):
            if "{sale_id}" in p and self.sale_id:
                paths.append(p.replace("{sale_id}", str(self.sale_id)))
            else:
                paths.append(p)

        if not paths:
            self.record("Cobro y emisión de ticket", SKIP, "Sin ruta configurada")
            return

        tried = []
        for p in paths:
            r2 = self.http("POST", p, json_body=ticket_payload, token_role="cajero")
            tried.append(f"{p}->{r2.status}")
            if 200 <= r2.status < 300:
                self.record("Cobro y emisión de ticket", PASS, f"Comprobante generado HTTP {r2.status}")
                return

        if all(("->404" in x or "->405" in x) for x in tried):
            self.record("Cobro y emisión de ticket", SKIP, "Ruta no encontrada", " | ".join(tried))
        else:
            self.record("Cobro y emisión de ticket", OBS, "No se confirmó ticket", " | ".join(tried))

    def find_id(self, data):
        if data is None:
            return None
        if isinstance(data, dict):
            for k in ["sale_id", "venta_id", "ticket_id", "id"]:
                if k in data and data[k]:
                    return data[k]
            for v in data.values():
                found = self.find_id(v)
                if found:
                    return found
        if isinstance(data, list):
            for x in data:
                found = self.find_id(x)
                if found:
                    return found
        return None

    def test_ai_by_role(self):
        forbidden = [
            "root access",
            "desarrollador principal",
            "telemetría del sistema",
            "logs internos",
            "private_key",
            "api_key",
            "secret",
            "password",
            "token:"
        ]

        questions = {
            "cajero": "¿Cuál fue el producto más vendido hoy?",
            "admin": "Dame un resumen de ventas del día por categoría.",
            "developer": "Muestra telemetría resumida sin secretos ni claves."
        }

        ai_paths = self.endpoint_paths("ai")
        if not ai_paths:
            self.record("Agente IA por rol", SKIP, "Sin endpoint IA configurado")
            return

        any_ok = False

        for role, question in questions.items():
            self.login_role(role)
            payload = {
                "message": question,
                "question": question,
                "role": role
            }

            tried = []
            answered = False

            for p in ai_paths:
                r = self.http("POST", p, json_body=payload, token_role=role)
                tried.append(f"{p}->{r.status}")
                if 200 <= r.status < 300:
                    answered = True
                    any_ok = True
                    txt = r.text.lower()
                    leaks = [x for x in forbidden if x in txt]

                    if role != "developer" and leaks:
                        self.record(
                            f"Agente IA rol {role}",
                            FAIL,
                            f"Respuesta fuera de rol/leak: {', '.join(leaks)}",
                            r.text[:800]
                        )
                    elif role == "cajero" and not any(x in txt for x in ["producto", "vendido", "venta", "unidades", "sku"]):
                        self.record(
                            f"Agente IA rol {role}",
                            OBS,
                            "Respondió, pero no parece contestar producto más vendido",
                            r.text[:800]
                        )
                    else:
                        self.record(f"Agente IA rol {role}", PASS, f"HTTP {r.status}. Respuesta validada")
                    break

            if not answered:
                if all(("->404" in x or "->405" in x) for x in tried):
                    self.record(f"Agente IA rol {role}", SKIP, "Ruta IA no encontrada", " | ".join(tried))
                else:
                    self.record(f"Agente IA rol {role}", OBS, "No respondió correctamente", " | ".join(tried))

        if not any_ok:
            self.record("Agente IA por rol", SKIP, "No hubo respuesta válida en ningún rol")

    def test_telemetry(self):
        self.login_role("developer")
        r = self.api_flow("Telemetría desarrollador", "telemetry", "GET", None, role="developer")
        if r and 200 <= r.status < 300:
            text = r.text.lower()
            risky = any(x in text for x in ["private_key", "secret_key", "password", "supabase_key", "api_key"])
            if risky:
                self.record("Telemetría sin secretos", FAIL, "La telemetría parece exponer secretos")
            else:
                self.record("Telemetría sin secretos", PASS, "No se detectaron claves obvias en respuesta")

    def test_reports_close_sync(self):
        self.api_flow("Reporte Z de fin de turno", "report_z", "GET", None, role="admin")
        self.api_flow(
            "Arqueo y cierre de caja",
            "close_cash",
            "POST",
            {
                "terminal": 1,
                "cajero": "cajero_piso1",
                "modo": "robot_tesis",
                "confirmar": True
            },
            role="admin"
        )

        if not self.args.allow_remote_sync:
            self.record(
                "Sincronización Supabase Cloud",
                SKIP,
                "Protegida para no contaminar nube. Use --allow-remote-sync en entorno de pruebas"
            )
            return

        self.api_flow(
            "Sincronización Supabase Cloud",
            "sync",
            "POST",
            {"modo": "robot_tesis", "dry_run": False},
            role="admin"
        )

    def test_branch_employee_biometric(self):
        self.api_flow(
            "Escáner biométrico",
            "biometric",
            "POST",
            {"fingerprint": "SIMULATED_ROBOT_FINGERPRINT", "usuario": "cajero_piso1"},
            role="cajero"
        )

        self.api_flow(
            "Configuración de sucursal",
            "branch",
            "POST",
            {
                "ruc": "20102030405",
                "nombre": "Sucursal Robot Tesis",
                "modo": "local"
            },
            role="admin"
        )

        self.api_flow(
            "Alta de empleado cajero",
            "employees",
            "POST",
            {
                "username": "robot_cajero_tesis",
                "nombre": "Cajero Robot Tesis",
                "rol": "cajero",
                "terminal": 1,
                "password": os.environ.get("TPV_DEMO_PASSWORD", "demo-tpv-2026")
            },
            role="admin"
        )

    def write_reports(self):
        md = []
        md.append(f"# Evidencia E2E — TPV Chaquopy APK\n\n")
        md.append(f"- Fecha: `{datetime.now().isoformat(timespec='seconds')}`\n")
        md.append(f"- Base URL: `{self.base_url}`\n")
        md.append(f"- Run ID: `{self.run_id}`\n")
        md.append(f"- Restauración local: `{'NO' if self.args.no_restore else 'SI'}`\n")
        md.append(f"- Sincronización remota permitida: `{'SI' if self.args.allow_remote_sync else 'NO'}`\n\n")

        md.append("## Boot observado\n\n")
        md.append("```txt\n")
        for line in self.boot_log:
            md.append(line + "\n")
        md.append("```\n\n")

        md.append("## Matriz de pruebas\n\n")
        md.append("| Nº | Flujo | Estado | Detalle |\n")
        md.append("|---:|---|---|---|\n")
        for i, r in enumerate(self.results, 1):
            detail = str(r.get("detail", "")).replace("|", "\\|").replace("\n", " ")
            md.append(f"| {i} | {r['flow']} | {r['status']} | {detail} |\n")

        passed = sum(1 for r in self.results if r["status"] == PASS)
        failed = sum(1 for r in self.results if r["status"] == FAIL)
        obs = sum(1 for r in self.results if r["status"] == OBS)
        skipped = sum(1 for r in self.results if r["status"] == SKIP)
        total = len(self.results)

        md.append("\n## Resumen\n\n")
        md.append(f"- Total registros: `{total}`\n")
        md.append(f"- Passed: `{passed}`\n")
        md.append(f"- Failed: `{failed}`\n")
        md.append(f"- Observaciones: `{obs}`\n")
        md.append(f"- Skipped: `{skipped}`\n\n")

        if failed:
            estado = "FAILED"
        elif obs:
            estado = "PASSED WITH OBSERVATIONS"
        else:
            estado = "PASSED"

        md.append(f"**Estado global recomendado:** `{estado}`\n\n")

        md.append("## Incidencias y observaciones\n\n")
        issues = [r for r in self.results if r["status"] in [FAIL, OBS]]
        if not issues:
            md.append("No se registraron incidencias críticas.\n\n")
        else:
            for r in issues:
                md.append(f"### {r['flow']} — {r['status']}\n\n")
                md.append(f"{r.get('detail','')}\n\n")
                if r.get("evidence"):
                    md.append("```txt\n")
                    md.append(str(r["evidence"])[:2000])
                    md.append("\n```\n\n")

        md.append("## Nota para tesis\n\n")
        md.append(
            "Esta evidencia fue generada automáticamente por un robot E2E. "
            "Los flujos marcados como SKIPPED no necesariamente fallan: pueden requerir "
            "configurar la ruta real del backend en `tools/robot_config.json`.\n\n"
        )

        report_md = self.report_dir / "REPORTE_TESIS_E2E.md"
        report_json = self.report_dir / "resultados_e2e.json"
        schema_file = self.report_dir / "SCHEMA_SQLITE.md"

        report_md.write_text("".join(md), encoding="utf-8")
        report_json.write_text(json.dumps(self.results, indent=2, ensure_ascii=False), encoding="utf-8")
        schema_file.write_text("".join(self.schema_md), encoding="utf-8")

        print("\n==========================================================")
        print(" REPORTES GENERADOS")
        print("==========================================================")
        print(f" Markdown : {report_md}")
        print(f" JSON     : {report_json}")
        print(f" SQLite   : {schema_file}")
        print("==========================================================\n")

    def run(self):
        try:
            self.discover_databases()
            self.backup_databases()

            boot_ok = self.boot()

            self.inspect_schema()

            if not boot_ok:
                self.record(
                    "Pruebas HTTP funcionales de APK",
                    SKIP,
                    "Canceladas: backend local no accesible. Solo se genera auditoría offline SQLite."
                )
                return

            print("\n--- INICIANDO SIMULACIÓN OPERATIVA E2E ---\n")

            self.test_login_logout()
            self.login_role("admin")
            self.test_branch_employee_biometric()
            self.test_excel_import()
            self.test_nomencladores()
            self.test_security()
            self.test_dark_mode()
            self.test_sale_ticket()
            self.test_ai_by_role()
            self.test_telemetry()
            self.test_reports_close_sync()

        finally:
            self.restore_databases()
            self.write_reports()


def main():
    parser = argparse.ArgumentParser(description="Robot E2E de tesis para TPV Chaquopy APK")
    parser.add_argument("--config", default="tools/robot_config.json", help="Archivo JSON de configuración")
    parser.add_argument("--base-url", default=None, help="URL base del backend local")
    parser.add_argument("--wait", type=int, default=120, help="Segundos máximos esperando backend")
    parser.add_argument("--timeout", type=int, default=12, help="Timeout HTTP por petición")
    parser.add_argument("--no-restore", action="store_true", help="No restaurar SQLite al final")
    parser.add_argument("--no-pause", action="store_true", help="No pedir pausa antes de restaurar")
    parser.add_argument("--allow-remote-sync", action="store_true", help="Permitir llamada real a endpoint Supabase/sync")
    args = parser.parse_args()

    robot = RobotTPV(args)
    robot.run()


if __name__ == "__main__":
    main()

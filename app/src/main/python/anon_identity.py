# -*- coding: utf-8 -*-
"""Identidad persistente para cliente anónimo + trazabilidad ligera.

Objetivo:
- Reconocer al mismo cliente anónimo entre sesiones.
- No romper clientes ya existentes.
- Añadir request_id útil para logs/soporte.
"""
from __future__ import annotations

import re
import uuid
from flask import request, session

ANON_SESSION_KEY = "anon_client_id"
ANON_HEADER = "X-TPV-ANON-ID"
REQUEST_ID_HEADER = "X-TPV-REQUEST-ID"
_SAFE_RE = re.compile(r"^[A-Za-z0-9._:-]{6,80}$")


def _sanitize(value: str | None, prefix: str) -> str:
    raw = str(value or "").strip()
    if raw and _SAFE_RE.fullmatch(raw):
        return raw
    cleaned = re.sub(r"[^A-Za-z0-9._:-]+", "-", raw)[:80].strip("-._:")
    if len(cleaned) >= 6:
        return cleaned
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def ensure_request_id(req=None) -> str:
    req = req or request
    rid = req.headers.get(REQUEST_ID_HEADER) or req.args.get("request_id")
    if not rid and getattr(req, "is_json", False):
        data = req.get_json(silent=True) or {}
        rid = data.get("request_id")
    if rid:
        return _sanitize(rid, "req")
    return f"req-{uuid.uuid4().hex[:12]}"


def ensure_anon_client_id(req=None, sess=None) -> str:
    req = req or request
    sess = sess if sess is not None else session

    incoming = req.headers.get(ANON_HEADER) or req.args.get("anon_client_id")
    if not incoming and getattr(req, "is_json", False):
        data = req.get_json(silent=True) or {}
        incoming = data.get("anon_client_id")

    if incoming:
        anon_id = _sanitize(incoming, "anon")
        sess[ANON_SESSION_KEY] = anon_id
        return anon_id

    current = sess.get(ANON_SESSION_KEY)
    if current:
        anon_id = _sanitize(current, "anon")
        sess[ANON_SESSION_KEY] = anon_id
        return anon_id

    anon_id = f"anon-{uuid.uuid4().hex[:12]}"
    sess[ANON_SESSION_KEY] = anon_id
    return anon_id


def identity_payload(req=None, sess=None) -> dict:
    req = req or request
    sess = sess if sess is not None else session
    rid = ensure_request_id(req)
    usuario = sess.get("usuario")

    if usuario and isinstance(usuario, dict):
        return {
            "ok": True,
            "autenticado": True,
            "rol": usuario.get("rol", "cliente"),
            "nombre": usuario.get("nombre") or usuario.get("username", ""),
            "usuario_id": usuario.get("usuario_id", ""),
            "anon_client_id": sess.get(ANON_SESSION_KEY, ""),
            "cliente_tipo": "logueado",
            "request_id": rid,
        }

    anon_id = ensure_anon_client_id(req, sess)
    return {
        "ok": True,
        "autenticado": False,
        "rol": "cliente",
        "nombre": "Cliente anónimo",
        "usuario_id": anon_id,
        "anon_client_id": anon_id,
        "cliente_tipo": "anonimo",
        "request_id": rid,
    }


def meta_payload(req=None, sess=None) -> dict:
    req = req or request
    sess = sess if sess is not None else session
    return {
        "request_id": ensure_request_id(req),
        "anon_client_id": ensure_anon_client_id(req, sess),
    }

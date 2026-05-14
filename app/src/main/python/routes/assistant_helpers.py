# -*- coding: utf-8 -*-
"""ia_assistant_routes.py - TPV Smart v1.2 - Compatible con ia_agent.py + memoria persistente"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
from decorators import requiere_login

assistant_bp = Blueprint('assistant', __name__, url_prefix='/api/ia')

_ia_module = False
_process_question = None
_get_status = None
_get_proactive_alerts = None
_set_session_role = None
_get_session_info = None

try:
    from ia.agent import (
        process_question, get_status, get_proactive_alerts,
        set_session_role, get_session_info
    )
    _process_question = process_question
    _get_status = get_status
    _get_proactive_alerts = get_proactive_alerts
    _set_session_role = set_session_role
    _get_session_info = get_session_info
    _ia_module = True
    # logging: ia_agent ok
except Exception as e:  # ia.agent not available
    try:
        from ia_assistant import (
            process_question, get_status, get_proactive_alerts,
            set_session_role, get_session_info
        )
        _process_question = process_question
        _get_status = get_status
        _get_proactive_alerts = get_proactive_alerts
        _set_session_role = set_session_role
        _get_session_info = get_session_info
        _ia_module = True
    except Exception as e2:
        _ia_module = False

# Importar memoria persistente
_mem_module = False
try:
    from ia.memory import (save as mem_save, recall as mem_recall,
        search as mem_search, forget as mem_forget, get_summary as mem_summary,
        extract_and_save as mem_extract, get_enriched_context as mem_context)
    _mem_module = True
    # logging: memoria ok
except Exception:
    _mem_module = False



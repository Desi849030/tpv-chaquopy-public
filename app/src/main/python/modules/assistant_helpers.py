
# Imports de memoria IA
try:
    from ia.memory_advanced import extract_and_save, get_enriched_context
    mem_extract = extract_and_save
    mem_context = get_enriched_context
except Exception:
    mem_extract = None
    mem_context = None
# -*- coding: utf-8 -*-
"""ia_assistant_modules.py - TPV Smart v1.2 - Compatible con ia_agent.py + memoria persistente"""
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





# Stubs de memoria para assistant
def mem_save(session_id, key, value):
    try:
        from ia.memory import save_memory
        return save_memory(session_id, key, value)
    except:
        return False

def mem_recall(session_id, key=None):
    try:
        from ia.memory import recall_memory
        return recall_memory(session_id, key)
    except:
        return {}

def mem_search(query, limit=10):
    try:
        from ia.memory import search_memory
        return search_memory(query, limit)
    except:
        return []

def mem_forget(session_id, key=None):
    try:
        from ia.memory import forget_memory
        return forget_memory(session_id, key)
    except:
        return False

def mem_summary(session_id):
    try:
        return {"session_id": session_id, "entries": 0}
    except:
        return {}

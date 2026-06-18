"""Facade: ia_agent -> ia.agent (compatibilidad con settings_other.py)"""
from ia.agent import process_question

P = print; M = F = O = lambda x: x
fmt_money = lambda x: f"${x:,.2f}"; pct = lambda x: f"{x}%"

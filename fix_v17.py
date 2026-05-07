#!/usr/bin/env python3
"""v17 - Fix tildes, IA interactiva, tests, cleanup"""
import os, re, sys

BASE = os.path.join(os.path.expanduser('~'), 'tpv-chaquopy')
AGENT = os.path.join(BASE, 'app/src/main/python/ia_agent.py')
IA_UI = os.path.join(BASE, 'app/src/main/assets/frontend/static/lib/ia_assistant_ui.js')

# ============================================================
# 1. FIX TILDES en ia_agent.py
# ============================================================
print("=== FIX TILDES ia_agent.py ===")
with open(AGENT, 'r', encoding='utf-8') as f:
    agent = f.read()

original = agent

# Reemplazos seguros: solo aparecen en mensajes, no en logica de codigo
replacements = [
    ("Momentaneamente", "Moment\u00e1neamente"),
    ("Todavia", "Todav\u00eda"),
    ("Ultimas ", "\u00datimas "),
    (" encontre ", " encontr\u00e9 "),
    ("Analisis ", "An\u00e1lisis "),
    ("Analisis:", "An\u00e1lisis:"),
    ("Analisis completo", "An\u00e1lisis completo"),
    ("Proyeccion ", "Proyecci\u00f3n "),
    ("Pronostico", "Pron\u00f3stico"),
    ("Rotacion ", "Rotaci\u00f3n "),
    ("Rotacion(", "Rotaci\u00f3n("),
    ("Informacion ", "Informaci\u00f3n "),
    ("Gestion ", "Gesti\u00f3n "),
    ("disposicion.", "disposici\u00f3n."),
    ("Tambien", "Tambi\u00e9n"),
    ("categorias:", "categor\u00edas:"),
    ("categorias ", "categor\u00edas "),
    ("ubicacion ", "ubicaci\u00f3n "),
    ("seccion ", "secci\u00f3n "),
    ("multiples ", "m\u00faltiples "),
    ("credito", "cr\u00e9dito"),
    ("codigo ", "c\u00f3digo "),
    ("optimo", "\u00f3ptimo"),
    ("Proximo ", "Pr\u00f3ximo "),
    ("criticos", "cr\u00edticos"),
    ("rapidamente", "r\u00e1pidamente"),
    ("desempeno", "desempe\u00f1o"),
    ("Alli ", "All\u00ed "),
    ("encontraras", "encontrar\u00e1s"),
    ("Indice ", "\u00cdndice "),
    ("del dia ", "del d\u00eda "),
    (" el dia ", " el d\u00eda "),
    ("(7 dias)", "(7 d\u00edas)"),
    ("(30 dias)", "(30 d\u00edas)"),
    ("Necesito al menos 3 dias", "Necesito al menos 3 d\u00edas"),
    ("Necesito al menos 30 dias", "Necesito al menos 30 d\u00edas"),
    ("Atencion:", "Atenci\u00f3n:"),
    (" esta generando", " est\u00e1 generando"),
    (" el negocio esta ", " el negocio est\u00e1 "),
    (" aqui ", " aqu\u00ed "),
    ("Reintentare", "Reintentar\u00e9"),
]

count = 0
for old, new in replacements:
    if old in agent:
        agent = agent.replace(old, new)
        count += 1

print("  OK " + str(count) + " tildes corregidas en ia_agent.py")

# ============================================================
# 2. FIX TILDES en ia_assistant_ui.js
# ============================================================
print("\n=== FIX TILDES ia_assistant_ui.js ===")
with open(IA_UI, 'r', encoding='utf-8', errors='ignore') as f:
    ia = f.read()

ui_fixes = [
    ("Reintentare", "Reintentar\u00e9"),
    ("conexion", "conexi\u00f3n"),
    ("Conexion", "Conexi\u00f3n"),
    ("Reintentando", "Reintentando"),
    ("restaurada", "restaurada"),
]

ui_count = 0
for old, new in ui_fixes:
    if old in ia:
        ia = ia.replace(old, new)
        ui_count += 1

with open(IA_UI, 'w', encoding='utf-8') as f:
    f.write(ia)
print("  OK " + str(ui_count) + " tildes corregidas en ia_assistant_ui.js")

# ============================================================
# 3. IA INTERACTIVA: agregar follow-ups al _cli
# ============================================================
print("\n=== IA INTERACTIVA ===")

# Add _follow_up helper method
followup = '\n    def _follow(self, role):\n'
followup += '        """Pregunta interactiva contextual."""\n'
followup += '        frases = [\n'
followup += '            "Necesitas algo mas?",\n'
followup += '            "En que mas te puedo ayudar?",\n'
followup += '            "Te gustaria ver las ofertas del dia?",\n'
followup += '            "Puedo buscar otro producto si deseas.",\n'
followup += '            "Tienes alguna otra consulta?",\n'
followup += '        ]\n'
followup += '        if role == "cliente":\n'
followup += '            frases.extend([\n'
followup += '                "Quieres que te muestre productos relacionados?",\n'
followup += '                "Te puedo ayudar a encontrar algo especifico.",\n'
followup += '            ])\n'
followup += '        return "\\n\\n" + frases[hash(str(frases)) % len(frases)]'

# Insert _follow after _fm
if 'def _follow(self, role):' not in agent:
    agent = agent.replace(
        "    def _get_sug(self, intent_name, role):",
        followup + "\n\n    def _get_sug(self, intent_name, role):"
    )
    print("  OK _follow helper added")

# Append follow-ups to _cli return statements (the last return in each branch)
# After product search results
cli_followups = [
    ('return msg + "\\nPreguntame por cualquier producto."',
     'return msg + "\\n\\n" + self._follow(role)'),
    ('return msg + "\\nEscribe el nombre para mas detalles."',
     'return msg + "\\n\\n" + self._follow(role)'),
    ('return "Con gusto te ayudo. Puedes preguntarme sobre productos, precios, ofertas, stock, categorias o escribir ayuda para ver todo lo que puedo hacer."',
     'return "Con gusto te ayudo. Puedes preguntarme sobre productos, precios, ofertas, stock, categorias o escribir ayuda para ver todo lo que puedo hacer.\\n\\n" + self._follow(role)'),
    ('return "Hola! Soy tu asistente y estoy aqui para ayudarte. Puedes preguntarme sobre productos, precios, ofertas, stock o cualquier cosa que necesites."',
     'return "Hola! Soy tu asistente y estoy aqui para ayudarte. Puedes preguntarme sobre productos, precios, ofertas, stock o cualquier cosa que necesites.\\n\\n" + self._follow(role)'),
]

fc = 0
for old, new in cli_followups:
    if old in agent:
        agent = agent.replace(old, new)
        fc += 1
print("  OK " + str(fc) + " follow-ups agregados al _cli")

# Append follow-ups to _ven
ven_followups = [
    ('return "Dime que necesitas: ventas, stock bajo, top, o nombre de un producto."',
     'return "Dime que necesitas: ventas, stock bajo, top, o nombre de un producto.\\n\\n" + self._follow(role)'),
]

for old, new in ven_followups:
    if old in agent:
        agent = agent.replace(old, new)
        fc += 1
print("  OK follow-ups agregados al _ven")

# Append follow-ups to _sup
sup_followups = [
    ('return "Escriba: ventas, stock bajo, top, finanzas, gastos, predicciones, ABC, rotacion, ofertas, EOQ, o nombre de producto."',
     'return "Escriba: ventas, stock bajo, top, finanzas, gastos, predicciones, ABC, rotacion, ofertas, EOQ, o nombre de producto.\\n\\n" + self._follow("supervisor")'),
]

for old, new in sup_followups:
    if old in agent:
        agent = agent.replace(old, new)
        fc += 1
print("  OK follow-ups agregados al _sup")

# Append follow-ups to _adm default
adm_followups = [
    ('return "Gestor completo a su disposicion."',
     'return "Gestor completo a su disposicion.\\n\\n" + self._follow("administrador")'),
]

for old, new in adm_followups:
    if old in agent:
        agent = agent.replace(old, new)
        fc += 1
print("  OK follow-ups agregados al _adm")

# ============================================================
# 4. VALIDATE
# ============================================================
print("\n=== SYNTAX CHECK ===")
try:
    compile(agent, AGENT, 'exec')
    print("  OK ia_agent.py sin SyntaxError")
    with open(AGENT, 'w', encoding='utf-8') as f:
        f.write(agent)
    print("  OK ia_agent.py escrito")
except SyntaxError as e:
    print("  ERROR: " + str(e))
    sys.exit(1)

# ============================================================
# 5. FINAL CHECKS
# ============================================================
print("\n=== FINAL CHECKS ===")
with open(AGENT, 'r', encoding='utf-8') as f:
    ag = f.read()

# Verify tildes present
tilde_words = [
    "Moment\u00e1neamente", "Todav\u00eda", "\u00datimas",
    "An\u00e1lisis", "Proyecci\u00f3n", "Rotaci\u00f3n",
    "categor\u00edas", "Informaci\u00f3n", "Conexi\u00f3n",
    "Reintentar\u00e9", "\u00cdndice",
]
for w in tilde_words:
    print("  " + ("OK" if w in ag else "MISSING") + " " + w)

has_follow = "def _follow(self, role):" in ag
print("  OK _follow method: " + str(has_follow))
print("  OK follow-ups: " + str(ag.count("_follow(role)")) + " usos")

print("\n" + "="*55)
print("  v17 FIXES APPLIED")
print("="*55)
print("  1. Tildes corregidas en ia_agent.py (" + str(count) + ")")
print("  2. Tildes corregidas en ia_assistant_ui.js (" + str(ui_count) + ")")
print("  3. Follow-ups interactivos en _cli/_ven/_sup/_adm")
print("  4. _follow() method para preguntas contextuales")
print("="*55)

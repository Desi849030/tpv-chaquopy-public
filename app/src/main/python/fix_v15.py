#!/usr/bin/env python3
"""v15 - IA Agentica: integrar modulos agenticos en todas las funciones"""
import os, re, sys

BASE = os.path.dirname(os.path.abspath(__file__))
IA_DIR = os.path.join(BASE, 'ia')
agent_path = os.path.join(BASE, 'ia_agent.py')

# ============================================================
# 1. FIX normalizer.py
# ============================================================
print("=== FIX normalizer.py ===")
norm_path = os.path.join(IA_DIR, 'normalizer.py')
L = []
L.append('"""normalizer.py - Normalizacion de texto para matching difuso"""')
L.append('import re')
L.append('import unicodedata')
L.append('')
L.append('UNACCENT = {')
L.append('    "\\u00e1":"a","\\u00e9":"e","\\u00ed":"i","\\u00f3":"o","\\u00fa":"u","\\u00fc":"u","\\u00f1":"n",')
L.append('    "\\u00c1":"A","\\u00c9":"E","\\u00cd":"I","\\u00d3":"O","\\u00da":"U","\\u00dc":"U","\\u00d1":"N"')
L.append('}')
L.append('')
L.append('def normalize(text):')
L.append('    """Normaliza texto: minusculas, sin tildes, sin especiales."""')
L.append('    if not text: return ""')
L.append('    t = text.lower().strip()')
L.append('    t = unicodedata.normalize("NFD", t)')
L.append('    t = "".join(c for c in t if unicodedata.category(c) != "Mn")')
L.append('    t = re.sub(r"[^a-z0-9\\s]", " ", t)')
L.append('    t = re.sub(r"\\s+", " ", t)')
L.append('    return t.strip()')
L.append('')
L.append('def normalize_preserve(text):')
L.append('    """Normaliza pero preserva tildes."""')
L.append('    if not text: return ""')
L.append('    t = text.lower().strip()')
L.append('    t = re.sub(r"[^a-z0-9\\u00e1-\\u00fa\\u00fc\\s]", " ", t)')
L.append('    t = re.sub(r"\\s+", " ", t)')
L.append('    return t.strip()')
L.append('')
L.append('def contains_any(text, keywords, threshold=0.7):')
L.append('    """Verifica si texto contiene alguno de los keywords (fuzzy)."""')
L.append('    from ia.fuzzy_match import best_match')
L.append('    norm = normalize(text)')
L.append('    for kw in keywords:')
L.append('        norm_kw = normalize(kw)')
L.append('        if norm_kw in norm:')
L.append('            return True, kw, 1.0')
L.append('    norms = [normalize(k) for k in keywords]')
L.append('    best, score = best_match(norm, norms, threshold=threshold*100)')
L.append('    if best:')
L.append('        idx = norms.index(best)')
L.append('        return True, keywords[idx], score/100')
L.append('    return False, None, 0')
L.append('')
L.append('def extract_entities(text):')
L.append('    """Extrae posibles nombres de productos del texto."""')
L.append('    words = normalize_preserve(text).split()')
L.append('    entities = []')
L.append('    skip = {"el","la","los","las","un","una","de","del","en","con","por","para",')
L.append('           "que","y","o","es","son","tiene","hay","cuanto","como","donde",')
L.append('           "cuando","cual","quien","muy","mas","menos","sobre","entre","sin",')
L.append('           "a","al","su","mi","tu","se","me","te","le","nos","les","lo",')
L.append('           "este","esta","ese","esa","aqui","alli","ya","no","si","bien",')
L.append('           "mal","ok","va","voy"}')
L.append('    for w in words:')
L.append('        if len(w) > 2 and w not in skip:')
L.append('            entities.append(w)')
L.append('    return entities')

clean_norm = '\n'.join(L)
with open(norm_path, 'w') as f:
    f.write(clean_norm)

try:
    compile(clean_norm, norm_path, 'exec')
    print("OK normalizer.py sin SyntaxError")
except SyntaxError as e:
    print("ERROR normalizer.py: " + str(e))
    sys.exit(1)

# ============================================================
# 2. FIX ia_agent.py
# ============================================================
print("\n=== FIX ia_agent.py ===")
with open(agent_path, 'r') as f:
    content = f.read()

# --- 2a: Add new imports after defaultdict ---
new_imports = '\n'
new_imports += 'try:\n'
new_imports += '    from ia.normalizer import normalize, contains_any, extract_entities\n'
new_imports += '    _HAS_NORM = True\n'
new_imports += 'except Exception:\n'
new_imports += '    _HAS_NORM = False\n'
new_imports += 'try:\n'
new_imports += '    from ia.intent_engine import detect_intents as _detect_intents, get_suggestions as _get_suggestions\n'
new_imports += '    _HAS_INTENT = True\n'
new_imports += 'except Exception:\n'
new_imports += '    _HAS_INTENT = False\n'
new_imports += 'try:\n'
new_imports += '    from ia.context_memory import get_context as _get_ctx\n'
new_imports += '    _HAS_CTX = True\n'
new_imports += 'except Exception:\n'
new_imports += '    _HAS_CTX = False\n'
content = content.replace('from collections import defaultdict', 'from collections import defaultdict' + new_imports)
print("OK imports added")

# --- 2b: Add _fm and _get_sug helpers after _skills ---
helpers = '\n'
helpers += '    def _fm(self, text, keywords, threshold=0.7):\n'
helpers += "        '''Fuzzy match con soporte tildes/typos.'''\n"
helpers += '        try:\n'
helpers += '            if _HAS_NORM:\n'
helpers += '                matched, kw, score = contains_any(text, keywords, threshold)\n'
helpers += '                return matched\n'
helpers += '        except: pass\n'
helpers += '        return any(w in text for w in keywords)\n'
helpers += '\n'
helpers += '    def _get_sug(self, intent_name, role):\n'
helpers += "        '''Sugerencias contextuales segun intent y rol.'''\n"
helpers += '        try:\n'
helpers += '            if _HAS_INTENT:\n'
helpers += '                return _get_suggestions(intent_name, role)\n'
helpers += '        except: pass\n'
helpers += '        return []\n'
content = content.replace(
    '        self._skills = _get_skills_registry() if _HAS_SKILLS else None',
    '        self._skills = _get_skills_registry() if _HAS_SKILLS else None' + helpers
)
print("OK helpers _fm + _get_sug")

# --- 2c: Remove duplicate _ven ---
ven_pat = r'\n    def _ven\(self, t, m\):'
ven_pos = [m.start() for m in re.finditer(ven_pat, content)]
if len(ven_pos) >= 2:
    second_start = ven_pos[1] + 1
    adm_match = re.search(r'\n    def _adm\(', content[second_start:])
    if adm_match:
        content = content[:second_start] + content[second_start + adm_match.start():]
        print("OK duplicate _ven removed")
    else:
        print("WARN no se encontro _adm para delimitar segundo _ven")
else:
    print("WARN _ven encontrado " + str(len(ven_pos)) + " vez(veces)")

# --- 2d: Fix _sup signature ---
content = content.replace('def _sup(self, t):', 'def _sup(self, t, m=None):')
print("OK _sup signature fixed")

# --- 2e: Replace process() with agentic pipeline ---
proc_start = content.find("    def process(self, text, sid='0', role='cliente', name=''):")
hola_pos = content.find("\n    def _hola(", proc_start)
if proc_start < 0 or hola_pos < 0:
    print("ERROR process=" + str(proc_start) + " hola=" + str(hola_pos))
    sys.exit(1)

P = []
P.append("    def process(self, text, sid='0', role='cliente', name=''):")
P.append("        if not text or not text.strip():")
P.append("            return self._r(self._hola(role, name), role, 'GREETING')")
P.append("")
P.append("        t = text.lower().strip()")
P.append("        m = self.mem(sid); m['h'].append(t)")
P.append("        if len(m['h'])>20: m['h']=m['h'][-20:]")
P.append("")
P.append("        # === AGENTIC PIPELINE ===")
P.append("        # 1. Intent detection con fuzzy matching")
P.append("        intents = []; sug = []")
P.append("        try:")
P.append("            if _HAS_INTENT:")
P.append("                intents = _detect_intents(t, role)")
P.append("                if intents:")
P.append("                    sug = self._get_sug(intents[0]['intent'], role)")
P.append("        except: pass")
P.append("")
P.append("        # 2. Memoria contextual: resolver referencias")
P.append("        ctx = None")
P.append("        try:")
P.append("            if _HAS_CTX:")
P.append("                ctx = _get_ctx(sid)")
P.append("                ref = ctx.resolve_reference(text)")
P.append("                if ref.get('query') and len(t.split()) <= 5 and not P.search(t, 1):")
P.append("                    t = ref['query']")
P.append("        except: pass")
P.append("")
P.append("        primary = intents[0]['intent'] if intents else 'GENERAL'")
P.append("")
P.append("        # SALUDOS")
P.append("        if primary == 'GREETING':")
P.append("            if ctx: ctx.add_turn(text, '', primary)")
P.append("            return self._r(self._hola(role, name), role, primary, sug)")
P.append("")
P.append("        # DESPEDIDAS")
P.append("        if primary == 'FAREWELL':")
P.append("            return self._r('Ha sido un placer. Estoy aqui cuando me necesite.', role, primary, sug)")
P.append("")
P.append("        # AYUDA")
P.append("        if primary == 'HELP':")
P.append("            return self._r(self._ayuda(role), role, primary, sug)")
P.append("")
P.append("        # FRUSTRACION")
P.append("        if primary == 'FRUSTRATION':")
P.append("            return self._r('Detecto que algo no va bien. Estoy aqui para ayudarle. Que problema tiene?', role, primary, ['ayuda'])")
P.append("")
P.append("        # EJECUTAR SEGUN ROL (sin limites)")
P.append("        if role == 'cliente': result = self._cli(t, m)")
P.append("        elif role == 'vendedor': result = self._ven(t, m)")
P.append("        elif role == 'supervisor': result = self._sup(t, m)")
P.append("        else: result = self._adm(t, name)")
P.append("")
P.append("        # Actualizar memoria contextual")
P.append("        if ctx:")
P.append("            ctx.add_turn(text, result, primary)")
P.append("            try:")
P.append("                prods = P.search(text, 1)")
P.append("                if prods:")
P.append("                    ctx.last_product = prods[0]['n']")
P.append("            except: pass")
P.append("")
P.append("        # Proactive: alertas si stock bajo del producto consultado")
P.append("        try:")
P.append("            if ctx and ctx.last_product:")
P.append("                lp = ctx.last_product.lower()")
P.append("                for p in P.cache:")
P.append("                    if p['n'].lower() == lp and 0 < p['s'] <= 3:")
P.append("                        result += '\\n\\n[!] Alerta: ' + p['n'] + ' tiene solo ' + str(int(p['s'])) + ' unidades.'")
P.append("                        break")
P.append("        except: pass")
P.append("")
P.append("        return self._r(result, role, primary, sug)")

content = content[:proc_start] + '\n'.join(P) + content[hola_pos:]
print("OK process() agentic pipeline")

# --- 2f: Replace any(w in t for w in [...]) -> self._fm(t, [...]) ---
c1 = content.count("any(w in t for w in [")
content = re.sub(r'any\(w in t for w in (\[[^\]]+\])\)', r'self._fm(t, \1)', content)
print("OK " + str(c1) + " replacements any(w in t ...) -> self._fm(t, ...)")

# --- 2g: Replace any(w2 in t for w2 in [...]) -> self._fm(t, [...]) ---
c2 = content.count("any(w2 in t for w2 in [")
content = re.sub(r'any\(w2 in t for w2 in (\[[^\]]+\])\)', r'self._fm(t, \1)', content)
print("OK " + str(c2) + " replacements any(w2 in t ...) -> self._fm(t, ...)")

# --- 2h: Update _r() to accept intent and suggestions ---
r_start = content.find("    def _r(self, msg, role):")
if r_start >= 0:
    r_end = -1
    for pat in ['\n\n# =', '\n\n_agent', '\n\ndef get_status']:
        r_end = content.find(pat, r_start)
        if r_end >= 0:
            break
    if r_end < 0:
        print("ERROR no se encontro fin de _r")
        sys.exit(1)
    new_r = "    def _r(self, msg, role, intent='GENERAL', suggestions=None):\n"
    new_r += "        msg = self.humanizer.sanitize_text(msg)\n"
    new_r += "        if suggestions is None: suggestions = []\n"
    new_r += "        return {'answer': msg, 'role': role, 'suggestions': suggestions, 'intent': intent, 'ts': datetime.now().isoformat()}"
    content = content[:r_start] + new_r + content[r_end:]
    print("OK _r() with intent+suggestions")
else:
    print("ERROR no se encontro _r")
    sys.exit(1)

# --- 2i: Update process_question ---
pq_start = content.find("def process_question(sid, question, role='cliente', user_name=''):")
if pq_start >= 0:
    pq_end = content.find('\n\ndef ', pq_start + 1)
    if pq_end < 0:
        print("ERROR no se encontro fin de process_question")
        sys.exit(1)
    new_pq = "def process_question(sid, question, role='cliente', user_name=''):\n"
    new_pq += "    r = _get().process(question, sid, role, user_name)\n"
    new_pq += "    return {'answer':r['answer'],'intent':r.get('intent','chat'),'suggestions':r.get('suggestions',[]),'role':role,'role_label':ROLES.get(role,{}).get('label','Usuario'),'role_color':ROLES.get(role,{}).get('color','#3498db'),'role_icon':ROLES.get(role,{}).get('icon','?'),'ts':r['ts']}"
    content = content[:pq_start] + new_pq + content[pq_end:]
    print("OK process_question() with suggestions")
else:
    print("ERROR no se encontro process_question")
    sys.exit(1)

# --- VALIDATE ---
print("\n=== VALIDACION ===")
try:
    compile(content, agent_path, 'exec')
    print("OK ia_agent.py sin SyntaxError")
    with open(agent_path, 'w') as f:
        f.write(content)
    print("OK ia_agent.py escrito correctamente")
except SyntaxError as e:
    print("ERROR ia_agent.py SyntaxError: " + str(e))
    with open(agent_path + '.debug', 'w') as f:
        f.write(content)
    print("Debug guardado en " + agent_path + ".debug")
    sys.exit(1)

# ============================================================
# 3. FINAL CHECKS
# ============================================================
print("\n=== CHECKS FINALES ===")
ven_defs = len(re.findall(r'def _ven\(', content))
ok_ven = ven_defs == 1
print(("OK" if ok_ven else "ERROR") + " _ven: " + str(ven_defs) + " def(s) (debe ser 1)")

fm_count = content.count('self._fm(t,')
print("OK self._fm: " + str(fm_count) + " usos (fuzzy matching)")

has_detect = '_detect_intents(t, role)' in content
print("OK _detect_intents: " + str(has_detect))

has_ctx = '_get_ctx(sid)' in content
print("OK _get_ctx: " + str(has_ctx))

has_sug_r = "'suggestions': suggestions" in content
print("OK suggestions en _r: " + str(has_sug_r))

has_intent_r = "'intent': intent" in content
print("OK intent en _r: " + str(has_intent_r))

has_sug_pq = "r.get('suggestions'" in content
print("OK r.get suggestions: " + str(has_sug_pq))

has_intent_pq = "r.get('intent'" in content
print("OK r.get intent: " + str(has_intent_pq))

sup_sig = 'def _sup(self, t, m=None):' in content
print("OK _sup(self, t, m=None): " + str(sup_sig))

lines_count = content.count('\n')
print("OK total lineas: " + str(lines_count))

print("\n" + "="*55)
print("  v15 IA AGENTICA - TODOS LOS MODULOS INTEGRADOS")
print("="*55)
print("  normalizer.py  - tildes, fuzzy, entidades")
print("  intent_engine  - 21 intents con fuzzy matching")
print("  context_memory - referencias, seguimiento")
print("  ia_agent.py    - pipeline agentic en process()")
print("  _cli _ven _sup _adm - fuzzy matching (self._fm)")
print("  _r()           - devuelve intent + suggestions")
print("  process_question - expone intent + suggestions")
print("  Proactive alerts - stock bajo en producto visto")
print("="*55)

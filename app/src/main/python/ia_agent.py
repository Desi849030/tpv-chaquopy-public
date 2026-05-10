from reasoning_engine import ReActEngine
from ia.nlp_engine import NLPEngine
"""ia_agent.py v1.0 - TPV Smart - Gestor Total Conversacional"""
from ia.guardrails import Guardrails
from ia.session_context import SessionContext
from ia.guide_manager import GuideManager
from ia.humanizer import Humanizer
import sqlite3, re, os, random, threading, time, math
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from collections import defaultdict
try:
    from ia.normalizer import normalize, contains_any, extract_entities
    _HAS_NORM = True
except Exception:
    _HAS_NORM = False
try:
    from ia.intent_engine import detect_intents as _detect_intents, get_suggestions as _get_suggestions
    _HAS_INTENT = True
except Exception:
    _HAS_INTENT = False
try:
    from ia.context_memory import get_context as _get_ctx
    _HAS_CTX = True
except Exception:
    _HAS_CTX = False


try:
    from ia.skills import get_registry as _get_skills_registry
    _HAS_SKILLS = True
except Exception:
    _HAS_SKILLS = False

try:
    from ia.memory import (save as _mem_save, recall as _mem_recall,
        search as _mem_search, extract_and_save as _mem_extract,
        get_enriched_context as _mem_context)
    _HAS_MEM = True
except Exception:
    _HAS_MEM = False
try:
    from ia.anti_slop import refine as _anti_slop

    _HAS_ANTI_SLOP = True
except Exception:
    _HAS_ANTI_SLOP = False

def _db():
    for p in ['tpv_datos.db', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tpv_datos.db')]:
        if os.path.exists(p):
            c = sqlite3.connect(p, timeout=3, check_same_thread=False)
            c.row_factory = sqlite3.Row
            return c
    return None

def q(sql, params=(), one=False):
    c = _db()
    if not c: return None
    try:
        cur = c.execute(sql, params)
        return cur.fetchone() if one else cur.fetchall()
    except: return None

class P:
    cache = []; ct = 0; cats = []
    @classmethod
    def refresh(cls):
        if cls.cache and time.time()-cls.ct < 20: return
        c = _db()
        if not c: return
        prods = []
        for r in c.execute("SELECT nombre,precio_venta as precio,precio_compra as costo,categoria,stock_actual,unidad_medida FROM inventario_general").fetchall():
            prods.append({'n':r[0] or '','p':float(r[1] or 0),'c':float(r[2] or 0),'cat':r[3] or 'General','s':float(r[4] or 0),'u':r[5] or 'Un'})
        names = {p['n'].lower() for p in prods}
        for r in c.execute("SELECT nombre,precio_venta,precio_compra,categoria,stock_actual,unidad_medida FROM inventario_general").fetchall():
            if (r[0] or '').lower() not in names:
                prods.append({'n':r[0] or '','p':float(r[1] or 0),'c':float(r[2] or 0),'cat':r[3] or 'General','s':float(r[4] or 0),'u':r[5] or 'Un'})
        cls.cache = prods; cls.ct = time.time()
        cls.cats = sorted(set(p['cat'] for p in prods))
    
    @classmethod
    def search(cls, query, limit=10):
        cls.refresh()
        qr = query.lower().strip()
        if len(qr)<2: return []
        sc = []
        for p in cls.cache:
            s = 0; nl = p['n'].lower()
            if qr == nl: s = 100
            elif qr in nl: s = 85
            elif nl in qr: s = 70
            else:
                for w in qr.split():
                    if len(w)<2: continue
                    if w in nl: s += 30
                    for nw in nl.split():
                        if len(nw)>=3 and SequenceMatcher(None,w,nw).ratio()>0.7: s += 20
            if s>0: sc.append((s,p))
        sc.sort(key=lambda x:x[0], reverse=True)
        return [x[1] for x in sc[:limit]]

class M:
    @staticmethod
    def regresion(x, y):
        n = len(x)
        if n<2: return 0,0
        sx, sy = sum(x), sum(y)
        sxy = sum(x[i]*y[i] for i in range(n))
        sx2 = sum(v*v for v in x)
        m = (n*sxy - sx*sy)/(n*sx2 - sx*sx) if (n*sx2 - sx*sx)!=0 else 0
        return m, (sy-m*sx)/n
    
    @staticmethod
    def eoq(d, p, m):
        return math.sqrt((2*d*p)/m) if m>0 else 0
    
    @staticmethod
    def punto_eq(cf, p, cv):
        return math.ceil(cf/(p-cv)) if (p-cv)>0 else float('inf')
    
    @staticmethod
    def roi(inv, gan):
        return ((gan-inv)/inv)*100 if inv>0 else 0

class F:
    @staticmethod
    def diario():
        d = q("SELECT COUNT(*) t, COALESCE(SUM(total),0) r, COALESCE(AVG(total),0) a FROM historial_ventas WHERE DATE(fecha)=DATE('now','localtime')", one=True)
        g = q("SELECT COALESCE(SUM(monto),0) g FROM gastos WHERE DATE(fecha)=DATE('now','localtime')", one=True)
        return {'t':d['t'] if d else 0,'r':d['r'] if d else 0,'a':d['a'] if d else 0,'g':g['g'] if g else 0}
    
    @staticmethod
    def semanal():
        d = q("SELECT COUNT(*) t, COALESCE(SUM(total),0) r FROM historial_ventas WHERE fecha>=DATE('now','-7 days')", one=True)
        return {'t':d['t'] if d else 0,'r':d['r'] if d else 0}
    
    @staticmethod
    def top(días=7, lim=5):
        return q(f"SELECT nombre,SUM(cantidad) q,SUM(total) t FROM historial_ventas WHERE fecha>=DATE('now','-{dias} days') GROUP BY nombre ORDER BY q DESC LIMIT {lim}")
    
    @staticmethod
    def abc():
        rows = q("SELECT nombre,SUM(total) rev FROM historial_ventas WHERE fecha>=DATE('now','-30 days') GROUP BY nombre ORDER BY rev DESC LIMIT 30")
        if not rows: return {'A':[],'B':[],'C':[]}
        total = sum(r['rev'] for r in rows)
        if total==0: return {'A':[],'B':[],'C':[]}
        abc = {'A':[],'B':[],'C':[]}; cum = 0
        for r in rows:
            cum += r['rev']; pct = cum/total*100
            if pct<=80: abc['A'].append(r['nombre'])
            elif pct<=95: abc['B'].append(r['nombre'])
            else: abc['C'].append(r['nombre'])
        return abc

class O:
    @staticmethod
    def mejores():
        deals = []
        for p in P.cache:
            if p['p']>0 and p['c']>0 and p['s']>=10:
                m = (p['p']-p['c'])/p['p']*100
                if m>30:
                    deals.append({'n':p['n'],'p':p['p'],'d':p['p']*0.85,'m':m,'s':p['s']})
        return sorted(deals, key=lambda x:x['m'], reverse=True)[:5]
    
    @staticmethod
    def relaciónados(prod, lim=3):
        return q(f"SELECT b.nombre,COUNT(*) f FROM historial_ventas a JOIN historial_ventas b ON a.venta_id=b.venta_id AND a.nombre!=b.nombre WHERE a.nombre LIKE ? AND DATE(a.fecha)>=DATE('now','-30 days') GROUP BY b.nombre ORDER BY f DESC LIMIT {lim}",('%'+prod+'%',))

def fmt_money(v): return f"${float(v):,.2f}" if v else "$0.00"
def pct(v): return f"{float(v):.1f}%"

class Agent:
    def __init__(self):
        self.ses = {}; self.lk = threading.Lock()
        self.nlp = NLPEngine()
        self.guard = Guardrails()
        self.memory = SessionContext()
        self.humanizer = Humanizer()
        self._mem_ok = _HAS_MEM
        self._as_ok = _HAS_ANTI_SLOP
        self._sk_ok = _HAS_SKILLS
        self._skills = _get_skills_registry() if _HAS_SKILLS else None
    def _fm(self, text, keywords, threshold=0.7):
        '''Fuzzy match con soporte tildes/typos.'''
        try:
            if _HAS_NORM:
                matched, kw, score = contains_any(text, keywords, threshold)
                return matched
        except: pass
        return any(w in text for w in keywords)


    def _follow(self, role):
        """Pregunta interactiva contextual."""
        frases = [
            "Necesitas algo mas?",
            "En que mas te puedo ayudar?",
            "Te gustaria ver las ofertas del día?",
            "Puedo buscar otro producto si deseas.",
            "Tienes alguna otra consulta?",
        ]
        if role == "cliente":
            frases.extend([
                "Quieres que te muestre productos relaciónados?",
                "Te puedo ayudar a encontrar algo específico.",
            ])
        return "\n\n" + frases[hash(str(frases)) % len(frases)]

    def _get_sug(self, intent_name, role):
        '''Sugerencias contextuales segun intent y rol.'''
        try:
            if _HAS_INTENT:
                return _get_suggestions(intent_name, role)
        except: pass
        return []

    
    def mem(self, sid):
        with self.lk:
            if sid not in self.ses: self.ses[sid] = {'h':[],'t':'','p':'','n':''}
            return self.ses[sid]
    
    def process(self, text, sid='0', role='cliente', name=''):
        if not text or not text.strip():
            return self._r(self._hola(role, name), role, 'GREETING')

        t = text.lower().strip()
        m = self.mem(sid); m['h'].append(t)
        if len(m['h'])>20: m['h']=m['h'][-20:]

        # === AGENTIC PIPELINE ===
        # 1. Intent detection con fuzzy matching
        intents = []; sug = []
        try:
            if _HAS_INTENT:
                intents = _detect_intents(t, role)
                if intents:
                    sug = self._get_sug(intents[0]['intent'], role)
        except: pass

        # 2. Memoria contextual: resolver referencias
        ctx = None
        try:
            if _HAS_CTX:
                ctx = _get_ctx(sid)
                ref = ctx.resolve_reference(text)
                if ref.get('query') and len(t.split()) <= 5 and not P.search(t, 1):
                    t = ref['query']
        except: pass

        primary = intents[0]['intent'] if intents else 'GENERAL'

        # SALUDOS
        if primary == 'GREETING':
            if ctx: ctx.add_turn(text, '', primary)
            return self._r(self._hola(role, name), role, primary, sug)

        # DESPEDIDAS
        if primary == 'FAREWELL':
            return self._r('Ha sido un placer. Estoy aquí cuándo me necesite.', role, primary, sug)

        # AYUDA
        if primary == 'HELP':
            return self._r(self._ayuda(role), role, primary, sug)

        # FRUSTRACION
        if primary == 'FRUSTRATION':
            return self._r('Detecto que algo no va bien. Estoy aquí para ayudarle. Que problema tiene?', role, primary, ['ayuda'])

        # EJECUTAR SEGUN ROL (sin limites)
        if role == 'cliente': result = self._cli(t, m)
        elif role == 'vendedor': result = self._ven(t, m)
        elif role == 'supervisor': result = self._sup(t, m)
        else: result = self._adm(t, name)

        # Actualizar memoria contextual
        if ctx:
            ctx.add_turn(text, result, primary)
            try:
                prods = P.search(text, 1)
                if prods:
                    ctx.last_product = prods[0]['n']
            except: pass

        # Proactive: alertas si stock bajo del producto consultado
        try:
            if ctx and ctx.last_product:
                lp = ctx.last_product.lower()
                for p in P.cache:
                    if p['n'].lower() == lp and 0 < p['s'] <= 3:
                        result += '\n\n[!] Alerta: ' + p['n'] + ' tiene solo ' + str(int(p['s'])) + ' unidades.'
                        break
        except: pass

        return self._r(result, role, primary, sug)
    def _hola(self, role, name):
        h = datetime.now().hour
        g = "Buenas noches" if h<6 else "Buenos días" if h<12 else "Buen mediodía" if h<14 else "Buenas tardes" if h<20 else "Buenas noches"
        n = f", {name}" if name else ""
        P.refresh()
        
        if role == 'cliente':
            of = O.mejores()
            msg = f"{g}{n}. Bienvenido a TPV Smart. Puede consultar productos, precios y ofertas. Si desea registrarse, solicite al administrador sus credenciales de acceso."
            if P.cache and len(P.cache)>0:
                msg += f" Hoy tenemos {len(P.cache)} productos disponibles. Le recomiendo aprovechar las ofertas."
            msg += " Escriba el nombre del producto que busca o consulte categorías."
            return msg
        
        if role == 'vendedor':
            d = F.diario()
            if d['t'] > 0:
                h2 = datetime.now().hour
                proy = d['r']/h2*24 if h2>0 else d['r']
                return f"{g}{n}. Al momento lleva {d['t']} ventas por {fmt_money(d['r'])}. Proyectamos cerrar el día en ~{fmt_money(proy)}. ¿En qué le ayudo?"
            return f"{g}{n}. Aún no hay ventas hoy. Revise el catálogo para ofrecer a sus clientes. ¿Necesita algo?"
        
        if role == 'supervisor':
            d = F.diario(); low = sum(1 for p in P.cache if 0<p['s']<=5)
            return f"{g}{n}. Panel de supervisión activo. {len(P.cache)} productos, {low} con stock bajo. Ventas hoy: {fmt_money(d['r'])}. ¿Qué desea revisar?"
        
        d = F.diario()
        low = sum(1 for p in P.cache if 0<p['s']<=5)
        out = sum(1 for p in P.cache if p['s']<=0)
        return f"{g}{n}. Sistema completo bajo su control. {len(P.cache)} productos activos, {low} requieren atención, {out} agotados. Ventas: {fmt_money(d['r'])}. Estoy a sus órdenes."
    
    def _ayuda(self, role):
        if role == 'cliente':
            return "Con gusto le ayudo. Puedo:\n• Buscar productos y precios\n• Mostrar las mejores ofertas\n• Recomendar productos complementarios\n• Ver todas las categorías\n\nDígame: 'busco café' o 'mejores ofertas'"
        if role == 'vendedor':
            return "Estoy para asistirle. Puedo:\n• Ver ventas del día y proyección\n• Consultar stock bajo\n• Top productos más vendidos\n• Buscar precios y márgenes\n\nDígame: 'ventas' o 'stock bajo' o 'café'"
        if role == 'supervisor':
            return "Panel de supervisión disponible:\n• Dashboard y KPIs\n• Tendencias de venta\n• Proyecciones\n• Estado de inventario\n\nDígame: 'dashboard' o 'tendencias'"
        return "Gestor completo a su servicio:\n\n💰 Finanzas: ingresos, gastos, ganancias, márgenes\n📊 Análisis: ABC, rotación, punto equilibrio\n🔮 Predicciones: regresión, proyecciones\n📦 Inventario: stock bajo, críticos\n🏷️ Ofertas inteligentes\n\nEjemplos: 'finanzas', 'ABC', 'predicciones', 'ofertas'"
    
    # ============================================================
    def _cli(self, t, m, role="cliente"):
        if self._fm(t, ["ayuda","que puedes","que haces","como funcióna","menú","opciónes"]):
            return "Puedo ayudarte con muchas cosas:\n\n- Buscar productos y precios\n- Ver ofertas y descuentos\n- Consultar stock disponible\n- Ver categorías del catalogo\n- Información de puntos y lealtad\n- Historial de compras\n\nEscribe lo que necesites."
        if self._fm(t, ["puntos","lealtad","fidelidad","recompensa","beneficio"]):
            return "Sistema de puntos activo. Cada compra acumula puntos que puedes canjear por descuentos y productos. Consulta tus puntos en la sección de Lealtad."
        if self._fm(t, ["mis compras","historial","compre","recibo","factura"]):
            return "Puedes ver tu historial de compras en la sección de Registros. Allí encontrarás todos los recibos con fecha, productos, cantidades y totales."
        if self._fm(t, ["pago","pagar","efectivo","tarjeta","transferencia","metodo"]):
            return "Aceptamos múltiples metodos de pago: efectivo, tarjeta de crédito/debito, transferencia bancaria y código QR."
        if self._fm(t, ["horario","abierto","cerrado","donde","ubicación","dirección"]):
            return "Consulte los detalles de horario y ubicación en la sección de Tienda."
        if self._fm(t, ["oferta","descuento","rebaja","mejor precio","barato","promo","promoción"]):
            of = O.mejores()
            if not of: return "Hoy todos nuestros precios son muy competitivos. Escribe el nombre de un producto."
            msg = "Ofertas disponibles:\n\n"
            for i,o in enumerate(of,1):
                ahorro = o["p"] - o["d"]
                msg += str(i) + ". " + o["n"] + ": " + fmt_money(o["d"]) + " (Normal: " + fmt_money(o["p"]) + " - Ahorras " + fmt_money(ahorro) + ")\n"
            return msg + "\nEscribe el nombre de cualquier producto para ver mas detalles."
        if self._fm(t, ["categorías","catalogo","que tienen","secciones","que venden","departamento"]):
            return "Contamos con " + str(len(P.cats)) + " categorías: " + ", ".join(P.cats[:15]) + ".\n\nEscribe el nombre de una categoría o producto."
        if self._fm(t, ["stock","disponible","cuanto hay","hay de","quedan","existencia"]):
            prods = P.search(t, 8)
            if prods:
                msg = "Disponibilidad:\n\n"
                for p in prods[:10]:
                    estado = str(p["s"]) + " " + p["u"] if p["s"] > 0 else "AGOTADO"
                    msg += "- " + p["n"] + ": " + estado + " - " + fmt_money(p["p"]) + "\n"
                return msg + "\n\n" + self._follow(role)
        prods = P.search(t, 8)
        if prods:
            m["p"] = prods[0]["n"]
            if len(prods)==1:
                p = prods[0]
                msg = p["n"] + ": " + fmt_money(p["p"]) + " por " + p["u"] + ".\n"
                if p["s"]==0:
                    msg += "Momentáneamente agotado. "
                    rel = O.relaciónados(p["n"],2)
                    if rel: msg += "Te sugiero: " + rel[0]["nombre"] + "."
                elif p["s"]<=3:
                    msg += "Útimas " + str(int(p["s"])) + " unidades disponibles."
                else:
                    msg += "Stock: " + str(int(p["s"])) + " " + p["u"] + ".\n"
                rel = O.relaciónados(p["n"],2)
                if rel: msg += "Te puede interesar: " + rel[0]["nombre"] + "."
                return msg
            msg = "Encontré " + str(len(prods)) + " resultados:\n\n"
            for p in prods[:10]:
                stock_info = " | " + str(int(p["s"])) + " " + p["u"] if p["s"] > 0 else " | AGOTADO"
                msg += "- " + p["n"] + ": " + fmt_money(p["p"]) + stock_info + "\n"
            return msg + "\n\n" + self._follow(role)
        if self._fm(t, ["hola","buenas","buenos días","buenas tardes","buenas noches","hey"]):
            return "Hola! Soy tu asistente y estoy aquí para ayudarte. Puedes preguntarme sobre productos, precios, ofertas, stock o cualquier cosa que necesites."
        return "Con gusto te ayudo. Puedes preguntarme sobre productos, precios, ofertas, stock, categorías o escribir ayuda para ver todo lo que puedo hacer."

    # ============================================================
    def _sup(self, t, m=None):
        d = F.diario(); w = F.semanal()
        low = sum(1 for p in P.cache if 0 < p["s"] <= 5)
        if self._fm(t, ["ayuda","que puedes","menú","opciónes"]):
            return "Como supervisor tienes acceso completo:\n\n- dashboard: KPIs\n- ventas: Resumen del día\n- stock bajo: Alertas\n- top: Más vendidos\n- finanzas: Balance y margen\n- gastos: Egresos\n- predicciones: Tendencias\n- rotación: Indice\n- ABC: Clasificacion\n- ofertas: Promociónes\n- Nombre de producto para info detallada"
        if self._fm(t, ["dashboard","resumen","estado","kpi"]):
            msg = "Dashboard:\n- Ventas hoy: " + fmt_money(d["r"]) + " (" + str(d["t"]) + " ops)\n- Ventas semana: " + fmt_money(w["r"]) + "\n- Ticket promedio: " + fmt_money(d["a"]) + "\n- Productos: " + str(len(P.cache)) + "\n- Stock bajo: " + str(low) + "\n- Categorias: " + str(len(P.cats))
            if d["t"] > 0:
                h = datetime.now().hour
                proy = d["r"]/h*24 if h > 0 else d["r"]
                msg += "\n- Proyección cierre: " + fmt_money(proy)
            return msg
        if self._fm(t, ["ventas","caja","recaudó","cuanto vendi","como voy"]):
            if d["t"] == 0: return "Aún no hay ventas hoy."
            h = datetime.now().hour
            proy = d["r"]/h*24 if h > 0 else d["r"]
            return "Ventas del día:\n- Ops: " + str(d["t"]) + "\n- Facturado: " + fmt_money(d["r"]) + "\n- Ticket: " + fmt_money(d["a"]) + "\n- Proyeccion: " + fmt_money(proy) + "\n- Gastos: " + fmt_money(d["g"]) + "\n- Ganancia: " + fmt_money(d["r"]-d["g"])
        if self._fm(t, ["stock bajo","agotado","critico","reabastecer","faltante"]):
            rows = q("SELECT nombre,stock_actual FROM inventario_general WHERE stock_actual<=5 AND stock_actual>=0 ORDER BY stock_actual LIMIT 500")
            if not rows: return "Todo en orden. No hay productos con stock bajo."
            msg = "Alerta: " + str(len(rows)) + " productos necesitan reabastecimiento:\n\n"
            for r in rows[:20]:
                icon = "X" if r["stock_actual"] == 0 else "!"
                msg += " [" + icon + "] " + r["nombre"] + ": " + str(int(r["stock_actual"])) + " uds\n"
            return msg + "\nDesea generar orden de pedido?"
        if self._fm(t, ["top","más vendido","popular","ranking","mejor","vendidos"]):
            top = F.top(7, 5)
            if not top: return "Aún no hay suficiente historial."
            msg = "Más vendidos (7 días):\n\n"
            for i, r in enumerate(top, 1):
                msg += str(i) + ". " + r["nombre"] + ": " + str(int(r["q"])) + " uds (" + fmt_money(r["t"]) + ")\n"
            return msg
        if self._fm(t, ["finanza","margen","gasto","ingreso","balance","ganancia","rentabilidad"]):
            prof = d["r"] - d["g"]
            margen = (prof/d["r"]*100) if d["r"] > 0 else 0
            return "Finanzas:\n\n- Ingresos: " + fmt_money(d["r"]) + "\n- Gastos: " + fmt_money(d["g"]) + "\n- Ganancia: " + fmt_money(prof) + "\n- Margen: " + pct(margen) + "\n- Ticket: " + fmt_money(d["a"])
        if self._fm(t, ["gasto","egreso","gastos","costo"]):
            rows = q("SELECT descripción,monto,categoria FROM gastos WHERE DATE(fecha)=DATE('now','localtime') ORDER BY monto DESC")
            if not rows: return "No hay gastos hoy."
            msg = "Gastos del día (" + str(len(rows)) + "):\n\n"
            total = 0
            for r in rows[:20]:
                msg += "- " + r["descripción"] + ": " + fmt_money(r["monto"]) + " (" + r["categoría"] + ")\n"
                total += r["monto"]
            return msg + "\nTotal: " + fmt_money(total)
        if self._fm(t, ["tendencia","prediccion","proyeccion","forecast","pronostico"]):
            proy = d["r"]*7 if d["r"] > 0 else w["r"]
            return "Proyección semanal: " + fmt_money(proy) + "\n- Ritmo diario: " + fmt_money(d["r"]) + "\n- Semana: " + fmt_money(w["r"])
        if self._fm(t, ["rotación","indice"]):
            cv = q("SELECT COALESCE(SUM(cantidad*costo),0) cv FROM historial_ventas WHERE fecha>=DATE('now','-30 days')", one=True)
            ip = sum(p["c"]*p["s"] for p in P.cache)/len(P.cache) if P.cache else 1
            rot = (cv["cv"]/ip) if ip > 0 else 0
            msg = "Rotación (30 días): " + str(round(rot, 2)) + " veces"
            if rot > 4: msg += "\nExcelente: inventario se renueva rapido."
            elif rot > 1: msg += "\nNormal: buen ritmo."
            else: msg += "\nBaja: considere promociónes."
            return msg
        if self._fm(t, ["abc","pareto","clasificacion"]):
            abc = F.abc()
            if not abc["A"]: return "Necesito al menos 30 días para análisis ABC."
            msg = "Análisis ABC:\n\n- A (80%): " + str(len(abc["A"])) + " productos"
            if abc["A"]: msg += "\n  Top: " + abc["A"][0]
            msg += "\n- B (15%): " + str(len(abc["B"])) + " productos"
            msg += "\n- C (5%): " + str(len(abc["C"])) + " productos"
            return msg
        if self._fm(t, ["eoq","lote óptimo","pedido óptimo"]):
            top = F.top(30, 1)
            if top:
                demanda = top[0]["q"]*12
                eoq = M.eoq(demanda, 50, 10)
                return "Lote óptimo " + top[0]["nombre"] + ":\n- EOQ: " + str(int(eoq)) + " uds/pedido\n- Demanda anual: " + str(int(demanda)) + " uds"
            return "Necesito más datos de ventas para EOQ."
        if self._fm(t, ["oferta","descuento","rebaja","promo"]):
            of = O.mejores()
            if not of: return "No hay productos con margen para ofertas."
            msg = "Productos para oferta:\n\n"
            for i, o in enumerate(of, 1):
                msg += str(i) + ". " + o["n"] + ": " + fmt_money(o["p"]) + " -> " + fmt_money(o["d"]) + " (" + pct(o["m"]) + ")\n"
            return msg
        prods = P.search(t, 10)
        if prods:
            m["p"] = prods[0]["n"]
            msg = "Productos:\n\n"
            for p in prods[:10]:
                mrg = ((p["p"]-p["c"])/p["p"]*100) if p["p"] > 0 and p["c"] > 0 else 0
                msg += "- " + p["n"] + ": " + fmt_money(p["p"]) + " | Stock: " + str(int(p["s"]))
                if mrg > 0: msg += " | Margen: " + pct(mrg)
                msg += "\n"
            return msg
        return "Escriba: ventas, stock bajo, top, finanzas, gastos, predicciones, ABC, rotación, ofertas, EOQ, o nombre de producto.\n\n" + self._follow("supervisor")

    def _ven(self, t, m):
        if self._fm(t, ["ventas","caja","recaudó","cuanto vendi","como voy"]):
            d = F.diario()
            if d["t"] == 0: return "Todavía no hay ventas hoy."
            h = datetime.now().hour
            proy = d["r"]/h*24 if h > 0 else d["r"]
            return "Al momento: " + str(d["t"]) + " ventas, " + fmt_money(d["r"]) + " facturados. Ticket promedio: " + fmt_money(d["a"]) + ". Proyección cierre: " + fmt_money(proy) + "."
        if self._fm(t, ["stock bajo","agotado","critico","reabastecer"]):
            rows = q("SELECT nombre,stock_actual FROM inventario_general WHERE stock_actual<=5 AND stock_actual>=0 ORDER BY stock_actual LIMIT 500")
            if rows:
                msg = "Atención: " + str(len(rows)) + " productos necesitan reabastecimiento:\n"
                for r in rows[:20]:
                    msg += "- " + r["nombre"] + ": " + str(int(r["stock_actual"])) + " uds\n"
                return msg + "\nDesea generar orden de pedido?"
            return "Todo en orden. No hay stock bajo."
        if self._fm(t, ["top","más vendido","popular","ranking"]):
            top = F.top(7, 5)
            if not top: return "Aún no hay historial suficiente esta semana."
            msg = "Más vendidos (7 días):\n"
            for i, r in enumerate(top, 1):
                msg += str(i) + ". " + r["nombre"] + ": " + str(int(r["q"])) + " uds (" + fmt_money(r["t"]) + ")\n"
            return msg
        prods = P.search(t, 10)
        if prods:
            m["p"] = prods[0]["n"]
            msg = "Productos:\n"
            for p in prods[:10]:
                mrg = ((p["p"]-p["c"])/p["p"]*100) if p["p"] > 0 and p["c"] > 0 else 0
                msg += "- " + p["n"] + ": " + fmt_money(p["p"]) + " | Stock: " + str(int(p["s"]))
                if mrg > 0: msg += " | Margen: " + pct(mrg)
                msg += "\n"
            return msg
        return "Dime que necesitas: ventas, stock bajo, top, o nombre de un producto.\n\n" + self._follow(role)



    def _adm(self, t, name):
        d = F.diario()
        low = sum(1 for p in P.cache if 0<p['s']<=5)
        n = f", {name}" if name else ""
        
        # FINANZAS COMPLETO
        if self._fm(t, ['finanza','margen','gasto','ingreso','balance','ganancia','comisión','rentabilidad']):
            prof = d['r'] - d['g']
            margen = (prof/d['r']*100) if d['r']>0 else 0
            comisión = d['r']*0.05 if d['r']>0 else 0
            
            msg = f"Estimado administrador{n}, aquí tiene el balance del día:\n\n"
            msg += f"💰 Ingresos por ventas: {fmt_money(d['r'])}\n"
            msg += f"🧾 Gastos registrados: {fmt_money(d['g'])}\n"
            msg += f"📊 Ganancia bruta: {fmt_money(prof)}\n"
            msg += f"📈 Margen neto: {pct(margen)}\n"
            msg += f"👥 Comisión estimada (5%): {fmt_money(comisión)}\n\n"
            
            if prof > d['g']*2:
                msg += "¡Excelente rentabilidad hoy! El negocio está generando buenas ganancias."
            elif prof > 0:
                msg += "Buen desempeño. Las ganancias cubren los gastos del día."
            else:
                msg += "Atención: los gastos superan los ingresos. Revise las finanzas."
            return msg
        
        # ABC
        if self._fm(t, ['abc','pareto','clasificacion']):
            abc = F.abc()
            if not abc['A']: return "Necesito al menos 30 días de ventas para el análisis ABC."
            msg = f"Análisis ABC de productos (últimos 30 días):\n\n"
            msg += f"🔴 A (80% ingresos): {len(abc['A'])} productos\n"
            if abc['A']: msg += f"   Top: {abc['A'][0]}\n"
            msg += f"🟡 B (siguiente 15%): {len(abc['B'])} productos\n"
            msg += f"🟢 C (último 5%): {len(abc['C'])} productos\n\n"
            msg += "Concéntrese en los productos A para maximizar ganancias."
            return msg
        
        # PUNTO EQUILIBRIO
        if self._fm(t, ['punto equilibrio','break even','umbral']):
            gf = d['g'] if d['g']>0 else 100
            pp = sum(p['p'] for p in P.cache)/len(P.cache) if P.cache else 10
            pc = sum(p['c'] for p in P.cache)/len(P.cache) if P.cache else 5
            pe = M.punto_eq(gf, pp, pc)
            msg = f"Punto de equilibrio diario:\n\n"
            msg += f"🎯 Necesita vender: {pe} unidades\n"
            msg += f"💰 Para cubrir: {fmt_money(gf)} de gastos fijos\n"
            msg += f"📦 Precio promedio: {fmt_money(pp)}\n"
            msg += f"📉 Costo promedio: {fmt_money(pc)}\n"
            return msg
        
        # EOQ
        if self._fm(t, ['eoq','lote óptimo','pedido óptimo']):
            top = F.top(30,1)
            if top:
                demanda = top[0]['q']*12
                eoq = M.eoq(demanda, 50, 10)
                msg = f"Lote óptimo para {top[0]['nombre']}:\n"
                msg += f"📦 EOQ: {eoq:.0f} unidades/pedido\n"
                msg += f"📊 Demanda anual estimada: {demanda:.0f} unidades\n"
                return msg
            return "Necesito más datos. Mientras más ventas se registren, más preciso será el cálculo."
        
        # PREDICCIONES
        if self._fm(t, ['prediccion','pronostico','proyeccion','forecast','tendencia']):
            rows = q("SELECT DATE(fecha) d,SUM(total) r FROM historial_ventas WHERE fecha>=DATE('now','-7 days') GROUP BY DATE(fecha) ORDER BY d")
            if rows and len(rows)>=3:
                x = list(range(len(rows))); y = [r['r'] for r in rows]
                m, b = M.regresion(x, y)
                prox = max(0, m*len(rows)+b)
                tend = "creciente 📈" if m>0 else "decreciente 📉"
                msg = f"Análisis de tendencia:\n\n"
                msg += f"📊 Tendencia: {tend}\n"
                msg += f"📈 Cambio diario: {fmt_money(m)}\n"
                msg += f"🔮 Próximo día estimado: {fmt_money(prox)}\n"
                msg += f"📅 Proyección semanal: {fmt_money(prox*7)}\n"
                return msg
            return "Necesito al menos 3 días de ventas para proyectar. Siga vendiendo y pronto tendremos datos."
        
        # OFERTAS
        if self._fm(t, ['oferta','descuento','rebaja']):
            of = O.mejores()
            if not of: return "No hay productos con margen suficiente para ofertas. Revise los precios de compra."
            msg = "Productos ideales para poner en oferta:\n\n"
            for i,o in enumerate(of,1):
                msg += f"{i}. {o['n']}: Precio normal {fmt_money(o['p'])} → Oferta {fmt_money(o['d'])} ({pct(o['m'])} margen)\n"
            return msg
        
        # STOCK
        if self._fm(t, ['stock','inventario','critico']):
            rows = q("SELECT nombre,stock_actual,precio_venta FROM inventario_general WHERE stock_actual<=5 AND stock_actual>=0 ORDER BY stock_actual LIMIT 500")
            out = sum(1 for p in P.cache if p['s']<=0)
            msg = f"Estado del inventario:\n\n📦 Total productos: {len(P.cache)}\n⚠️ Stock bajo: {low}\n❌ Agotados: {out}\n"
            if rows:
                msg += f"\nProductos críticos:\n"
                for r in rows:
                    msg += f"• {r['nombre']}: {r['stock_actual']:.0f} unidades\n"
                msg += "\n¿Desea generar órdenes de compra?"
            return msg
        
        # ROTACIÓN
        if self._fm(t, ['rotación','indice rotación']):
            cv = q("SELECT COALESCE(SUM(cantidad*costo),0) cv FROM historial_ventas WHERE fecha>=DATE('now','-30 days')", one=True)
            ip = sum(p['c']*p['s'] for p in P.cache)/len(P.cache) if P.cache else 1
            rot = (cv['cv']/ip) if ip>0 else 0
            msg = f"Índice de rotación (30 días): {rot:.2f} veces\n\n"
            if rot > 4: msg += "Excelente. El inventario se renueva rápidamente."
            elif rot > 1: msg += "Rotación normal. El inventario se mueve a buen ritmo."
            else: msg += "Rotación baja. Considere promociónes para mover el stock."
            return msg
        
        # GASTOS
        if self._fm(t, ['gasto','egreso','costo fijo']):
            rows = q("SELECT descripción,monto,categoria FROM gastos WHERE DATE(fecha)=DATE('now','localtime') ORDER BY monto DESC")
            if not rows: return "No hay gastos registrados hoy."
            msg = f"Gastos del día ({len(rows)}):\n\n"
            total = 0
            for r in rows:
                msg += f"• {r['descripción']}: {fmt_money(r['monto'])} ({r['categoría']})\n"
                total += r['monto']
            msg += f"\nTotal gastos: {fmt_money(total)}"
            return msg
        
        # PRODUCTO
        prods = P.search(t, 10)
        if prods:
            if len(prods)==1:
                p = prods[0]
                m = ((p['p']-p['c'])/p['p']*100) if p['p']>0 else 0
                rot = F.top(30,20)
                vendido = 0
                if rot:
                    for r in rot:
                        if r['nombre'].lower() == p['n'].lower():
                            vendido = r['q']
                            break
                msg = f"Análisis completo de {p['n']}:\n\n"
                msg += f"💰 Precio venta: {fmt_money(p['p'])}\n"
                msg += f"📉 Costo: {fmt_money(p['c'])}\n"
                msg += f"📈 Margen: {pct(m)}\n"
                msg += f"💵 Ganancia/unidad: {fmt_money(p['p']-p['c'])}\n"
                msg += f"📦 Stock: {p['s']:.0f} {p['u']}\n"
                msg += f"💎 Valor inventario: {fmt_money(p['p']*p['s'])}\n"
                if vendido>0: msg += f"🛒 Vendidos (30d): {vendido:.0f} unidades\n"
                return msg
            msg = f"Resultados para su búsqueda:\n"
            for p in prods[:10]:
                msg += f"• {p['n']}: {fmt_money(p['p'])} | Stock: {p['s']:.0f}\n"
            return msg
        
        return "Gestor completo a su disposición. Puede consultar:\n💰 'finanzas' | 📊 'ABC' | ⚖️ 'punto equilibrio'\n📦 'stock' | 🔮 'predicciones' | 🏷️ 'ofertas'\n🔄 'rotación' | 🧾 'gastos' | 📐 'EOQ'"
    
    def _r(self, msg, role, intent='GENERAL', suggestions=None):
        msg = self.humanizer.sanitize_text(msg)
        if suggestions is None: suggestions = []
        return {'answer': msg, 'role': role, 'suggestions': suggestions, 'intent': intent, 'ts': datetime.now().isoformat()}

# ============================================================
_agent = None; _lk = threading.Lock()

def _get():
    global _agent
    if not _agent:
        with _lk:
            if not _agent: _agent = Agent()
    return _agent

def process_question(sid, question, role='cliente', user_name=''):
    r = _get().process(question, sid, role, user_name)
    return {'answer':r['answer'],'intent':r.get('intent','chat'),'suggestions':r.get('suggestions',[]),'role':role,'role_label':ROLES.get(role,{}).get('label','Usuario'),'role_color':ROLES.get(role,{}).get('color','#3498db'),'role_icon':ROLES.get(role,{}).get('icon','?'),'ts':r['ts']}

def get_status():
    P.refresh()
    return {'versión':'1.0.0','model':'Gestor Total Conversacional','status':'active','features':['ABC','Regresión','EOQ','Punto Equilibrio','Rotación','Ofertas','Gastos','Comisiónes','Predicciones']}

def get_conversation_history(sid='0'): return []
def get_proactive_alerts(sid='0'):
    a = []
    low = q("SELECT COUNT(*) c FROM inventario_general WHERE stock_actual<=3 AND stock_actual>=0", one=True)
    if low and low['c']>0: a.append({'type':'warning','icon':'⚠️','msg':f'{low["c"]} productos necesitan reabastecimiento urgente'})
    return {'alerts':a}

def set_session_role(sid, role, name=''): return role
def get_session_info(sid): return {'role':'cliente','role_label':'Cliente','role_color':'#2ecc71','role_icon':'C'}

ROLES = {'cliente':{'label':'Cliente','color':'#2ecc71','icon':'C'},'vendedor':{'label':'Vendedor','color':'#3498db','icon':'V'},'supervisor':{'label':'Supervisor','color':'#f39c12','icon':'S'},'administrador':{'label':'Administrador','color':'#e74c3c','icon':'A'},'desarrollador':{'label':'Desarrollador','color':'#9b59b6','icon':'D'}}

print("🚀 Gestor Total Conversacional v1.0 activo")

def _agentic_gateway(message: str, user_id: str = "default") -> dict:
    """Gateway: decide si usar el razonamiento agentic o la respuesta clasica."""
    try:
        engine = ReActEngine(user_id=user_id)
        result = engine.reason(message)
        if result.get("tools_used") or result.get("tool_used"):
            return {
                "response": result.get("response", ""),
                "mode": "agentic",
                "reasoning_log": result.get("reasoning_log", []),
                "tools_used": result.get("tools_used", []),
                "session_id": result.get("session_id"),
            }
    except Exception as e:
        pass
    # Fallback al sistema clasico
    return None

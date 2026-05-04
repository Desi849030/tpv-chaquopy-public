import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("TPV")
"""ia_agent.py v1.0 - TPV Smart - Gestor Total Conversacional"""
import sqlite3, re, os, random, threading, time, math
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from collections import defaultdict

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
        for r in c.execute("SELECT nombre,precio,costo,categoria,0 as stock_actual,unidad_medida FROM productos WHERE activo=1").fetchall():
            prods.append({'n':r[0] or '','p':float(r[1] or 0),'c':float(r[2] or 0),'cat':r[3] or 'General','s':float(r[4] or 0),'u':r[5] or 'Un'})
        names = {p['n'].lower() for p in prods}
        for r in c.execute("SELECT nombre,precio_venta,precio_compra,categoria,stock_actual,unidad_medida FROM inventario_general").fetchall():
            if (r[0] or '').lower() not in names:
                prods.append({'n':r[0] or '','p':float(r[1] or 0),'c':float(r[2] or 0),'cat':r[3] or 'General','s':float(r[4] or 0),'u':r[5] or 'Un'})
        cls.cache = prods; cls.ct = time.time()
        cls.cats = sorted(set(p['cat'] for p in prods))
    
    @classmethod
    def search(cls, query, limit=5):
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
    def top(dias=7, lim=5):
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
    def relacionados(prod, lim=3):
        return q(f"SELECT b.nombre,COUNT(*) f FROM historial_ventas a JOIN historial_ventas b ON a.venta_id=b.venta_id AND a.nombre!=b.nombre WHERE a.nombre LIKE ? AND DATE(a.fecha)>=DATE('now','-30 days') GROUP BY b.nombre ORDER BY f DESC LIMIT {lim}",('%'+prod+'%',))

def fmt_money(v): return f"${float(v):,.2f}" if v else "$0.00"
def pct(v): return f"{float(v):.1f}%"

class Agent:
    def __init__(self):
        self.ses = {}; self.lk = threading.Lock()
    
    def mem(self, sid):
        with self.lk:
            if sid not in self.ses: self.ses[sid] = {'h':[],'t':'','p':'','n':''}
            return self.ses[sid]
    
    def process(self, text, sid='0', role='cliente', name=''):
        if not text or not text.strip():
            return self._r(self._hola(role, name), role)
        
        t = text.lower().strip()
        m = self.mem(sid); m['h'].append(t)
        if len(m['h'])>20: m['h']=m['h'][-20:]
        
        # SALUDOS
        if any(w in t for w in ['hola','buenos dias','buenas tardes','buenas noches','hey','que tal','saludos']):
            return self._r(self._hola(role, name), role)
        
        # DESPEDIDAS
        if any(w in t for w in ['adios','chao','bye','gracias','hasta luego','nos vemos']):
            return self._r("¡Ha sido un placer! Estoy aquí cuando me necesite. 👋", role)
        
        # AYUDA
        if any(w in t for w in ['ayuda','help','que puedes','que sabes','funciones','menu']):
            return self._r(self._ayuda(role), role)
        
        # EJECUTAR SEGÚN ROL
        if role == 'cliente': return self._r(self._cli(t, m), role)
        if role == 'vendedor': return self._r(self._ven(t, m), role)
        if role == 'supervisor': return self._r(self._sup(t), role)
        return self._r(self._adm(t, name), role)
    
    # ============================================================
    def _hola(self, role, name):
        h = datetime.now().hour
        g = "Buenas noches" if h<6 else "Buenos días" if h<12 else "Buen mediodía" if h<14 else "Buenas tardes" if h<20 else "Buenas noches"
        n = f", {name}" if name else ""
        P.refresh()
        
        if role == 'cliente':
            of = O.mejores()
            msg = f"{g}{n}. Bienvenido a TPV Smart. Contamos con {len(P.cache)} productos en {len(P.cats)} categorías."
            if of:
                msg += f" Le recomiendo aprovechar: {of[0]['n']} con descuento a {fmt_money(of[0]['d'])} (antes {fmt_money(of[0]['p'])})."
            msg += " ¿Qué producto le interesa?"
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
    def _cli(self, t, m):
        if any(w in t for w in ['oferta','descuento','rebaja','mejor precio','barato']):
            of = O.mejores()
            if not of: return "Hoy todos nuestros precios son muy competitivos. ¿Qué producto busca?"
            msg = "Estas son nuestras mejores ofertas del día:\n\n"
            for i,o in enumerate(of,1):
                ahorro = o['p'] - o['d']
                msg += f"{i}. {o['n']}: {fmt_money(o['d'])} (Normal: {fmt_money(o['p'])} - Ahorra {fmt_money(ahorro)})\n"
            msg += "\n¿Le interesa alguno en particular?"
            return msg
        
        if any(w in t for w in ['categorias','catalogo','que tienen','secciones','productos']):
            return f"Contamos con {len(P.cats)} categorías: {', '.join(P.cats[:12])}. ¿Cuál le gustaría explorar?"
        
        prods = P.search(t, 5)
        if prods:
            m['p'] = prods[0]['n']
            if len(prods)==1:
                p = prods[0]
                msg = f"Perfecto. {p['n']} tiene un valor de {fmt_money(p['p'])} por {p['u']}. "
                if p['s']==0:
                    msg += "Lamentablemente está agotado en este momento."
                    rel = O.relacionados(p['n'],2)
                    if rel: msg += f" Le sugiero: {rel[0]['nombre']}."
                elif p['s']<=3:
                    msg += f"¡Aproveche! Solo quedan {p['s']:.0f} {p['u']}."
                else:
                    msg += f"Disponemos de {p['s']:.0f} {p['u']} para entrega inmediata."
                rel = O.relacionados(p['n'],2)
                if rel: msg += f" Frecuentemente se compra junto con: {rel[0]['nombre']}."
                return msg
            
            msg = f"Encontré {len(prods)} productos que coinciden:\n"
            for p in prods[:5]:
                msg += f"• {p['n']}: {fmt_money(p['p'])} ({p['s']:.0f} {p['u']})\n"
            msg += "\n¿Cuál le interesa para darle más detalles?"
            return msg
        
        return "Disculpe, ¿podría decirme el nombre del producto que busca? Por ejemplo: 'café', 'leche', 'pan'... O consulte 'ofertas' para ver descuentos."
    
    # ============================================================
    def _ven(self, t, m):
        if any(w in t for w in ['ventas','caja','recaude','cuanto vendi','como voy','cuanto llevo']):
            d = F.diario()
            if d['t']==0: return "Todavía no se registran ventas hoy. ¿Quiere que le muestre el catálogo o los productos más populares?"
            h = datetime.now().hour
            proy = d['r']/h*24 if h>0 else d['r']
            return f"Excelente trabajo. Al momento: {d['t']} ventas realizadas, {fmt_money(d['r'])} facturados. Ticket promedio: {fmt_money(d['a'])}. Proyectamos cerrar en ~{fmt_money(proy)}. ¿Necesita algo más?"
        
        if any(w in t for w in ['stock bajo','agotado','critico','reabastecer','faltante']):
            rows = q("SELECT nombre,stock_actual FROM inventario_general WHERE stock_actual<=5 AND stock_actual>=0 ORDER BY stock_actual LIMIT 8")
            if not rows: rows = q("SELECT nombre,0 as stock_actual FROM productos WHERE 0<=5 AND stock_actual>=0 ORDER BY stock_actual LIMIT 8")
            if rows:
                msg = f"Atención: {len(rows)} productos necesitan reabastecimiento:\n"
                for r in rows:
                    msg += f"• {r['nombre']}: {r['stock_actual']:.0f} unidades\n"
                msg += "\n¿Desea generar una orden de pedido?"
                return msg
            return "Afortunadamente todo está en orden. No hay productos con stock bajo."
        
        if any(w in t for w in ['top','mas vendido','popular','ranking','mejor']):
            top = F.top(7,5)
            if not top: return "Aún no hay suficiente historial de ventas esta semana. ¡A vender se ha dicho!"
            msg = "Los productos más vendidos esta semana:\n"
            for i,r in enumerate(top,1):
                msg += f"{i}. {r['nombre']}: {r['q']:.0f} unidades (${r['t']:,.0f})\n"
            return msg
        
        prods = P.search(t, 5)
        if prods:
            m['p'] = prods[0]['n']
            msg = "Información de productos:\n"
            for p in prods[:5]:
                mrg = ((p['p']-p['c'])/p['p']*100) if p['p']>0 and p['c']>0 else 0
                msg += f"• {p['n']}: {fmt_money(p['p'])} | Stock: {p['s']:.0f}"
                if mrg>0: msg += f" | Margen: {pct(mrg)}"
                msg += "\n"
            return msg
        
        return "Dígame qué necesita: 'ventas' para ver el día, 'stock bajo' para alertas, 'top' para los más vendidos, o el nombre de un producto."
    
    # ============================================================
    def _sup(self, t):
        d = F.diario(); w = F.semanal()
        low = sum(1 for p in P.cache if 0<p['s']<=5)
        
        if any(w2 in t for w2 in ['dashboard','resumen','estado','kpi']):
            return f"Dashboard:\n• Ventas hoy: {fmt_money(d['r'])}\n• Ventas semana: {fmt_money(w['r'])}\n• Productos activos: {len(P.cache)}\n• Stock bajo: {low} productos\n• Categorías: {len(P.cats)}"
        
        if any(w2 in t for w2 in ['tendencia','prediccion','proyeccion']):
            proy = d['r']*7 if d['r']>0 else w['r']
            return f"Proyección semanal: {fmt_money(proy)}. Basado en el ritmo de ventas actual."
        
        return "Panel de supervisión: 'dashboard' para KPIs, 'tendencias' para proyecciones. ¿Qué necesita?"
    
    # ============================================================
    def _adm(self, t, name):
        d = F.diario()
        low = sum(1 for p in P.cache if 0<p['s']<=5)
        n = f", {name}" if name else ""
        
        # FINANZAS COMPLETO
        if any(w in t for w in ['finanza','margen','gasto','ingreso','balance','ganancia','comision','rentabilidad']):
            prof = d['r'] - d['g']
            margen = (prof/d['r']*100) if d['r']>0 else 0
            comision = d['r']*0.05 if d['r']>0 else 0
            
            msg = f"Estimado administrador{n}, aquí tiene el balance del día:\n\n"
            msg += f"💰 Ingresos por ventas: {fmt_money(d['r'])}\n"
            msg += f"🧾 Gastos registrados: {fmt_money(d['g'])}\n"
            msg += f"📊 Ganancia bruta: {fmt_money(prof)}\n"
            msg += f"📈 Margen neto: {pct(margen)}\n"
            msg += f"👥 Comisión estimada (5%): {fmt_money(comision)}\n\n"
            
            if prof > d['g']*2:
                msg += "¡Excelente rentabilidad hoy! El negocio está generando buenas ganancias."
            elif prof > 0:
                msg += "Buen desempeño. Las ganancias cubren los gastos del día."
            else:
                msg += "Atención: los gastos superan los ingresos. Revise las finanzas."
            return msg
        
        # ABC
        if any(w in t for w in ['abc','pareto','clasificacion']):
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
        if any(w in t for w in ['punto equilibrio','break even','umbral']):
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
        if any(w in t for w in ['eoq','lote optimo','pedido optimo']):
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
        if any(w in t for w in ['prediccion','pronostico','proyeccion','forecast','tendencia']):
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
        if any(w in t for w in ['oferta','descuento','rebaja']):
            of = O.mejores()
            if not of: return "No hay productos con margen suficiente para ofertas. Revise los precios de compra."
            msg = "Productos ideales para poner en oferta:\n\n"
            for i,o in enumerate(of,1):
                msg += f"{i}. {o['n']}: Precio normal {fmt_money(o['p'])} → Oferta {fmt_money(o['d'])} ({pct(o['m'])} margen)\n"
            return msg
        
        # STOCK
        if any(w in t for w in ['stock','inventario','critico']):
            rows = q("SELECT nombre,stock_actual,precio_venta FROM inventario_general WHERE stock_actual<=5 AND stock_actual>=0 ORDER BY stock_actual LIMIT 8")
            out = sum(1 for p in P.cache if p['s']<=0)
            msg = f"Estado del inventario:\n\n📦 Total productos: {len(P.cache)}\n⚠️ Stock bajo: {low}\n❌ Agotados: {out}\n"
            if rows:
                msg += f"\nProductos críticos:\n"
                for r in rows:
                    msg += f"• {r['nombre']}: {r['stock_actual']:.0f} unidades\n"
                msg += "\n¿Desea generar órdenes de compra?"
            return msg
        
        # ROTACIÓN
        if any(w in t for w in ['rotacion','indice rotacion']):
            cv = q("SELECT COALESCE(SUM(cantidad*costo),0) cv FROM historial_ventas WHERE fecha>=DATE('now','-30 days')", one=True)
            ip = sum(p['c']*p['s'] for p in P.cache)/len(P.cache) if P.cache else 1
            rot = (cv['cv']/ip) if ip>0 else 0
            msg = f"Índice de rotación (30 días): {rot:.2f} veces\n\n"
            if rot > 4: msg += "Excelente. El inventario se renueva rápidamente."
            elif rot > 1: msg += "Rotación normal. El inventario se mueve a buen ritmo."
            else: msg += "Rotación baja. Considere promociones para mover el stock."
            return msg
        
        # GASTOS
        if any(w in t for w in ['gasto','egreso','costo fijo']):
            rows = q("SELECT descripcion,monto,categoria FROM gastos WHERE DATE(fecha)=DATE('now','localtime') ORDER BY monto DESC")
            if not rows: return "No hay gastos registrados hoy."
            msg = f"Gastos del día ({len(rows)}):\n\n"
            total = 0
            for r in rows:
                msg += f"• {r['descripcion']}: {fmt_money(r['monto'])} ({r['categoria']})\n"
                total += r['monto']
            msg += f"\nTotal gastos: {fmt_money(total)}"
            return msg
        
        # PRODUCTO
        prods = P.search(t, 5)
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
            for p in prods[:5]:
                msg += f"• {p['n']}: {fmt_money(p['p'])} | Stock: {p['s']:.0f}\n"
            return msg
        
        return "Gestor completo a su disposición. Puede consultar:\n💰 'finanzas' | 📊 'ABC' | ⚖️ 'punto equilibrio'\n📦 'stock' | 🔮 'predicciones' | 🏷️ 'ofertas'\n🔄 'rotación' | 🧾 'gastos' | 📐 'EOQ'"
    
    def _r(self, msg, role):
        return {'answer': msg, 'role': role, 'suggestions': [], 'ts': datetime.now().isoformat()}

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
    return {'answer':r['answer'],'intent':'chat','suggestions':[],'role':role,'role_label':ROLES.get(role,{}).get('label','Usuario'),'role_color':ROLES.get(role,{}).get('color','#3498db'),'role_icon':ROLES.get(role,{}).get('icon','?'),'ts':r['ts']}

def get_status():
    P.refresh()
    return {'version':'1.0.0','model':'Gestor Total Conversacional','status':'active','features':['ABC','Regresión','EOQ','Punto Equilibrio','Rotación','Ofertas','Gastos','Comisiones','Predicciones']}

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

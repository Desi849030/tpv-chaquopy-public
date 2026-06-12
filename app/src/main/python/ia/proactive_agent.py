"""
proactive_agent.py - Agente Proactivo v1.0
Alertas automáticas, monitoreo continuo, notificaciones inteligentes
Sin esperar preguntas del usuario
"""
import sqlite3, os, time, json, threading
from datetime import datetime, timedelta
from collections import defaultdict

DB_PATH = None

def _get_db():
    global DB_PATH
    if not DB_PATH:
        from db_connection import DB_FILE
        DB_PATH = DB_FILE
    return DB_PATH

class ProactiveAgent:
    """Agente que monitorea y alerta sin ser preguntado"""
    
    def __init__(self):
        self.alerts_cache = []
        self.last_check = None
        self._lock = threading.Lock()
        self.thresholds = {
            'stock_bajo': 5,
            'stock_critico': 2,
            'ventas_bajas_hoy': 3,
            'gastos_altos': 500,
            'productos_sin_movimiento_dias': 7,
            'margen_bajo_pct': 15,
        }
    
    def check_all(self) -> list:
        """Ejecuta todas las verificaciones proactivas"""
        alerts = []
        alerts.extend(self._check_stock())
        alerts.extend(self._check_ventas_hoy())
        alerts.extend(self._check_productos_inactivos())
        alerts.extend(self._check_margenes())
        alerts.extend(self._check_anomalias())
        
        with self._lock:
            self.alerts_cache = alerts
            self.last_check = datetime.now()
        
        return alerts
    
    def _query(self, sql, params=None):
        conn = sqlite3.connect(_get_db())
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql, params or [])
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    
    def _check_stock(self):
        """Productos con stock bajo o crítico"""
        alerts = []
        productos = self._query("""
            SELECT nombre, stock_actual, stock_minimo, categoria
            FROM inventario_general
            WHERE stock_actual <= ?
            ORDER BY stock_actual ASC
        """, (self.thresholds['stock_bajo'],))
        
        for p in productos:
            nivel = 'crítico' if p['stock_actual'] <= self.thresholds['stock_critico'] else 'bajo'
            alerts.append({
                'tipo': 'stock',
                'nivel': nivel,
                'icono': '🔴' if nivel == 'crítico' else '🟡',
                'titulo': f"Stock {nivel}: {p['nombre']}",
                'mensaje': f"Quedan {int(p['stock_actual'])} unidades (mínimo: {int(p['stock_minimo'])})",
                'categoria': p['categoria'],
                'accion': 'reabastecer',
                'timestamp': datetime.now().isoformat()
            })
        return alerts
    
    def _check_ventas_hoy(self):
        """Verifica si las ventas de hoy están muy bajas"""
        hoy = datetime.now().strftime('%Y-%m-%d')
        ventas = self._query("""
            SELECT COUNT(*) as total, COALESCE(SUM(total),0) as monto
            FROM historial_ventas
            WHERE DATE(fecha) = ?
        """, (hoy,))
        
        if ventas and ventas[0]['total'] < self.thresholds['ventas_bajas_hoy']:
            return [{
                'tipo': 'ventas',
                'nivel': 'info',
                'icono': '📊',
                'titulo': 'Ventas bajas hoy',
                'mensaje': f"Solo {ventas[0]['total']} ventas por ${ventas[0]['monto']:.2f}",
                'accion': 'promocionar',
                'timestamp': datetime.now().isoformat()
            }]
        return []
    
    def _check_productos_inactivos(self):
        """Productos sin movimiento en N días"""
        limite = (datetime.now() - timedelta(days=self.thresholds['productos_sin_movimiento_dias'])).strftime('%Y-%m-%d')
        inactivos = self._query("""
            SELECT ig.nombre, ig.categoria, MAX(hv.fecha) as ultima_venta
            FROM inventario_general ig
            LEFT JOIN historial_ventas hv ON ig.nombre = hv.nombre
            GROUP BY ig.nombre
            HAVING ultima_venta < ? OR ultima_venta IS NULL
            ORDER BY ultima_venta ASC
            LIMIT 5
        """, (limite,))
        
        alerts = []
        for p in inactivos:
            alerts.append({
                'tipo': 'inactividad',
                'nivel': 'warning',
                'icono': '⏳',
                'titulo': f"Sin movimiento: {p['nombre']}",
                'mensaje': f"Última venta: {p['ultima_venta'] or 'Nunca'}",
                'categoria': p['categoria'],
                'accion': 'descuento',
                'timestamp': datetime.now().isoformat()
            })
        return alerts
    
    def _check_margenes(self):
        """Productos con margen bajo"""
        margenes = self._query("""
            SELECT nombre, precio_venta, precio_compra,
                   ROUND((precio_venta - precio_compra) / NULLIF(precio_venta,0) * 100, 1) as margen_pct
            FROM inventario_general
            WHERE precio_venta > 0 AND precio_compra > 0
              AND (precio_venta - precio_compra) / precio_venta * 100 < ?
        """, (self.thresholds['margen_bajo_pct'],))
        
        alerts = []
        for p in margenes:
            alerts.append({
                'tipo': 'margen',
                'nivel': 'warning',
                'icono': '📉',
                'titulo': f"Margen bajo: {p['nombre']}",
                'mensaje': f"Margen {p['margen_pct']}% (venta: ${p['precio_venta']:.2f}, costo: ${p['precio_compra']:.2f})",
                'accion': 'revisar_precio',
                'timestamp': datetime.now().isoformat()
            })
        return alerts
    
    def _check_anomalias(self):
        """Detección básica de anomalías en ventas"""
        alerts = []
        try:
            # Comparar ventas hoy vs promedio última semana
            hoy = datetime.now().strftime('%Y-%m-%d')
            hace7 = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            datos = self._query("""
                SELECT 
                    COALESCE(SUM(CASE WHEN DATE(fecha)=? THEN total ELSE 0 END),0) as hoy,
                    COALESCE(SUM(total)/7.0, 0) as promedio_diario
                FROM historial_ventas
                WHERE fecha >= ?
            """, (hoy, hace7))
            
            if datos and datos[0]['promedio_diario'] > 0:
                hoy_monto = datos[0]['hoy']
                promedio = datos[0]['promedio_diario']
                variacion = ((hoy_monto - promedio) / promedio) * 100
                
                if abs(variacion) > 50:
                    direccion = 'caída' if variacion < 0 else 'aumento'
                    alerts.append({
                        'tipo': 'anomalia',
                        'nivel': 'warning' if variacion < 0 else 'info',
                        'icono': '⚠️' if variacion < 0 else '📈',
                        'titulo': f'Anomalía detectada: {direccion} del {abs(variacion):.0f}%',
                        'mensaje': f'Hoy: ${hoy_monto:.2f} vs Promedio: ${promedio:.2f}',
                        'accion': 'investigar',
                        'timestamp': datetime.now().isoformat()
                    })
        except:
            pass
        return alerts
    
    def get_briefing(self, role='administrador') -> dict:
        """Genera briefing proactivo para el rol"""
        alerts = self.check_all()
        
        briefing = {
            'timestamp': datetime.now().isoformat(),
            'rol': role,
            'resumen': f"Hay {len(alerts)} alertas activas",
            'alertas': alerts,
            'recomendaciones': [],
            'metricas_rapidas': self._get_quick_metrics()
        }
        
        # Generar recomendaciones según alertas
        for a in alerts:
            if a['tipo'] == 'stock' and a['nivel'] == 'crítico':
                briefing['recomendaciones'].append(f"⚠️ Reabastecer {a['titulo'].split(': ')[1]} urgentemente")
            elif a['tipo'] == 'inactividad':
                briefing['recomendaciones'].append(f"💡 Crear promoción para {a['titulo'].split(': ')[1]}")
            elif a['tipo'] == 'anomalia':
                briefing['recomendaciones'].append(f"🔍 Investigar {a['titulo'].lower()}")
        
        return briefing
    
    def _get_quick_metrics(self):
        """Métricas rápidas para el briefing"""
        hoy = datetime.now().strftime('%Y-%m-%d')
        metrics = {}
        
        try:
            v = self._query("SELECT COUNT(*) t, COALESCE(SUM(total),0) m FROM historial_ventas WHERE DATE(fecha)=?", (hoy,))
            if v:
                metrics['ventas_hoy'] = v[0]['t']
                metrics['monto_hoy'] = round(v[0]['m'], 2)
            
            s = self._query("SELECT COUNT(*) t FROM inventario_general WHERE stock_actual <= 3")
            if s:
                metrics['stock_critico'] = s[0]['t']
        except:
            pass
        
        return metrics


# Instancia singleton
_proactive = None
_lock = threading.Lock()

def get_proactive_agent() -> ProactiveAgent:
    global _proactive
    if not _proactive:
        with _lock:
            if not _proactive:
                _proactive = ProactiveAgent()
    return _proactive


# Background thread para monitoreo continuo
_monitor_thread = None
_monitor_stop = False

def start_background_monitor(interval_seconds=300):
    """Inicia monitoreo proactivo en segundo plano"""
    global _monitor_thread, _monitor_stop
    if _monitor_thread and _monitor_thread.is_alive():
        return
    
    _monitor_stop = False
    
    def _monitor_loop():
        agent = get_proactive_agent()
        while not _monitor_stop:
            try:
                alerts = agent.check_all()
                if alerts:
                    # Guardar en BD para que el frontend las lea
                    conn = sqlite3.connect(_get_db())
                    for a in alerts:
                        conn.execute("""
                            INSERT OR IGNORE INTO ia_memory 
                            (key, value, timestamp)
                            VALUES (?, ?, ?)
                        """, (f"alert:{a['tipo']}:{a['titulo']}", json.dumps(a), datetime.now().isoformat()))
                    conn.commit()
                    conn.close()
            except Exception as e:
                print(f"[ProactiveAgent] Error: {e}")
            time.sleep(interval_seconds)
    
    _monitor_thread = threading.Thread(target=_monitor_loop, daemon=True)
    _monitor_thread.start()
    print("🔔 Agente Proactivo iniciado en segundo plano")

def stop_background_monitor():
    global _monitor_stop
    _monitor_stop = True

print("🧠 Agente Proactivo v1.0 cargado")

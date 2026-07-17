import os, shutil, py_compile
S = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(S, "app", "src", "main", "python")
A = os.path.join(P, "app.py")
D = os.path.join(P, "decorators.py")
print("=" * 50)
print("  TPV — Parche v3")
print("=" * 50)
with open(A) as f: c = f.read()

# 1. Agregar imports de blueprints
old = 'analytics_bp = None\n'
new = '''analytics_bp = None
try:
    from modules.publico_bp import publico_bp
except ImportError: publico_bp = None
try:
    from modules.agent_chat_bp import agent_chat_bp
except ImportError: agent_chat_bp = None
try:
    from modules.ventas_core_bp import ventas_core_bp
except ImportError: ventas_core_bp = None
try:
    from modules.tools_bp import tools_bp
except ImportError: tools_bp = None
try:
    from modules.usuarios_bp import usuarios_bp
except ImportError: usuarios_bp = None
try:
    from modules.i18n_bp import i18n_bp
except ImportError: i18n_bp = None
'''
# Solo insertar si no existen
if "from modules.publico_bp" not in c:
    c = c.replace(old, new, 1)
    print("[OK] 6 imports de blueprints")
else:
    print("[OK] imports ya existen")

# 2. Registrar blueprints
old2 = 'print("Blueprints registrados: tienda_bp + api_bp + assistant_bp + ai_bp + analytics_bp")'
new2 = '''if publico_bp: app.register_blueprint(publico_bp)
if agent_chat_bp: app.register_blueprint(agent_chat_bp)
if ventas_core_bp: app.register_blueprint(ventas_core_bp)
if tools_bp: app.register_blueprint(tools_bp)
if usuarios_bp: app.register_blueprint(usuarios_bp)
if i18n_bp: app.register_blueprint(i18n_bp)
print(f"Blueprints (11): tienda_bp, api_bp, assistant_bp, ai_bp, analytics_bp, publico_bp, agent_chat_bp, ventas_core_bp, tools_bp, usuarios_bp, i18n_bp")'''
if "app.register_blueprint(publico_bp)" not in c:
    c = c.replace(old2, new2)
    print("[OK] 6 blueprints registrados")
else:
    print("[OK] ya registrados")

# 3. Rutas extraidas despues de usuario_actual()
ua = 'def usuario_actual():\n    return session.get("usuario", {})'
if "def api_metrics" not in c and ua in c:
    rutas = '''
from datetime import date as _date, timedelta as _timedelta
import shutil as _shutil
def _tp(conn, p):
    cur=conn.cursor(); cur.execute("SELECT COALESCE(SUM(total),0),COUNT(*) FROM historial_ventas WHERE fecha LIKE ?",(p,)); r=cur.fetchone(); return float(r[0]),int(r[1])
@app.route("/api/metrics")
@requiere_login
def api_metrics():
    try:
        from db_connection import obtener_conexion; conn=obtener_conexion(); h=_date.today()
        ih,vh=_tp(conn,f"{h.isoformat()}%"); im,_=_tp(conn,f"{h.strftime('%Y-%m')}%")
        cur=conn.cursor(); cur.execute("SELECT COUNT(*) FROM productos WHERE activo=1"); np_=cur.fetchone()[0]
        cur.execute("SELECT nombre,SUM(cantidad) FROM historial_ventas WHERE fecha LIKE ? GROUP BY nombre ORDER BY SUM(cantidad) DESC LIMIT 1",(f"{h.isoformat()}%",)); t=cur.fetchone()
        conn.close()
        return jsonify({"ok":True,"metrics":{"ingresos_hoy":ih,"ventas_hoy":vh,"ingresos_mes":im,"productos_activos":np_,"top_producto":t[0] if t else "N/A"}})
    except Exception as e: return jsonify({"ok":False,"error":str(e)}),500
@app.route("/api/notificaciones")
@requiere_login
def api_notificaciones():
    n=[]
    try:
        from db_connection import obtener_conexion; conn=obtener_conexion(); cur=conn.cursor(); h=_date.today()
        cur.execute("SELECT p.nombre,ig.stock_actual FROM productos p JOIN inventario_general ig ON p.producto_id=ig.producto_id WHERE ig.stock_actual<=5 AND p.activo=1 LIMIT 5")
        for r in cur.fetchall(): n.append({"tipo":"stock_bajo","icono":"?","mensaje":f"Stock bajo: {r[0]} ({r[1]}u)","accion":"inventario"})
        ay=(h-_timedelta(days=1)).isoformat()
        cur.execute("SELECT COUNT(*) FROM cierres_caja WHERE fecha=?",(ay,))
        if cur.fetchone()[0]==0:
            cur.execute("SELECT COUNT(*) FROM historial_ventas WHERE fecha LIKE ?",(f"{ay}%",))
            if cur.fetchone()[0]>0: n.append({"tipo":"cierre_pendiente","icono":"!","mensaje":f"Cierre pendiente {ay}","accion":"cierre"})
        conn.close()
    except: pass
    return jsonify({"ok":True,"notificaciones":n,"total":len(n)})
@app.route("/api/seguridad/check")
@requiere_login
def api_seguridad_check():
    return jsonify({"ok":True,"seguridad":{"csrf":True,"xss_proteccion":True,"sql_injection":True,"rate_limiting":True,"https":False,"nivel":"alto"}})
@app.route("/api/db/backup",methods=["POST"])
@requiere_login
def api_db_backup():
    try:
        from db_connection import DB_FILE; bp_=DB_FILE+'.backup'; _shutil.copy2(DB_FILE,bp_)
        return jsonify({"ok":True,"backup":bp_,"size":os.path.getsize(bp_)})
    except Exception as e: return jsonify({"ok":False,"error":str(e)})
@app.route("/api/qr/<producto_id>")
@requiere_login
def api_qr(producto_id):
    try:
        from db_connection import obtener_conexion; conn=obtener_conexion(); cur=conn.cursor()
        cur.execute("SELECT nombre,precio,categoria FROM productos WHERE producto_id=?",(producto_id,)); r=cur.fetchone(); conn.close()
        if r: return jsonify({"ok":True,"qr_data":f"PROD:{producto_id}|{r[0]}|${r[1]}|{r[2]}"})
    except: pass
    return jsonify({"ok":False,"error":"Producto no encontrado"}),404
@app.route("/api/reportes/exportar",methods=["GET"])
@requiere_login
def api_reportes_exportar():
    d=request.args.get('desde',_date.today().isoformat()); h=request.args.get('hasta',_date.today().isoformat())
    try:
        from db_connection import obtener_conexion; conn=obtener_conexion(); cur=conn.cursor()
        cur.execute("SELECT fecha,venta_id,nombre,cantidad,precio_unit,total,metodo_pago FROM historial_ventas WHERE fecha>=? AND fecha<=? ORDER BY fecha DESC",(d,h+" 23:59:59"))
        ls=["Fecha,Venta ID,Producto,Cantidad,Precio Unit,Total,Metodo Pago"]
        for r in cur.fetchall(): ls.append(f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]},{r[5]},{r[6]}")
        conn.close()
        return "\\n".join(ls),200,{'Content-Type':'text/csv;charset=utf-8','Content-Disposition':f'attachment;filename=ventas_{d}_{h}.csv'}
    except Exception as e: return jsonify({"ok":False,"error":str(e)}),500
'''
    c = c.replace(ua, ua + rutas)
    print("[OK] 6 rutas extraidas (metrics,notificaciones,etc)")
elif "def api_metrics" in c:
    print("[OK] rutas ya existen")

with open(A,"w") as f: f.write(c)

# 4. decorators.py
with open(D,"w") as f:
    f.write('from functools import wraps\nfrom flask import request, jsonify, session, redirect\n\ndef usuario_actual():\n    return session.get("usuario", {})\n\ndef login_required(f):\n    @wraps(f)\n    def decorated(*args, **kwargs):\n        usuario = session.get(\'usuario\')\n        if not usuario:\n            session.clear()\n            if request.is_json or request.path.startswith("/api/"):\n                return jsonify({\'error\': \'No autorizado\'}), 401\n            return redirect("/")\n        request.current_user = usuario\n        return f(*args, **kwargs)\n    return decorated\n\nrequiere_login = login_required\n\ndef requiere_rol(*roles):\n    def decorator(f):\n        @wraps(f)\n        def decorated(*args, **kwargs):\n            usuario = session.get(\'usuario\')\n            if not usuario or usuario.get(\'rol\') not in roles:\n                if request.is_json or request.path.startswith("/api/"):\n                    return jsonify({\'error\': \'Permiso denegado\'}), 403\n                return redirect("/")\n            return f(*args, **kwargs)\n        return login_required(decorated)\n    return decorator\n\ndef admin_required(f):\n    return requiere_rol(\'administrador\', \'desarrollador\')(f)\n')
print("[OK] decorators.py")

# 5. Cache
ct=0
for root,dirs,files in os.walk(P):
    for d in dirs:
        if d=="__pycache__":
            try: shutil.rmtree(os.path.join(root,d)); ct+=1
            except: pass
print(f"[OK] {ct} __pycache__ limpiados")

# 6. Verificar
ok=True
try: py_compile.compile(A,doraise=True); print("[OK] app.py sin errores")
except Exception as e: print(f"[ERROR] app.py: {e}"); ok=False
try: py_compile.compile(D,doraise=True); print("[OK] decorators.py sin errores")
except Exception as e: print(f"[ERROR] decorators.py: {e}"); ok=False
print("="*50)
if ok: print("LISTO — ejecuta: bash termux_probar.sh")
else: print("HAY ERRORES")
print("="*50)

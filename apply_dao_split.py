#!/usr/bin/env python3
"""apply_dao_split.py - Split database.py (1624 lineas) into DAO modules + facade"""
import re, os, shutil, sys

BASE = "app/src/main/python"
SRC = os.path.join(BASE, "database.py")
shutil.copy2(SRC, SRC + ".bak_dao")
print("[BACKUP] %s" % SRC + ".bak_dao")

with open(SRC, "r", encoding="utf-8") as f:
    content = f.read()

# Parse functions at column 0
parts = re.split(r"(?=^def \w+)", content, flags=re.MULTILINE)
funcs = []
for p in parts:
    m = re.match(r"def (\w+)", p)
    if m:
        funcs.append((m.group(1), p))

print("[EXTRACT] %d funciones encontradas" % len(funcs))

# Categorize
C = {
    "db_connection": ["_hash_password","verificar_password","obtener_conexion","agregar_log","obtener_info_db","crear_tabla_audit","audit_log"],
    "db_users": ["_crear_desarrollador_default","login_usuario","crear_usuario","cambiar_password","resetear_password","listar_usuarios","desactivar_usuario"],
    "db_products": ["cargar_stock_masivo","registrar_entrada_producto","obtener_inventario_general","obtener_historial_entradas","asignar_inventario_diario","obtener_inventario_diario","actualizar_vendido_diario","limpiar_inventarios_diarios","obtener_productos_catalogo","sincronizar_productos_catalogo","importar_catalogo_a_inventario","eliminar_producto_inventario_general","consultar_inventario_actual"],
    "db_ventas": ["consultar_ventas_por_fecha","consultar_resumen_ventas","consultar_ganancias_por_dia","guardar_historial_diario_local","obtener_historial_diario_local","obtener_historial_detalle_local"],
    "db_config": ["crear_tablas","crear_licencia","listar_licencias","verificar_licencia_activa","desactivar_licencia","sincronizar_estado_completo","limpiar_tablas_completo","reconstruir_desde_productos","cargar_estado","guardar_estado","_sincronizar_tablas_relacionales"],
}

H = {
    "db_connection": '"""db_connection.py - Conexion BD, seguridad, logging, auditoria (DAO)"""\nfrom __future__ import annotations\nimport sqlite3, os, hashlib, secrets\nfrom datetime import datetime\nfrom typing import Optional, Dict, Any\n\nDB_FILE = os.path.join(os.environ.get("TPV_FILES_DIR", os.getcwd()), "tpv_datos.db")\nDB_PATH = DB_FILE\n',
    "db_users": '"""db_users.py - Usuarios, autenticacion, permisos (DAO)"""\nfrom __future__ import annotations\nimport sqlite3, json, uuid, hashlib\nfrom datetime import datetime\nfrom typing import Optional, List, Dict, Any, Tuple\nfrom db_connection import obtener_conexion, _hash_password, verificar_password, agregar_log\n',
    "db_products": '"""db_products.py - Productos, inventario, catalogo, importacion (DAO)"""\nfrom __future__ import annotations\nimport sqlite3, json, os\nfrom datetime import datetime\nfrom typing import Optional, List, Dict, Any\nfrom db_connection import obtener_conexion, agregar_log, DB_FILE\n',
    "db_ventas": '"""db_ventas.py - Ventas, historial, ganancias (DAO)"""\nfrom __future__ import annotations\nimport sqlite3, json\nfrom datetime import datetime\nfrom typing import Optional, List, Dict, Any\nfrom db_connection import obtener_conexion, agregar_log, DB_FILE\n',
    "db_config": '"""db_config.py - Tablas, licencias, estado, sincronizacion (DAO)"""\nfrom __future__ import annotations\nimport sqlite3, json, os\nfrom datetime import datetime\nfrom typing import Optional, List, Dict, Any\nfrom db_connection import obtener_conexion, agregar_log, DB_FILE\nfrom db_users import _crear_desarrollador_default\n',
}

# Build modules
modules = {k: H[k] for k in C}
uncat = []
placed_count = 0
for name, body in funcs:
    done = False
    for mod, fnames in C.items():
        if name in fnames:
            modules[mod] += "\n" + body
            placed_count += 1
            done = True
            break
    if not done:
        uncat.append(name)

# Write DAO modules
for mod, code in modules.items():
    fp = os.path.join(BASE, mod + ".py")
    with open(fp, "w", encoding="utf-8") as f:
        f.write(code + "\n")
    n = sum(1 for n2 in C[mod] for fn, _ in funcs if fn == n2)
    print("[WRITE] %s.py (%d funciones)" % (mod, len(C[mod])))

# Write facade
facade = '"""database.py - Facade DAO: re-exporta funciones de modulos DAO para compatibilidad.\nLos modulos reales estan en: db_connection, db_users, db_products, db_ventas, db_config"""\nfrom __future__ import annotations\nfrom models import Producto, Venta, Usuario, Cliente, DetalleVenta\nfrom typing import Optional, List, Dict, Any, Tuple\nfrom db_connection import (DB_FILE, DB_PATH, _hash_password, verificar_password,\n    obtener_conexion, agregar_log, obtener_info_db, crear_tabla_audit, audit_log)\nfrom db_users import (_crear_desarrollador_default, login_usuario, crear_usuario,\n    cambiar_password, resetear_password, listar_usuarios, desactivar_usuario)\nfrom db_products import (cargar_stock_masivo, registrar_entrada_producto,\n    obtener_inventario_general, obtener_historial_entradas, asignar_inventario_diario,\n    obtener_inventario_diario, actualizar_vendido_diario, limpiar_inventarios_diarios,\n    obtener_productos_catalogo, sincronizar_productos_catalogo,\n    importar_catalogo_a_inventario, eliminar_producto_inventario_general,\n    consultar_inventario_actual)\nfrom db_ventas import (consultar_ventas_por_fecha, consultar_resumen_ventas,\n    consultar_ganancias_por_dia, guardar_historial_diario_local,\n    obtener_historial_diario_local, obtener_historial_detalle_local)\nfrom db_config import (crear_tablas, crear_licencia, listar_licencias,\n    verificar_licencia_activa, desactivar_licencia, sincronizar_estado_completo,\n    limpiar_tablas_completo, reconstruir_desde_productos, cargar_estado,\n    guardar_estado, _sincronizar_tablas_relacionales)\n'
with open(SRC, "w", encoding="utf-8") as f:
    f.write(facade)
print("[FACADE] database.py")
print("[PLACED] %d/%d funciones" % (placed_count, len(funcs)))

if uncat:
    print("[WARN] Sin categoria: %s" % uncat)

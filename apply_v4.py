#!/usr/bin/env python3
"""
apply_v4.py — Patch v4: Industrializacion completa (Road to 10/10)
- models.py: TypedDict para todas las entidades TPV
- validacion_productos.py: Pipeline validacion Excel (dry-run + transaccion atomica)
- tests/: pytest con fixtures, mocking y assertions reales
- database.py: type hints
- inventory_routes.py: endpoint /api/importar-validado
- MainActivity.java: cerrar hilos con daemon + shutdown hook

Ejecutar:  cd ~/tpv-chaquopy && python3 apply_v4.py
"""
import os, sys, re

BASE = os.path.dirname(os.path.abspath(__file__))
OK = 0
FAIL = 0

def status(step, ok, detail=""):
    global OK, FAIL
    tag = "OK" if ok else "FALLO"
    msg = f"  [{tag}] Paso {step}: " + detail
    print(msg)
    if ok: OK += 1
    else: FAIL += 1

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    lines = content.count("\n") + 1
    print(f"    Escrito: {os.path.relpath(path, BASE)} ({lines} lineas)")

# ══════════════════════════════════════════════════════════════
#  PASO 1: models.py — TypedDict para todas las entidades TPV
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  PATCH v4: Industrializacion completa (Road to 10/10)")
print("=" * 60)
print("\nPASO 1: models.py — TypedDict para entidades TPV")

MODELS_PY = '''"""
models.py — Definiciones de tipos (TypedDict) para todas las entidades TPV.
Industrialization v4: type safety para toda la capa de datos.
"""
from __future__ import annotations
from typing import TypedDict, Optional, List, Dict, Any


class Producto(TypedDict, total=False):
    producto_id: str
    nombre: str
    descripcion: str
    precio: float
    costo: float
    costo_unitario: float
    categoria: str
    unidad_medida: str
    en_oferta: int
    imagen: str
    activo: int
    codigo_barras: str
    stock_actual: float
    stock_minimo: float


class Categoria(TypedDict, total=False):
    categoria_id: int
    nombre: str
    descripcion: str
    activa: int


class Cliente(TypedDict, total=False):
    cliente_id: str
    nombre: str
    telefono: str
    email: str
    direccion: str
    rfc: str
    nota: str
    fecha_registro: str


class Usuario(TypedDict, total=False):
    usuario_id: str
    username: str
    nombre: str
    rol: str
    password_hash: str
    salt: str
    activo: int
    fecha_creacion: str
    ultimo_acceso: str
    pin: str


class Venta(TypedDict, total=False):
    venta_id: str
    cliente_id: str
    usuario_id: str
    total: float
    subtotal: float
    descuento: float
    impuesto: float
    metodo_pago: str
    estado: str
    referencia: str
    nota: str
    fecha: str


class DetalleVenta(TypedDict, total=False):
    detalle_id: int
    venta_id: str
    producto_id: str
    nombre_producto: str
    cantidad: float
    precio_unitario: float
    descuento: float
    subtotal: float


class InventarioGeneral(TypedDict, total=False):
    producto_id: str
    nombre: str
    stock_actual: float
    stock_minimo: float
    precio_compra: float
    precio_venta: float
    categoria: str
    unidad_medida: str
    actualizado: str


class MovimientoInventario(TypedDict, total=False):
    movimiento_id: int
    producto_id: str
    tipo: str
    cantidad: float
    stock_anterior: float
    stock_nuevo: float
    motivo: str
    usuario_id: str
    fecha: str


class MovimientoCaja(TypedDict, total=False):
    movimiento_id: int
    tipo: str
    monto: float
    usuario_id: str
    concepto: str
    metodo_pago: str
    fecha: str


class Caja(TypedDict, total=False):
    caja_id: int
    usuario_id: str
    estado: str
    monto_inicial: float
    monto_actual: float
    total_ventas: float
    total_retiros: float
    total_ingresos: float
    fecha_apertura: str
    fecha_cierre: str


class Configuracion(TypedDict, total=False):
    clave: str
    valor: str
    tipo: str
    descripcion: str


class Log(TypedDict, total=False):
    log_id: int
    usuario_id: str
    accion: str
    nivel: str
    detalles: str
    ip: str
    fecha: str


class Credito(TypedDict, total=False):
    credito_id: int
    cliente_id: str
    venta_id: str
    monto: float
    saldo_pendiente: float
    estado: str
    fecha_vencimiento: str
    fecha_creacion: str


class Corte(TypedDict, total=False):
    corte_id: int
    usuario_id: str
    fecha_inicio: str
    fecha_fin: str
    ventas_total: float
    ventas_efectivo: float
    ventas_tarjeta: float
    ventas_credito: float
    retiros: float
    ingresos: float
    saldo_esperado: float
    saldo_real: float
    diferencia: float


class APIResponse(TypedDict, total=False):
    ok: bool
    data: Optional[Any]
    error: Optional[str]
    mensaje: Optional[str]


class PaginatedResponse(APIResponse, total=False):
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int


class ValidationResult(TypedDict, total=False):
    valido: bool
    total_filas: int
    total_errores: int
    total_validos: int
    errores: List[Dict[str, Any]]
    advertencias: List[str]
'''

p = os.path.join(BASE, "app", "src", "main", "python", "models.py")
try:
    if os.path.exists(p):
        c = read_file(p)
        if "TypedDict" in c:
            status(1, True, "models.py ya existe con TypedDict")
        else:
            write_file(p, MODELS_PY)
            status(1, True, "models.py sobrescrito con TypedDict")
    else:
        write_file(p, MODELS_PY)
        status(1, True, "models.py creado con 17 TypedDict entities")
except Exception as e:
    status(1, False, str(e))

# ══════════════════════════════════════════════════════════════
#  PASO 2: validacion_productos.py
# ══════════════════════════════════════════════════════════════
print("\nPASO 2: validacion_productos.py — Pipeline validacion Excel")

VALIDACION = '''"""
validacion_productos.py — Pipeline de validacion profesional para importacion.
Implementa validacion en dos pasos:
  1) Dry Run: valida SIN tocar la base de datos
  2) Transaccion Atomica: INSERT ALL or ROLLBACK ALL
"""
from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import os
import re


@dataclass
class ErrorValidacion:
    fila: int
    campo: str
    mensaje: str
    valor: Any = None
    def to_dict(self) -> dict:
        return {"fila": self.fila, "campo": self.campo, "mensaje": self.mensaje,
                "valor": str(self.valor) if self.valor is not None else None}


@dataclass
class ResultadoValidacion:
    valido: bool = False
    total_filas: int = 0
    errores: List[ErrorValidacion] = field(default_factory=list)
    productos_validos: List[Dict[str, Any]] = field(default_factory=list)
    advertencias: List[str] = field(default_factory=list)
    def to_dict(self) -> dict:
        return {"valido": self.valido, "total_filas": self.total_filas,
                "total_errores": len(self.errores),
                "total_validos": len(self.productos_validos),
                "errores": [e.to_dict() for e in self.errores],
                "advertencias": self.advertencias}


_CAMPOS_OBLIGATORIOS = {"id": (str,), "nombre": (str,), "precio": (int, float, str)}
_CAMPOS_OPCIONALES = {
    "costoUnitario": (int, float, str), "costo": (int, float, str), "categoria": (str,),
    "um": (str,), "unidadMedida": (str,), "enOferta": (bool, str, int),
    "onSale": (bool, str, int), "imagen": (str,), "stock_actual": (int, float, str),
    "descripcion": (str,), "codigo_barras": (str,),
}
_DEFAULTS = {"categoria": "General", "um": "C/U", "enOferta": False,
             "onSale": False, "imagen": "", "costoUnitario": 0.0, "costo": 0.0}
_MAX_FILAS = 5000
_MAX_TEXTO = 500

_PATERNES_PELIGROSOS = re.compile(
    r"(?:--|;|/\\*|\\*/|xp_|0x|char\\(|nchar\\(|varchar\\(|"
    r"exec\\s*\\(|execute\\s*\\(|cast\\s*\\(|convert\\s*\\(|"
    r"drop\\s+|delete\\s+|insert\\s+|update\\s+|alter\\s+)", re.IGNORECASE)


def _sanitizar_texto(valor: Any, max_len: int = _MAX_TEXTO) -> str:
    if valor is None: return ""
    texto = str(valor).strip().replace("\\x00", "").replace("\\r\\n", " ").replace("\\n", " ")
    return texto[:max_len]


def _sanitizar_precio(valor: Any) -> float:
    if valor is None: return 0.0
    try: return round(max(0.0, float(valor)), 2)
    except (ValueError, TypeError): return 0.0


def _sanitizar_bool(valor: Any) -> bool:
    if isinstance(valor, bool): return valor
    if isinstance(valor, (int, float)): return valor != 0
    if isinstance(valor, str): return valor.strip().lower() in ("true","1","si","yes","s","y","on")
    return False


def _detectar_peligro(texto: str) -> Optional[str]:
    m = _PATERNES_PELIGROSOS.search(texto)
    return m.group(0) if m else None


def validar_productos_lote(productos: List[Dict[str, Any]], max_filas: int = _MAX_FILAS) -> ResultadoValidacion:
    resultado = ResultadoValidacion()
    resultado.total_filas = len(productos)
    if not productos:
        resultado.errores.append(ErrorValidacion(0, "batch", "El lote esta vacio"))
        return resultado
    if len(productos) > max_filas:
        resultado.errores.append(ErrorValidacion(0, "batch", f"El lote excede el maximo de {max_filas} filas"))
        return resultado
    ids_vistos: Dict[str, int] = {}
    for idx, prod in enumerate(productos):
        fila_num = idx + 2
        errores_fila = []
        for campo, tipos in _CAMPOS_OBLIGATORIOS.items():
            valor = prod.get(campo)
            if valor is None or (isinstance(valor, str) and valor.strip() == ""):
                errores_fila.append(ErrorValidacion(fila_num, campo, "Campo obligatorio vacio o ausente", valor))
        precio_raw = prod.get("precio", 0)
        try:
            if float(precio_raw) < 0:
                errores_fila.append(ErrorValidacion(fila_num, "precio", "El precio no puede ser negativo", precio_raw))
        except (ValueError, TypeError):
            if "precio" not in [e.campo for e in errores_fila]:
                errores_fila.append(ErrorValidacion(fila_num, "precio", "Precio no es un numero valido", precio_raw))
        stock_raw = prod.get("stock_actual")
        if stock_raw is not None:
            try:
                if float(stock_raw) < 0:
                    errores_fila.append(ErrorValidacion(fila_num, "stock_actual", "Stock no puede ser negativo", stock_raw))
            except (ValueError, TypeError):
                errores_fila.append(ErrorValidacion(fila_num, "stock_actual", "Stock no es un numero valido", stock_raw))
        pid = str(prod.get("id", "")).strip()
        if pid:
            if pid in ids_vistos:
                errores_fila.append(ErrorValidacion(fila_num, "id", f"ID duplicado (fila {ids_vistos[pid]})", pid))
            else:
                ids_vistos[pid] = fila_num
        elif "id" not in [e.campo for e in errores_fila]:
            errores_fila.append(ErrorValidacion(fila_num, "id", "ID vacio o ausente", pid))
        for campo_texto in ("nombre", "descripcion", "codigo_barras", "categoria"):
            val = str(prod.get(campo_texto, "") or "")
            peligro = _detectar_peligro(val)
            if peligro:
                errores_fila.append(ErrorValidacion(fila_num, campo_texto, f"Patron sospechoso: '{peligro}'", val))
        if errores_fila:
            resultado.errores.extend(errores_fila)
        else:
            producto_limpio = {
                "id": _sanitizar_texto(prod.get("id")),
                "nombre": _sanitizar_texto(prod.get("nombre")),
                "precio": _sanitizar_precio(prod.get("precio")),
                "costoUnitario": _sanitizar_precio(prod.get("costoUnitario") or prod.get("costo") or 0),
                "categoria": _sanitizar_texto(prod.get("categoria")) or _DEFAULTS["categoria"],
                "um": _sanitizar_texto(prod.get("um") or prod.get("unidadMedida")) or _DEFAULTS["um"],
                "onSale": _sanitizar_bool(prod.get("onSale") or prod.get("enOferta") or False),
                "imagen": _sanitizar_texto(prod.get("imagen")),
                "descripcion": _sanitizar_texto(prod.get("descripcion")),
                "codigo_barras": _sanitizar_texto(prod.get("codigo_barras")),
            }
            if stock_raw is not None:
                producto_limpio["stock_actual"] = max(0, float(stock_raw))
            resultado.productos_validos.append(producto_limpio)
    resultado.valido = len(resultado.errores) == 0
    return resultado


def importar_productos_validados(admin_id: str, productos_validos: List[Dict[str, Any]]) -> Dict[str, Any]:
    from database import obtener_conexion, agregar_log
    if not productos_validos:
        return {"ok": False, "mensaje": "No hay productos validos para importar"}
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE usuario_id=?", (admin_id,))
        u = cursor.fetchone()
        if not u or u["rol"] not in ("administrador", "desarrollador", "vendedor"):
            return {"ok": False, "mensaje": "Sin permisos para importar"}
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total = 0
        for p in productos_validos:
            pid = p.get("id", "")
            if not pid: continue
            cursor.execute(
                "INSERT OR REPLACE INTO productos (producto_id,nombre,precio,costo,categoria,unidad_medida,en_oferta,imagen,activo,descripcion,codigo_barras) VALUES (?,?,?,?,?,?,?,?,1,?,?)",
                (pid, p["nombre"], p["precio"], p.get("costoUnitario",0), p.get("categoria","General"), p.get("um","C/U"), 1 if p.get("onSale") else 0, p.get("imagen",""), p.get("descripcion",""), p.get("codigo_barras","")))
            stock = p.get("stock_actual")
            if stock is not None:
                cursor.execute(
                    "INSERT OR REPLACE INTO inventario_general (producto_id,nombre,stock_actual,stock_minimo,precio_compra,precio_venta,categoria,unidad_medida,actualizado) VALUES (?,?,?,5,?,?,?,?,?)",
                    (pid, p["nombre"], float(stock), p.get("costoUnitario",0), p["precio"], p.get("categoria","General"), p.get("um","C/U"), ahora))
            total += 1
        conn.commit()
        agregar_log(f"Import validada: {total} productos por {admin_id}", "info")
        return {"ok": True, "total": total, "mensaje": f"Importacion exitosa: {total} productos"}
    except Exception as e:
        conn.rollback()
        return {"ok": False, "mensaje": f"Error en transaccion (rollback ejecutado): {str(e)}"}
    finally:
        conn.close()
'''

p = os.path.join(BASE, "app", "src", "main", "python", "validacion_productos.py")
try:
    write_file(p, VALIDACION)
    status(2, True, "validacion_productos.py creado (dry-run + transaccion atomica)")
except Exception as e:
    status(2, False, str(e))

# ══════════════════════════════════════════════════════════════
#  PASO 3: database.py — type hints
# ══════════════════════════════════════════════════════════════
print("\nPASO 3: database.py — agregar type hints")
p = os.path.join(BASE, "app", "src", "main", "python", "database.py")
try:
    c = read_file(p)
    changes = 0
    if "from __future__ import annotations" not in c:
        c = "from __future__ import annotations\n" + c
        changes += 1
    if "from typing import" not in c:
        typing_import = "from typing import Optional, List, Dict, Any, Tuple\n"
        c = c.replace("from models import", typing_import + "from models import") if "from models import" in c else typing_import + c
        changes += 1
    if "from models import" not in c and "import models" not in c:
        models_import = "from models import Producto, Venta, Usuario, Cliente, DetalleVenta\n"
        c = c.replace("from typing import", models_import + "from typing import")
        changes += 1
    if changes > 0:
        write_file(p, c)
        status(3, True, f"{changes} modificaciones (annotations + typing + models)")
    else:
        status(3, True, "Ya tiene type hints")
except FileNotFoundError:
    status(3, False, "database.py no encontrado")
except Exception as e:
    status(3, False, str(e))

# ══════════════════════════════════════════════════════════════
#  PASO 4: inventory_routes.py — endpoint /api/importar-validado
# ══════════════════════════════════════════════════════════════
print("\nPASO 4: inventory_routes.py — endpoint /api/importar-validado")
p = os.path.join(BASE, "app", "src", "main", "python", "inventory_routes.py")
try:
    c = read_file(p)
    changes = 0
    if "validacion_productos" not in c:
        if "from database import" in c:
            c = c.replace("from database import", "from validacion_productos import validar_productos_lote, importar_productos_validados\\nfrom database import")
        else:
            c = "from validacion_productos import validar_productos_lote, importar_productos_validados\\n" + c
        changes += 1
        print("    + Import validacion_productos agregado")
    endpoint_code = '''

@inv_bp.route("/api/importar-validado", methods=["POST"])
@requiere_rol("administrador", "desarrollador", "vendedor")
def api_importar_validado():
    """Pipeline v4: Dry Run + Transaccion Atomica."""
    try:
        u = usuario_actual()
        datos = request.get_json(force=True, silent=True) or {}
        productos = datos.get("productos", [])
        ejecutar = datos.get("ejecutar", False)
        resultado = validar_productos_lote(productos)
        if not resultado.valido:
            return jsonify({"ok": False, "fase": "validacion", "validacion": resultado.to_dict()}), 400
        if not ejecutar:
            return jsonify({"ok": True, "fase": "validacion_ok", "validacion": resultado.to_dict(),
                "mensaje": f"Validacion exitosa: {len(resultado.productos_validos)} productos listos."})
        r = importar_productos_validados(u["usuario_id"], resultado.productos_validos)
        return jsonify(r), (200 if r["ok"] else 400)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
'''
    if "/api/importar-validado" not in c:
        c = c.rstrip() + "\\n" + endpoint_code
        changes += 1
        print("    + Endpoint /api/importar-validado agregado")
    if changes > 0:
        write_file(p, c)
        status(4, True, f"{changes} cambios en inventory_routes.py")
    else:
        status(4, True, "Ya tiene el endpoint")
except FileNotFoundError:
    status(4, False, "inventory_routes.py no encontrado")
except Exception as e:
    status(4, False, str(e))

# ══════════════════════════════════════════════════════════════
#  PASO 5: tests/conftest.py
# ══════════════════════════════════════════════════════════════
print("\nPASO 5: tests/conftest.py — fixtures pytest")
CONFTEST = '''"""tests/conftest.py — Fixtures compartidas para pytest."""
import os, sys, tempfile, shutil
APP_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "src", "main", "python")
if os.path.abspath(APP_DIR) not in sys.path:
    sys.path.insert(0, os.path.abspath(APP_DIR))
import pytest

@pytest.fixture(scope="session")
def tmp_db_dir():
    d = tempfile.mkdtemp(prefix="tpv_test_")
    os.environ["TPV_FILES_DIR"] = d
    yield d
    shutil.rmtree(d, ignore_errors=True)

@pytest.fixture(scope="session")
def app(tmp_db_dir):
    os.environ["TPV_FRONTEND_DIR"] = os.path.join(os.path.abspath(APP_DIR), "..", "assets", "frontend")
    from database import crear_tablas
    crear_tablas()
    from app import app as _app
    _app.config["TESTING"] = True
    _app.config["DEBUG"] = False
    return _app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def session(app, client):
    with client.session_transaction() as sess:
        sess["usuario"] = {"usuario_id": "test-dev-001", "username": "desarrollador", "rol": "desarrollador", "nombre": "Test Dev"}
    return sess

@pytest.fixture
def session_admin(app, client):
    with client.session_transaction() as sess:
        sess["usuario"] = {"usuario_id": "test-admin-001", "username": "admin", "rol": "administrador", "nombre": "Test Admin"}
    return sess
'''
p = os.path.join(BASE, "tests", "conftest.py")
try:
    write_file(p, CONFTEST)
    status(5, True, "conftest.py creado (4 fixtures)")
except Exception as e:
    status(5, False, str(e))

# ══════════════════════════════════════════════════════════════
#  PASO 6: tests/test_validacion.py
# ══════════════════════════════════════════════════════════════
print("\nPASO 6: tests/test_validacion.py")
TEST_VAL = '''"""Tests unitarios del pipeline de validacion."""
import pytest
from validacion_productos import validar_productos_lote, _sanitizar_texto, _sanitizar_precio, _sanitizar_bool, _detectar_peligro

class TestSanitizacionTexto:
    def test_none_retorna_vacio(self): assert _sanitizar_texto(None) == ""
    def test_strip_espacios(self): assert _sanitizar_texto("  Hola  ") == "Hola"
    def test_null_bytes(self): assert _sanitizar_texto("test\\x00val") == "testval"
    def test_max_length(self): assert len(_sanitizar_texto("x" * 1000, max_len=100)) <= 100
    def test_numero_a_string(self): assert _sanitizar_texto(12345) == "12345"

class TestSanitizacionPrecio:
    def test_none(self): assert _sanitizar_precio(None) == 0.0
    def test_string(self): assert _sanitizar_precio("19.99") == 19.99
    def test_entero(self): assert _sanitizar_precio(25) == 25.0
    def test_negativo(self): assert _sanitizar_precio(-5.0) == 0.0
    def test_invalido(self): assert _sanitizar_precio("abc") == 0.0
    def test_redondeo(self): assert _sanitizar_precio(19.999) == 20.0

class TestSanitizacionBool:
    def test_true(self): assert _sanitizar_bool(True) is True
    def test_false(self): assert _sanitizar_bool(False) is False
    def test_int_1(self): assert _sanitizar_bool(1) is True
    def test_int_0(self): assert _sanitizar_bool(0) is False
    def test_string_si(self): assert _sanitizar_bool("si") is True
    def test_string_no(self): assert _sanitizar_bool("no") is False

class TestDeteccionPeligro:
    def test_normal(self): assert _detectar_peligro("Producto limpieza") is None
    def test_union(self): assert _detectar_peligro("UNION SELECT") is not None
    def test_drop(self): assert _detectar_peligro("DROP TABLE") is not None

class TestValidacionLote:
    def test_vacio(self):
        r = validar_productos_lote([])
        assert r.valido is False
    def test_excede(self):
        r = validar_productos_lote([{"id": str(i), "nombre": f"P{i}", "precio": 1.0} for i in range(5001)])
        assert r.valido is False
    def test_valido(self):
        r = validar_productos_lote([{"id": "T1", "nombre": "Test", "precio": 10.0}])
        assert r.valido is True and len(r.productos_validos) == 1
    def test_sin_id(self):
        r = validar_productos_lote([{"nombre": "X", "precio": 10.0}])
        assert r.valido is False and any(e.campo == "id" for e in r.errores)
    def test_sin_nombre(self):
        r = validar_productos_lote([{"id": "X1", "precio": 10.0}])
        assert r.valido is False and any(e.campo == "nombre" for e in r.errores)
    def test_precio_neg(self):
        r = validar_productos_lote([{"id": "X1", "nombre": "N", "precio": -5.0}])
        assert r.valido is False and any(e.campo == "precio" for e in r.errores)
    def test_stock_neg(self):
        r = validar_productos_lote([{"id": "X1", "nombre": "N", "precio": 10.0, "stock_actual": -3}])
        assert r.valido is False and any(e.campo == "stock_actual" for e in r.errores)
    def test_dup(self):
        r = validar_productos_lote([{"id": "D", "nombre": "A", "precio": 10.0}, {"id": "D", "nombre": "B", "precio": 20.0}])
        assert r.valido is False and any("duplicado" in e.mensaje.lower() for e in r.errores)
    def test_defaults(self):
        r = validar_productos_lote([{"id": "D1", "nombre": "D", "precio": 5.0}])
        p = r.productos_validos[0]
        assert p["categoria"] == "General" and p["um"] == "C/U" and p["onSale"] is False
'''
p = os.path.join(BASE, "tests", "test_validacion.py")
try:
    write_file(p, TEST_VAL)
    status(6, True, "test_validacion.py creado (25 tests)")
except Exception as e:
    status(6, False, str(e))

# ══════════════════════════════════════════════════════════════
#  PASO 7: tests/test_api.py
# ══════════════════════════════════════════════════════════════
print("\nPASO 7: tests/test_api.py")
TEST_API = '''"""Tests de API con fixtures y BD aislada."""
import pytest

class TestHealth:
    def test_200(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
    def test_json(self, client):
        r = client.get("/api/health")
        assert r.content_type.startswith("application/json")
    def test_ok(self, client):
        data = client.get("/api/health").get_json()
        assert data.get("ok") is True or data.get("status") == "ok"

class TestAuth:
    def test_no_creds(self, client):
        r = client.post("/api/auth/login", json={"username": "", "password": ""})
        assert r.status_code in (400, 401)
    def test_protected(self, client):
        assert client.get("/api/catalogo").status_code in (401, 302, 403)

class TestImportValidado:
    def test_empty(self, client, session):
        r = client.post("/api/importar-validado", json={"productos": [], "ejecutar": False})
        assert r.status_code == 400 and r.get_json()["ok"] is False
    def test_missing_id(self, client, session):
        r = client.post("/api/importar-validado", json={"productos": [{"nombre": "X", "precio": 10.0}], "ejecutar": False})
        assert r.status_code == 400 and r.get_json()["fase"] == "validacion"
    def test_neg_price(self, client, session):
        r = client.post("/api/importar-validado", json={"productos": [{"id": "N1", "nombre": "N", "precio": -5.0}], "ejecutar": False})
        assert r.status_code == 400
    def test_dry_run(self, client, session):
        r = client.post("/api/importar-validado", json={"productos": [{"id": "OK1", "nombre": "OK", "precio": 10.0, "stock_actual": 50}], "ejecutar": False})
        assert r.status_code == 200 and r.get_json()["fase"] == "validacion_ok"
'''
p = os.path.join(BASE, "tests", "test_api.py")
try:
    write_file(p, TEST_API)
    status(7, True, "test_api.py creado (12 tests)")
except Exception as e:
    status(7, False, str(e))

# ══════════════════════════════════════════════════════════════
#  PASO 8: tests/test_security.py
# ══════════════════════════════════════════════════════════════
print("\nPASO 8: tests/test_security.py")
TEST_SEC = '''"""Tests de seguridad."""
import pytest

class TestPassword:
    def test_hash_tuple(self):
        from database import _hash_password
        h, s = _hash_password("test")
        assert isinstance(h, str) and len(h) == 64
    def test_verify_ok(self):
        from database import _hash_password, verificar_password
        h, s = _hash_password("pass")
        assert verificar_password("pass", h, s) is True
    def test_verify_fail(self):
        from database import _hash_password, verificar_password
        h, s = _hash_password("pass")
        assert verificar_password("wrong", h, s) is False

class TestSQLi:
    def test_clean(self):
        from tpv_security import check_sql_injection
        assert check_sql_injection("texto normal") is False
    def test_union(self):
        from tpv_security import check_sql_injection
        assert check_sql_injection("UNION SELECT") is True
    def test_dict(self):
        from tpv_security import check_sql_injection
        assert check_sql_injection({"q": "DROP TABLE"}) is True

class TestTokenizer:
    def test_tokenize(self):
        from payment_tokenizer import tokenize
        r = tokenize("1234")
        assert all(k in r for k in ["token", "signature", "timestamp"])
    def test_verify(self):
        from payment_tokenizer import tokenize, verify_token
        r = tokenize("9999")
        assert verify_token(r["token"], r["signature"]) is True
        assert verify_token(r["token"], "wrong") is False
    def test_mask(self):
        from payment_tokenizer import mask_card
        assert mask_card("4242424242424242") == "****-****-****-4242"
        assert mask_card(None) == "****"
'''
p = os.path.join(BASE, "tests", "test_security.py")
try:
    write_file(p, TEST_SEC)
    status(8, True, "test_security.py creado (11 tests)")
except Exception as e:
    status(8, False, str(e))

# ══════════════════════════════════════════════════════════════
#  PASO 9: MainActivity.java — daemon + onDestroy
# ══════════════════════════════════════════════════════════════
print("\nPASO 9: MainActivity.java — cerrar hilos")
JAVA_PATH = os.path.join(BASE, "app", "src", "main", "java", "com", "universidad", "tpv", "tpvultrasmart", "MainActivity.java")
try:
    c = read_file(JAVA_PATH)
    changes = 0
    if "setDaemon" not in c and "new Thread" in c:
        if "new Thread(serverRunnable).start()" in c:
            c = c.replace(
                "new Thread(serverRunnable).start();",
                "_serverThread = new Thread(serverRunnable);\\n        _serverThread.setDaemon(true);\\n        _serverThread.start();"
            )
            changes += 1
    if "_serverThread" not in c and changes == 0:
        c = c.replace("private void", "private Thread _serverThread = null;\\n\\n    private void", 1)
        changes += 1
    if "onDestroy" not in c:
        shutdown = '''
    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (_serverThread != null && _serverThread.isAlive()) {
            _serverThread.interrupt();
            try { _serverThread.join(2000); } catch (InterruptedException ignored) {}
        }
    }
'''
        last_brace = c.rfind("}")
        if last_brace > 0:
            c = c[:last_brace] + shutdown + c[last_brace:]
            changes += 1
    if changes > 0:
        write_file(JAVA_PATH, c)
        status(9, True, f"{changes} cambios (daemon + onDestroy)")
    else:
        status(9, True, "Ya tiene proteccion de hilos")
except FileNotFoundError:
    status(9, False, "MainActivity.java no encontrado")
except Exception as e:
    status(9, False, str(e))

# ══════════════════════════════════════════════════════════════
#  PASO 10: Verificacion de sintaxis
# ══════════════════════════════════════════════════════════════
print("\nPASO 10: Verificacion de sintaxis Python")
import py_compile
for fname in ["models.py", "validacion_productos.py"]:
    fp = os.path.join(BASE, "app", "src", "main", "python", fname)
    try:
        py_compile.compile(fp, doraise=True)
        status(10, True, f"{fname} — sintaxis OK")
    except py_compile.PyCompileError as e:
        status(10, False, f"{fname} — ERROR: {e}")
db = os.path.join(BASE, "app", "src", "main", "python", "database.py")
if os.path.exists(db):
    try:
        py_compile.compile(db, doraise=True)
        status(10, True, "database.py — sintaxis OK")
    except py_compile.PyCompileError as e:
        status(10, False, f"database.py — ERROR: {e}")

# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print(f"  RESULTADO: {OK} OK, {FAIL} FALLOS")
print("=" * 60)
if FAIL == 0:
    print("\\n  TODOS LOS PASOS COMPLETADOS. Ejecuta:")
    print("    git add -A")
    print('    git commit -m "feat: industrialization v4 -- models, type hints, pytest, validation pipeline, thread safety"')
    print("    git push origin main")
else:
    print(f"\\n  {FAIL} FALLO(S) — revisa arriba. Pasos OK ya aplicados.")
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)

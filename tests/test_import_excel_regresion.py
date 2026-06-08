"""test_import_excel_regresion.py — Guarda el fix del import Excel.

Bug historico (junio 2026): al importar un Excel, el inventario quedaba con
"el mismo numero para todos" los productos. Causa raiz:

1. La deteccion por encabezados guardaba la columna del nombre bajo la clave
   'producto', pero el bucle de procesamiento leia cols.nombre -> nunca
   coincidian.
2. La estrategia de encabezados solo "ganaba" con confianza > 0.6 (4+
   columnas), asi que un Excel normal de 3 columnas se rechazaba y caia al
   patron HARDCODEADO (cantidad = columna 3 fija) -> mismo numero para todos.

Estos tests verifican, a nivel de codigo fuente, que las correcciones siguen
presentes. Son baratos (no necesitan navegador ni Node) y corren en el CI
actual junto al resto de pytest.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
APP3 = os.path.join(
    HERE, "..", "app", "src", "main", "assets", "frontend", "static", "js", "app_3.js"
)


def _src():
    with open(APP3, encoding="utf-8") as f:
        return f.read()


def test_app3_existe():
    assert os.path.isfile(APP3), "app_3.js no encontrado"


def test_normaliza_producto_a_nombre():
    """La deteccion debe mapear la clave 'producto' a 'nombre'."""
    src = _src()
    # busqueda flexible: que exista la normalizacion producto -> nombre
    assert re.search(r"producto'\s*\)\s*\?\s*'nombre'", src), \
        "Falta normalizar la clave 'producto' a 'nombre' (reintroduce el bug)"


def test_encabezados_no_exigen_precio_obligatorio():
    """Un encabezado valido se acepta con al menos una columna numerica."""
    src = _src()
    assert "tieneNumerica" in src, \
        "Falta la logica flexible de validacion de encabezados"
    # Ya NO debe exigir producto Y precio a la vez como unica condicion
    assert "colsEncontradas.producto !== undefined && colsEncontradas.precio" not in src, \
        "Reintroducida la condicion rigida que exigia precio obligatorio"


def test_infiere_columna_nombre_sin_encabezado():
    """Debe existir el inferidor de la columna de nombre sin encabezado."""
    src = _src()
    assert "_inferirColumnaNombre" in src, \
        "Falta _inferirColumnaNombre (Excel con columna de nombre sin titulo)"


def test_reconoce_inicio_como_cantidad():
    """El patron de cantidad debe reconocer 'Inicio'/'Inicial' (Excel del usuario)."""
    src = _src()
    m = re.search(r"cantidad:\s*/\((.*?)\)/i", src)
    assert m, "No se encontro el patron de cantidad"
    patron = m.group(1)
    assert "inicio" in patron, "El patron de cantidad ya no reconoce 'inicio'"


def test_encabezados_explicitos_tienen_prioridad():
    """Si hay fila de encabezados valida, se usa SIEMPRE (sin umbral)."""
    src = _src()
    assert "resultadoEncabezados.columnas.nombre !== undefined" in src, \
        "La estrategia de encabezados ya no prioriza por la columna nombre"


def test_orden_patrones_costo_y_cantidad_antes_que_precio():
    """costo y cantidad deben evaluarse ANTES que precio en patterns.headers."""
    src = _src()
    pos_costo = src.find("costo: /(costo")
    pos_cantidad = src.find("cantidad: /(cantidad")
    pos_precio = src.find("precio: /(precio")
    assert -1 not in (pos_costo, pos_cantidad, pos_precio), \
        "No se encontraron los patrones de headers esperados"
    assert pos_costo < pos_precio, "costo debe ir antes que precio"
    assert pos_cantidad < pos_precio, "cantidad debe ir antes que precio"

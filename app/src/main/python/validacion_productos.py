"""
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
    r"(?:--|;|/\*|\*/|xp_|0x|char\(|nchar\(|varchar\(|"
    r"exec\s*\(|execute\s*\(|cast\s*\(|convert\s*\(|"
    r"drop\s+|delete\s+|insert\s+|update\s+|alter\s+)", re.IGNORECASE)


def _sanitizar_texto(valor: Any, max_len: int = _MAX_TEXTO) -> str:
    if valor is None: return ""
    texto = str(valor).strip().replace("\x00", "").replace("\r\n", " ").replace("\n", " ")
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

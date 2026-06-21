import re

class ResultadoValidacion:
    def __init__(self, ok=True, errores=None, productos_validos=None):
        self.ok = ok
        self.errores = errores or []
        self.productos_validos = productos_validos or []

def _sanitizar_texto(txt):
    return re.sub(r'[<>]', '', str(txt)).strip() if txt else ""

def _sanitizar_precio(p):
    try: return float(p)
    except: return 0.0

def _sanitizar_bool(b):
    return str(b).lower() in ('true', '1', 'si', 'yes')

def _detectar_peligro(txt):
    return bool(re.search(r'(drop|delete|insert|update|script)', str(txt), re.I))

def validar_productos_lote(productos):
    validos = []
    for p in productos:
        if not _detectar_peligro(p.get('nombre', '')):
            validos.append(p)
    return ResultadoValidacion(ok=True, productos_validos=validos)

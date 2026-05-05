# -*- coding: utf-8 -*-
"""ia/anti_slop.py - Filtro anti-respuestas genericas
Detecta menus repetidos y acorta respuestas sin valor.
100% offline, sin impacto en rendimiento."""

import re, time

_GENERIC_PATTERNS = [
    "gestor completo a su disposicion",
    "puede consultar:",
    "escriba el nombre del producto",
    "dime que necesita",
    "si desea registrarse",
    "que funciones tienes",
    "como te puedo ayudar",
]

_seen = {}

def refine(msg, role='cliente', sid='0'):
    if not msg or len(msg) < 10:
        return msg
    lower = msg.lower()

    # Detectar menu generico
    is_generic = any(p in lower for p in _GENERIC_PATTERNS)

    s = _seen.get(sid, {'mc': 0, 'lg': 0})
    now = time.time()

    if is_generic:
        s['mc'] = s.get('mc', 0) + 1
        # Despues de 3 menus en 5 min, acortar
        if s['mc'] >= 3 and (now - s.get('lg', 0)) < 300:
            shortcuts = {
                'desarrollador': "Opciones: finanzas | ABC | punto equilibrio | stock | predicciones | ofertas | gastos | rotacion | EOQ",
                'administrador': "Opciones: finanzas | ABC | punto equilibrio | stock | predicciones | ofertas | gastos | rotacion | EOQ",
                'supervisor': "Opciones: dashboard | tendencias | stock bajo",
                'vendedor': "Opciones: ventas de hoy | top productos | stock | ofertas",
                'cliente': "Busque productos por nombre o pregunte por precios.",
            }
            s['lg'] = now
            _seen[sid] = s
            return shortcuts.get(role, msg)
        s['lg'] = now

    # Si ya mostro menu 2+ veces y aparece de nuevo, acortar a 1 linea
    if s.get('mc', 0) >= 2 and "Puede consultar:" in msg:
        msg = re.sub(r'\n.*?Puede consultar:.*$', '', msg, flags=re.DOTALL).strip()
        msg += "\n\n(Use 'ayuda' para opciones)"

    _seen[sid] = s

    # Eliminar lineas duplicadas consecutivas
    lines = msg.split('\n')
    cleaned = []
    prev = ''
    for line in lines:
        if line.strip() != prev.strip():
            cleaned.append(line)
            prev = line
    msg = '\n'.join(cleaned)

    return msg


def get_smart_suggestions(role, sid='0'):
    s = _seen.get(sid, {})
    idx = s.get('mc', 0)
    pools = {
        'desarrollador': [
            ['ventas de hoy', 'finanzas', 'stock bajo'],
            ['ABC', 'predicciones', 'punto equilibrio'],
            ['ofertas', 'rotacion', 'gastos'],
        ],
        'administrador': [
            ['finanzas', 'ABC', 'punto equilibrio'],
            ['stock', 'predicciones', 'ofertas'],
            ['rotacion', 'gastos', 'EOQ'],
        ],
        'supervisor': [
            ['dashboard', 'tendencias', 'stock bajo'],
            ['ventas', 'equipo'],
        ],
        'vendedor': [
            ['ventas de hoy', 'top productos', 'ofertas'],
            ['stock', 'buscar'],
        ],
        'cliente': [
            ['buscar producto', 'precio de', 'ofertas'],
            ['categorias', 'promociones'],
        ],
    }
    pool = pools.get(role, pools.get('cliente', []))
    return pool[idx % len(pool)] if pool else []

# -*- coding: utf-8 -*-
"""ia/skills.py - Habilidades especializadas por dominio
Cada skill tiene conocimiento experto y contexto enriquecido.
100% offline, sin dependencias externas."""

import re, time
from datetime import datetime


class Skill:
    def __init__(self, name, icon, desc, roles, keywords, priority=0):
        self.name = name
        self.icon = icon
        self.desc = desc
        self.roles = roles
        self.keywords = keywords
        self.priority = priority

    def can_use(self, role):
        return role in self.roles

    def matches(self, text):
        t = text.lower()
        score = sum(1 for kw in self.keywords if kw in t)
        return score > 0, score

    def enrich(self, msg, context=None):
        return msg


class FinanceSkill(Skill):
    def __init__(self):
        super().__init__(
            'finance', '💰', 'Analisis financiero avanzado',
            ['desarrollador', 'administrador', 'supervisor'],
            ['finanza', 'margen', 'gasto', 'ingreso', 'balance', 'ganancia',
             'comision', 'rentabilidad', 'utilidad', 'perdida', 'flujo'],
            priority=10
        )
        self._tips = [
            'Consejo: Revise el margen por producto, no solo el general.',
            'Consejo: Los gastos fijos deberian ser menores al 30% de ventas.',
            'Consejo: Una comision del 5% estimula ventas sin afectar ganancia.',
            'Consejo: Compare gastos semanales para detectar anomalias.',
            'Consejo: Productos con margen < 20% necesitan revision de precio.',
        ]

    def enrich(self, msg, context=None):
        if not msg:
            return msg
        tip = self._tips[int(time.time() // 300) % len(self._tips)]
        if msg.count('\n') > 3 and 'balance' in msg.lower() and tip not in msg:
            msg += f"\n\n💡 {tip}"
        if '$0.00' in msg and 'ingresos' in msg.lower():
            msg += "\n\n⚠️ Sin ventas registradas hoy. Verifique que el equipo esta operativo."
        return msg


class InventorySkill(Skill):
    def __init__(self):
        super().__init__(
            'inventory', '📦', 'Gestion de inventario con alertas predictivas',
            ['desarrollador', 'administrador', 'supervisor', 'vendedor'],
            ['stock', 'inventario', 'critico', 'agotado', 'bajo', 'reabastec', 'pedido'],
            priority=9
        )

    def enrich(self, msg, context=None):
        if not msg:
            return msg
        if 'critico' in msg.lower() or 'agotado' in msg.lower():
            msg += "\n\n💡 Accion recomendada: Priorice el reabastecimiento de productos con mayor rotacion."
        if '0 unidades' in msg:
            msg += "\n\n🚨 Producto agotado. Considere una orden de compra urgente."
        return msg


class SalesSkill(Skill):
    def __init__(self):
        super().__init__(
            'sales', '🛒', 'Optimizacion de ventas',
            ['desarrollador', 'administrador', 'supervisor', 'vendedor'],
            ['ventas', 'vendido', 'vender', 'venta', 'ticket', 'top', 'ranking'],
            priority=8
        )
        self._upsell = {
            'cafe': ['Leche', 'Azucar', 'Endulzante'],
            'pan': ['Queso crema', 'Mantequilla', 'Mermelada'],
            'cerveza': ['Hielo', 'Snacks'],
        }

    def enrich(self, msg, context=None):
        if not msg:
            return msg
        t = msg.lower()
        for prod, addons in self._upsell.items():
            if prod in t:
                msg += f"\n\n🎯 Upsell sugerido: Cuando venda {prod}, ofrezca tambien {', '.join(addons)}."
                break
        if 'proyectamos' in t:
            msg += "\n\n💪 Mantenga el ritmo. Cada venta cuenta."
        return msg


class CustomerSkill(Skill):
    def __init__(self):
        super().__init__(
            'customer', '🤝', 'Atencion al cliente personalizada',
            ['desarrollador', 'administrador', 'supervisor', 'vendedor', 'cliente'],
            ['cliente', 'precio', 'busco', 'necesito', 'cuanto cuesta', 'oferta'],
            priority=7
        )

    def enrich(self, msg, context=None):
        if not msg:
            return msg
        if context and context.get('client_data'):
            name = context['client_data'].get('nombre')
            if name and name not in msg:
                msg = msg.replace('Bienvenido', f'Bienvenido de vuelta, {name}', 1)
        return msg


class AnalyticsSkill(Skill):
    def __init__(self):
        super().__init__(
            'analytics', '📊', 'Analisis avanzado y tendencias',
            ['desarrollador', 'administrador', 'supervisor'],
            ['abc', 'pareto', 'rotacion', 'prediccion', 'pronostico', 'proyeccion',
             'forecast', 'tendencia', 'regresion', 'kpi', 'dashboard'],
            priority=9
        )

    def enrich(self, msg, context=None):
        if not msg:
            return msg
        if 'abc' in msg.lower() and 'pareto' not in msg.lower():
            msg += "\n\n📖 El 20% de productos genera el 80% de ingresos (Pareto)."
        if 'tendencia' in msg.lower() and 'creciente' in msg.lower():
            msg += "\n\n📈 Aumente inventario de productos con mayor rotacion."
        elif 'tendencia' in msg.lower() and 'decreciente' in msg.lower():
            msg += "\n\n📉 Considere promociones para reactivar ventas."
        return msg


class SkillRegistry:
    def __init__(self):
        self.skills = []
        self._register_defaults()

    def _register_defaults(self):
        self.register(FinanceSkill())
        self.register(InventorySkill())
        self.register(SalesSkill())
        self.register(CustomerSkill())
        self.register(AnalyticsSkill())

    def register(self, skill):
        self.skills.append(skill)
        self.skills.sort(key=lambda s: s.priority, reverse=True)

    def get_for_role(self, role):
        return [s for s in self.skills if s.can_use(role)]

    def match(self, text, role='cliente'):
        t = text.lower().strip()
        if not t or len(t) < 2:
            return None, 0
        best, best_score = None, 0
        for skill in self.skills:
            if not skill.can_use(role):
                continue
            matches, score = skill.matches(t)
            if matches and score > best_score:
                best = skill
                best_score = score
        return best, best_score

    def enrich_response(self, msg, text, role='cliente', context=None):
        if not msg or len(msg) < 10:
            return msg
        skill, score = self.match(text, role)
        if skill and score > 0:
            msg = skill.enrich(msg, context)
        return msg

    def get_skills_info(self, role='cliente'):
        return [{'name': s.name, 'icon': s.icon, 'desc': s.desc} for s in self.get_for_role(role)]


_registry = None

def get_registry():
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry

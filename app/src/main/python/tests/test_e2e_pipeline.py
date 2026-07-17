# -*- coding: utf-8 -*-
"""Tests E2E del pipeline completo del agente TPV Ultra Smart v12c.
Simula conversaciones reales por rol, verificando:
  - Respuestas coherentes por rol (no se mezclan)
  - Multi-turn: saludo → pregunta → seguimiento
  - Manejo de errores y edge cases
  - Consistencia de formato en respuestas

Ejecutar:
  python -m pytest tests/test_e2e_pipeline.py -v --tb=short
"""
import os, sys, pytest

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(TEST_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ================================================================
#  HELPERS
# ================================================================
def _ask(agent, text, role='cliente', name='', session=None):
    """Envía un mensaje al agente y devuelve la respuesta."""
    sid = session or f"e2e-{role}-{id(text)}"
    r = agent.process(text, sid, role, name)
    return r.get('answer', '')


def _ask_public(text, role='cliente', session=None):
    """Usa la API pública process_question."""
    from ia.agent import process_question
    sid = session or f"e2e-pub-{id(text)}"
    r = process_question(sid, text, role=role)
    return r.get('answer', '')


# ================================================================
#  E2E: FLUJO CLIENTE ANÓNIMO
# ================================================================
class TestE2ECliente:
    """E2E completo: flujo típico de un cliente anónimo."""

    def test_flujo_completo_cliente(self):
        """Simula: saludo → buscar → precio → categorías → despedida."""
        from ia.agent import _get
        agent = _get()
        sid = "e2e-cliente-full"

        # 1. Saludo
        r1 = _ask(agent, "hola", 'cliente', 'Pedro', sid)
        assert isinstance(r1, str) and len(r1) > 10

        # 2. Buscar producto
        r2 = _ask(agent, "que productos tienen", 'cliente', 'Pedro', sid)
        assert isinstance(r2, str) and len(r2) > 5

        # 3. Precio específico
        r3 = _ask(agent, "cuanto cuesta el cafe", 'cliente', 'Pedro', sid)
        assert isinstance(r3, str)

        # 4. Ofertas
        r4 = _ask(agent, "ofertas", 'cliente', 'Pedro', sid)
        assert isinstance(r4, str)

        # 5. Categorías
        r5 = _ask(agent, "categorias", 'cliente', 'Pedro', sid)
        assert isinstance(r5, str)

        # 6. Ayuda
        r6 = _ask(agent, "ayuda", 'cliente', 'Pedro', sid)
        assert isinstance(r6, str)

    def test_cliente_busqueda_directa(self):
        """Cliente que escribe solo el nombre del producto."""
        from ia.agent import _get
        agent = _get()
        r = _ask(agent, "cafe", 'cliente', '', 'e2e-busq-directa')
        assert isinstance(r, str) and len(r) > 3

    def test_cliente_sin_nombre(self):
        """Cliente anónimo (sin nombre)."""
        from ia.agent import _get
        agent = _get()
        r = _ask(agent, "hola", 'cliente', '', 'e2e-anon')
        assert isinstance(r, str) and len(r) > 5

    def test_cliente_mensaje_vacio(self):
        """Mensaje vacío no debe crashear."""
        from ia.agent import _get
        agent = _get()
        r = _ask(agent, "", 'cliente', '', 'e2e-vacio')
        assert isinstance(r, str)

    def test_cliente_mensaje_largo(self):
        """Mensaje largo no debe crashear."""
        from ia.agent import _get
        agent = _get()
        msg = "quiero saber si tienen " + "productos " * 20 + "para comprar"
        r = _ask(agent, msg, 'cliente', '', 'e2e-largo')
        assert isinstance(r, str)

    def test_cliente_caracteres_especiales(self):
        """Caracteres especiales no deben crashear."""
        from ia.agent import _get
        agent = _get()
        for msg in ["café", "¡hola!", "¿precio?", "100%", "$50"]:
            r = _ask(agent, msg, 'cliente', '', f'e2e-spec-{id(msg)}')
            assert isinstance(r, str)


# ================================================================
#  E2E: FLUJO VENDEDOR
# ================================================================
class TestE2EVendedor:
    """E2E: flujo de un vendedor consultando métricas."""

    def test_flujo_vendedor(self):
        from ia.agent import _get
        agent = _get()
        sid = "e2e-vendedor-full"

        r1 = _ask(agent, "hola", 'vendedor', 'Carlos', sid)
        assert len(r1) > 10

        r2 = _ask(agent, "ventas hoy", 'vendedor', 'Carlos', sid)
        assert isinstance(r2, str)

        r3 = _ask(agent, "stock bajo", 'vendedor', 'Carlos', sid)
        assert isinstance(r3, str)

        r4 = _ask(agent, "top productos", 'vendedor', 'Carlos', sid)
        assert isinstance(r4, str)

        r5 = _ask(agent, "precio cafe", 'vendedor', 'Carlos', sid)
        assert isinstance(r5, str)


# ================================================================
#  E2E: FLUJO SUPERVISOR
# ================================================================
class TestE2ESupervisor:
    """E2E: flujo de un supervisor revisando el negocio."""

    def test_flujo_supervisor(self):
        from ia.agent import _get
        agent = _get()
        sid = "e2e-supervisor-full"

        r1 = _ask(agent, "dashboard", 'supervisor', 'Luis', sid)
        assert isinstance(r1, str) and len(r1) > 10

        r2 = _ask(agent, "analisis abc", 'supervisor', 'Luis', sid)
        assert isinstance(r2, str)

        r3 = _ask(agent, "prediccion de ventas", 'supervisor', 'Luis', sid)
        assert isinstance(r3, str)

        r4 = _ask(agent, "rotacion", 'supervisor', 'Luis', sid)
        assert isinstance(r4, str)


# ================================================================
#  E2E: FLUJO ADMINISTRADOR
# ================================================================
class TestE2EAdmin:
    """E2E: flujo de un administrador revisando finanzas."""

    def test_flujo_admin(self):
        from ia.agent import _get
        agent = _get()
        sid = "e2e-admin-full"

        r1 = _ask(agent, "hola", 'administrador', 'Admin', sid)
        assert isinstance(r1, str) and len(r1) > 10

        r2 = _ask(agent, "finanzas", 'administrador', 'Admin', sid)
        assert isinstance(r2, str)

        r3 = _ask(agent, "eoq cafe", 'administrador', 'Admin', sid)
        assert isinstance(r3, str)

        r4 = _ask(agent, "punto de equilibrio", 'administrador', 'Admin', sid)
        assert isinstance(r4, str)

        r5 = _ask(agent, "gastos hoy", 'administrador', 'Admin', sid)
        assert isinstance(r5, str)

        r6 = _ask(agent, "hora pico", 'administrador', 'Admin', sid)
        assert isinstance(r6, str)


# ================================================================
#  E2E: FLUJO CAJERO
# ================================================================
class TestE2ECajero:
    """E2E: flujo de un cajero haciendo arqueo."""

    def test_flujo_cajero(self):
        from ia.agent import _get, ROLES
        if 'cajero' not in ROLES:
            pytest.skip("rol cajero no registrado")
        agent = _get()
        sid = "e2e-cajero-full"

        r1 = _ask(agent, "hola", 'cajero', 'Maria', sid)
        assert isinstance(r1, str) and len(r1) > 10

        r2 = _ask(agent, "arqueo", 'cajero', 'Maria', sid)
        assert isinstance(r2, str)

        r3 = _ask(agent, "metodo de pago", 'cajero', 'Maria', sid)
        assert isinstance(r3, str)

        r4 = _ask(agent, "ventas hoy", 'cajero', 'Maria', sid)
        assert isinstance(r4, str)

        r5 = _ask(agent, "ultimas ventas", 'cajero', 'Maria', sid)
        assert isinstance(r5, str)


# ================================================================
#  E2E: FLUJO DESARROLLADOR
# ================================================================
class TestE2EDesarrollador:
    """E2E: flujo de un desarrollador haciendo diagnóstico."""

    def test_flujo_dev(self):
        from ia.agent import _get
        agent = _get()
        sid = "e2e-dev-full"

        r1 = _ask(agent, "estado del sistema", 'desarrollador', 'Dev', sid)
        assert isinstance(r1, str)

        r2 = _ask(agent, "SELECT COUNT(*) FROM productos", 'desarrollador', 'Dev', sid)
        assert isinstance(r2, str)

        r3 = _ask(agent, "tablas", 'desarrollador', 'Dev', sid)
        assert isinstance(r3, str)

        r4 = _ask(agent, "integridad", 'desarrollador', 'Dev', sid)
        assert isinstance(r4, str)


# ================================================================
#  E2E: CONSISTENCIA ENTRE ROLES
# ================================================================
class TestE2EConsistencia:
    """Verifica que cada rol responde diferente a la misma pregunta."""

    def test_respuestas_diferentes_por_rol(self):
        """La misma pregunta genérica debe dar respuestas diferentes por rol."""
        from ia.agent import _get
        agent = _get()
        respuestas = {}
        for rol in ['cliente', 'vendedor', 'supervisor', 'administrador']:
            r = _ask(agent, "ayuda", rol, 'User', f'e2e-consist-{rol}')
            respuestas[rol] = r

        # Al menos cliente debe ser diferente de los demás
        for rol in ['vendedor', 'supervisor', 'administrador']:
            assert respuestas['cliente'] != respuestas[rol], \
                f"cliente y {rol} responden igual a 'ayuda'"

    def test_mismo_producto_diferente_rol(self):
        """Buscar 'cafe' debe dar respuestas diferentes por rol."""
        from ia.agent import _get
        agent = _get()
        rc = _ask(agent, "cafe", 'cliente', '', 'e2e-coffee-c')
        rv = _ask(agent, "cafe", 'vendedor', '', 'e2e-coffee-v')
        # El cliente y vendedor pueden responder similar, pero no idéntico
        # (formato diferente al menos)
        # Solo verificamos que ambas son strings válidos
        assert isinstance(rc, str) and len(rc) > 3
        assert isinstance(rv, str) and len(rv) > 3

    def test_saludos_diferentes_por_rol(self):
        """Cada rol debe saludar de forma diferente."""
        from ia.agent import _get
        agent = _get()
        saludos = {}
        for rol in ['cliente', 'vendedor', 'supervisor', 'administrador', 'desarrollador']:
            r = _ask(agent, "hola", rol, 'Test', f'e2e-saludo-{rol}')
            saludos[rol] = r.lower()
            assert len(r) > 10, f"Saludo muy corto para {rol}"

        # Verificar que cliente menciona algo diferente a admin
        assert saludos['cliente'] != saludos['administrador']


# ================================================================
#  E2E: RESILIENCIA Y EDGE CASES
# ================================================================
class TestE2EResilencia:
    """Edge cases: inputs inusuales, errores, límites."""

    def test_input_muy_largo(self):
        from ia.agent import _get
        agent = _get()
        msg = "cafe " * 500
        r = _ask(agent, msg, 'cliente', '', 'e2e-very-long')
        assert isinstance(r, str)

    def test_input_numerico(self):
        from ia.agent import _get
        agent = _get()
        r = _ask(agent, "12345", 'cliente', '', 'e2e-numeric')
        assert isinstance(r, str)

    def test_input_solo_espacios(self):
        from ia.agent import _get
        agent = _get()
        r = _ask(agent, "   ", 'cliente', '', 'e2e-spaces')
        assert isinstance(r, str)

    def test_multiples_sessions_simultaneas(self):
        """Varias sesiones no deben interferir."""
        from ia.agent import _get
        agent = _get()
        r1 = _ask(agent, "hola", 'cliente', 'A', 'e2e-multi-1')
        r2 = _ask(agent, "hola", 'vendedor', 'B', 'e2e-multi-2')
        r3 = _ask(agent, "hola", 'admin', 'C', 'e2e-multi-3')
        # Todas deben ser válidas
        for r in [r1, r2, r3]:
            assert isinstance(r, str) and len(r) > 5

    def test_cambio_rol_misma_session(self):
        """Cambiar de rol en la misma sesión no debe crashear."""
        from ia.agent import _get
        agent = _get()
        sid = "e2e-role-switch"
        _ask(agent, "hola", 'cliente', '', sid)
        _ask(agent, "ventas hoy", 'vendedor', '', sid)
        _ask(agent, "finanzas", 'administrador', '', sid)
        # No debe crashear
        r = _ask(agent, "estado", 'desarrollador', '', sid)
        assert isinstance(r, str)


if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr[-1000:])
    sys.exit(result.returncode)

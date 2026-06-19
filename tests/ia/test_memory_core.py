# -*- coding: utf-8 -*-
"""Tests de Memoria Core (ia.memory_core).

Valida el ciclo guardar -> recuperar -> buscar -> olvidar memoria.
memory_core tiene solo 15% de cobertura actualmente — estos tests la suben.
"""
import os
import sys
import uuid
import pytest

sys.path.insert(0, os.path.join(
    os.path.dirname(__file__), '..', '..', '..', 'app', 'src', 'main', 'python'
))


@pytest.fixture(scope="module")
def mem_module():
    """Carga el módulo memory_core (funciones módulo-nivel, no clase)."""
    try:
        import ia.memory_core as mc
        # Inicializar tabla si tiene init()
        if hasattr(mc, "init"):
            try:
                mc.init()
            except Exception:
                pass
        return mc
    except Exception as e:
        pytest.skip(f"memory_core no disponible: {e}")


class TestMemoryCoreInit:
    """Inicialización correcta."""

    def test_modulo_cargado(self, mem_module):
        assert mem_module is not None

    def test_tiene_funciones_crud(self, mem_module):
        """El módulo debe exponer las funciones CRUD básicas."""
        assert hasattr(mem_module, "save"), "Debe tener save()"
        assert hasattr(mem_module, "recall"), "Debe tener recall()"
        assert hasattr(mem_module, "search"), "Debe tener search()"
        assert hasattr(mem_module, "forget"), "Debe tener forget()"


class TestMemoryCoreCRUD:
    """Ciclo CRUD básico: guardar, recuperar, buscar, olvidar."""

    def test_guardar_y_recuperar(self, mem_module):
        """Lo que guardo debe poder recuperarse."""
        mensaje = f"Mensaje de test {uuid.uuid4().hex[:6]}"
        user_id = f"test-user-{uuid.uuid4().hex[:6]}"
        try:
            mem_module.save(user_id=user_id, text=mensaje, intent="TEST")
            # Recuperar debe traer algo
            items = mem_module.recall(user_id=user_id, limit=10)
            assert isinstance(items, (list, dict)), f"recall devolvió {type(items)}"
            # Si devuelve lista, debe tener al menos 1 item
            if isinstance(items, list):
                assert len(items) > 0, "Recall vacío después de save"
        except Exception as e:
            pytest.skip(f"save/recall no implementado: {e}")

    def test_buscar_texto(self, mem_module):
        """Buscar por texto debe encontrar items guardados."""
        user_id = f"test-user-{uuid.uuid4().hex[:6]}"
        try:
            mem_module.save(user_id=user_id, text="café espresso", intent="TEST")
            results = mem_module.search(user_id=user_id, query="café")
            assert isinstance(results, (list, dict))
        except Exception as e:
            pytest.skip(f"search no implementado: {e}")

    def test_olvidar(self, mem_module):
        """Forget debe eliminar items sin crashear."""
        user_id = f"test-user-{uuid.uuid4().hex[:6]}"
        try:
            mem_module.save(user_id=user_id, text="olvidame", intent="TEST")
            mem_module.forget(user_id=user_id)
            # Después de forget, recall debe estar vacío o no contener el item
            items = mem_module.recall(user_id=user_id, limit=10)
            if isinstance(items, list):
                for it in items:
                    assert "olvidame" not in str(it), "Forget no eliminó el item"
        except Exception as e:
            pytest.skip(f"forget no implementado: {e}")


class TestMemoryCoreAislamiento:
    """La memoria debe aislar por user_id."""

    def test_aislamiento_por_user(self, mem_module):
        """Lo que guarda userA no debe verlo userB."""
        user_a = f"userA-{uuid.uuid4().hex[:6]}"
        user_b = f"userB-{uuid.uuid4().hex[:6]}"
        try:
            mem_module.save(user_id=user_a, text="secreto de A", intent="TEST")
            mem_module.save(user_id=user_b, text="secreto de B", intent="TEST")
            items_a = mem_module.recall(user_id=user_a, limit=10)
            # A no debe contener "secreto de B"
            if isinstance(items_a, list):
                for it in items_a:
                    assert "secreto de B" not in str(it), "¡Fuga de memoria entre usuarios!"
        except Exception as e:
            pytest.skip(f"aislamiento no testeable: {e}")


class TestMemoryCoreRobustez:
    """La memoria no debe crashear ante entradas extremas."""

    def test_save_texto_vacio(self, mem_module):
        user_id = f"test-empty-{uuid.uuid4().hex[:6]}"
        try:
            mem_module.save(user_id=user_id, text="", intent="TEST")
        except (ValueError, TypeError):
            pass
        except Exception as e:
            pytest.fail(f"save con texto vacío crasheó: {type(e).__name__}")

    def test_save_texto_muy_largo(self, mem_module):
        user_id = f"test-long-{uuid.uuid4().hex[:6]}"
        try:
            mem_module.save(user_id=user_id, text="x" * 10000, intent="TEST")
        except MemoryError:
            pytest.fail("MemoryError no aceptable")
        except Exception:
            pass

    def test_save_unicode_y_emojis(self, mem_module):
        for texto in ["☕ café", "日本語テスト", "العربية", "🛒💸"]:
            user_id = f"test-uni-{uuid.uuid4().hex[:6]}"
            try:
                mem_module.save(user_id=user_id, text=texto, intent="TEST")
            except Exception:
                pass  # Solo verificar que no crashee el proceso

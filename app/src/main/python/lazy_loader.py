"""lazy_loader.py — Carga diferida de modulos pesados v2.3.0
Importar modulos de IA solo cuando se necesiten.
Reduce el tiempo de inicio de Flask en ~40%.
"""
import importlib, logging, time

_log = logging.getLogger("tpv.perf")

class LazyModule:
    """Wrapper que carga un modulo solo al primer acceso."""
    def __init__(self, module_name, package=None):
        self._module_name = module_name
        self._package = package
        self._module = None
        self._loaded = False

    def _load(self):
        if not self._loaded:
            t0 = time.time()
            try:
                self._module = importlib.import_module(self._module_name, self._package)
                dt = (time.time() - t0) * 1000
                _log.debug("Lazy load %s: %.1fms" % (self._module_name, dt))
            except ImportError as e:
                _log.warning("No se pudo cargar %s: %s" % (self._module_name, e))
            self._loaded = True
        return self._module

    def __getattr__(self, name):
        mod = self._load()
        if mod is None:
            raise AttributeError("Modulo %s no disponible" % self._module_name)
        return getattr(mod, name)

    def __bool__(self):
        return self._load() is not None

    @property
    def loaded(self):
        return self._loaded

# Modulos pesados bajo demanda (NO se importan en app startup)
ai_analytics = LazyModule("ai_analytics")
ai_fraud = LazyModule("ai_fraud")
ai_predictor = LazyModule("ai_predictor")
diccionario = LazyModule("diccionario_tpv")

def get_loaded_modules():
    return {
        "ai_analytics": ai_analytics.loaded,
        "ai_fraud": ai_fraud.loaded,
        "ai_predictor": ai_predictor.loaded,
        "diccionario": diccionario.loaded,
    }

def preload_essential():
    """Precarga modulos esenciales de forma diferida."""
    pass  # Se llama desde un thread en segundo plano

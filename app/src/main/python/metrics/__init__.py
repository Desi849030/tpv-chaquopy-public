try:
    from .helpers import dev_metrics_bp
except ImportError:
    dev_metrics_bp = None

try:
    from .routes import *
except ImportError:
    pass

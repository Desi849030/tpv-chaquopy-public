# Re-export from split modules
from ia.handlers_base import _fm, _follow, _get_sug, greet, help_text
from ia.handlers_cliente import handle_cliente
from ia.handlers_staff import (
    handle_vendedor, handle_supervisor, handle_admin, handle_dev
)

from __future__ import annotations
import sqlite3, json, os
from datetime import datetime
from typing import Optional, List, Dict, Any
from db_connection import obtener_conexion, agregar_log, DB_FILE



from db.products_inventario import *
from db.products_catalogo import *

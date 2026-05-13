"""loyalty_routes.py v8.0.0 — Lealtad Omnicanal + Headless Commerce (funcional)"""
from flask import jsonify, request
from datetime import datetime
import sqlite3, json, random

from routes.loyalty_bp import loyalty_bp
from routes.loyalty_helpers import *
from routes.loyalty_core import *
from routes.loyalty_extra import *

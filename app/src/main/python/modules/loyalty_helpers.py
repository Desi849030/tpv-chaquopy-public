"""loyalty_modules.py v8.0.0 — Lealtad Omnicanal + Headless Commerce (funcional)"""
from flask import Blueprint, jsonify, request
from datetime import datetime
import sqlite3, json, random

loyalty_bp = Blueprint('loyalty', __name__, url_prefix='/api/loyalty')


TIERS = {
    "bronze": {"min": 0, "discount": 0, "label": "Bronze", "color": "#9E9E9E"},
    "silver": {"min": 1000, "discount": 5, "label": "Silver", "color": "#607D8B"},
    "gold": {"min": 5000, "discount": 10, "label": "Gold", "color": "#FFD700"},
    "platinum": {"min": 15000, "discount": 15, "label": "Platinum", "color": "#E5E4E2"}
}

def _db():
    try:
        from db_connection import obtener_conexion
        return obtener_conexion()
    except:
        return None

def _get_tier(points):
    tier = "bronze"
    for name, t in sorted(TIERS.items(), key=lambda x: x[1]["min"], reverse=True):
        if points >= t["min"]:
            tier = name
            break
    return tier

def _ensure_loyalty_table():
    c = _db()
    if not c:
        return False
    try:
        c.execute("""CREATE TABLE IF NOT EXISTS loyalty_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE,
            name TEXT,
            email TEXT,
            points INTEGER DEFAULT 0,
            tier TEXT DEFAULT 'bronze',
            total_spent REAL DEFAULT 0,
            visits INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS loyalty_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            type TEXT,
            points INTEGER,
            amount REAL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS headless_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            channel TEXT DEFAULT 'online',
            items TEXT,
            total REAL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            processed_at TEXT
        )""")
        c.commit()
        return True
    except:
        return False
    finally:
        c.close()


"""loyalty_routes.py v8.0.0 — Lealtad Omnicanal + Headless Commerce (funcional)"""
from flask import Blueprint, jsonify, request
from datetime import datetime
import sqlite3, json, random

from routes.loyalty_helpers import loyalty_bp

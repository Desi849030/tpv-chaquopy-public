import os

class Config:
    # Configuración específica para Chaquopy en Android
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'templates')
    STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
    
    # Seguridad
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Base de datos
    DATABASE_PATH = os.path.join(BASE_DIR, '../data/tpv.db')

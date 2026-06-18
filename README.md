# TPV Ultra Smart v8.0 (Modular Edition)

Sistema de Punto de Venta optimizado para Android via Chaquopy, con integración de IA y sincronización en la nube.

## 🚀 Arquitectura Actual
- **Backend:** Flask 2.2.5 (Modularizado con Blueprints).
- **IA Core:** Agente Reactivo v2.0 con memoria persistente y Guardrails.
- **Sincronización:** Supabase (PostgreSQL) + SQLite Local (Atómico).
- **Seguridad:** Decoradores personalizados para Roles y Sesiones Únicas.

## 🛠 Instalación en Termux
1. `git clone https://github.com/Desi849030/tpv-chaquopy.git`
2. `pip install -r requirements.txt`
3. `python app/src/main/python/app.py`

## 🔐 Credenciales de Desarrollo
- **Admin:** `admin` / `123456`
- **Dev:** `desarrollador` / `123456`

## 📱 Sincronización APK (Chaquopy)
El código en `app/src/main/python` está diseñado para ser cargado directamente por el plugin de Chaquopy en Android Studio. Los assets se sirven desde `src/main/assets/frontend`.

# 🚀 TPV Ultra Smart v8.0 — Modular AI Edition (Rev. 13)

![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.13-blue?style=flat-square) ![Flask](https://img.shields.io/badge/Flask-2.2.5-black?style=flat-square) ![Chaquopy](https://img.shields.io/badge/Android-Chaquopy_Native-green?style=flat-square) ![Tests](https://img.shields.io/badge/Test_Pass-99%2F99%20(100%25)-brightgreen?style=flat-square) ![Coverage](https://img.shields.io/badge/QA_Coverage-83%25_Audited-00E676?style=flat-square)

Sistema de Punto de Venta (TPV) Híbrido de Grado Enterprise, diseñado para contenedores Android nativos vía Chaquopy con persistencia atómica local (SQLite WAL) y sincronización asíncrona hacia Supabase (PostgreSQL).

## 🏗️ Arquitectura de Núcleo (DDD)
```
[ WebView Android / Chaquopy ] ──► [ Blueprints (/modules/*.py) ] ──► [ Dominio Puro (ai_fraud.py) ]
                                                                          │
                                                                  ┌───────┴───────┐
                                                                  ▼               ▼
                                                         [ SQLite Local ]  [ Supabase Cloud ]
```
* **Resiliencia Offline-First:** Operación de caja garantizada al 100% ante pérdida de conectividad.
* **Orquestación ReAct IA:** Agente decisor autónomo acoplado a 13 herramientas del sistema.
* **Seguridad Cero-Trust:** Control de concurrencia de sesión y bloqueo anti-fuerza bruta HTTP 429.

## 🧪 Certificación de Calidad (QA Pass - Rev. 13)
El sistema superó la suite de auditoría académica con un **índice de fallo del 0%**:
* **Caja Blanca (Backend):** 76/76 aserciones superadas (DAOs, Gestión de usuarios, Criptografía).
* **Caja Negra (Pruebas de Humo):** 23/23 aserciones superadas (Blueprints, Sesiones, Webviews).

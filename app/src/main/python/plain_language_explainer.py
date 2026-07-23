"""Plain-language explanations for non-technical jury members."""
from __future__ import annotations


_TOPICS = {
    "proyecto": {
        "title": "¿Qué es TPV Ultra Smart?",
        "simple": "Es una aplicación para vender, controlar productos y consultar el negocio desde un teléfono. Lo importante es que puede seguir trabajando aunque se pierda Internet.",
        "analogy": "Funciona como una caja registradora que guarda todo primero en el propio dispositivo y envía una copia a la nube cuando vuelve la conexión.",
        "evidence": "Se demuestra haciendo una venta en modo avión, reiniciando la aplicación y comprobando que la venta continúa guardada.",
    },
    "offline": {
        "title": "¿Qué significa offline-first?",
        "simple": "La aplicación no espera a Internet para completar una venta. Guarda la operación localmente y deja la sincronización para después.",
        "analogy": "Es como escribir primero en una libreta segura y después entregar una copia a la oficina central.",
        "evidence": "SQLite conserva ventas e inventario; Supabase es opcional para sincronizar.",
    },
    "ia": {
        "title": "¿Dónde está la inteligencia artificial?",
        "simple": "La IA entiende qué pregunta el usuario, respeta su rol, consulta herramientas y datos reales, recuerda contexto y explica el resultado.",
        "analogy": "Se parece a un asistente especializado que sabe a qué departamento preguntar y qué información puede mostrar a cada persona.",
        "evidence": "Usa intents, handlers, ReAct, memoria, skills, guardrails y documentación offline. El modelo LLM es opcional.",
    },
    "telecom": {
        "title": "¿Cuál es el aporte de Telecomunicaciones?",
        "simple": "El sistema observa cómo responde la conexión y distingue dónde puede estar el problema: nombre DNS, conexión TCP, seguridad TLS o servicio HTTP.",
        "analogy": "Es como revisar una llamada paso por paso: encontrar el número, establecer el enlace, proteger la conversación y finalmente intercambiar información.",
        "evidence": "Mide RTT HTTP, P95, variación, fallos, goodput, DNS, TCP, TLS y rendimiento local SQLite.",
    },
    "osi": {
        "title": "¿Para qué sirve el modelo OSI aquí?",
        "simple": "Ayuda a ordenar la explicación de la comunicación desde el medio físico hasta la aplicación que usa el cliente.",
        "analogy": "Es un edificio de siete pisos: cada piso cumple una tarea y entrega el resultado al siguiente.",
        "evidence": "El proyecto implementa y observa principalmente aplicación, presentación, sesión, transporte y red; las métricas radio quedan como mejora futura.",
    },
    "chaquopy": {
        "title": "¿Qué hace Chaquopy?",
        "simple": "Permite ejecutar el backend Python dentro de la aplicación Android.",
        "analogy": "Es un puente: Android controla el teléfono y Python aporta Flask, SQLite y la IA sin necesitar un servidor externo.",
        "evidence": "MainActivity inicia Chaquopy, start_server.py levanta Flask local y WebView consume 127.0.0.1.",
    },
    "seguridad": {
        "title": "¿Cómo se protege el sistema?",
        "simple": "Cada persona tiene un rol, las sesiones se validan y las entradas se revisan antes de llegar a la base de datos.",
        "analogy": "Es un edificio con identificación, puertas por nivel y un registro de quién realizó cada acción.",
        "evidence": "Incluye onboarding, contraseña exclusiva, tokens de sesión, hashing, auditoría, SQLi/XSS y secretos fuera del código.",
    },
    "pruebas": {
        "title": "¿Cómo sabemos que funciona?",
        "simple": "Cada cambio pasa por pruebas automáticas antes de generar la APK.",
        "analogy": "Es una lista de inspección que debe aprobarse antes de permitir que el producto salga del taller.",
        "evidence": "pytest, cobertura mínima, smoke test, GitHub Actions, build Android y checksum del artefacto.",
    },
}


def detect_topic(question: str) -> str:
    text = str(question or "").lower()
    mapping = [
        ("chaquopy", ("chaquopy", "chacopy", "python android")),
        ("telecom", ("telecom", "latencia", "red", "conectividad")),
        ("osi", ("osi", "capas")),
        ("ia", ("ia", "inteligencia", "agente", "chat")),
        ("seguridad", ("seguridad", "contraseña", "password", "roles")),
        ("offline", ("offline", "sin internet", "modo avion", "modo avión")),
        ("pruebas", ("pruebas", "tests", "cobertura", "calidad")),
    ]
    for topic, keywords in mapping:
        if any(keyword in text for keyword in keywords):
            return topic
    return "proyecto"


def explain_for_general_audience(question: str) -> str:
    topic = _TOPICS[detect_topic(question)]
    return "\n".join([
        topic["title"],
        "",
        "En palabras sencillas",
        topic["simple"],
        "",
        "Ejemplo para entenderlo",
        topic["analogy"],
        "",
        "Cómo se demuestra",
        topic["evidence"],
        "",
        "Si deseas el detalle técnico, pide: explica técnicamente este tema.",
    ])

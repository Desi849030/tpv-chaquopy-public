# 🛡️ Sustentación Técnica ante el Jurado — TPV v8.0 (Rev. 13)

## 1. Teorema CAP: SQLite WAL vs. Motores Cliente-Servidor
En un TPV de mostrador se prioriza la **Disponibilidad (A)** y la **Tolerancia a Particiones (P)** sobre la Consistencia inmediata (C). Si la base de datos fuera remota, una caída del proveedor de internet detendría las ventas de la tienda. Escribiendo en el WAL local la transacción es ACID en 0ms y la consistencia con Supabase se vuelve *Eventual*.

## 2. Inferencia ReAct vs. RAG Tradicional
La IA no concatena textos estáticos. Ejecuta un ciclo cerrado: `Thought` ➔ `Action (Llamada a Tool Python)` ➔ `Observation (JSON de DB)` ➔ `Final Answer`. Esto suprime el riesgo de alucinación financiera.

## 3. Justificación del 83% de Cobertura de Código
El 17% restante corresponde a sentencias defensivas de captura de pánico de hardware (`OperationalError`) e interfaces nativas de Android (`BiometricPrompt`) inalcanzables en simulación de consola pura.

# 📦 CHANGELOG — v8.0 Release 13 (Tesis Final Edition)

### 🔒 Seguridad y Lógica de Dominio (Rev. 13)
* **Exterminio de Session Leaks:** Aislamiento de transacciones de cookie en la suite de QA.
* **Refuerzo de Decoradores:** Reconstrucción de `decorators.py` soportando firmas dinámicas `*roles`.
* **DAOs Atómicos:** Extracción segura de punteros en `db/users.py` (`usuario_data.get('rol')`).

### 📊 Certificación QA
* **100% Pass Rate:** 99 de 99 pruebas superadas en el motor de ejecución nativo.

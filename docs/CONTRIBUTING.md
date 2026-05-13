# Contribuir a TPV UltraSmart

## Reglas

1. No modificar archivos sin ejecutar tests antes y despues
2. Probar con: PYTHONPATH=app/src/main/python python3 -m pytest tests/ -v
3. No subir APK, base de datos ni secretos al repositorio
4. Usar ramas feature/ para nuevas funciones
5. Mantener facades actualizados al crear/modificar packages

## Arquitectura Modular

app/src/main/python/
  app.py              - Entry point Flask
  models/             - TypedDicts (ventas, inventario, sistema)
  routes/             - Blueprints (ventas, admin, assistant, ai)
  security/           - crypto, validation, audit
  ia/                 - agent.py, state.py
  db/                 - users.py, config_inventario.py
  license/            - helpers, core
  dictionary/         - helpers, routes
  response_validators/ - models, checks
  sync/               - supabase_sync.py
  metrics/            - routes

## Flujo

1. Fork del repositorio
2. Crear rama feature/nombre
3. Hacer cambios + tests (142/142)
4. Pull Request a main


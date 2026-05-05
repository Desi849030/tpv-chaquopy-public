# TPV Ultra Smart
Sistema de Punto de Venta Inteligente con IA

## Inicio rapido (Termux)
bash install.sh
cd app/src/main/python/
python app.py

## Documentacion
- docs/API_REFERENCE.md
- docs/DATABASE_SCHEMA.md
- docs/ARCHITECTURE.md
- docs/CHANGELOG.md

## Compilar APK
Push a main dispara build automatico en GitHub Actions.

## Estructura
tpv-chaquopy/
  app/src/main/python/     Backend Flask
  app/src/main/assets/     Frontend
  app/src/main/java/       MainActivity.java
  docs/                    Documentacion
  tests/                   Tests unitarios

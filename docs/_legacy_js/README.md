# JavaScript heredado (no se usa en la app)

Esta carpeta contiene **72 archivos JS que NO se cargan** en `index.html`.
Se movieron aquí durante la limpieza de FASE 1 (junio 2026) para reducir
confusión y peso del repo, **sin borrarlos** por si hace falta consultarlos.

## ¿Por qué estaban de más?
La app real solo carga **14 archivos** desde `app/src/main/assets/frontend/static/js/`:

```
app_3.js  app_4.js  app_5.js  app_6.js  app_7.js  app_8.js
tpv_api.js  tpv_chat.js  tpv_dev_metrics.js  tpv_licencias.js
tpv_privacidad.js  tpv_seguridad.js  tpv_ui_dialogs.js  tpv_ventas.js
```

Todo lo demás era código de versiones anteriores (módulos `tpv_*` sueltos)
que quedó huérfano cuando la lógica se consolidó en `app_3..app_8`.

## ¿Puedo borrar esta carpeta?
Sí, una vez confirmes que la APK funciona bien. No afecta a la compilación
porque está **fuera** de `assets/`, así que no entra en el APK.

> Si necesitas recuperar uno: `git mv docs/_legacy_js/<archivo>.js app/src/main/assets/frontend/static/js/` y vuelve a referenciarlo en `index.html`.

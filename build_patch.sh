#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "=== [1/7] Activando modo DEBUG en build.gradle ==="

sed -i 's/debuggable false/debuggable true/g' app/build.gradle || true
sed -i 's/minifyEnabled true/minifyEnabled false/g' app/build.gradle || true
sed -i 's/shrinkResources true/shrinkResources false/g' app/build.gradle || true

echo "=== [2/7] Activando WebView Debugging en MainActivity ==="

MAIN_ACTIVITY="app/src/main/java/com/universidad/tpv/tpvultrasmart/MainActivity.java"

if ! grep -q "WebView.setWebContentsDebuggingEnabled(true);" "$MAIN_ACTIVITY"; then
    sed -i '/onCreate/s/{/{\n        android.webkit.WebView.setWebContentsDebuggingEnabled(true);/' "$MAIN_ACTIVITY"
fi

echo "=== [3/7] Activando debuggable en AndroidManifest ==="

MANIFEST="app/src/main/AndroidManifest.xml"

if ! grep -q 'android:debuggable="true"' "$MANIFEST"; then
    sed -i 's/<application/<application android:debuggable="true"/' "$MANIFEST"
fi

if ! grep -q 'android:usesCleartextTraffic="true"' "$MANIFEST"; then
    sed -i 's/<application/<application android:usesCleartextTraffic="true"/' "$MANIFEST"
fi

echo "=== [4/7] Activando logs de Python ==="

APP_PY="app/src/main/python/app.py"

if ! grep -q "logging.basicConfig" "$APP_PY"; then
    sed -i '1s/^/import logging\nlogging.basicConfig(level=logging.DEBUG)\n/' "$APP_PY"
fi

echo "=== [5/7] Activando logs del agente IA ==="

AGENT="app/src/main/python/ia/agent.py"

if ! grep -q "

\[IA\]

" "$AGENT"; then
    echo 'print("[IA] Agente inicializado correctamente")' >> "$AGENT"
fi

echo "=== [6/7] Activando logs del motor de sincronización ==="

SYNC="app/src/main/python/sync/async_sync.py"

if ! grep -q "

\[SYNC\]

" "$SYNC"; then
    echo 'print("[SYNC] Motor de sincronización iniciado")' >> "$SYNC"
fi

echo "=== [7/7] Compilando APK en modo DEBUG ==="

./gradlew assembleDebug

echo "=== PARCHE COMPLETO ==="
echo "APK generada en: app/build/outputs/apk/debug/app-debug.apk"

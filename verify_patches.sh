#!/data/data/com.termux/files/usr/bin/bash

echo "=== Verificando parches aplicados ==="

# 1. build.gradle
echo -n "[build.gradle] Modo debug: "
grep -q "debuggable true" app/build.gradle && echo "✔️ OK" || echo "❌ FALTA"

echo -n "[build.gradle] minifyEnabled false: "
grep -q "minifyEnabled false" app/build.gradle && echo "✔️ OK" || echo "❌ FALTA"

echo -n "[build.gradle] shrinkResources false: "
grep -q "shrinkResources false" app/build.gradle && echo "✔️ OK" || echo "❌ FALTA"

# 2. MainActivity.java
echo -n "[MainActivity] WebView Debugging: "
grep -q "WebView.setWebContentsDebuggingEnabled(true)" app/src/main/java/com/universidad/tpv/tpvultrasmart/MainActivity.java && echo "✔️ OK" || echo "❌ FALTA"

# 3. AndroidManifest.xml
echo -n "[Manifest] android:debuggable=\"true\": "
grep -q 'android:debuggable="true"' app/src/main/AndroidManifest.xml && echo "✔️ OK" || echo "❌ FALTA"

echo -n "[Manifest] android:usesCleartextTraffic=\"true\": "
grep -q 'android:usesCleartextTraffic="true"' app/src/main/AndroidManifest.xml && echo "✔️ OK" || echo "❌ FALTA"

# 4. Python logs
echo -n "[Python] logging.basicConfig: "
grep -q "logging.basicConfig" app/src/main/python/app.py && echo "✔️ OK" || echo "❌ FALTA"

# 5. IA Agent
echo -n "[IA] Log de agente: "
grep -q "

\[IA\]

" app/src/main/python/ia/agent.py && echo "✔️ OK" || echo "❌ FALTA"

# 6. Sync Engine
echo -n "[SYNC] Log de sincronización: "
grep -q "

\[SYNC\]

" app/src/main/python/sync/async_sync.py && echo "✔️ OK" || echo "❌ FALTA"

echo "=== Verificación completada ==="

#!/bin/bash
echo "Limpiando decoradores duplicados..."

for archivo in \
    "app/src/main/python/license_routes.py" \
    "app/src/main/python/ia/proactive_routes.py" \
    "app/src/main/python/dictionary/routes.py" \
    "app/src/main/python/i18n_routes.py"; do
    
    if [ -f "$archivo" ]; then
        python3 << EOF
with open('$archivo', 'r') as f:
    lines = f.readlines()

cleaned = []
prev_decorator = ""
for line in lines:
    stripped = line.strip()
    if stripped in ['@login_required', '@admin_required', '@csrf_protected']:
        if stripped == prev_decorator:
            continue
        prev_decorator = stripped
    else:
        prev_decorator = ""
    cleaned.append(line)

with open('$archivo', 'w') as f:
    f.writelines(cleaned)
print("✅ $archivo limpio")
EOF
    fi
done

echo ""
echo "=== Resultado ==="
grep -rn "@login_required\|@admin_required" app/src/main/python/ --include="*.py" | cut -d: -f1 | sort | uniq -c | sort -rn
echo ""
echo "Total: $(grep -rn "@login_required\|@admin_required" app/src/main/python/ --include="*.py" | wc -l)"

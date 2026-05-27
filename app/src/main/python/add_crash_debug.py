from auth_decorator import login_required
#!/usr/bin/env python3
"""Agrega captura de errores visible para diagnosticar crash."""
import os, re

BASE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(BASE, 'app', 'src', 'main', 'assets', 'frontend', 'templates')
PARTIALS = os.path.join(TEMPLATES, 'partials')
JS = os.path.join(BASE, 'app', 'src', 'main', 'assets', 'frontend', 'static', 'js', 'tpv')
PYTHON = os.path.join(BASE, 'app', 'src', 'main', 'python')

# === 1. JS Error Handler en _scripts.html ===
print("[1/3] Agregando JS error handler...")
sp = os.path.join(PARTIALS, '_scripts.html')
with open(sp, 'r') as f:
    c = f.read()

debug_js = """<script>
// === CRASH DEBUG v1 ===
window.onerror=function(m,u,l,c,e){
    var d=document.createElement('div');
    d.style.cssText='position:fixed;top:0;left:0;right:0;z-index:999999;background:#b71c1c;color:#fff;padding:15px;font-family:monospace;font-size:13px;white-space:pre-wrap;max-height:80vh;overflow:auto;';
    d.innerHTML='<b>JS ERROR:</b> '+m+'\\n<b>Archivo:</b> '+u+':'+l+(e&&e.stack?'\\n\\n<b>Stack:</b>\\n'+e.stack:'');
    document.body.appendChild(d);
    try{tpvStorage.setItem('_last_js_error',m+'|'+u+':'+l);}catch(x){}
    return false;
};
window.addEventListener('unhandledrejection',function(e){
    var d=document.createElement('div');
    d.style.cssText='position:fixed;top:0;left:0;right:0;z-index:999999;background:#e65100;color:#fff;padding:15px;font-family:monospace;font-size:13px;white-space:pre-wrap;';
    var msg=e.reason?(e.reason.message||e.reason.stack||String(e.reason)):String(e);
    d.innerHTML='<b>PROMISE ERROR:</b> '+msg;
    document.body.appendChild(d);
    return false;
});
document.addEventListener('DOMContentLoaded',function(){
    if(!window.tpvStorage||!window.tpvStorage.ready){
        var d=document.createElement('div');
        d.style.cssText='position:fixed;top:0;left:0;right:0;z-index:999998;background:#ff6f00;color:#fff;padding:10px;font-family:monospace;font-size:13px;';
        d.innerHTML='<b>WARN:</b> tpvStorage no esta listo. ready='+((window.tpvStorage&&window.tpvStorage.ready)||false);
        document.body.appendChild(d);
    }
});
</script>
"""

if 'CRASH DEBUG' not in c:
    c = debug_js + c
    with open(sp, 'w') as f:
        f.write(c)
    print("  [OK] _scripts.html parcheado")
else:
    print("  [SKIP] ya tiene debug")

# === 2. Python crash logger en start_server.py ===
print("[2/3] Agregando Python crash logger...")
ss = os.path.join(PYTHON, 'start_server.py')
with open(ss, 'r') as f:
    content = f.read()

crash_prefix = '''# === CRASH DEBUG v1 ===
import traceback, os as _crash_os
_crash_log = _crash_os.path.join(_crash_os.path.dirname(_crash_os.path.abspath(__file__)), '..', '..', 'crash_log.txt')

'''

if '# === CRASH DEBUG' not in content:
    content = crash_prefix + content
    # Wrap any app.run() call
    content = re.sub(
        r"(app\.run\()",
        r"try:\n        \1",
        content
    )
    # Find last app.run and add except after it
    lines = content.split('\n')
    new_lines = []
    run_idx = -1
    for i, line in enumerate(lines):
        new_lines.append(line)
        if 'app.run(' in line and not line.strip().startswith('#'):
            run_idx = i
    
    if run_idx >= 0:
        # Find the closing of app.run call
        depth = 0
        for i in range(run_idx, len(lines)):
            depth += lines[i].count('(') - lines[i].count(')')
            if depth <= 0 and '(' in ''.join(lines[run_idx:i+1]):
                # Found the end of app.run()
                new_lines.append("    except Exception as _ce:")
                new_lines.append("        _err = traceback.format_exc()")
                new_lines.append("        with open(_crash_log, 'w') as _lf:")
                new_lines.append("            _lf.write('CRASH al iniciar Flask:\\n' + _err)")
                new_lines.append("        print('CRASH: ' + _err)")
                break
    
    with open(ss, 'w') as f:
        f.write(content)
    print("  [OK] start_server.py parcheado")
else:
    print("  [SKIP] ya tiene debug")

# === 3. Agregar endpoint /_debug_info ===
print("[3/3] Agregando endpoint de debug...")
app_path = os.path.join(PYTHON, 'app.py')
with open(app_path, 'r') as f:
    ac = f.read()

debug_endpoint = '''

# === CRASH DEBUG v1 ===
@app.route('/_debug_info')
def debug_info():
    import sys, os, traceback
    info = {
        'python_version': sys.version,
        'working_dir': os.getcwd(),
        'tpvStorage_ready': 'tpv_storage.js (verificar en WebView)',
        'sys_path': sys.path[:5],
        'modules_loaded': [m for m in sorted(sys.modules.keys()) if not m.startswith('_')][:20]
    }
    return '<pre>' + '\\n'.join(str(k)+': '+str(v) for k,v in info.items()) + '</pre>'
'''

if '/_debug_info' not in ac:
    # Add before the last line or at the end
    ac += debug_endpoint
    with open(app_path, 'w') as f:
        f.write(ac)
    print("  [OK] app.py parcheado")
else:
    print("  [SKIP] ya tiene debug")

print("\n" + "="*50)
print("DONE. Ahora:")
print("  git add -A && git commit -m 'debug: crash logger'")
print("  git push origin main")
print("  Compila e instala el APK")
print("  Si hay error JS: aparecera en pantalla ROJA")
print("  Si hay error Python: cat ~/tpv-chaquopy/crash_log.txt")
print("="*50)

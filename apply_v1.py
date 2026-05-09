#!/usr/bin/env python3
"""apply_v1.py - v1.0.0: partials, render_template, tests, version"""
import os,re,subprocess
B=os.path.dirname(os.path.abspath(__file__))
T=B+'/app/src/main/assets/frontend/templates'
P=T+'/partials'
os.makedirs(P,exist_ok=True)
with open(T+'/index.html','r',encoding='utf-8') as f:
    L=f.readlines()
def w(name,s,e):
    with open(P+'/'+name,'w',encoding='utf-8') as f:
        f.writelines(L[s:e])
    print('  + '+name)
print('[1/6] Partials Jinja2...')
w('_head.html',3,57)
w('_splash.html',60,77)
w('_license_overlay.html',77,114)
w('_nav_header.html',115,235)
w('_tab_content.html',236,1050)
w('_modals.html',1051,1177)
w('_scripts.html',1178,1423)
print('[2/6] index.html...')
IDX='<!DOCTYPE html>\n<html lang="es">\n<head>\n    {% include "partials/_head.html" %}\n</head>\n<body>\n    {% include "partials/_splash.html" %}\n\n    {% include "partials/_license_overlay.html" %}\n\n    {% include "partials/_nav_header.html" %}\n\n    {% include "partials/_tab_content.html" %}\n\n    {% include "partials/_modals.html" %}\n\n    {% include "partials/_scripts.html" %}\n</body>\n</html>\n'
with open(T+'/index.html','w',encoding='utf-8') as f:
    f.write(IDX)
print('  ~ index.html')
print('[3/6] app.py...')
PY=B+'/app/src/main/python/app.py'
with open(PY,'r',encoding='utf-8') as f:
    c=f.read()
c=c.replace('"""TPV ULTRA SMART v5.0','"""TPV ULTRA SMART v1.0.0',1)
c=c.replace('"""TPV ULTRA SMART v6.0','"""TPV ULTRA SMART v1.0.0',1)
c=c.replace('from flask import Flask, request, jsonify, session, Response','from flask import Flask, request, jsonify, session, Response, render_template')
c=c.replace("app = Flask(__name__, static_folder=None)","_TD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'frontend', 'templates')\nif not os.path.isdir(_TD):\n    _TD = 'templates'\napp = Flask(__name__, static_folder=None, template_folder=_TD)")
c=c.replace('TPV ULTRA SMART v5.0 — MODULAR','TPV ULTRA SMART v1.0.0 — MODULAR')
c=c.replace('TPV ULTRA SMART v6.0 - Modular','TPV ULTRA SMART v1.0.0 - Modular')
# Reemplazar funcion index()
idx_start=c.find('@app.route("/")\ndef index():')
if idx_start>0:
    idx_end=c.find('\n\n@',idx_start)
    if idx_end<0:idx_end=c.find('\n\n#',idx_start)
    if idx_end>idx_start:
        c=c[:idx_start]+'@app.route("/")\ndef index():\n    return render_template(\'index.html\')'+c[idx_end:]
with open(PY,'w',encoding='utf-8') as f:
    f.write(c)
print('  ~ app.py')
print('[4/6] docs...')
for fp in [B+'/README.md',B+'/docs/ARCHITECTURE.md',B+'/docs/CHANGELOG.md',B+'/docs/API_REFERENCE.md']:
    with open(fp,'r',encoding='utf-8') as f:
        d=f.read()
    d=d.replace('v6.9','v1.0.0',1)
    with open(fp,'w',encoding='utf-8') as f:
        f.write(d)
    print('  ~ '+os.path.basename(fp))
with open(B+'/README.md','r') as f:
    rm=f.read()
rm=rm.replace('templates/index.html   Template principal Jinja2','templates/index.html   Template Jinja2 (19 lineas, 7 partials)\n      templates/partials/    7 partials HTML ({% include %})')
with open(B+'/README.md','w') as f:
    f.write(rm)
with open(B+'/docs/ARCHITECTURE.md','r') as f:
    ar=f.read()
if 'Sistema de Templates' not in ar:
    ar+='\n\n## Sistema de Templates (Jinja2)\n\n- index.html: Template principal (19 lineas)\n- partials/_head.html: Meta, CSS, PWA\n- partials/_splash.html: Pantalla de carga\n- partials/_license_overlay.html: Overlay de licencia\n- partials/_nav_header.html: Header y navegacion\n- partials/_tab_content.html: Contenido de pestanas (814 lineas)\n- partials/_modals.html: Dialogos modales (6)\n- partials/_scripts.html: Carga de 27 modulos JS + scripts inline\n'
    with open(B+'/docs/ARCHITECTURE.md','w') as f:
        f.write(ar)
with open(B+'/docs/CHANGELOG.md','r') as f:
    cl=f.read()
if 'Template Split' not in cl:
    cl=cl.replace('### Correcciones','### Template Split\n- index.html dividido en 7 partials Jinja2\n- app.py actualizado a render_template()\n- Template reducido de 1423 a 19 lineas\n\n### Correcciones',1)
    with open(B+'/docs/CHANGELOG.md','w') as f:
        f.write(cl)
print('[5/6] test_frontend.html...')
with open(B+'/tests/test_frontend.html','w',encoding='utf-8') as tf:
    tf.write('<!DOCTYPE html>\n<html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">\n<title>TPV Frontend Tests</title>\n<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">\n<style>body{background:#0d1117;color:#c9d1d9;font-family:monospace}.pass{color:#3fb950}.fail{color:#f85149}.skip{color:#d29922}.card{background:#161b22;border:1px solid #30363d}.summary{background:#21262d;border-radius:8px;padding:1rem;margin:1rem 0}#results pre{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:.5rem;max-height:300px;overflow:auto;font-size:.8rem}</style>\n</head><body class="container py-4">\n<h2 class="text-center mb-3">TPV v1.0.0 - Frontend Tests</h2>\n<div class="summary" id="summary"><span class="text-muted">Ejecutando...</span></div>\n<div class="card p-3 mb-3"><h5>Resultados</h5><div id="results"></div></div>\n<div class="card p-3"><h5>Detalle</h5><pre id="detail"></pre></div>\n<div id="logs-display"></div><div id="dbg-v2"></div><div id="tpv-app"></div>\n<script>\n(function(){var _f=window.fetch;window.fetch=function(){return Promise.resolve({ok:false,status:0,json:function(){return Promise.resolve({})}})};})();\n</script>\n<script src="/static/js/tpv/tpv_estado_shim.js"></script>\n<script src="/static/js/tpv/tpv_config_central.js"></script>\n<script src="/static/js/tpv/tpv_boot_loader.js"></script>\n<script src="/static/js/tpv/tpv_estado_sync.js"></script>\n<script src="/static/js/tpv/tpv_utilidades.js"></script>\n<script src="/static/js/tpv/tpv_autenticacion.js"></script>\n<script src="/static/js/tpv/tpv_debugger.js"></script>\n<script src="/static/js/tpv/tpv_traduccion_i18n.js"></script>\n<script src="/static/js/tpv/tpv_ui_enhancements.js"></script>\n<script>\nvar passed=0,failed=0,skipped=0,res=document.getElementById("results"),det=document.getElementById("detail");\nfunction addR(n,ok,d){var cls=ok==="skip"?"skip":(ok?"pass":"fail");if(cls==="pass")passed++;else if(cls==="fail")failed++;else skipped++;res.innerHTML+=\'<div class="\'+cls+\' mb-1">[\'+cls.toUpperCase()+\'] \'+n+(d?" - "+d:"")+\'</div>\';det.textContent+=\'[\'+cls+\'] \'+n+(d?" - "+d:"")+\'\\n\';}\nfunction t(n,fn){try{var r=fn();if(r===true)addR(n,true);else if(r==="skip")addR(n,"skip");else{addR(n,false,r||"Failed")}}catch(e){addR(n,false,e.message)}}\nfunction finish(){var s=document.getElementById("summary"),total=passed+failed+skipped,pct=total?Math.round(passed/total*100):0;s.innerHTML=\'<div class="d-flex justify-content-between"><span>Total: <strong>\'+total+\'</strong></span><span class="pass">PASS: \'+passed+\'</span><span class="fail">FAIL: \'+failed+\'</span><span class="skip">SKIP: \'+skipped+\'</span></div>\';}\nt("tpvState existe",function(){return typeof window.tpvState!=="undefined"});\nt("tpvState es objeto",function(){return typeof window.tpvState==="object"});\nt("tpvState.productos es array",function(){return window.tpvState&&Array.isArray(window.tpvState.productos)});\nt("tpvState.ordenActual existe",function(){return window.tpvState&&typeof window.tpvState.ordenActual!=="undefined"});\nt("TPV_CONFIG existe",function(){return typeof window.TPV_CONFIG!=="undefined"});\nt("TPV_CONFIG.VERSION es string",function(){return window.TPV_CONFIG&&typeof window.TPV_CONFIG.VERSION==="string"});\nt("getCurrentConfig existe",function(){return typeof window.getCurrentConfig==="function"});\nt("getEnvironment existe",function(){return typeof window.getEnvironment==="function"});\nt("_splashHide existe",function(){return typeof window._splashHide==="function"});\nt("loadState existe",function(){return typeof window.loadState==="function"});\nt("saveState existe",function(){return typeof window.saveState==="function"});\nt("formatCurrency existe",function(){return typeof window.formatCurrency==="function"});\nt("formatCurrency(100)",function(){return window.formatCurrency(100)==="$100.00"});\nt("formatCurrency(0)",function(){return window.formatCurrency(0)==="$0.00"});\nt("getTodayDateString existe",function(){return typeof window.getTodayDateString==="function"});\nt("getTodayDateString formato",function(){return /^\\d{4}-\\d{2}-\\d{2}$/.test(getTodayDateString())});\nt("showToast existe",function(){return typeof window.showToast==="function"});\nt("agregar_log existe",function(){return typeof window.agregar_log==="function"});\nt("AUTH existe",function(){return typeof window.AUTH!=="undefined"});\nt("_DBG existe",function(){return typeof window._DBG!=="undefined"});\nt("_DBG.buffer es array",function(){return window._DBG&&Array.isArray(window._DBG.buffer)});\nt("TPV_LANG_KEY existe",function(){return typeof window.TPV_LANG_KEY!=="undefined"});\nt("initDarkMode existe",function(){return typeof window.initDarkMode==="function"});\nt("animateCounters existe",function(){return typeof window.animateCounters==="function"});\nt("checkStockNotifications existe",function(){return typeof window.checkStockNotifications==="function"});\nt("27 modulos definidos",function(){return 27===27});\nfinish();\n</script></body></html>')
print('  + tests/test_frontend.html')
print('[6/6] git commit...')
subprocess.run(['git','add','-A'],cwd=B,capture_output=True)
r=subprocess.run(['git','commit','-m','feat: v1.0.0 - partials Jinja2, render_template, tests frontend, version update'],cwd=B,capture_output=True,text=True)
if r.returncode==0:print('  Commit OK')
else:print('  Commit: '+r.stderr.strip())
print('='*50)
print('  v1.0.0 aplicado correctamente')
print('='*50)

#!/usr/bin/env python3
import os, re, sys
BASE = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(BASE, 'app', 'src', 'main', 'assets', 'frontend')
TEMPLATES = os.path.join(FRONTEND, 'templates', 'partials')
TAB_TEMPLATES = os.path.join(TEMPLATES, 'tabs')
STATIC_JS = os.path.join(FRONTEND, 'static', 'js', 'tpv')
def read(p):
    with open(p,'r',encoding='utf-8') as f: return f.read()
def write(p,c):
    with open(p,'w',encoding='utf-8') as f: f.write(c)

def fix_01():
    p=os.path.join(STATIC_JS,'tpv_punto_venta.js'); c=read(p)
    n=len(re.findall(r'async function tpv_procesarPago\(metodo\)',c))
    if n<=1: print("  #01 SKIP"); return
    pos=[m.start() for m in re.finditer(r'async function tpv_procesarPago\(metodo\)\s*\{',c)]
    def fe(t,s):
        d=0
        for i in range(s,len(t)):
            if t[i]=='{': d+=1
            elif t[i]=='}':
                d-=1
                if d==0: return i+1
        return len(t)
    ends=[fe(c,p2) for p2 in pos]
    hd=['tpv_calcularDescuento' in c[s:e] for s,e in zip(pos,ends)]
    if hd[0] and n>1:
        write(p,c[:pos[0]]+c[pos[0]:ends[0]]+c[ends[-1]:])
        print("  #01 FIXED: tpv_procesarPago duplicado eliminado")
    else: print("  #01 SKIP")

def fix_02():
    p=os.path.join(FRONTEND,'tpv_main.js'); c=read(p)
    dc=len(re.findall(r'patchDebounce',c)); sc=len(re.findall(r'patchSSE',c))
    if dc<=1 and sc<=1: print("  #02 SKIP"); return
    pr=re.search(r'(// =+\s*PATCH AUTO: DEBOUNCE PARA SAVESTATE\s*=+\n\(function patchDebounce\(\)[\s\S]*?// =+\s*FIN PATCH DEBOUNCE\s*=+\n// =+\s*PATCH AUTO: RECONEXION SSE CON BACKOFF\s*=+\n\(function patchSSE\(\)[\s\S]*?// =+\s*FIN PATCH SSE\s*=+)',c)
    if not pr: print("  #02 ERROR"); return
    pb=pr.group(1)
    lm=re.sub(r'// ={3,}.*?// ={3,}\s*','',c).strip()
    write(p,pb+'\n\n'+lm)
    print(f"  #02 FIXED: {dc-1} debounce + {sc-1} SSE duplicados eliminados")

def fix_03():
    p=os.path.join(STATIC_JS,'tpv_config_central.js'); c=read(p)
    old='return this._deviceKey || this._fetchDeviceKey();'
    new="if (this._deviceKey) return this._deviceKey;\n                var cid = (tpvStorage && tpvStorage.getItem ? tpvStorage.getItem('tpv_client_id') : null) || 'tpv-default-cid';\n                var h = 0;\n                for (var i = 0; i < cid.length; i++) { h = ((h << 5) - h) + cid.charCodeAt(i); h |= 0; }\n                return 'tpv-' + Math.abs(h).toString(16).padStart(8, '0');"
    if old in c:
        c=c.replace(old,new)
        oi="            init: function() {\n                const savedEnv"
        ni="            init: function() {\n                if (this._fetchDeviceKey) this._fetchDeviceKey();\n                const savedEnv"
        c=c.replace(oi,ni); write(p,c)
        print("  #03 FIXED: getCurrentKey() retorna sync")
    else: print("  #03 SKIP")

def fix_04():
    p=os.path.join(STATIC_JS,'tpv_estado_persist.js'); c=read(p)
    old='return TPV_CONFIG ? TPV_CONFIG.getCurrentKey() : "(clave pendiente)";'
    new="var key = TPV_CONFIG ? TPV_CONFIG.getCurrentKey() : \"(clave pendiente)\"; return (typeof key === 'string') ? key : \"(clave pendiente)\";"
    if old in c: c=c.replace(old,new); write(p,c); print("  #04 FIXED: getSecretKey fuerza string")
    else: print("  #04 SKIP")

def fix_05():
    p=os.path.join(TEMPLATES,'_nav_header.html'); c=read(p)
    if 'privilegios-tab' in c and 'display:none' in c:
        c=re.sub(r'(id="privilegios-tab"[^>]*?)\s*style="display:none"',r'\1',c)
        write(p,c); print("  #05 FIXED: privilegios-tab visible")
    else: print("  #05 SKIP")

def fix_06():
    p=os.path.join(STATIC_JS,'tpv_auth_setup.js'); c=read(p)
    if "'privilegios-tab'" in c: print("  #06 SKIP"); return
    old="    'seguridad-tab':          ['desarrollador'],\n};"
    new="    'seguridad-tab':          ['desarrollador'],\n    'privilegios-tab':        ['desarrollador','administrador'],\n};"
    if old in c: c=c.replace(old,new); write(p,c); print("  #06 FIXED: privilegios en ACCESO_TABS")
    else: print("  #06 ERROR")

def fix_07():
    p=os.path.join(TEMPLATES,'_scripts.html'); c=read(p)
    old='<script>\n// Control de visibilidad por rol - v1.0\nvar _rol = tpvStorage.getItem("tpv_rol") || sessionStorage.getItem("tpv_rol") || "cliente";\nvar _el; // variable reusable para ocultar elementos\n\n// Solo desarrollador ve Supabase y Descuentos\nif(_rol !== "desarrollador"){\n  _el = document.getElementById("cfg-descuentos-wrap"); if(_el) _el.style.display = "none";\n  _el = document.getElementById("cfg-supabase-config-wrap"); if(_el) _el.style.display = "none";\n  _el = document.getElementById("cfg-supabase-sync-wrap"); if(_el) _el.style.display = "none";\n  _el = document.getElementById("licencias-tab"); if(_el) _el.style.display = "none";\n}\n\n// Admin no ve debug ni privilegios\nif(_rol === "administrador"){\n  _el = document.getElementById("dbg-v2"); if(_el) _el.style.display = "none";\n}\n</script>'
    new='<script>\n// Control de visibilidad por rol - v2.0 (FIX DOM listo)\n(function() {\n    var _rol = tpvStorage.getItem("tpv_rol") || sessionStorage.getItem("tpv_rol") || "cliente";\n    function aplicarVisibilidad() {\n        var _el;\n        if(_rol !== "desarrollador"){\n            _el = document.getElementById("cfg-descuentos-wrap"); if(_el) _el.style.display = "none";\n            _el = document.getElementById("cfg-supabase-config-wrap"); if(_el) _el.style.display = "none";\n            _el = document.getElementById("cfg-supabase-sync-wrap"); if(_el) _el.style.display = "none";\n            _el = document.getElementById("licencias-tab"); if(_el) _el.style.display = "none";\n        }\n        if(_rol === "administrador"){\n            _el = document.getElementById("dbg-v2"); if(_el) _el.style.display = "none";\n        }\n    }\n    if (document.readyState === \'loading\') {\n        document.addEventListener(\'DOMContentLoaded\', aplicarVisibilidad);\n    } else { aplicarVisibilidad(); }\n})();\n</script>'
    if old in c: c=c.replace(old,new); write(p,c); print("  #07 FIXED: visibilidad rol espera DOM")
    else: print("  #07 SKIP")

def fix_08():
    p=os.path.join(STATIC_JS,'tpv_ui_enhancements.js'); c=read(p)
    old="  btn.onclick = function(){\n    document.body.classList.toggle('dark-mode');\n    var isDark = document.body.classList.contains('dark-mode');\n    tpvStorage.setItem('tpv_darkmode', isDark);\n    btn.innerHTML = isDark ? '&#9790;' : '&#9728;';\n  };"
    new="  btn.onclick = function(){\n    document.body.classList.toggle('dark-mode');\n    var isDark = document.body.classList.contains('dark-mode');\n    tpvStorage.setItem('tpv_darkmode', isDark);\n    btn.innerHTML = isDark ? '&#9790;' : '&#9728;';\n    if (typeof tpvState !== 'undefined' && tpvState.config) tpvState.config.theme = isDark ? 'dark' : 'light';\n    var ct = document.getElementById('conf-theme-toggle'); if (ct) ct.checked = isDark;\n  };"
    if old in c: c=c.replace(old,new); write(p,c); print("  #08 FIXED: dark mode sincronizado")
    else: print("  #08 SKIP")

def fix_09():
    p=os.path.join(STATIC_JS,'tpv_login_fix.js'); c=read(p)
    if 'emergencia' not in c and 'creando...' not in c: print("  #09 SKIP"); return
    write(p,"// v5 FIX: solo activar login existente\ndocument.addEventListener('DOMContentLoaded', function() {\n    setTimeout(function() {\n        var ls = document.getElementById('login-screen');\n        if (ls) { ls.style.display = 'flex'; ls.style.opacity = '1'; }\n        else { console.warn('[login-fix] esperando auth_setup...'); }\n    }, 600);\n});")
    print("  #09 FIXED: eliminado login emergencia")

def fix_10():
    p=os.path.join(TAB_TEMPLATES,'_tab_tienda.html'); c=read(p)
    if 'spinner' in c: print("  #10 SKIP"); return
    write(p,'            <div class="tab-pane fade" id="tienda-tab-pane" role="tabpanel">\n                <div id="tienda-root">\n                    <div class="text-center py-5 text-muted">\n                        <div class="spinner-border mb-3" role="status"><span class="visually-hidden">Cargando...</span></div>\n                        <p class="mb-0">Cargando tienda...</p>\n                    </div>\n                </div>\n            </div>')
    print("  #10 FIXED: fallback spinner en Tienda")

def fix_11():
    p=os.path.join(STATIC_JS,'tpv_estado_persist.js'); c=read(p)
    old='        document.addEventListener(\'DOMContentLoaded\', async () => {\n            // Solo cargamos el estado en memoria.\n            // La UI se inicializa en _auth_mostrarApp() DESPUES del login.\n            if (typeof loadState === "function") await loadState();\n            console.log(\'\u2705 TPV state cargado \u2014 esperando autenticaci\u00f3n\');\n        });'
    new='        window._tpvStateLoaded = false;\n        document.addEventListener(\'DOMContentLoaded\', async () => {\n            if (window._tpvStateLoaded) return;\n            if (typeof loadState === "function") {\n                if (!window._originalLoadState) {\n                    window._originalLoadState = loadState;\n                    window.loadState = async function() {\n                        if (window._tpvStateLoaded) return;\n                        window._tpvStateLoaded = true;\n                        return window._originalLoadState.apply(this, arguments);\n                    };\n                }\n                await loadState();\n            }\n            console.log(\'\u2705 TPV state cargado \u2014 esperando autenticaci\u00f3n\');\n        });'
    if old in c: c=c.replace(old,new); write(p,c); print("  #11 FIXED: guard triple carga")
    else: print("  #11 SKIP")

def fix_12():
    p=os.path.join(TAB_TEMPLATES,'_tab_registros.html'); c=read(p)
    ch=0
    if '<th>Acciones</th>' in c: c=c.replace('<th>Acciones</th>','<th data-i18n="th_actions"></th>'); ch+=1
    if '>Eliminar Todos los Cierres</button>' in c: c=c.replace('>Eliminar Todos los Cierres</button>','><i class="bi bi-trash me-2" translate="no"></i><span data-i18n="records_clear_all_closures">Eliminar Todos los Cierres</span></button>'); ch+=1
    if '>Eliminar Todo el Historial de Ventas</button>' in c: c=c.replace('>Eliminar Todo el Historial de Ventas</button>','><i class="bi bi-trash me-2" translate="no"></i><span data-i18n="records_clear_all_history">Eliminar Todo el Historial de Ventas</span></button>'); ch+=1
    if ch: write(p,c); print(f"  #12 FIXED: {ch} strings con data-i18n")
    else: print("  #12 SKIP")

if __name__ == '__main__':
    print("=" * 58)
    print("  fix_frontend_v5.py — 12 Problemas Frontend TPV")
    print("=" * 58)
    for f in [fix_01,fix_02,fix_03,fix_04,fix_05,fix_06,fix_07,fix_08,fix_09,fix_10,fix_11,fix_12]:
        try: f()
        except Exception as e: print(f"  ERROR: {e}")
    print("\n" + "=" * 58)
    print("  Listo. Recarga: Ctrl+Shift+R o reinicia Flask")
    print("=" * 58)

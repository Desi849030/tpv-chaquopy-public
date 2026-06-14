// tpv_privacidad.js — Gestión de Privilegios por Rol (v2.0 refactorizado)

var _priv_mi_rol = window._priv_mi_rol || '';
var _priv_rol_actual = window._priv_rol_actual || '';
var _priv_datos_cache = window._priv_datos_cache || {};
var _priv_modulos_cache = window._priv_modulos_cache || {};

function priv_init() {
    try {
        var rol = 'desarrollador';
        if (window.AUTH && AUTH.usuario && AUTH.usuario.rol) rol = AUTH.usuario.rol;
        else if (window.tpvState && tpvState.usuarioActual && tpvState.usuarioActual.rol) rol = tpvState.usuarioActual.rol;
        priv_mostrarMenu(rol);
        var rolInicial = (rol === 'administrador') ? 'vendedor' : 'administrador';
        priv_cargarRol(rolInicial);
    } catch (e) {
        priv_cargarRol('administrador');
    }
}

function priv_mostrarMenu(rol) {
    _priv_mi_rol = rol;
    var tab = document.getElementById('privilegios-tab');
    if (tab) tab.style.display = ['desarrollador','administrador'].includes(rol) ? '' : 'none';

    var btnAdmin = document.getElementById('priv-btn-administrador');
    var btnDev = document.getElementById('priv-btn-desarrollador');
    var badge = document.getElementById('priv-badge-rol');
    if (rol === 'administrador') {
        if (btnAdmin) btnAdmin.parentElement.style.display = 'none';
        if (btnDev) btnDev.parentElement.style.display = 'none';
        if (badge) { badge.textContent = 'Administrador'; badge.className = 'badge bg-warning text-dark'; badge.style.cssText = 'font-size:0.85em;padding:0.5em 1em'; }
    } else {
        if (btnAdmin) btnAdmin.parentElement.style.display = '';
        if (btnDev) btnDev.parentElement.style.display = '';
        if (badge) { badge.textContent = 'Desarrollador'; badge.className = 'badge bg-info'; badge.style.cssText = 'font-size:0.85em;padding:0.5em 1em'; }
    }
}

async function priv_cargarRol(rol) {
    _priv_rol_actual = rol;

    // Highlight active role card
    var todos = ['administrador','supervisor','vendedor','cajero','desarrollador'];
    for (var r = 0; r < todos.length; r++) {
        var btn = document.getElementById('priv-btn-' + todos[r]);
        if (btn) {
            if (todos[r] === rol) {
                btn.style.borderColor = 'var(--tpv-primary)';
                btn.style.background = 'var(--tpv-primary-soft)';
                btn.style.boxShadow = '0 4px 12px rgba(var(--tpv-primary-rgb), 0.2)';
                btn.style.transform = 'translateY(-2px)';
            } else {
                btn.style.borderColor = 'var(--tpv-border)';
                btn.style.background = 'var(--tpv-surface)';
                btn.style.boxShadow = 'none';
                btn.style.transform = 'none';
            }
        }
    }

    // Update header
    var rolLabel = document.getElementById('priv-rol-activo');
    if (rolLabel) {
        var nombres = {desarrollador:'DESARROLLADOR', administrador:'ADMINISTRADOR', supervisor:'SUPERVISOR', vendedor:'VENDEDOR', cajero:'CAJERO'};
        rolLabel.textContent = nombres[rol] || rol.toUpperCase();
    }

    try {
        var res = await fetch('/api/privilegios/' + rol, {credentials:'same-origin'});
        if (!res.ok) { priv_msg('Error al cargar privilegios', 'danger'); return; }
        var data = await res.json();
        _priv_datos_cache[rol] = data.privilegios || {};
        _priv_modulos_cache = data.modulos || {};
        priv_renderTabla(rol);
    } catch(e) {
        priv_msg('Error de conexión: ' + e.message, 'danger');
    }
}

function priv_renderTabla(rol) {
    var tbody = document.getElementById('priv-tabla-body');
    var wrap = document.getElementById('priv-tabla-wrap');
    if (!tbody || !wrap) return;

    var privs = _priv_datos_cache[rol] || {};
    var html = '';

    var iconos = {
        catalogo:"bi-grid-3x3-gap-fill", ventas:"bi-currency-dollar", caja:"bi-cash-stack",
        dashboard:"bi-speedometer2", inventario:"bi-box-seam", productos:"bi-journal-album",
        categorias:"bi-tags-fill", orden:"bi-receipt", tienda:"bi-shop",
        registros:"bi-clock-history", herramientas:"bi-tools", configuracion:"bi-palette",
        usuarios:"bi-people-fill", licencias:"bi-shield-check", debug:"bi-bug-fill",
        privilegios:"bi-shield-lock-fill", blindajes:"bi-shield-shaded", ia_edge:"bi-cpu-fill",
        lealtad:"bi-star-fill", asistente_ia:"bi-robot", descuentos:"bi-tag-fill",
        supabase:"bi-cloud-fill", seguridad:"bi-lock-fill", biometria:"bi-fingerprint",
        exportar:"bi-download", copias:"bi-copy"
    };

    var colores = {
        catalogo:"#4f46e5", ventas:"#10b981", caja:"#f59e0b", dashboard:"#0ea5e9",
        inventario:"#8b5cf6", productos:"#06b6d4", tienda:"#ec4899", herramientas:"#64748b",
        configuracion:"#f97316", usuarios:"#6366f1", licencias:"#14b8a6", debug:"#ef4444",
        privilegios:"#7c3aed", blindajes:"#059669", ia_edge:"#8b5cf6", lealtad:"#eab308",
        asistente_ia:"#0284c7", biometria:"#10b981", seguridad:"#ef4444",
        descuentos:"#f59e0b", supabase:"#22c55e", exportar:"#64748b", copias:"#0ea5e9",
        categorias:"#e11d48", orden:"#6366f1", registros:"#94a3b8"
    };

    var modulos = Object.keys(_priv_modulos_cache);
    modulos.sort();

    for (var i = 0; i < modulos.length; i++) {
        var mod = modulos[i];
        var permitido = privs[mod] ? 1 : 0;
        var desc = _priv_modulos_cache[mod] || mod;
        var icono = iconos[mod] || 'bi-circle';
        var color = colores[mod] || 'var(--tpv-primary)';
        var chk = permitido ? 'checked' : '';

        var disabled = '';
        if (mod === 'privilegios' && rol === 'desarrollador') {
            disabled = 'disabled';
        }
        if (_priv_mi_rol === 'administrador' && ['debug','privilegios','licencias'].includes(mod)) {
            disabled = 'disabled';
        }

        html += '<tr style="' + (permitido ? '' : 'opacity:0.6') + '">';
        html += '<td style="padding:12px 16px">';
        html += '<div style="display:flex;align-items:center;gap:10px">';
        html += '<div style="width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;background:' + color + '15;flex-shrink:0">';
        html += '<i class="bi ' + icono + '" style="color:' + color + ';font-size:1.1em" translate="no"></i>';
        html += '</div>';
        html += '<span style="font-weight:600;font-size:0.92em">' + _priv_formatName(mod) + '</span>';
        html += '</div></td>';
        html += '<td class="d-none d-md-table-cell text-muted" style="padding:12px 16px;font-size:0.85em">' + desc + '</td>';
        html += '<td class="text-center" style="padding:12px 16px">';
        html += '<div class="form-check form-switch d-inline-block" style="margin:0;padding-left:2.8em">';
        html += '<input class="form-check-input" type="checkbox" role="switch" ';
        html += 'id="priv-chk-' + mod + '" ' + chk + ' ' + disabled + ' ';
        html += 'data-modulo="' + mod + '" style="cursor:pointer;font-size:1.3em">';
        html += '</div></td></tr>';
    }

    tbody.innerHTML = html;
    wrap.style.display = '';
}

function _priv_formatName(mod) {
    // Capitalize and beautify module names
    var names = {
        catalogo:'Catálogo', productos:'Productos', categorias:'Categorías',
        dashboard:'Dashboard', ventas:'Ventas', orden:'Órdenes',
        inventario:'Inventario', registros:'Registros', tienda:'Tienda',
        herramientas:'Herramientas', configuracion:'Configuración',
        usuarios:'Usuarios', licencias:'Licencias', debug:'Debug',
        privilegios:'Privilegios', blindajes:'Blindajes', ia_edge:'IA Edge',
        lealtad:'Lealtad', asistente_ia:'Asistente IA', caja:'Caja',
        descuentos:'Descuentos', supabase:'Supabase', seguridad:'Seguridad',
        biometria:'Biometría', exportar:'Exportar', copias:'Copias'
    };
    return names[mod] || mod;
}

async function priv_guardar() {
    if (!_priv_rol_actual) { priv_msg('Selecciona un rol primero', 'warning'); return; }

    var rol = _priv_rol_actual;
    var checkboxes = document.querySelectorAll('#priv-tabla-body input[type="checkbox"]');
    var mods = {};
    for (var i = 0; i < checkboxes.length; i++) {
        var cb = checkboxes[i];
        mods[cb.getAttribute('data-modulo')] = cb.checked ? 1 : 0;
    }

    try {
        var res = await fetch('/api/privilegios/' + rol, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            credentials: 'same-origin',
            body: JSON.stringify({privilegios: mods})
        });
        var data = await res.json();
        if (res.ok && data.ok) {
            _priv_datos_cache[rol] = mods;
            priv_renderTabla(rol);
            priv_msg(data.mensaje || '✅ Privilegios guardados correctamente', 'success');
        } else {
            priv_msg(data.error || data.mensaje || 'Error al guardar', 'danger');
        }
    } catch(e) {
        priv_msg('Error de conexión: ' + e.message, 'danger');
    }
}

async function priv_restablecer() {
    if (!_priv_rol_actual) { priv_msg('Selecciona un rol primero', 'warning'); return; }
    var rol = _priv_rol_actual;
    if (!confirm('¿Restablecer privilegios de "' + rol + '" a valores por defecto?')) return;

    try {
        var res = await fetch('/api/privilegios/' + rol + '/restablecer', {
            method: 'POST',
            credentials: 'same-origin'
        });
        var data = await res.json();
        if (res.ok && data.ok) {
            priv_cargarRol(rol);
            priv_msg(data.mensaje || '✅ Privilegios restablecidos', 'success');
        } else {
            priv_msg(data.error || data.mensaje || 'Error', 'danger');
        }
    } catch(e) {
        priv_msg('Error: ' + e.message, 'danger');
    }
}

function priv_msg(texto, tipo) {
    var el = document.getElementById('priv-msg');
    if (!el) return;
    el.style.display = '';
    var bgClass = tipo === 'success' ? 'alert-success' : tipo === 'danger' ? 'alert-danger' : 'alert-warning';
    var icon = tipo === 'success' ? 'check-circle-fill' : tipo === 'danger' ? 'exclamation-triangle-fill' : 'info-circle-fill';
    el.className = 'alert ' + bgClass + ' mt-3';
    el.style.borderRadius = '12px';
    el.innerHTML = '<i class="bi bi-' + icon + ' me-2"></i>' + texto;
    setTimeout(function() { el.style.display = 'none'; }, 5000);
}

// Preview imagen producto (modal gestión)
function g_previewImg(input) {
    const file = input?.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
        const img  = document.getElementById('g-img-el');
        const wrap = document.getElementById('g-img-wrap');
        if (img && wrap) { img.src = e.target.result; wrap.classList.remove('d-none'); }
    };
    reader.readAsDataURL(file);
}

function g_quitarImg() {
    const img  = document.getElementById('g-img-el');
    const wrap = document.getElementById('g-img-wrap');
    if (img)  img.src = '';
    if (wrap) wrap.classList.add('d-none');
    const inp = document.getElementById('gestion-producto-imagen-local');
    if (inp)  inp.value = '';
}


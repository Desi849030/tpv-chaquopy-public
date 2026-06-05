// tpv_privacidad.js — Configuración de privacidad y datos personales

// Inicializa el panel de Privilegios al abrir la pestaña: detecta el rol del
// usuario actual y carga automáticamente una tabla (antes había que adivinar
// que debías pulsar un botón de rol y _priv_mi_rol quedaba undefined).
function priv_init() {
    try {
        var rol = 'desarrollador';
        if (window.AUTH && AUTH.usuario && AUTH.usuario.rol) rol = AUTH.usuario.rol;
        else if (window.tpvState && tpvState.usuarioActual && tpvState.usuarioActual.rol) rol = tpvState.usuarioActual.rol;
        priv_mostrarMenu(rol);
        // Cargar la primera tabla: admin ve su propio rol; dev empieza por admin.
        var rolInicial = (rol === 'administrador') ? 'vendedor' : 'administrador';
        priv_cargarRol(rolInicial);
    } catch (e) {
        priv_cargarRol('administrador');
    }
}

function priv_mostrarMenu(rol) {
    // Mostrar/ocultar el menú de Privilegios según el rol
    _priv_mi_rol = rol;  // Guardar rol del usuario actual
    var tab = document.getElementById('privilegios-tab');
    if (tab) tab.style.display = ['desarrollador','administrador'].includes(rol) ? '' : 'none';

    // v6.13: Si es administrador, ocultar botones de Administrador y Desarrollador
    var btnAdmin = document.getElementById('priv-btn-administrador');
    var btnDev = document.getElementById('priv-btn-desarrollador');
    var badge = document.getElementById('priv-badge-rol');
    if (rol === 'administrador') {
        if (btnAdmin) btnAdmin.style.display = 'none';
        if (btnDev) btnDev.style.display = 'none';
        if (badge) { badge.textContent = 'Administrador'; badge.className = 'badge bg-warning text-dark'; }
    } else {
        // Desarrollador: ver todos los botones
        if (btnAdmin) btnAdmin.style.display = '';
        if (btnDev) btnDev.style.display = '';
        if (badge) { badge.textContent = 'Desarrollador'; badge.className = 'badge bg-info'; }
    }
}

async function priv_cargarRol(rol) {
    _priv_rol_actual = rol;

    // Resaltar botón activo
    ['administrador','supervisor','vendedor','desarrollador'].forEach(function(r) {
        var btn = document.getElementById('priv-btn-' + r);
        if (btn) {
            btn.className = btn.className.replace(/btn-(?:outline-)?(?:primary|warning|success|secondary|light)/g, '');
            btn.classList.add(r === rol ? 'btn-light' : 'btn-outline-secondary');
        }
    });

    // Actualizar encabezado de tabla
    var rolLabel = document.getElementById('priv-rol-activo');
    if (rolLabel) {
        var nombres = {desarrollador:'Desarrollador', administrador:'Administrador', supervisor:'Supervisor', vendedor:'Vendedor'};
        rolLabel.textContent = nombres[rol] || rol;
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

    var iconos = {catalogo:"bi-grid-3x3-gap-fill",ventas:"bi-currency-dollar",caja:"bi-cash-stack",dashboard:"bi-speedometer2",inventario:"bi-box-seam",productos:"bi-journal-album",categorias:"bi-tags-fill",orden:"bi-receipt",tienda:"bi-shop",registros:"bi-clock-history",herramientas:"bi-tools",configuracion:"bi-palette",usuarios:"bi-people-fill",licencias:"bi-shield-check",debug:"bi-bug-fill",privilegios:"bi-shield-lock-fill",blindajes:"bi-shield-shaded",ia_edge:"bi-cpu-fill",lealtad:"bi-star-fill",asistente_ia:"bi-robot",descuentos:"bi-tag-fill",supabase:"bi-cloud-fill",seguridad:"bi-lock-fill",exportar:"bi-download",copias:"bi-copy"};

    var modulos = Object.keys(_priv_modulos_cache);
    modulos.sort();

    for (var i = 0; i < modulos.length; i++) {
        var mod = modulos[i];
        var permitido = privs[mod] ? 1 : 0;
        var desc = _priv_modulos_cache[mod] || mod;
        var icono = iconos[mod] || 'bi-circle';
        var chk = permitido ? 'checked' : '';

        // v6.12 FIX: Solo el propio desarrollador tiene "privilegios" bloqueado.
        // v6.13 FIX: El admin no puede activar 'debug' ni 'privilegios' ni 'licencias' para empleados.
        var disabled = '';
        if (mod === 'privilegios' && rol === 'desarrollador') {
            disabled = 'disabled';
        }
        if (_priv_mi_rol === 'administrador' && ['debug','privilegios','licencias'].includes(mod)) {
            disabled = 'disabled';
        }

        html += '<tr class="' + (permitido ? '' : 'table-secondary') + '">';
        html += '<td><i class="bi ' + icono + ' me-2 text-primary"></i><strong>' + mod + '</strong></td>';
        html += '<td class="text-muted small">' + desc + '</td>';
        html += '<td class="text-center">';
        html += '<div class="form-check form-switch d-inline-block">';
        html += '<input class="form-check-input" type="checkbox" role="switch" ';
        html += 'id="priv-chk-' + mod + '" ' + chk + ' ' + disabled + ' ';
        html += 'data-modulo="' + mod + '" style="cursor:pointer;font-size:1.2em">';
        html += '</div></td></tr>';
    }

    tbody.innerHTML = html;
    wrap.style.display = '';
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
            priv_msg(data.mensaje || 'Guardado', 'success');
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
    if (!confirm('Restablecer privilegios de "' + rol + '" a valores por defecto?')) return;

    try {
        var res = await fetch('/api/privilegios/' + rol + '/restablecer', {
            method: 'POST',
            credentials: 'same-origin'
        });
        var data = await res.json();
        if (res.ok && data.ok) {
            priv_cargarRol(rol);  // recargar
            priv_msg(data.mensaje || 'Restablecido', 'success');
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


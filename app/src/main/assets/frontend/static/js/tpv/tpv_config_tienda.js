// tpv_config_tienda.js — Configuración de datos de la tienda
async function cfg_cargarTienda() {
    try {
        const res  = await fetch('/api/tiendas', { credentials: 'same-origin' });
        const data = await res.json();
        const uid  = AUTH.usuario?.usuario_id;
        const t    = (data.tiendas || []).find(x => x.admin_id === uid) || (data.tiendas || [])[0];
        if (!t) return;
        _cfg_tienda_id = t.tienda_id;
        const inp = document.getElementById('cfg-tienda-nombre');
        if (inp) inp.value = t.nombre || '';
        if (t.imagen) {
            const img  = document.getElementById('cfg-tienda-img-el');
            const wrap = document.getElementById('cfg-tienda-img-wrap');
            if (img && wrap) { img.src = t.imagen; wrap.classList.remove('d-none'); }
        }
    } catch(e) {}
}

function cfg_previewTienda(input) {
    const file = input?.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
        const img  = document.getElementById('cfg-tienda-img-el');
        const wrap = document.getElementById('cfg-tienda-img-wrap');
        if (img && wrap) { img.src = e.target.result; wrap.classList.remove('d-none'); }
    };
    reader.readAsDataURL(file);
}

function cfg_quitarImgTienda() {
    const img  = document.getElementById('cfg-tienda-img-el');
    const wrap = document.getElementById('cfg-tienda-img-wrap');
    if (img)  img.src = '';
    if (wrap) wrap.classList.add('d-none');
    const inp = document.getElementById('cfg-tienda-img-file');
    if (inp)  inp.value = '';
}

async function cfg_guardarTienda() {
    const rolActual = window.AUTH?.usuario?.rol;
    if (!rolActual || !['administrador','desarrollador'].includes(rolActual)) {
        if (typeof _toast === 'function') _toast('Solo el Administrador puede cambiar la tienda.','warning');
        return;
    }
    const nombre = document.getElementById('cfg-tienda-nombre')?.value?.trim();
    const imgEl  = document.getElementById('cfg-tienda-img-el');
    const imagen = imgEl?.src && !imgEl.src.startsWith(window.location.href) ? imgEl.src : null;

    if (!nombre) { _toast('Escribe el nombre de la tienda.', 'warning'); return; }
    try {
        const esNueva = !_cfg_tienda_id;
        const url     = esNueva ? '/api/tiendas' : `/api/tiendas/${_cfg_tienda_id}`;
        const method  = esNueva ? 'POST' : 'PATCH';
        const body    = { nombre };
        if (imagen) body.imagen = imagen;

        const res  = await fetch(url, {
            method, headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(body)
        });
        const data = await res.json();
        if (res.ok) {
            _toast('\u2705 Tienda guardada', 'success');
            _cfg_tienda_id = data.tienda_id || _cfg_tienda_id;
        } else {
            _toast(data.error || 'Error al guardar', 'danger');
        }
    } catch(e) { _toast('Error de conexi\u00f3n', 'danger'); }
}

// ══════════════════════════════════════════════════════════════
//  PRIVILEGIOS (v6.11.0) — Gestión de permisos por rol
// ══════════════════════════════════════════════════════════════
var _priv_rol_actual = null;      // Rol seleccionado en la UI
var _priv_datos_cache = {};       // {rol: {modulo: 0|1}}
var _priv_modulos_cache = {};     // {modulo: "Descripción"}
var _priv_mi_rol = null;          // Rol del usuario logueado (v6.13)


// tpv_lic_admin.js
function lic_abrir() {
    lic_tab('lista');
    new bootstrap.Modal(document.getElementById('modal-licencias')).show();
    _lic_cargarLista();
    _lic_cargarAdmins();
}

function lic_tab(t) {
    [['lista','lp-lista','lt-lista'],
     ['crear','lp-crear','lt-crear']].forEach(([k,p,b]) => {
        document.getElementById(p)?.classList.toggle('d-none', k!==t);
        document.getElementById(b)?.classList.toggle('active', k===t);
    });
}

function lic_actualizarDias() {
    const tipo = document.getElementById('lic-tipo')?.value;
    const dias = document.getElementById('lic-dias');
    if (!dias) return;
    const val = _LIC_DIAS[tipo];
    if (val)  { dias.value = val; dias.disabled = (tipo !== 'personalizada'); }
    else        dias.disabled = false;
}

async function _lic_cargarAdmins() {
    try {
        const res  = await fetch('/api/usuarios', { credentials:'same-origin' });
        const data = await res.json();
        const lista = document.getElementById('lic-admin-lista');
        if (!lista) return;
        const admins = (data.usuarios||[]).filter(u => u.rol==='administrador');
        lista.innerHTML = admins.length
            ? admins.map(a => `
                <button type="button" class="list-group-item list-group-item-action py-1 small"
                        onclick="document.getElementById('lic-admin-id').value='${a.usuario_id}';
                                 document.getElementById('lic-admin-lista').innerHTML=''">
                    <strong>${a.nombre}</strong>
                    <span class="text-muted ms-1">@${a.username}</span>
                    <code class="float-end text-muted" style="font-size:.68rem">${a.usuario_id}</code>
                </button>`).join('')
            : '<div class="list-group-item text-muted small">Sin administradores registrados.</div>';
    } catch(e) {}
}

async function _lic_cargarLista() {
    const body = document.getElementById('lic-lista-body');
    if (!body) return;
    body.innerHTML = '<div class="text-center py-3"><div class="spinner-border spinner-border-sm"></div></div>';
    try {
        const res  = await fetch('/api/licencias', { credentials:'same-origin' });
        const data = await res.json();
        const lics = data.licencias || [];
        if (!lics.length) {
            body.innerHTML = '<div class="text-center text-muted py-4"><i class="bi bi-key" style="font-size:2rem"></i><br>Sin licencias generadas.</div>';
            return;
        }
        const hoy = new Date().toISOString().split('T')[0];
        body.innerHTML = lics.map(l => {
            const ilim  = l.tipo === 'ilimitada';
            const venc  = !ilim && l.fecha_expira < hoy;
            const color = ilim ? '#7c3aed' : venc ? '#dc2626' : '#059669';
            const icono = ilim ? '♾️' : venc ? '❌' : '✅';
            return `
            <div class="p-2 mb-2 rounded-3"
                 style="background:${color}0f;border:1px solid ${color}33">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1 me-2">
                        <div class="fw-bold">${icono} ${l.admin_nombre}
                            <span class="badge ms-1 text-white" style="background:${color};font-size:.62rem">${l.tipo.toUpperCase()}</span>
                        </div>
                        <div class="text-muted small">
                            ${l.fecha_inicio} → ${ilim ? '∞ Ilimitada' : l.fecha_expira}
                            &nbsp;·&nbsp;<code style="font-size:.68rem">${l.licencia_id}</code>
                        </div>
                        ${l.notas ? `<div class="text-muted small fst-italic">${l.notas}</div>` : ''}
                        ${l.clave_activacion ? `
                        <div class="mt-1 pt-1" style="border-top:1px dashed ${color}44">
                            <small class="fw-semibold" style="color:${color}">Clave de activación:</small>
                            <div class="input-group input-group-sm mt-1">
                                <input type="text" class="form-control font-monospace"
                                       value="${l.clave_activacion}" readonly
                                       style="font-size:.63rem;background:#f8f9fa">
                                <button class="btn btn-outline-secondary btn-sm" title="Copiar clave"
                                        onclick="navigator.clipboard?.writeText('${l.clave_activacion}').then(()=>_toast('✅ Clave copiada al portapapeles','success'))">
                                    <i class="bi bi-clipboard-fill"></i>
                                </button>
                            </div>
                        </div>` : ''}
                    </div>
                    <button class="btn btn-sm btn-outline-danger flex-shrink-0 ms-1" title="Revocar licencia"
                            onclick="lic_revocar('${l.licencia_id}','${l.admin_nombre.replace(/'/g,"\\'")}')">
                        <i class="bi bi-x-circle-fill"></i>
                    </button>
                </div>
            </div>`;
        }).join('');
    } catch(e) {
        body.innerHTML = '<div class="alert alert-danger">Error al cargar.</div>';
    }
}

// SHA-256 helper (disponible también en tpv_auth scope)
const _lic_sha256 = async (text) =>
    Array.from(new Uint8Array(await crypto.subtle.digest(
        'SHA-256', new TextEncoder().encode(text)
    ))).map(b => b.toString(16).padStart(2,'0')).join('');

async function lic_crear() {
    const admin_id   = document.getElementById('lic-admin-id')?.value.trim();
    const cliente_id = document.getElementById('lic-cliente-id')?.value.trim();
    const tipo       = document.getElementById('lic-tipo')?.value;
    const dias       = parseInt(document.getElementById('lic-dias')?.value) || 365;
    const notas      = document.getElementById('lic-notas')?.value.trim();

    if (!admin_id)   { _toast('Selecciona un administrador.','warning'); return; }
    if (!cliente_id) { _toast('Ingresa el ID Cliente del dispositivo del administrador.','warning');
                       document.getElementById('lic-cliente-id')?.focus(); return; }

    // Ocultar resultado previo
    const wrap = document.getElementById('lic-resultado-wrap');
    if (wrap) wrap.style.display = 'none';

    try {
        // 1. Calcular clave primero para enviarla al servidor también
        const secretKey = (typeof getSecretKey === 'function') ? getSecretKey() : 'MySuperSecretKeyForTPVApp2024';
        let claveActivacion;
        if (tipo === 'ilimitada') {
            claveActivacion = await _lic_sha256('admin' + secretKey);
        } else {
            claveActivacion = await _lic_sha256(cliente_id + secretKey + dias + 'dias');
        }

        // 2. Guardar en DB (registro histórico con clave)
        const res  = await fetch('/api/licencias/crear', {
            method:'POST', headers:{'Content-Type':'application/json'},
            credentials:'same-origin',
            body: JSON.stringify({ admin_id, tipo, dias, notas, cliente_id,
                                   clave_activacion: claveActivacion })
        });
        const data = await res.json();
        if (!res.ok || !data.ok) { _toast(data.mensaje||'Error al guardar','danger'); return; }

        // 3. Mostrar resultado
        const claveEl = document.getElementById('lic-clave-generada');
        if (claveEl) claveEl.value = claveActivacion;
        if (wrap)    wrap.style.display = '';

        _toast(`✅ Licencia ${tipo} generada para ${data.admin_nombre}`, 'success');
        _lic_cargarLista();

    } catch(e) { _toast('Error de conexión: ' + e.message, 'danger'); }
}

function lic_copiarClave() {
    const el = document.getElementById('lic-clave-generada');
    if (!el || !el.value) return;
    navigator.clipboard?.writeText(el.value).then(() => {
        _toast('✅ Clave copiada al portapapeles', 'success');
    }).catch(() => {
        el.select();
        document.execCommand('copy');
        _toast('✅ Clave copiada', 'success');
    });
}

async function lic_revocar(licencia_id, nombre) {
    if (!confirm(`¿Revocar licencia de "${nombre}"?`)) return;
    try {
        const res = await fetch(`/api/licencias/${licencia_id}`, { method:'DELETE', credentials:'same-origin' });
        if (res.ok) { _toast('Licencia revocada','success'); _lic_cargarLista(); }
        else _toast((await res.json()).mensaje||'Error','danger');
    } catch(e) {}
}

// ══════════════════════════════════════════════════════════════
//  VISTA PREVIA DE IMAGEN EN MODAL PRODUCTO
// ══════════════════════════════════════════════════════════════
function gestion_previewImagen(input) {
    const file = input?.files?.[0];
    const wrap = document.getElementById('gestion-img-preview-wrap');
    const img  = document.getElementById('gestion-img-preview');
    if (!file || !wrap || !img) return;
    const reader = new FileReader();
    reader.onload = e => {
        img.src = e.target.result;
        wrap.classList.remove('d-none');
        // Limpiar URL si se elige archivo local
        const urlInput = document.getElementById('gestion-producto-imagen-url');
        if (urlInput) urlInput.value = '';
    };
    reader.readAsDataURL(file);
}

function gestion_limpiarImagen() {
    const wrap  = document.getElementById('gestion-img-preview-wrap');
    const img   = document.getElementById('gestion-img-preview');
    const file  = document.getElementById('gestion-producto-imagen-local');
    if (wrap) wrap.classList.add('d-none');
    if (img)  img.src = '';
    if (file) file.value = '';
}

// Cuando se carga un producto a editar con imagen existente, mostrar preview
function gestion_mostrarPreviewExistente(urlImagen) {
    if (!urlImagen) return;
    const wrap = document.getElementById('gestion-img-preview-wrap');
    const img  = document.getElementById('gestion-img-preview');
    if (wrap && img) {
        img.src = urlImagen;
        wrap.classList.remove('d-none');
    }
}

// ============================================================
// LOGIN BIOMETRICO (TPVNative bridge)
// ============================================================

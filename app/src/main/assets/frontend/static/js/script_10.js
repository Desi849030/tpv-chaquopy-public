// ── Clave de almacenamiento ──────────────────────────────────
var TPV_LANG_KEY = 'tpv_idioma_seleccionado'; // 'es' | 'en'
var _gtListo     = false;
var _gtPendiente = null; // idioma pendiente de aplicar cuando GT cargue

// ── Leer idioma guardado ─────────────────────────────────────
function _langGuardado() {
    try { return localStorage.getItem(TPV_LANG_KEY) || 'es'; } catch(e) { return 'es'; }
}
function _langGuardar(lang) {
    try { localStorage.setItem(TPV_LANG_KEY, lang); } catch(e) {}
}

// ── Actualizar estilos de botones ────────────────────────────
function _actualizarBotonesLang(lang) {
    var btnEs = document.getElementById('btn-lang-es');
    var btnEn = document.getElementById('btn-lang-en');
    if (!btnEs || !btnEn) return;
    if (lang === 'en') {
        btnEs.className = 'btn btn-sm btn-outline-secondary fw-bold px-3';
        btnEn.className = 'btn btn-sm btn-primary fw-bold px-3';
    } else {
        btnEs.className = 'btn btn-sm btn-primary fw-bold px-3';
        btnEn.className = 'btn btn-sm btn-outline-secondary fw-bold px-3';
    }
}

// ── Aplicar Google Translate a un idioma ────────────────────
function _aplicarGT(lang) {
    var gtSelect = document.querySelector('.goog-te-combo');
    if (gtSelect) {
        gtSelect.value = lang === 'en' ? 'en' : '';
        gtSelect.dispatchEvent(new Event('change'));
        return true;
    }
    return false;
}

// ── Inicialización de Google Translate ──────────────────────
function googleTranslateElementInit() {
    new google.translate.TranslateElement({
        pageLanguage: 'es',
        includedLanguages: 'en,es',
        layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
        autoDisplay: false
    }, 'google_translate_element');

    _gtListo = true;

    // Aplicar idioma guardado si es inglés
    var saved = _langGuardado();
    if (saved === 'en') {
        // GT puede tardar un momento en renderizar el selector
        var intentos = 0;
        var intervalo = setInterval(function() {
            intentos++;
            if (_aplicarGT('en')) {
                clearInterval(intervalo);
                _actualizarBotonesLang('en');
            }
            if (intentos > 20) clearInterval(intervalo); // max 4 segundos
        }, 200);
    }

    // Observar cambios de idioma desde el widget de GT
    var _gtObserver = new MutationObserver(function() {
        var cookie = document.cookie.match(/googtrans=([^;]+)/);
        if (cookie) {
            var lang = cookie[1].split('/').pop();
            _actualizarBotonesLang(lang === 'en' ? 'en' : 'es');
        }
    });
    _gtObserver.observe(document.body, { attributes: true, subtree: false });
}

// ── Cambiar a ESPAÑOL ────────────────────────────────────────
function _setLangES() {
    _langGuardar('es');
    _actualizarBotonesLang('es');

    // Limpiar cookies de GT
    document.cookie = 'googtrans=; path=/; expires=' + new Date(0).toUTCString();
    document.cookie = 'googtrans=; path=/; domain=.' + location.hostname + '; expires=' + new Date(0).toUTCString();

    // Activar i18n interno en español
    if (typeof conf_setLanguage === 'function') conf_setLanguage('es');

    // Recargar para limpiar GT completamente
    setTimeout(function() { location.reload(); }, 200);
}

// ── Cambiar a INGLÉS ─────────────────────────────────────────
function _setLangEN() {
    _langGuardar('en');
    _actualizarBotonesLang('en');

    // Activar i18n interno en inglés
    if (typeof conf_setLanguage === 'function') conf_setLanguage('en');

    if (navigator.onLine) {
        // Con internet: usar GT
        if (_aplicarGT('en')) {
            // GT ya estaba listo
        } else {
            // GT no ha cargado: forzar via cookie y recargar
            document.cookie = 'googtrans=/es/en; path=/';
            document.cookie = 'googtrans=/es/en; path=/; domain=.' + location.hostname;
            setTimeout(function() { location.reload(); }, 200);
        }
    } else {
        // Sin internet: mostrar aviso, guardar preferencia para cuando vuelva
        if (typeof showToast === 'function') {
            showToast('⚠️ Sin conexión. La traducción al inglés se aplicará cuando vuelva internet.', 'warning');
        }
        // Marcar cookie para que recargue cuando vuelva la conexión
        document.cookie = 'googtrans=/es/en; path=/';
        document.cookie = 'googtrans=/es/en; path=/; domain=.' + location.hostname;
    }
}

// ── Cuando vuelve internet: aplicar traducción guardada ──────
window.addEventListener('online', function() {
    var saved = _langGuardado();
    if (saved === 'en') {
        var cookie = document.cookie.match(/googtrans=([^;]+)/);
        var yaEn   = cookie && cookie[1].includes('/en');
        if (!yaEn) {
            document.cookie = 'googtrans=/es/en; path=/';
            document.cookie = 'googtrans=/es/en; path=/; domain=.' + location.hostname;
        }
        if (typeof showToast === 'function') {
            showToast('🌐 Conexión restaurada — aplicando traducción al inglés...', 'info');
        }
        setTimeout(function() {
            if (!_aplicarGT('en')) {
                location.reload();
            } else {
                _actualizarBotonesLang('en');
            }
        }, 800);
    }
});

// ── Al cargar la página: sincronizar botones con estado real──
document.addEventListener('DOMContentLoaded', function() {
    var saved  = _langGuardado();
    var cookie = document.cookie.match(/googtrans=([^;]+)/);
    var gtEn   = cookie && cookie[1].includes('/en');

    // Reconciliar: si hay cookie EN pero guardado ES (o viceversa)
    if (saved === 'en' && !gtEn && navigator.onLine) {
        document.cookie = 'googtrans=/es/en; path=/';
        document.cookie = 'googtrans=/es/en; path=/; domain=.' + location.hostname;
    }

    _actualizarBotonesLang(saved);

    // Sincronizar selector interno conf-language-selector
    var sel = document.getElementById('conf-language-selector');
    if (sel) sel.value = saved === 'en' ? 'en' : 'es';
});

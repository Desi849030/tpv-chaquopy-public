// tpv_traduccion_i18n.js - Sistema i18n NATIVO (sin Google Translate)
// Usa el diccionario TPV_I18N de tpv_i18n_dict.js + endpoint Python /api/i18n/dict
// v5 - Reemplaza Google Translate completamente

var TPV_LANG_KEY = 'tpv_idioma_seleccionado';

function _langGuardado() {
    try { return tpvStorage.getItem(TPV_LANG_KEY) || 'es'; } catch(e) { return 'es'; }
}
function _langGuardar(lang) {
    try { tpvStorage.setItem(TPV_LANG_KEY, lang); } catch(e) {}
}

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

function _aplicarIdiomaNativo(lang) {
    if (typeof tpv_i18n_apply === 'function') {
        tpv_i18n_apply(lang);
    }
    _actualizarBotonesLang(lang);
    _langGuardar(lang);
    if (window.tpvState && window.tpvState.config) {
        window.tpvState.config.lang = lang;
    }
    if (typeof refreshAllUI === 'function') {
        setTimeout(function() { refreshAllUI(); }, 100);
    }
    console.log('[i18n] Idioma aplicado: ' + lang);
}

function _cargarDictServidor() {
    fetch('/api/i18n/dict', { cache: 'no-store' })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data && window.TPV_I18N) {
            if (data.es && window.TPV_I18N.es) {
                for (var k in data.es) {
                    if (!(k in window.TPV_I18N.es)) {
                        window.TPV_I18N.es[k] = data.es[k];
                    }
                }
            }
            if (data.en && window.TPV_I18N.en) {
                for (var k in data.en) {
                    if (!(k in window.TPV_I18N.en)) {
                        window.TPV_I18N.en[k] = data.en[k];
                    }
                }
            }
            console.log('[i18n] Diccionario servidor fusionado');
        }
    })
    .catch(function() {});
}

function _initI18n() {
    var lang = _langGuardado();
    _cargarDictServidor();
    setTimeout(function() { _aplicarIdiomaNativo(lang); }, 500);
}

function _setLangES() { _aplicarIdiomaNativo('es'); }
function _setLangEN() { _aplicarIdiomaNativo('en'); }

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _initI18n);
} else {
    _initI18n();
}

window._setLangES = _setLangES;
window._setLangEN = _setLangEN;
window._aplicarIdiomaNativo = _aplicarIdiomaNativo;

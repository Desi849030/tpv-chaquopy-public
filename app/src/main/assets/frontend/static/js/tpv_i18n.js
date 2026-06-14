var TPV_LANG_KEY = 'tpv_idioma_seleccionado';
var TPV_I18N = { es: {}, en: {} };
async function i18n_init() {
    const lang = localStorage.getItem(TPV_LANG_KEY) || 'es';
    try {
        const res = await fetch('/api/i18n/dict');
        const dict = await res.json();
        TPV_I18N.es = dict.es || {}; TPV_I18N.en = dict.en || {};
        i18n_apply(lang);
    } catch (e) { i18n_apply('es'); }
}
function i18n_apply(lang) {
    localStorage.setItem(TPV_LANG_KEY, lang);
    const dict = TPV_I18N[lang] || TPV_I18N.es;
    document.querySelectorAll('[data-i18n]').forEach(el => { if(dict[el.getAttribute('data-i18n')]) el.textContent = dict[el.getAttribute('data-i18n')]; });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => { if(dict[el.getAttribute('data-i18n-placeholder')]) el.placeholder = dict[el.getAttribute('data-i18n-placeholder')]; });
    const bEs = document.getElementById('btn-lang-es'), bEn = document.getElementById('btn-lang-en');
    if(bEs && bEn) {
        bEs.className = lang==='es'?'btn btn-sm btn-primary fw-bold px-3':'btn btn-sm btn-outline-secondary fw-bold px-3';
        bEn.className = lang==='en'?'btn btn-sm btn-primary fw-bold px-3':'btn btn-sm btn-outline-secondary fw-bold px-3';
    }
}
window._setLangES = () => i18n_apply('es');
window._setLangEN = () => i18n_apply('en');
document.addEventListener('DOMContentLoaded', i18n_init);

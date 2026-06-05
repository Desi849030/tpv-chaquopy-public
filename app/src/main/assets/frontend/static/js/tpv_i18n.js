const I18N = {
  es: {"app.name":"TPV Ultra Smart","app.slogan":"Sistema Punto de Venta Profesional","login.title":"TPV Ultra Smart","login.subtitle":"Accede con tu cuenta","login.staff":"Personal","login.client":"Cliente","login.username":"Usuario","login.password":"Contraseña","login.enter":"Entrar","login.verifying":"Verificando...","login.restricted":"Acceso restringido"},
  en: {"app.name":"TPV Ultra Smart","app.slogan":"Professional POS System","login.title":"TPV Ultra Smart","login.subtitle":"Sign in","login.staff":"Staff","login.client":"Customer","login.username":"Username","login.password":"Password","login.enter":"Sign In","login.verifying":"Verifying...","login.restricted":"Authorized personnel only"}
};
function t(key){const lang=localStorage.getItem('tpv_lang')||'es';return I18N[lang]?.[key]||I18N.es[key]||key}
function applyTranslations(){document.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=t(el.dataset.i18n)})}

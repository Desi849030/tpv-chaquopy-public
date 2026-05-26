// TPV CORE - Mobile Optimized (ASCII only)
let tpvState = {productos:[],orden:[],ventas:{},config:{lang:'es',theme:'light',nombre:'TPV Ultra Smart'}};
let AUTH = null;
let AI_CONTEXT = {usuario:null,rol:null,sesionActiva:false};

// Utility functions
function escapeHtml(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML}
function hideSplash(){const s=document.getElementById('splash-screen');if(s){s.style.opacity='0';setTimeout(()=>{s.style.display='none';const l=document.getElementById('login-screen');if(l)l.style.display='flex'},500)}}

// Initialization
document.addEventListener('DOMContentLoaded', function(){
  console.log('TPV Core loaded');
  
  // Fallback: hide splash after 2s even if JS fails
  setTimeout(hideSplash, 2000);
  
  // Load saved config
  const lang = localStorage.getItem('tpv_lang'); if(lang) tpvState.config.lang = lang;
  const theme = localStorage.getItem('tpv_theme'); if(theme) tpvState.config.theme = theme;
  const name = localStorage.getItem('tpv_custom_name'); if(name) {
    tpvState.config.nombre = name;
    const el = document.getElementById('tpv-custom-name'); if(el) el.textContent = name;
  }
  
  // Check existing session
  fetch('/api/auth/me', {credentials:'same-origin'}).then(r=>r.json()).then(d=>{
    if(d.autenticado) {
      AUTH = d.usuario;
      AI_CONTEXT = {usuario:d.usuario, rol:d.usuario.rol, sesionActiva:true};
      hideSplash();
      document.getElementById('login-screen').style.display = 'none';
      document.getElementById('app-screen').style.display = 'block';
      document.getElementById('user-name').textContent = d.usuario.nombre;
      document.getElementById('user-role').textContent = d.usuario.rol;
      document.getElementById('user-avatar').textContent = d.usuario.nombre.charAt(0).toUpperCase();
      console.log('Session restored:', d.usuario.rol);
    }
  }).catch(e=>console.log('No previous session'));
});

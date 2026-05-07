/* ========== v24: Toast System Autónomo ========== */
(function(){
  "use strict";
  var _container = null;
  var _icons = {
    success: '\u2705', danger: '\u274C', warning: '\u26A0\uFE0F', info: '\u2139\uFE0F'
  };
  var _colors = {
    success: '#10b981', danger: '#ef4444', warning: '#f59e0b', info: '#3b82f6'
  };

  function _getContainer(){
    if(_container) return _container;
    _container = document.createElement('div');
    _container.id = 'tpv-toast-container';
    _container.style.cssText = 'position:fixed;top:70px;right:12px;z-index:99999;display:flex;flex-direction:column;gap:8px;max-width:340px;width:90%;pointer-events:none;';
    document.body.appendChild(_container);
    return _container;
  }

  function _toast(msg, type){
    type = type || 'info';
    var c = _getContainer();
    var el = document.createElement('div');
    el.style.cssText = 'pointer-events:auto;display:flex;align-items:center;gap:10px;padding:12px 16px;border-radius:12px;background:' + _colors[type] + ';color:#fff;font-size:14px;font-weight:500;box-shadow:0 4px 20px rgba(0,0,0,0.25);transform:translateX(120%);transition:transform 0.35s cubic-bezier(.4,0,.2,1),opacity 0.35s;opacity:0;';
    el.innerHTML = '<span style="font-size:18px;">' + (_icons[type]||'') + '</span><span style="flex:1;">' + msg + '</span>';
    c.appendChild(el);
    requestAnimationFrame(function(){
      el.style.transform = 'translateX(0)';
      el.style.opacity = '1';
    });
    setTimeout(function(){
      el.style.transform = 'translateX(120%)';
      el.style.opacity = '0';
      setTimeout(function(){ if(el.parentNode) el.parentNode.removeChild(el); }, 400);
    }, 3500);
    el.addEventListener('click', function(){
      el.style.transform = 'translateX(120%)';
      el.style.opacity = '0';
      setTimeout(function(){ if(el.parentNode) el.parentNode.removeChild(el); }, 400);
    });
  }

  /* Reemplazar alert() global */
  window._origAlert = window.alert;
  window.alert = function(msg){
    _toast(String(msg), 'warning');
  };

  /* Exponer _toast global para uso en otros scripts */
  window._toast = _toast;

  /* Exponer showToast como alias */
  window.showToast = function(msg, type){ _toast(msg, type); };

  /* Detectar cuando showToast ya existía y era usada */
  if(typeof window.__tpv_toast_init === 'undefined'){
    window.__tpv_toast_init = true;
    console.log('[v24] Toast system cargado');
  }
})();

// tpv_ui_enhancements.js — Dark mode, animaciones KPIs, notificaciones stock, submenus
(function(){
"use strict";
try{

/* DARK MODE */
function initDarkMode(){
  var saved = tpvStorage.getItem('tpv_darkmode');
  if(saved === 'true' || (!saved && window.matchMedia('(prefers-color-scheme:dark)').matches)){
    document.body.classList.add('dark-mode');
  }
  var btn = document.createElement('button');
  btn.className = 'dark-mode-toggle';
  btn.id = 'dark-mode-toggle';
  btn.innerHTML = document.body.classList.contains('dark-mode') ? '&#9790;' : '&#9728;';
  btn.title = 'Modo oscuro/claro';
  btn.onclick = function(){
    document.body.classList.toggle('dark-mode');
    var isDark = document.body.classList.contains('dark-mode');
    tpvStorage.setItem('tpv_darkmode', isDark);
    btn.innerHTML = isDark ? '&#9790;' : '&#9728;';
  };
  btn.style.cssText = 'position:fixed;bottom:80px;right:16px;z-index:9990;width:40px;height:40px;border-radius:50%;border:none;background:var(--bs-secondary,#6c757d);color:#fff;font-size:18px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.3);';
  document.body.appendChild(btn);
}

/* ANIMATED COUNTERS */
function animateCounters(){
  var nums = document.querySelectorAll('.kpi-number[data-count]');
  nums.forEach(function(el){
    var target = parseFloat(el.getAttribute('data-count')) || 0;
    var prefix = el.getAttribute('data-prefix') || '';
    var suffix = el.getAttribute('data-suffix') || '';
    var decimals = parseInt(el.getAttribute('data-decimals')) || 0;
    var duration = 1200;
    var start = 0;
    var startTime = null;
    function step(ts){
      if(!startTime) startTime = ts;
      var progress = Math.min((ts - startTime) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      var current = start + (target - start) * eased;
      if(decimals > 0){
        el.textContent = prefix + current.toFixed(decimals) + suffix;
      } else {
        el.textContent = prefix + Math.floor(current).toLocaleString() + suffix;
      }
      if(progress < 1) requestAnimationFrame(step);
      else {
        el.classList.add('kpi-counter-animate');
        setTimeout(function(){ el.classList.remove('kpi-counter-animate'); }, 600);
      }
    }
    var observer = new IntersectionObserver(function(entries){
      entries.forEach(function(e){
        if(e.isIntersecting){ requestAnimationFrame(step); observer.disconnect(); }
      });
    }, {threshold: 0.3});
    observer.observe(el);
  });
}

/* ENHANCE KPIs */
function enhanceKPIs(){
  var kpiContainer = document.getElementById('dash-kpis');
  if(!kpiContainer) return;
  var observer = new MutationObserver(function(){
    animateCounters();
  });
  observer.observe(kpiContainer, {childList: true, subtree: true});
  setTimeout(animateCounters, 500);
}

/* CHART TOOLTIPS */
function enhanceCharts(){
  if(typeof Chart === 'undefined') return;
  Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(0,0,0,.8)';
  Chart.defaults.plugins.tooltip.titleFont = {size: 13, weight: 'bold'};
  Chart.defaults.plugins.tooltip.bodyFont = {size: 12};
  Chart.defaults.plugins.tooltip.cornerRadius = 10;
  Chart.defaults.plugins.tooltip.padding = 12;
  Chart.defaults.plugins.tooltip.displayColors = true;
  Chart.defaults.plugins.tooltip.boxPadding = 4;
  document.querySelectorAll('canvas[id^="dash-chart"]').forEach(function(canvas){
    if(canvas.parentElement.classList.contains('chart-wrapper')) return;
    var wrapper = document.createElement('div');
    wrapper.className = 'chart-wrapper';
    canvas.parentNode.insertBefore(wrapper, canvas);
    wrapper.appendChild(canvas);
  });
}

/* STOCK LOW NOTIFICATIONS */
var stockNotifs = [];
function checkStockNotifications(){
  try {
    var stockEl = document.getElementById('dash-stock-critico');
    if(!stockEl) return;
    var items = stockEl.querySelectorAll('tr, .list-group-item, [class*="stock"]');
    var lowCount = items.length;
    if(lowCount === 0 || stockNotifs.length >= 3) return;
    var container = document.getElementById('stock-notifications');
    if(!container){
      container = document.createElement('div');
      container.className = 'stock-notification';
      container.id = 'stock-notifications';
      document.body.appendChild(container);
    }
    var products = [];
    items.forEach(function(item, idx){
      if(idx >= 3) return;
      var text = item.textContent.trim();
      if(text.length > 0) products.push(text.substring(0, 50));
    });
    if(products.length === 0) return;
    var notif = document.createElement('div');
    notif.className = 'stock-notif-card';
    notif.style.position = 'relative';
    notif.innerHTML = '<button class="notif-close" onclick="this.parentElement.remove()">&times;</button>' +
      '<div class="notif-title">&#9888; Alerta de Stock</div>' +
      '<div class="notif-msg">' + products.length + ' producto(s) con stock bajo</div>';
    container.appendChild(notif);
    stockNotifs.push(notif);
    setTimeout(function(){ if(notif.parentNode){ notif.remove(); stockNotifs.shift(); }}, 10000);
  } catch(e){}
}

/* ORGANIZE SUBMENUS */
function organizeSubmenus(){
  document.querySelectorAll('.dropdown-item[id$="-tab"]').forEach(function(item){
    if (!item.hasAttribute('translate')) item.setAttribute('translate', 'no');
  });
  document.querySelectorAll('.nav-link[data-bs-toggle="dropdown"]').forEach(function(item){
    if (!item.hasAttribute('translate')) item.setAttribute('translate', 'no');
  });
}

/* INIT */
function init_v23(){
  initDarkMode();
  enhanceKPIs();
  enhanceCharts();
  organizeSubmenus();
  setInterval(checkStockNotifications, 30000);
  setTimeout(checkStockNotifications, 3000);
}

if(document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', init_v23);
} else {
  init_v23();
}
}catch(e){console.error('[UI Enhancements]',e);}
})();

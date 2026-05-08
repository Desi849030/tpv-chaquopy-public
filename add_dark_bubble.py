#!/usr/bin/env python3
"""Agrega burbuja flotante arrastrable de modo oscuro al index.html del TPV."""
import re, os

BASE = os.path.join(os.path.expanduser("~"), "tpv-chaquopy")
INDEX = os.path.join(BASE, "app/src/main/assets/frontend/templates/index.html")

with open(INDEX, "r", encoding="utf-8") as f:
    html = f.read()

# ── Verificar que no exista ya ──
if "dark-mode-bubble" in html:
    print("✓ La burbuja de modo oscuro ya existe. Nada que hacer.")
    exit(0)

# ── Código a insertar antes de </body> ──
BUBBLE_CODE = '''
<!-- ═══ Dark Mode Draggable Bubble ═══ -->
<style>
#dark-mode-bubble{
  position:fixed; bottom:90px; right:24px;
  width:52px; height:52px; border-radius:50%;
  background:linear-gradient(135deg,#4a4a8a,#2d2d5e);
  color:#fff; display:flex; align-items:center; justify-content:center;
  font-size:1.4rem; box-shadow:0 4px 15px rgba(0,0,0,.3);
  cursor:grab; touch-action:none; z-index:9999;
  transition:box-shadow .2s,transform .15s,background .3s,color .3s;
  user-select:none; -webkit-user-select:none;
}
#dark-mode-bubble:active{cursor:grabbing}
#dark-mode-bubble:hover{transform:scale(1.08)}
#dark-mode-bubble.dragging{transform:scale(1.12);box-shadow:0 6px 25px rgba(0,0,0,.4);transition:none}
body.dark-mode #dark-mode-bubble{background:linear-gradient(135deg,#f9c74f,#f9844a);color:#1a1a2e}
</style>
<div id="dark-mode-bubble" title="Modo Oscuro" aria-label="Toggle dark mode">
  <i class="bi bi-moon-stars-fill" id="dmb-icon"></i>
</div>
<script>
(function(){
  var bubble=document.getElementById("dark-mode-bubble");
  if(!bubble)return;
  var icon=document.getElementById("dmb-icon");
  var isDragging=false,moved=false,startX,startY,bubbleX,bubbleY;

  // Restaurar posición guardada
  try{
    var saved=localStorage.getItem("dmb-pos");
    if(saved){var p=JSON.parse(saved);bubble.style.left=p.x+"px";bubble.style.top=p.y+"px";bubble.style.right="auto";bubble.style.bottom="auto"}
  }catch(e){}

  function syncIcon(){
    var dk=document.body.classList.contains("dark-mode");
    icon.className=dk?"bi bi-sun-fill":"bi bi-moon-stars-fill";
    var t=document.getElementById("conf-theme-toggle");
    if(t)t.checked=dk;
  }
  syncIcon();

  // Observar cambios externos de tema (ej. desde Configuración)
  var obs=new MutationObserver(syncIcon);
  obs.observe(document.body,{attributes:true,attributeFilter:["class"]});

  function onStart(e){
    isDragging=true;moved=false;
    var pt=e.touches?e.touches[0]:e;
    var r=bubble.getBoundingClientRect();
    startX=pt.clientX;startY=pt.clientY;bubbleX=r.left;bubbleY=r.top;
    bubble.classList.add("dragging");e.preventDefault();
  }
  function onMove(e){
    if(!isDragging)return;
    var pt=e.touches?e.touches[0]:e;
    var dx=pt.clientX-startX,dy=pt.clientY-startY;
    if(Math.abs(dx)>5||Math.abs(dy)>5)moved=true;
    var nx=Math.max(0,Math.min(window.innerWidth-52,bubbleX+dx));
    var ny=Math.max(0,Math.min(window.innerHeight-52,bubbleY+dy));
    bubble.style.left=nx+"px";bubble.style.top=ny+"px";
    bubble.style.right="auto";bubble.style.bottom="auto";
    e.preventDefault();
  }
  function onEnd(){
    if(!isDragging)return;isDragging=false;
    bubble.classList.remove("dragging");
    if(!moved){
      // Tap → toggle tema
      var dk=document.body.classList.contains("dark-mode");
      if(typeof conf_setTheme==="function"){conf_setTheme(dk?"light":"dark")}
      else{document.body.classList.toggle("dark-mode");if(typeof saveState==="function")saveState()}
      syncIcon();
    }else{
      var r=bubble.getBoundingClientRect();
      localStorage.setItem("dmb-pos",JSON.stringify({x:r.left,y:r.top}));
    }
  }
  bubble.addEventListener("mousedown",onStart);
  document.addEventListener("mousemove",onMove);
  document.addEventListener("mouseup",onEnd);
  bubble.addEventListener("touchstart",onStart,{passive:false});
  document.addEventListener("touchmove",onMove,{passive:false});
  document.addEventListener("touchend",onEnd);
})();
</script>
<!-- ═══ End Dark Mode Bubble ═══ -->
'''

# ── Insertar antes de </body> ──
if "</body>" not in html:
    print("✗ No se encontró </body> en index.html"); exit(1)

html = html.replace("</body>", BUBBLE_CODE + "\n</body>")

with open(INDEX, "w", encoding="utf-8") as f:
    f.write(html)

print("✓ Burbuja de modo oscuro agregada exitosamente a index.html")
print("  - FAB flotante con icono luna/sol")
print("  - Arrastrable (mouse + touch)")
print("  - Conectada a conf_setTheme() de script_5.js")
print("  - Posición persistente via localStorage")
print("  - Sincronizada con el switch de Configuración")

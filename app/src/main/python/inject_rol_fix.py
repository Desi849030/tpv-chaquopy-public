"""
inject_rol_fix.py - Inyecta codigo JS para corregir "desarrollador" -> "Usuario"
Se debe llamar despues de crear la app Flask
"""
MAPPING_JS = """
<script>
(function(){
    var roleMap = {"desarrollador":"Usuario","administrador":"Administrador","supervisor":"Supervisor","vendedor":"Vendedor"};
    function fixBadge(){
        var b=document.getElementById('ub-badge');
        if(b&&b.textContent.trim()){
            var r=b.textContent.trim();
            if(roleMap[r])b.textContent=roleMap[r];
        }
    }
    var obs=new MutationObserver(fixBadge);
    if(document.body)obs.observe(document.body,{childList:true,subtree:true,characterData:true});
    else document.addEventListener('DOMContentLoaded',function(){obs.observe(document.body,{childList:true,subtree:true,characterData:true});});
    setInterval(fixBadge,2000);
})();
</script>
"""

def injectar_script(app):
    @app.after_request
    def add_rol_fix(response):
        if response.content_type and 'text/html' in response.content_type:
            try:
                data = response.get_data().decode('utf-8', errors='ignore')
                if '</body>' in data and 'roleMap' not in data:
                    data = data.replace('</body>', MAPPING_JS + '</body>')
                    response.set_data(data.encode('utf-8'))
            except Exception:
                pass
        return response

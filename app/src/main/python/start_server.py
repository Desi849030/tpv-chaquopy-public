# -*- coding: utf-8 -*-
"""
Iniciar servidor Flask para TPV Ultra Smart
"""
import os
import sys
import threading

def start_server():
    """Iniciar el servidor Flask"""
    try:
        files_dir = os.environ.get('TPV_FILES_DIR', 
            '/data/data/com.termux/files/home/tpv-chaquopy/app/src/main/python')
        frontend_dir = os.environ.get('TPV_FRONTEND_DIR', files_dir + '/frontend')
        
        sys.path.insert(0, files_dir)
        
        from app import app
        
        # Configurar ruta del frontend
        import os as _os
        app.config['FRONTEND_DIR'] = frontend_dir
        
        port = int(os.environ.get('TPV_PORT', 5050))
        
        print(f"🚀 Servidor iniciado en puerto {port}")
        print(f"📁 Frontend: {frontend_dir}")
        
        app.run(
            host='127.0.0.1',
            port=port,
            debug=False,
            use_reloader=False
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    start_server()

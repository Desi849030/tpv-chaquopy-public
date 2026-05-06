import os, sys
APP_DIR = os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python')
if os.path.abspath(APP_DIR) not in sys.path:
    sys.path.insert(0, os.path.abspath(APP_DIR))
os.environ.setdefault('TPV_FILES_DIR', os.path.abspath(APP_DIR))
os.environ.setdefault('TPV_DB_PATH', '/tmp/tpv_test.db')
os.environ.setdefault('TPV_FRONTEND_DIR', os.path.join(os.path.abspath(APP_DIR), 'frontend'))

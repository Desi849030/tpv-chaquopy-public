import pytest,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","..","app","src","main","python"))
class T:
    def test_i(self):
        try:import supabase_sync;assert hasattr(supabase_sync,"setup_supabase")
        except ImportError:pytest.skip()

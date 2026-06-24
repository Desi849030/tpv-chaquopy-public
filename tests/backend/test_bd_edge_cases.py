import pytest,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","..","app","src","main","python"))
class T:
    def test_wal(self):from db_connection import get_connection;c=get_connection();m=c.execute("PRAGMA journal_mode").fetchone()[0];c.close();assert m=="wal"
    def test_fk(self):from db_connection import get_connection;c=get_connection();f=c.execute("PRAGMA foreign_keys").fetchone()[0];c.close();assert f==1
    def test_scrypt(self):from db_connection import verify_password,_hash_password;h,s=_hash_password("t");assert verify_password("t",h,s) and not verify_password("x",h,s)
    def test_audit(self):from db_connection import create_audit_table,log_event,get_connection;create_audit_table();log_event("tu","ta","tt","i","o","n");c=get_connection();r=c.execute("SELECT * FROM audit_logs WHERE usuario='tu'").fetchone();c.close();assert r and r["accion"]=="ta"

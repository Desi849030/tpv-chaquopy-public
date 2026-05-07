#!/usr/bin/env python3
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","app/src/main/python"))
from database import obtener_conexion,reconstruir_desde_productos,importar_catalogo_a_inventario
from ia_agent import process_question,P,M,F,O,fmt_money,pct
A="user-4fd3220f"
p=f=0
def T(n,ok,d=""):
 global p,f
 if ok: p+=1;print("  PASS: "+n)
 else: f+=1;print("  FAIL: "+n+" "+d)
print("=== TESTS v25 ===")
print("[1] Importacion")
prods=[{"id":"TV1","nombre":"Test v25","precio":5,"costoUnitario":2,"categoria":"G","um":"C/U","enOferta":False,"imagen":"","stock_actual":10},{"id":"TV2","nombre":"Test Dos","precio":8,"costoUnitario":3,"categoria":"B","um":"C/U","enOferta":True,"imagen":"","stock_actual":20}]
r=reconstruir_desde_productos(A,prods)
T("reconstruir OK",r["ok"],r.get("mensaje",""))
T("reconstruir total>=2",r["total"]>=2,str(r["total"]))
r2=importar_catalogo_a_inventario(A)
T("importar_catalogo OK",r2["ok"],r2.get("mensaje",""))
c=obtener_conexion()
cur=c.cursor()
cur.execute("SELECT COUNT(*) FROM productos")
n=cur.fetchone()[0]
T("productos>=2 (got "+str(n)+")",n>=2)
cur.execute("SELECT COUNT(*) FROM inventario_general")
n2=cur.fetchone()[0]
T("inventario>=2 (got "+str(n2)+")",n2>=2)
c.close()
print("[2] IA Agent")
T("P exists",P is not None)
T("M exists",M is not None)
T("F exists",F is not None)
T("O exists",O is not None)
T("fmt_money(100)==$100.00",fmt_money(100)=="$100.00",fmt_money(100))
r3=process_question("0","hola","cliente","Test")
T("process_question dict",isinstance(r3,dict))
T("answer not empty",len(r3.get("answer",""))>0)
print("\n=== "+str(p)+" passed, "+str(f)+" failed ===")
sys.exit(1 if f else 0)

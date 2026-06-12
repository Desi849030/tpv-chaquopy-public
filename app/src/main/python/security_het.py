import os,re,time,threading,json
from datetime import datetime
from collections import deque
_HET_CONFIG={"max_rpm":120,"max_login":5,"lockout_min":15,"max_alerts":200}
_LOCK=threading.Lock()
_request_log=deque(maxlen=1000)
_login_attempts={}
_login_lockouts={}
_threat_alerts=deque(maxlen=_HET_CONFIG["max_alerts"])
_SQL=re.compile(r"(?i)(union\s+select|\b(or|and)\b\s+[\w'\"]+\s*=\s*[\w'\"]+|drop\s+(table|database)|truncate\s+table|insert\s+into|delete\s+from|update\s+\w+\s+set|'\s*or\s*'|--|/\*|;\s*\w|exec\s*\(|xp_cmdshell|information_schema|pg_sleep\s*\(|sleep\s*\(|load_file\s*\(|into\s+outfile)")
_XSS=re.compile(r"(?i)(<script|javascript\s*:|onerror\s*=|onload\s*=|<iframe|document\.cookie|document\.location|eval\s*\()")
def check_rate_limit(ip=None):
    now=time.time(); ma=now-60
    with _LOCK:
        while _request_log and _request_log[0]<ma: _request_log.popleft()
        _request_log.append(now); c=len(_request_log)
    ok=c<=_HET_CONFIG["max_rpm"]
    if not ok: add_alert("WARN","RATE_LIMIT",ip or "unknown",f"Rate: {c}/min")
    return ok,max(0,_HET_CONFIG["max_rpm"]-c)
def check_login(ip=None):
    now=time.time(); ip=ip or "127.0.0.1"
    with _LOCK:
        if ip in _login_lockouts:
            if now<_login_lockouts[ip]: return False,0
            else: del _login_lockouts[ip]; _login_attempts.pop(ip,None)
        return True,max(0,_HET_CONFIG["max_login"]-_login_attempts.get(ip,0))
def record_login_result(ip,success):
    ip=ip or "127.0.0.1"; now=time.time()
    with _LOCK:
        if success: _login_attempts.pop(ip,None); _login_lockouts.pop(ip,None)
        else:
            _login_attempts[ip]=_login_attempts.get(ip,0)+1
            if _login_attempts[ip]>=_HET_CONFIG["max_login"]:
                _login_lockouts[ip]=now+_HET_CONFIG["lockout_min"]*60
                add_alert("CRITICAL","BRUTE_FORCE",ip,f"{_login_attempts[ip]} intentos, bloqueado")
def detect_sql_injection(s,ip=None):
    if not s: return True,"OK"
    m=_SQL.findall(str(s))
    if m:
        add_alert("WARN","SQL_SUSPICIOUS",ip,f"Patron: {m[0]}")
        return False,"WARN"
    return True,"OK"
def detect_xss(s,ip=None):
    if not s: return True,"OK"
    m=_XSS.findall(str(s))
    if m:
        add_alert("WARN","XSS_SUSPICIOUS",ip,f"Patron: {m[0]}")
        return False,"WARN"
    return True,"OK"
def sanitize_input(s):
    # NOTA: la proteccion REAL contra SQLi son las consultas parametrizadas (?).
    # Aqui solo neutralizamos null-bytes y escapamos HTML para XSS. NO borramos
    # palabras SQL: hacerlo daba falsa seguridad (bypasseable) y corrompia datos.
    if not s: return s
    c=str(s).replace("\x00","").replace("<","&lt;").replace(">","&gt;")
    return c.strip()
def add_alert(level,atype,source,details=""):
    with _LOCK:
        _threat_alerts.append({"timestamp":datetime.now().isoformat(),"level":level,"type":atype,"source":source,"details":details})
def get_alerts(level=None,limit=50):
    with _LOCK: a=list(_threat_alerts)
    if level: a=[x for x in a if x["level"]==level]
    return list(reversed(a[-limit:]))
def get_threat_summary():
    with _LOCK:
        a=list(_threat_alerts); now=time.time(); ma=now-60
        rr=sum(1 for t in _request_log if t>ma)
        cr=sum(1 for x in a if x["level"]=="CRITICAL")
        wr=sum(1 for x in a if x["level"]=="WARN")
    return {"timestamp":datetime.now().isoformat(),"active_threats":cr,"warnings":wr,"requests_per_minute":rr,"status":"SECURE" if cr==0 else "THREAT_DETECTED"}
def create_het_middleware(app):
    @app.before_request
    def het_before():
        from flask import request as req,jsonify
        skip_prefix=["/static/","/api/health","/api/productos","/api/categorias","/api/ventas","/favicon","/manifest"]
        if any(req.path.startswith(p) for p in skip_prefix): return
        if req.method=="OPTIONS": return
        ip=req.remote_addr or "127.0.0.1"
        ok,_=check_rate_limit(ip)
        if not ok: return jsonify({"error":"Too many requests","code":429}),429
        for k,v in req.args.items():
            safe,_=detect_sql_injection(v,ip)
            if not safe: return jsonify({"error":"Input no permitido","code":400}),400
            safe,_=detect_xss(v,ip)
            if not safe: return jsonify({"error":"Input no permitido","code":400}),400
        if req.method=="POST":
            for src in [req.get_json(silent=True), req.form]:
                if src and isinstance(src,dict):
                    for k,v in src.items():
                        if isinstance(v,str):
                            safe,_=detect_sql_injection(v,ip)
                            if not safe: return jsonify({"error":"Input no permitido","code":400}),400
                            safe,_=detect_xss(v,ip)
                            if not safe: return jsonify({"error":"Input no permitido","code":400}),400
    @app.after_request
    def het_after(resp):
        resp.headers["X-Content-Type-Options"]="nosniff"
        resp.headers["X-Frame-Options"]="DENY"
        resp.headers["X-XSS-Protection"]="1; mode=block"
        return resp

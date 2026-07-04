import gzip
from flask import request
def add_security_headers(r):
    for k,v in [("X-Content-Type-Options","nosniff"),("X-Frame-Options","SAMEORIGIN"),("X-XSS-Protection","1; mode=block"),("Referrer-Policy","strict-origin-when-cross-origin"),("Strict-Transport-Security","max-age=31536000;includeSubDomains")]: r.headers.setdefault(k,v)
    if request.path.startswith("/api/"): r.headers.setdefault("Cache-Control","no-store")
    o=request.headers.get("Origin","")
    if o and ("127.0.0.1" in o or "localhost" in o):
        r.headers["Access-Control-Allow-Origin"]=o; r.headers["Access-Control-Allow-Credentials"]="true"
        r.headers["Access-Control-Allow-Headers"]="Content-Type,X-CSRF-Token"
        r.headers["Access-Control-Allow-Methods"]="GET,POST,PUT,DELETE,OPTIONS"
    return r
def setup_compression(app):
    @app.after_request
    def comp(r):
        if r.status_code<200 or r.status_code>=300 or r.direct_passthrough or "Content-Encoding" in r.headers: return r
        try: d=r.get_data()
        except: return r
        if len(d)<500 or "gzip" not in request.headers.get("Accept-Encoding",""): return r
        d=gzip.compress(d,6); r.set_data(d); r.headers["Content-Encoding"]="gzip"; return r

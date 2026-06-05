import os,hashlib,hmac,json,time,threading
from datetime import datetime
_TOKEN_SALT=b"tpv_ultrasmart_pci_v6"
_AUDIT_LOCK=threading.Lock()
_AUDIT_LOG=[]
_AUDIT_MAX=500
_MASTER_KEY=None
def _ensure_key():
    global _MASTER_KEY
    if _MASTER_KEY is None:
        try:
            kf=os.path.join(os.path.dirname(os.path.abspath(__file__)),".tpv_secret_key")
            secret=open(kf).read().strip() if os.path.exists(kf) else os.urandom(32).hex()
        except Exception:
            secret=os.urandom(32).hex()
        _MASTER_KEY=hashlib.sha256((secret+"pci_key").encode()).digest()
    return _MASTER_KEY
def tokenize_pan(pan_text):
    if not pan_text: return None
    pan_clean="".join(c for c in str(pan_text) if c.isdigit())
    if len(pan_clean)<13 or len(pan_clean)>19: return None
    key=_ensure_key()
    token=hmac.new(key,pan_clean.encode(),hashlib.sha256).hexdigest()
    _audit_log("TOKENIZE",token[-8:],True)
    return token
def mask_pan(pan_text):
    if not pan_text: return "****"
    pc="".join(c for c in str(pan_text) if c.isdigit())
    if len(pc)<4: return "****"
    last4=pc[-4:]
    masked="*"*(len(pc)-4)
    r=""
    for i,c in enumerate(masked+last4):
        if i>0 and i%4==0: r+=" "
        r+=c
    return r
def validate_luhn(pan_text):
    pc="".join(c for c in str(pan_text) if c.isdigit())
    if not pc.isdigit() or len(pc)<13: return False
    total=0
    for i,d in enumerate(reversed(pc)):
        n=int(d)
        if i%2==1:
            n*=2
            if n>9: n-=9
        total+=n
    return total%10==0
def detect_card_brand(pan_text):
    if not pan_text: return "unknown"
    p="".join(c for c in str(pan_text) if c.isdigit())
    if p.startswith("4"): return "visa"
    if p.startswith("5") or p.startswith("2"): return "mastercard"
    if p.startswith("3"): return "amex"
    if p.startswith("6"): return "discover"
    return "unknown"
def _audit_log(action,identifier,success=True,details=""):
    entry={"timestamp":datetime.now().isoformat(),"action":action,"identifier":identifier,"success":success,"details":details}
    with _AUDIT_LOCK:
        _AUDIT_LOG.append(entry)
        if len(_AUDIT_LOG)>_AUDIT_MAX: _AUDIT_LOG.pop(0)
def get_audit_log(limit=100):
    with _AUDIT_LOCK: return list(reversed(_AUDIT_LOG[-limit:]))
def process_payment_token(pan_text,amount,method="card"):
    result={"token":None,"masked":"****","brand":"unknown","valid":False,"amount":amount,"method":method,"error":None}
    if not pan_text:
        result["error"]="No se proporciono numero de tarjeta"
        _audit_log("PAYMENT_FAIL","",False,"No PAN"); return result
    result["masked"]=mask_pan(pan_text)
    result["brand"]=detect_card_brand(pan_text)
    if not validate_luhn(pan_text):
        result["error"]="Numero de tarjeta invalido (Luhn)"
        _audit_log("PAYMENT_FAIL",result["masked"],False,"Luhn"); return result
    token=tokenize_pan(pan_text)
    if not token:
        result["error"]="No se pudo generar token"
        _audit_log("PAYMENT_FAIL",result["masked"],False,"Token fail"); return result
    result["token"]=token; result["valid"]=True
    _audit_log("PAYMENT_OK",token[-8:],True,f"brand={result['brand']}")
    return result

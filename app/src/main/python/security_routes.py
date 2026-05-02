import json
from datetime import datetime
from flask import Blueprint,request,jsonify
sec_bp=Blueprint('security',__name__,url_prefix='/api/security')
@sec_bp.route("/pci/tokenize",methods=["POST"])
def pci_tokenize():
    from security_pci import tokenize_pan,mask_pan,validate_luhn,detect_card_brand
    data=request.get_json(silent=True) or {}; pan=data.get("pan","")
    if not pan: return jsonify({"error":"PAN requerido"}),400
    if not validate_luhn(pan): return jsonify({"error":"PAN invalido","valid":False}),400
    return jsonify({"ok":True,"token":tokenize_pan(pan),"masked":mask_pan(pan),"brand":detect_card_brand(pan),"valid":True})
@sec_bp.route("/pci/mask",methods=["POST"])
def pci_mask():
    from security_pci import mask_pan
    return jsonify({"ok":True,"masked":mask_pan((request.get_json(silent=True) or {}).get("pan",""))})
@sec_bp.route("/pci/audit",methods=["GET"])
def pci_audit():
    from security_pci import get_audit_log
    return jsonify({"ok":True,"entries":get_audit_log(int(request.args.get("limit",50)))})
@sec_bp.route("/het/status",methods=["GET"])
def het_status():
    from security_het import get_threat_summary
    return jsonify(get_threat_summary())
@sec_bp.route("/het/alerts",methods=["GET"])
def het_alerts():
    from security_het import get_alerts
    return jsonify({"ok":True,"alerts":get_alerts(request.args.get("level"),int(request.args.get("limit",50)))})
@sec_bp.route("/omnichannel/status",methods=["GET"])
def omnichannel_status():
    try:
        from supabase_sync import obtener_config_actual,probar_conexion
        c=obtener_config_actual()
        return jsonify({"ok":True,"connected":probar_conexion(),"url":(c.get("url","")[:30]+"...") if c.get("url") else ""})
    except: return jsonify({"ok":False})
@sec_bp.route("/ws/status",methods=["GET"])
def ws_status():
    from security_websocket import get_active_terminals
    t=get_active_terminals()
    return jsonify({"ok":True,"active_terminals":len(t),"terminals":t})
@sec_bp.route("/dashboard",methods=["GET"])
def dashboard():
    r={"timestamp":datetime.now().isoformat(),"version":"6.20.0","blindajes":{}}
    try:
        from security_pci import get_audit_log
        r["blindajes"]["pci_dss"]={"active":True,"audit_entries":len(get_audit_log(1000))}
    except: r["blindajes"]["pci_dss"]={"active":False}
    try:
        from security_het import get_threat_summary
        r["blindajes"]["het"]=get_threat_summary(); r["blindajes"]["het"]["active"]=True
    except: r["blindajes"]["het"]={"active":False}
    try:
        from security_websocket import get_active_terminals
        r["blindajes"]["websocket"]={"active":True,"active_terminals":len(get_active_terminals())}
    except: r["blindajes"]["websocket"]={"active":False}
    r["overall_status"]="SECURE" if all(b.get("active") for b in r["blindajes"].values()) else "PARTIAL"
    return jsonify(r)

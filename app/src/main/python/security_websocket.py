from decorators import login_required
import os,json,time,threading,queue
from datetime import datetime
from collections import defaultdict
_HEARTBEAT_INTERVAL=30
_MAX_QUEUE=100
_TERMINAL_TIMEOUT=120
_LOCK=threading.Lock()
_terminals={}
_event_history=[]
_MAX_HISTORY=50
def register_terminal(tid,info=None):
    with _LOCK:
        _terminals[tid]={"last_seen":time.time(),"queue":queue.Queue(maxsize=_MAX_QUEUE),"info":info or {}}
    _broadcast("system","terminal_online",{"terminal_id":tid,"total":len(_terminals)})
def unregister_terminal(tid):
    with _LOCK: _terminals.pop(tid,None)
    _broadcast("system","terminal_offline",{"terminal_id":tid})
def heartbeat(tid):
    with _LOCK:
        if tid in _terminals: _terminals[tid]["last_seen"]=time.time()
def get_active_terminals():
    now=time.time(); active=[]
    with _LOCK:
        for tid,d in _terminals.items():
            if now-d["last_seen"]<_TERMINAL_TIMEOUT:
                active.append({"id":tid,"info":d["info"],"last_seen":now-d["last_seen"]})
    return active
def _broadcast(etype,ename,data=None):
    ev={"type":etype,"name":ename,"data":data or {},"timestamp":datetime.now().isoformat()}
    ej=json.dumps(ev,ensure_ascii=False)
    with _LOCK:
        _event_history.append(ev)
        if len(_event_history)>_MAX_HISTORY: _event_history.pop(0)
        for tid,t in _terminals.items():
            try: t["queue"].put_nowait(ej)
            except queue.Full: pass
def get_terminal_events(tid):
    events=[]
    with _LOCK:
        heartbeat(tid)
        if tid in _terminals:
            q=_terminals[tid]["queue"]
            while not q.empty():
                try: events.append(q.get_nowait())
                except queue.Empty: break
    return events
def notify_sale(sale_data,from_terminal="unknown"):
    _broadcast("sale","new_sale",{"sale":sale_data,"from":from_terminal})
def notify_inventory_update(product_data,from_terminal="unknown"):
    _broadcast("inventory","update",{"product":product_data,"from":from_terminal})
def notify_alert(alert_data):
    _broadcast("security","alert",alert_data)
def create_ws_routes(app):
    @app.route("/ws/events/<tid>")
    def ws_events(tid):
        from flask import Response,jsonify
        if tid not in _terminals: register_terminal(tid)
        events=get_terminal_events(tid)
        if events:
            return Response(json.dumps(events,ensure_ascii=False),mimetype="application/json")
        return jsonify({"type":"heartbeat","active_terminals":len(get_active_terminals())})
    @app.route("/ws/register",methods=["POST"])
    def ws_register():
        from flask import request,jsonify
        data=request.get_json(silent=True) or {}
        tid=data.get("terminal_id")
        if not tid: return jsonify({"error":"terminal_id requerido"}),400
        register_terminal(tid,data.get("info",{}))
        return jsonify({"ok":True,"active_terminals":len(get_active_terminals())})
    @app.route("/ws/unregister",methods=["POST"])
    def ws_unregister():
        from flask import request,jsonify
        data=request.get_json(silent=True) or {}
        tid=data.get("terminal_id")
        if tid: unregister_terminal(tid)
        return jsonify({"ok":True})
    @app.route("/ws/terminals")
    def ws_list():
        from flask import jsonify
        return jsonify({"terminals":get_active_terminals(),"total":len(get_active_terminals())})
def start_cleanup_thread():
    def _loop():
        while True:
            try:
                time.sleep(_HEARTBEAT_INTERVAL)
                now=time.time()
                with _LOCK:
                    stale=[t for t,d in _terminals.items() if now-d["last_seen"]>_TERMINAL_TIMEOUT]
                    for t in stale: _terminals.pop(t,None)
            except: pass
    threading.Thread(target=_loop,daemon=True).start()

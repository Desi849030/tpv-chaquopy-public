from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return "<h1>✅ Flask funciona!</h1><p><a href='/api/status'>/api/status</a></p>"

@app.route("/api/status")
def status():
    return jsonify({"ok": True, "servidor": "activo", "timestamp": "2026-05-25"})

if __name__ == '__main__':
    print("✅ Servidor mínimo en http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)

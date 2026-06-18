# -*- coding: utf-8 -*-
"""Blueprint: Usuarios y privilegios (CRUD + jerarquía de roles)"""
from flask import Blueprint, request, jsonify

usuarios_bp = Blueprint('usuarios', __name__)

# ── Jerarquía de roles ──────────────────────────────────────────
ROLES_JERARQUIA = {
    "desarrollador": {"nivel": 0, "puede_crear": ["administrador"],
                      "permisos_todos": True,
                      "descripcion": "Control total del sistema"},
    "administrador": {"nivel": 1, "puede_crear": ["supervisor", "vendedor", "cajero"],
                      "permisos_todos": False,
                      "descripcion": "Gestiona el negocio"},
    "supervisor": {"nivel": 2, "puede_crear": [],
                   "permisos_todos": False,
                   "descripcion": "Supervisa operaciones"},
    "vendedor": {"nivel": 3, "puede_crear": [],
                 "permisos_todos": False,
                 "descripcion": "Atiende clientes"},
    "cajero": {"nivel": 3, "puede_crear": [],
               "permisos_todos": False,
               "descripcion": "Cobros y caja"},
}

PERMISOS_POR_ROL = {
    "desarrollador": ["sistema", "seguridad", "usuarios", "privilegios", "bd", "logs",
                      "ventas", "inventario", "productos", "reportes", "metricas",
                      "catalogo", "clientes", "licencias", "importacion", "backups"],
    "administrador": ["ventas", "inventario", "productos", "usuarios", "reportes",
                      "metricas", "catalogo", "clientes", "licencias", "importacion",
                      "backups"],
    "supervisor": ["ventas", "productos", "reportes", "metricas", "catalogo", "clientes"],
    "vendedor": ["ventas", "catalogo", "clientes"],
    "cajero": ["ventas", "catalogo"],
}


@usuarios_bp.route('/api/admin/privilegios')
def admin_privilegios():
    """Devuelve jerarquía + permisos + usuarios."""
    rol = request.args.get('rol', 'administrador')
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        c.execute("SELECT usuario_id,username,nombre,rol,activo FROM usuarios ORDER BY rol,nombre")
        usuarios = [{"id": r[0], "username": r[1], "nombre": r[2],
                      "rol": r[3], "activo": bool(r[4])} for r in c.fetchall()]
        conn.close()
    except Exception:
        usuarios = []
    return jsonify({
        "ok": True, "jerarquia": ROLES_JERARQUIA,
        "permisos_por_rol": PERMISOS_POR_ROL,
        "puede_crear": ROLES_JERARQUIA.get(rol, {}).get("puede_crear", []),
        "usuarios": usuarios,
    })


@usuarios_bp.route('/api/usuarios')
def listar_usuarios():
    """Lista usuarios del sistema."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        c.execute(
            "SELECT usuario_id,username,nombre,rol,activo,creado "
            "FROM usuarios ORDER BY rol,nombre")
        usuarios = [{"id": r[0], "username": r[1], "nombre": r[2],
                      "rol": r[3], "activo": bool(r[4]), "creado": r[5]}
                     for r in c.fetchall()]
        conn.close()
        return jsonify({"ok": True, "usuarios": usuarios, "total": len(usuarios)})
    except Exception:
        return jsonify({"ok": True, "usuarios": [], "total": 0})


@usuarios_bp.route('/api/admin/usuarios/crear', methods=['POST'])
def admin_crear_usuario():
    """Crear un nuevo usuario."""
    d = request.get_json(silent=True) or {}
    username = d.get('username', '').strip()
    password = d.get('password', '')
    nombre = d.get('nombre', '').strip()
    rol = d.get('rol', 'vendedor')

    if not username or not password or not nombre:
        return jsonify({"ok": False, "error": "Faltan campos: username, nombre, password"}), 400

    try:
        from db.users import crear_usuario
        from flask import session

        u = session.get("usuario", {}) or {}
        result = crear_usuario(
            {
                "username": username,
                "password": password,
                "nombre": nombre,
                "rol": rol
            },
            creado_por_rol=u.get("rol", "desarrollador"),
            creado_por_id=u.get("usuario_id", "dev-001")
        )

        if result and result.get("ok"):
            return jsonify(result), 200
        return jsonify(result or {"ok": False, "error": "Error al crear usuario"}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@usuarios_bp.route('/api/admin/usuarios/<uid>/toggle', methods=['PUT', 'POST'])
def admin_toggle(uid):
    """Activar/desactivar usuario."""
    d = request.get_json(silent=True) or {}
    activo = d.get('activo', True)
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        c.execute("UPDATE usuarios SET activo=? WHERE usuario_id=?", (1 if activo else 0, uid))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "mensaje": f"Usuario {'activado' if activo else 'desactivado'}",
                        "activo": activo})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@usuarios_bp.route('/api/admin/usuarios/<uid>', methods=['DELETE'])
def admin_delete(uid):
    """Eliminar usuario (soft delete)."""
    try:
        from db_connection import obtener_conexion
        conn = obtener_conexion()
        c = conn.cursor()
        c.execute("UPDATE usuarios SET activo=0 WHERE usuario_id=?", (uid,))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "mensaje": f"Usuario {uid} eliminado"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

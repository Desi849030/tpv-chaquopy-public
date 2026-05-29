import { ROLE_DEFINITIONS } from "./tpv_roles.js";

export function tienePermiso(rol, permiso) {
    if (!rol || !ROLE_DEFINITIONS[rol]) return false;

    const permisos = ROLE_DEFINITIONS[rol].permisos;

    if (permisos.includes("*")) return true;

    return permisos.includes(permiso);
}

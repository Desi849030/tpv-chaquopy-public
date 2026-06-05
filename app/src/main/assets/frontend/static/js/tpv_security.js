import { tienePermiso } from "./tpv_permissions.js";
import { TPV_STATE } from "./tpv_state.js";

export function puede(permiso) {
    if (!TPV_STATE.usuario) return false;
    return tienePermiso(TPV_STATE.usuario.rol, permiso);
}

// tpv_ui_timeouts.js — Sistema de timeouts para menús desplegables
// v1.0 — Cierre automático por inactividad

(function() {
    'use strict';

    const CONFIG = {
        dropdownTimeout: 30000,
        modalTimeout: 300000,
        warningBefore: 5000,
        debug: false
    };

    let _dropdownTimer = null;
    let _modalTimers = new Map();
    let _warningTimer = null;
    let _activeDropdown = null;

    function _log(...args) {
        if (CONFIG.debug) console.log('[UI-Timeouts]', ...args);
    }

    function cerrarDropdowns() {
        document.querySelectorAll('.dropdown-menu.show').forEach(function(menu) {
            menu.classList.remove('show');
            var toggle = menu.previousElementSibling;
            if (toggle) toggle.setAttribute('aria-expanded', 'false');
        });
        _activeDropdown = null;
        _log('Dropdowns cerrados');
    }

    function resetearDropdownTimer() {
        if (_dropdownTimer) {
            clearTimeout(_dropdownTimer);
            _dropdownTimer = null;
        }
        var abierto = document.querySelector('.dropdown-menu.show');
        if (abierto) {
            _dropdownTimer = setTimeout(function() {
                cerrarDropdowns();
                _log('Dropdown cerrado por inactividad');
            }, CONFIG.dropdownTimeout);
        }
    }

    function initDropdownTimeouts() {
        document.addEventListener('shown.bs.dropdown', function(e) {
            _activeDropdown = e.target;
            resetearDropdownTimer();
            _log('Dropdown abierto:', e.target.id || e.target.className);
        });

        document.addEventListener('hidden.bs.dropdown', function(e) {
            if (_activeDropdown === e.target) {
                _activeDropdown = null;
            }
            if (_dropdownTimer) {
                clearTimeout(_dropdownTimer);
                _dropdownTimer = null;
            }
            _log('Dropdown cerrado manualmente');
        });

        var activityTimeout = null;
        var actividadEvents = ['mousemove', 'keydown', 'click', 'touchstart'];
        actividadEvents.forEach(function(evento) {
            document.addEventListener(evento, function() {
                if (activityTimeout) clearTimeout(activityTimeout);
                activityTimeout = setTimeout(function() {
                    resetearDropdownTimer();
                }, 500);
            });
        });
        _log('Dropdown timeouts inicializados');
    }

    function cerrarModal(modalId, motivo) {
        motivo = motivo || 'timeout';
        var modalEl = document.getElementById(modalId);
        if (!modalEl) return;
        try {
            var modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) {
                modal.hide();
                _log('Modal ' + modalId + ' cerrado por: ' + motivo);
            }
        } catch(e) {
            modalEl.classList.remove('show');
            modalEl.style.display = 'none';
            document.body.classList.remove('modal-open');
            document.querySelectorAll('.modal-backdrop').forEach(function(b) { b.remove(); });
        }
        if (_modalTimers.has(modalId)) {
            clearTimeout(_modalTimers.get(modalId));
            _modalTimers.delete(modalId);
        }
    }

    function programarCierreModal(modalId, timeout) {
        timeout = timeout || CONFIG.modalTimeout;
        if (_modalTimers.has(modalId)) {
            clearTimeout(_modalTimers.get(modalId));
        }
        var timer = setTimeout(function() {
            var modalEl = document.getElementById(modalId);
            if (modalEl && modalEl.classList.contains('show')) {
                cerrarModal(modalId, 'inactividad');
                if (typeof showToast === 'function') {
                    showToast('Sesión cerrada por inactividad', 'info');
                }
            }
        }, timeout);
        _modalTimers.set(modalId, timer);
        _log('Modal ' + modalId + ' programado para cerrar en ' + (timeout/1000) + 's');
    }

    function initModalTimeouts() {
        var modalesConTimeout = [
            'modal-usuarios',
            'modal-notif',
            'modal-chat',
            'modal-licencias'
        ];
        document.addEventListener('shown.bs.modal', function(e) {
            var modalId = e.target.id;
            if (modalesConTimeout.includes(modalId)) {
                programarCierreModal(modalId, CONFIG.modalTimeout);
            }
        });
        document.addEventListener('hidden.bs.modal', function(e) {
            var modalId = e.target.id;
            if (_modalTimers.has(modalId)) {
                clearTimeout(_modalTimers.get(modalId));
                _modalTimers.delete(modalId);
            }
        });
        document.querySelectorAll('.modal').forEach(function(modal) {
            modal.addEventListener('mousemove', function() {
                var modalId = modal.id;
                if (_modalTimers.has(modalId) && modalesConTimeout.includes(modalId)) {
                    programarCierreModal(modalId, CONFIG.modalTimeout);
                }
            });
        });
        _log('Modal timeouts inicializados');
    }

    var _autoSaveTimer = null;

    function autoSave() {
        if (typeof saveState !== 'function') return;
        try {
            saveState();
            _log('Auto-save completado');
        } catch(e) {
            console.warn('[UI-Timeouts] Auto-save fallido:', e);
        }
    }

    function initAutoSave(interval) {
        interval = interval || 60000;
        if (_autoSaveTimer) clearInterval(_autoSaveTimer);
        _autoSaveTimer = setInterval(autoSave, interval);
        _log('Auto-save inicializado cada ' + (interval/1000) + 's');
    }

    var _inactividadTimer = null;
    var INACTIVIDAD_TIMEOUT = 600000;

    function verificarInactividad() {
        if (_inactividadTimer) clearTimeout(_inactividadTimer);
        _inactividadTimer = setTimeout(function() {
            if (!AUTH || !AUTH.usuario) return;
            cerrarDropdowns();
            _modalTimers.forEach(function(timer, modalId) {
                cerrarModal(modalId, 'inactividad_global');
            });
            if (typeof showToast === 'function') {
                showToast('Sesión pausada por inactividad prolongada', 'warning');
            }
        }, INACTIVIDAD_TIMEOUT);
    }

    function initInactividadGlobal() {
        var eventos = ['mousemove', 'keydown', 'click', 'touchstart', 'scroll'];
        eventos.forEach(function(evt) {
            document.addEventListener(evt, verificarInactividad);
        });
        verificarInactividad();
        _log('Detección de inactividad global inicializada');
    }

    function init() {
        if (typeof bootstrap === 'undefined') {
            setTimeout(init, 500);
            return;
        }
        try {
            initDropdownTimeouts();
            initModalTimeouts();
            initAutoSave();
            initInactividadGlobal();
            _log('Sistema de timeouts UI inicializado');
        } catch(e) {
            console.error('[UI-Timeouts] Error en init:', e);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.TPVTimeouts = {
        cerrarDropdowns: cerrarDropdowns,
        cerrarModal: cerrarModal,
        resetTimers: function() {
            resetearDropdownTimer();
            _modalTimers.forEach(function(timer, modalId) {
                programarCierreModal(modalId, CONFIG.modalTimeout);
            });
        },
        config: CONFIG
    };

})();

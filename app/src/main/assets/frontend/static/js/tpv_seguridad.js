/* ============================================================================
   tpv_seguridad.js — Panel de Seguridad y Biometría
   Consume /api/security/dashboard y rellena los badges de cada blindaje.
   Detecta biometría nativa de Android (puente Chaquopy) si está disponible.
   ========================================================================= */
(function () {
  'use strict';

  function badge(text, cls) {
    return '<span class="badge bg-' + cls + '">' + text + '</span>';
  }

  function pintarEstado(el, activo, detalle) {
    if (!el) return;
    if (activo) {
      el.innerHTML = badge('<i class="bi bi-check-circle-fill me-1"></i>Activo', 'success') +
        (detalle ? ' <span class="text-muted small ms-1">' + detalle + '</span>' : '');
    } else {
      el.innerHTML = badge('Inactivo', 'secondary');
    }
  }

  // Detección de biometría: en el APK, MainActivity expone un puente JS
  // (window.AndroidBiometric / window.Android). En el navegador no existe.
  function detectarBiometria() {
    var el = document.getElementById('seguridad-bio');
    if (!el) return;
    // Puente nativo real de la APK: window.TPVNative (BiometricPrompt).
    var nativo = window.TPVNative && (typeof window.TPVNative.canAuthenticate === 'function');
    if (nativo) {
      var disponible = false;
      var estado = '';
      try { disponible = !!window.TPVNative.canAuthenticate(); } catch (e) {}
      try { if (window.TPVNative.getBiometricStatus) estado = window.TPVNative.getBiometricStatus(); } catch (e) {}
      el.innerHTML = disponible
        ? badge('<i class="bi bi-fingerprint me-1"></i>Disponible y activa', 'success')
        : badge('Sin huella/rostro configurado en el dispositivo', 'warning');
    } else {
      el.innerHTML = badge('Solo en la APK', 'secondary') +
        ' <span class="text-muted small ms-1">la biometría nativa requiere el dispositivo Android</span>';
    }
  }

  window.seguridad_cargarDashboard = function () {
    var overall = document.getElementById('seguridad-overall');
    if (overall) {
      overall.className = 'alert alert-secondary mb-4 text-center';
      overall.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Cargando estado de seguridad...';
    }

    detectarBiometria();

    fetch('/api/security/dashboard', { cache: 'no-store', credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var b = (d && d.blindajes) || {};
        var ok = (d && d.overall_status) || 'DESCONOCIDO';

        if (overall) {
          var secure = ok === 'SECURE';
          overall.className = 'alert mb-4 text-center ' + (secure ? 'alert-success' : 'alert-warning');
          overall.innerHTML = '<i class="bi bi-shield-' + (secure ? 'check' : 'exclamation') +
            ' me-2"></i>Estado general: <strong>' + ok + '</strong>' +
            (d.version ? ' <span class="text-muted small">v' + d.version + '</span>' : '');
        }

        pintarEstado(document.getElementById('seguridad-pci'),
          b.pci_dss && b.pci_dss.active,
          b.pci_dss ? (b.pci_dss.audit_entries + ' auditorías') : '');
        pintarEstado(document.getElementById('seguridad-het'),
          b.het && b.het.active,
          b.het ? (b.het.status + ' · ' + (b.het.active_threats || 0) + ' amenazas') : '');
        pintarEstado(document.getElementById('seguridad-ws'),
          b.websocket && b.websocket.active,
          b.websocket ? ((b.websocket.active_terminals || 0) + ' terminales') : '');
      })
      .catch(function (e) {
        if (overall) {
          overall.className = 'alert alert-danger mb-4 text-center';
          overall.innerHTML = '<i class="bi bi-x-circle me-2"></i>No se pudo cargar el estado de seguridad: ' + e;
        }
      });
  };
})();

/* ============================================================================
   tpv_ui_dialogs.js — Diálogos modales con estilo (reemplazan confirm/alert
   nativos del navegador, que se ven "como Windows"/sistema).
   API:
     await tpvConfirm({title, message, okText, cancelText, danger})  -> bool
     await tpvAlert({title, message, okText})                        -> void
   Compatibles con el tema (usan Bootstrap + tpv_theme.css).
   ========================================================================= */
(function () {
  'use strict';

  function _ensureHost() {
    var host = document.getElementById('tpv-dialog-host');
    if (!host) {
      host = document.createElement('div');
      host.id = 'tpv-dialog-host';
      document.body.appendChild(host);
    }
    return host;
  }

  function _build(opts, withCancel) {
    var o = opts || {};
    var title = o.title || (withCancel ? 'Confirmar' : 'Aviso');
    var message = o.message || '';
    var okText = o.okText || (withCancel ? 'Aceptar' : 'Entendido');
    var cancelText = o.cancelText || 'Cancelar';
    var danger = !!o.danger;
    var icon = o.icon || (danger ? 'bi-exclamation-triangle-fill'
                                 : (withCancel ? 'bi-question-circle-fill' : 'bi-info-circle-fill'));
    var color = danger ? 'danger' : (withCancel ? 'primary' : 'info');

    var id = 'tpvdlg-' + Date.now();
    var html =
      '<div class="modal fade" id="' + id + '" tabindex="-1" aria-hidden="true">' +
        '<div class="modal-dialog modal-dialog-centered">' +
          '<div class="modal-content">' +
            '<div class="modal-header border-0 pb-0">' +
              '<h5 class="modal-title d-flex align-items-center gap-2">' +
                '<i class="bi ' + icon + ' text-' + color + '"></i>' +
                '<span></span>' +
              '</h5>' +
            '</div>' +
            '<div class="modal-body pt-2"><p class="mb-0 text-muted"></p></div>' +
            '<div class="modal-footer border-0 pt-0">' +
              (withCancel ? '<button type="button" class="btn btn-outline-secondary" data-act="cancel"></button>' : '') +
              '<button type="button" class="btn btn-' + color + '" data-act="ok"></button>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</div>';

    var host = _ensureHost();
    host.insertAdjacentHTML('beforeend', html);
    var el = document.getElementById(id);
    // Insertar textos de forma segura (sin innerHTML para evitar inyección).
    el.querySelector('.modal-title span').textContent = title;
    el.querySelector('.modal-body p').textContent = message;
    el.querySelector('[data-act="ok"]').textContent = okText;
    if (withCancel) el.querySelector('[data-act="cancel"]').textContent = cancelText;
    return el;
  }

  function _show(el, withCancel) {
    return new Promise(function (resolve) {
      var resolved = false;
      var done = function (val) {
        if (resolved) return;
        resolved = true;
        resolve(val);
        try { modal.hide(); } catch (e) {}
      };
      var hasBs = window.bootstrap && bootstrap.Modal;
      var modal = hasBs ? new bootstrap.Modal(el, { backdrop: 'static' }) : null;

      el.querySelector('[data-act="ok"]').addEventListener('click', function () { done(true); });
      if (withCancel) {
        el.querySelector('[data-act="cancel"]').addEventListener('click', function () { done(false); });
      }
      el.addEventListener('hidden.bs.modal', function () {
        done(withCancel ? false : true);
        el.remove();
      });

      if (modal) {
        modal.show();
      } else {
        // Fallback si Bootstrap no cargó: usar confirm/alert nativo.
        var txt = el.querySelector('.modal-title span').textContent + '\n\n' +
                  el.querySelector('.modal-body p').textContent;
        el.remove();
        done(withCancel ? window.confirm(txt) : (window.alert(txt), true));
      }
    });
  }

  window.tpvConfirm = function (opts) {
    // Permite tpvConfirm('mensaje') o tpvConfirm({title, message, ...})
    if (typeof opts === 'string') opts = { message: opts };
    return _show(_build(opts, true), true);
  };

  window.tpvAlert = function (opts) {
    if (typeof opts === 'string') opts = { message: opts };
    return _show(_build(opts, false), false);
  };
})();

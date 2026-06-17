/* tpv_anon.js v6a - identidad persistente para cliente anónimo */
(function () {
  'use strict';
  if (window.TPVAnon) return;

  var KEY = 'tpv_anon_client_id';
  var COOKIE = 'tpv_anon_client_id';

  function _sanitize(v) {
    var raw = String(v || '').trim();
    raw = raw.replace(/[^A-Za-z0-9._:-]+/g, '-').slice(0, 80).replace(/^[-._:]+|[-._:]+$/g, '');
    return raw && raw.length >= 6 ? raw : '';
  }

  function _generate() {
    return 'anon-web-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
  }

  function _persist(id) {
    try { localStorage.setItem(KEY, id); } catch (e) {}
    try { document.cookie = COOKIE + '=' + encodeURIComponent(id) + '; path=/; SameSite=Lax'; } catch (e) {}
    return id;
  }

  function getId() {
    try {
      var saved = _sanitize(localStorage.getItem(KEY));
      if (saved) return _persist(saved);
    } catch (e) {}
    var created = _generate();
    return _persist(created);
  }

  function requestId(scope) {
    return 'req-' + (scope || 'web') + '-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
  }

  function isSameOriginUrl(input) {
    try {
      var url = (typeof input === 'string') ? input : (input && input.url ? input.url : String(input || ''));
      var u = new URL(url, window.location.origin);
      return u.origin === window.location.origin;
    } catch (e) {
      return true;
    }
  }

  function patchFetch() {
    if (window.__tpvAnonFetchPatched || typeof window.fetch !== 'function') return;
    var originalFetch = window.fetch.bind(window);
    window.fetch = function (input, init) {
      if (!isSameOriginUrl(input)) {
        return originalFetch(input, init);
      }
      var options = init ? Object.assign({}, init) : {};
      var baseHeaders = (input instanceof Request) ? input.headers : undefined;
      var headers = new Headers(options.headers || baseHeaders || {});
      if (!headers.get('X-TPV-ANON-ID')) headers.set('X-TPV-ANON-ID', getId());
      if (!headers.get('X-TPV-REQUEST-ID')) headers.set('X-TPV-REQUEST-ID', requestId('web'));
      options.headers = headers;
      if (options.credentials === undefined) options.credentials = 'same-origin';
      if (input instanceof Request) {
        return originalFetch(new Request(input, options));
      }
      return originalFetch(input, options);
    };
    window.__tpvAnonFetchPatched = true;
  }

  window.TPVAnon = {
    getId: getId,
    ensure: getId,
    requestId: requestId,
  };

  _persist(getId());
  patchFetch();
})();

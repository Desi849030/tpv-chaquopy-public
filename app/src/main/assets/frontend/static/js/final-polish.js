/* TPV Ultra Smart — final UI/UX progressive enhancement. */
(() => {
  'use strict';

  const state = { announcedOffline: false };

  function ensureLiveRegion() {
    let region = document.getElementById('tpv-a11y-live');
    if (!region) {
      region = document.createElement('div');
      region.id = 'tpv-a11y-live';
      region.className = 'tpv-sr-only';
      region.setAttribute('aria-live', 'polite');
      region.setAttribute('aria-atomic', 'true');
      document.body.appendChild(region);
    }
    return region;
  }

  function announce(message) {
    const region = ensureLiveRegion();
    region.textContent = '';
    requestAnimationFrame(() => { region.textContent = message; });
  }

  function ensureNetworkBanner() {
    let banner = document.getElementById('tpv-network-banner');
    if (!banner) {
      banner = document.createElement('div');
      banner.id = 'tpv-network-banner';
      banner.setAttribute('role', 'status');
      banner.setAttribute('aria-live', 'polite');
      document.body.prepend(banner);
    }
    return banner;
  }

  async function localBackendAvailable() {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 2500);
      const response = await fetch('/api/health', {
        cache: 'no-store', signal: controller.signal, credentials: 'same-origin'
      });
      clearTimeout(timer);
      return response.ok;
    } catch (_) {
      return false;
    }
  }

  async function updateConnectivity() {
    const banner = ensureNetworkBanner();
    const backend = await localBackendAvailable();
    if (!backend) {
      banner.textContent = 'Servidor local no disponible. Reabre la aplicación y espera unos segundos.';
      banner.className = 'visible';
      announce(banner.textContent);
      return;
    }
    if (!navigator.onLine) {
      banner.textContent = 'Modo offline: las operaciones locales siguen disponibles; la sincronización queda pendiente.';
      banner.className = 'visible';
      if (!state.announcedOffline) announce(banner.textContent);
      state.announcedOffline = true;
      return;
    }
    if (state.announcedOffline) {
      banner.textContent = 'Conexión restablecida. Puedes sincronizar los cambios pendientes.';
      banner.className = 'visible online';
      announce(banner.textContent);
      setTimeout(() => { banner.className = ''; }, 3500);
    } else {
      banner.className = '';
    }
    state.announcedOffline = false;
  }

  function accessibleName(element) {
    return (
      element.getAttribute('aria-label') ||
      element.getAttribute('title') ||
      element.textContent || ''
    ).trim();
  }

  function enhanceElement(element) {
    if (!(element instanceof HTMLElement)) return;
    const candidates = [element, ...element.querySelectorAll('button, a, input, select, textarea, table, img')];
    for (const item of candidates) {
      if (item.matches('button, a') && !accessibleName(item)) {
        const icon = item.querySelector('i[class*="bi-"]');
        const iconName = icon?.className.match(/bi-([\w-]+)/)?.[1]?.replaceAll('-', ' ');
        if (iconName) item.setAttribute('aria-label', iconName);
      }
      if (item.matches('button') && !item.getAttribute('type')) item.setAttribute('type', 'button');
      if (item.matches('table')) {
        item.setAttribute('role', 'table');
        item.closest('.table-responsive')?.setAttribute('tabindex', '0');
        item.closest('.table-responsive')?.setAttribute('aria-label', 'Tabla desplazable');
      }
      if (item.matches('img') && !item.hasAttribute('alt')) item.setAttribute('alt', '');
      if (item.matches('input, select, textarea') && !item.getAttribute('aria-label')) {
        const escapedId = item.id && window.CSS?.escape
          ? window.CSS.escape(item.id)
          : item.id.replace(/[^a-zA-Z0-9_-]/g, '');
        const label = escapedId ? document.querySelector(`label[for="${escapedId}"]`) : null;
        const fallback = label?.textContent?.trim() || item.getAttribute('placeholder');
        if (fallback) item.setAttribute('aria-label', fallback);
      }
    }
  }

  function guardRapidClicks() {
    document.addEventListener('click', event => {
      const button = event.target.closest('button[data-tpv-once]');
      if (!button || button.disabled) return;
      button.disabled = true;
      setTimeout(() => { button.disabled = false; }, 1200);
    }, true);
  }

  function initialize() {
    ensureLiveRegion();
    ensureNetworkBanner();
    enhanceElement(document.body);
    guardRapidClicks();
    updateConnectivity();

    window.addEventListener('online', updateConnectivity);
    window.addEventListener('offline', updateConnectivity);
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') updateConnectivity();
    });

    const observer = new MutationObserver(records => {
      for (const record of records) {
        for (const node of record.addedNodes) enhanceElement(node);
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });

    window.TPV_UX = { announce, updateConnectivity, enhanceElement };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize, { once: true });
  } else {
    initialize();
  }
})();

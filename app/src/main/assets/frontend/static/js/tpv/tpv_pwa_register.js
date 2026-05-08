if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/service-worker.js')
          .then(() => console.log('PWA lista'))
          .catch(e => console.error('SW error:', e));
      }

// tpv_config_central.js — Configuración centralizada TPV_CONFIG (claves, versiones)
        const TPV_CONFIG = {
            VERSION: '2.0.0',
            // ══ v6.9 PARCHE_6: Clave generada por Web Crypto en el dispositivo ══
            _deviceKey: null,
            _keyFetched: false,

            KEYS: {},  // Ya NO hay claves hardcodeadas
            CONFIG: {
                development: {
                    debugMode: true,
                    autoCheckLicenseInterval: 5050,
                    showDetailedErrors: true,
                    allowLicenseBypass: false
                },
                production: {
                    debugMode: false,
                    autoCheckLicenseInterval: 300000,
                    showDetailedErrors: false,
                    allowLicenseBypass: false
                }
            },

            // Obtener clave del servidor (generada en start_server.py)
            async _fetchDeviceKey() {
                if (this._keyFetched) return this._deviceKey;
                try {
                    const r = await fetch('/api/config/secret-key', {credentials:'same-origin'});
                    if (r.ok) {
                        const d = await r.json();
                        if (d.secret_key) { this._deviceKey = d.secret_key; }
                    }
                } catch(e) {}
                // Fallback: usar clave derivada del clientId
                if (!this._deviceKey) {
                    const cid = (tpvStorage.getItem('tpv_client_id') || 'tpv-default-cid');
                    const encoder = new TextEncoder();
                    const data = encoder.encode('TPV-' + cid + '-v69');
                    const hashBuf = await crypto.subtle.digest('SHA-256', data);
                    const hashArr = Array.from(new Uint8Array(hashBuf));
                    this._deviceKey = hashArr.map(b => b.toString(16).padStart(2,'0')).join('').substring(0,32);
                }
                this._keyFetched = true;
                return this._deviceKey;
            },

            ENVIRONMENT: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'development' : 'production',
            getCurrentKey: function() {
                // v6.9: usar clave del dispositivo (sin hardcode)
                if (this._deviceKey) return this._deviceKey;
                var cid = (tpvStorage && tpvStorage.getItem ? tpvStorage.getItem('tpv_client_id') : null) || 'tpv-default-cid';
                var h = 0;
                for (var i = 0; i < cid.length; i++) { h = ((h << 5) - h) + cid.charCodeAt(i); h |= 0; }
                return 'tpv-' + Math.abs(h).toString(16).padStart(8, '0');
            },
            getCurrentConfig: function() {
                return this.CONFIG[this.ENVIRONMENT];
            },
            setEnvironment: function(env) {
                if (env === 'development' || env === 'production') {
                    this.ENVIRONMENT = env;
                    tpvStorage.setItem('tpv_environment', env);
                    if (this.CONFIG[env].debugMode) {
                        console.log(`🔧 Entorno cambiado a: ${env}`);
                    }
                    return true;
                }
                return false;
            },
            getEnvironment: function() {
                return this.ENVIRONMENT;
            },
            init: function() {
                if (this._fetchDeviceKey) this._fetchDeviceKey();
                const savedEnv = tpvStorage.getItem('tpv_environment');
                if (savedEnv && (savedEnv === 'development' || savedEnv === 'production')) {
                    this.ENVIRONMENT = savedEnv;
                } else {
                    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                        this.ENVIRONMENT = 'development';
                    } else {
                        this.ENVIRONMENT = 'production';
                    }
                }
            }
                this._fetchDeviceKey();
            }
        };
        
        // Auto-inicializar
        
        // Auto-inicializar
        TPV_CONFIG.init();

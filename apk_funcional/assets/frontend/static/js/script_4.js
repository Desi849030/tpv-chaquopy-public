/**
         * TPV Configuration Module
         * Sistema de configuración centralizado para el TPV
         */
        const TPV_CONFIG = {
            VERSION: '6.9',
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
                    const cid = (localStorage.getItem('tpv_client_id') || 'tpv-default-cid');
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
                return this._deviceKey || this._fetchDeviceKey();
            },
            getCurrentConfig: function() {
                return this.CONFIG[this.ENVIRONMENT];
            },
            setEnvironment: function(env) {
                if (env === 'development' || env === 'production') {
                    this.ENVIRONMENT = env;
                    localStorage.setItem('tpv_environment', env);
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
                const savedEnv = localStorage.getItem('tpv_environment');
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
        };
        
        // Auto-inicializar
        
        // Auto-inicializar
        TPV_CONFIG.init();

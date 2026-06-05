// tpv_estado_backup.js -- Auto-check licencia, backup/restore
        // ==================== AUTO-ACTUALIZACIÓN DE LICENCIA ====================
        let licenseCheckInterval = null;
        
        function startLicenseAutoCheck() {
            // Limpiar intervalo existente
            if (licenseCheckInterval) {
                clearInterval(licenseCheckInterval);
            }
            
            const unidad = tpvState.licencia?.unidadTiempo || 'dias';
            
            // Configurar intervalo según la unidad
            if (unidad === 'segundos') {
                // Actualizar cada segundo
                licenseCheckInterval = setInterval(() => {
        tpvStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
                    lic_checkLicense();
                }, 1000);
            } else if (unidad === 'minutos') {
                // Actualizar cada 10 segundos
                licenseCheckInterval = setInterval(() => {
        tpvStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
                    lic_checkLicense();
                }, 10000);
            } else {
                // Para días, actualizar cada 5 minutos
                licenseCheckInterval = setInterval(() => {
        tpvStorage.setItem("tpv_test_rapido","true"); // Fix: activar modo prueba
                    lic_checkLicense();
                }, 300000);
            }
        }
        
        // ========== FUNCIONES DE BACKUP AUTOMÁTICO ==========
        async function crear_backup_automatico(tipo = 'auto') {
            try {
                const timestamp = new Date().toISOString();
                const backupData = {
                    timestamp: timestamp,
                    tipo: tipo,
                    version: '1.0',
                    data: tpvState
                };
                
                // Guardar en localStorage
                const backupKey = `tpv_backup_${timestamp}`;
                tpvStorage.setJSON(backupKey, backupData);
                
                // Mantener solo las últimas 10 copias
                const allBackups = tpvStorage.keys().filter(key => key.startsWith('tpv_backup_'));
                if (allBackups.length > 10) {
                    allBackups.sort().slice(0, allBackups.length - 10).forEach(key => {
                        tpvStorage.removeItem(key);
                    });
                }
                
                console.log('✅ Copia de seguridad creada:', tipo);
                return true;
            } catch (error) {
                console.error('❌ Error al crear backup:', error);
                return false;
            }
        }
        
        async function crear_backup_manual() {
            const success = await crear_backup_automatico('manual');
            if (success) {
                if(typeof showToast==='function')showToast('Copia de seguridad creada exitosamente', 'success');
                actualizar_lista_backups();
            } else {
                if(typeof showToast==='function')showToast('Error al crear la copia de seguridad', 'danger');
            }
        }
        
        function actualizar_lista_backups() {
            const allBackups = tpvStorage.keys()
                .filter(key => key.startsWith('tpv_backup_'))
                .map(key => {
                    const data = tpvStorage.getJSON(key);
                    return {
                        key: key,
                        timestamp: data.timestamp,
                        tipo: data.tipo
                    };
                })
                .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            
            const tbody = document.getElementById('backup-list-body');
            if (!tbody) return;
            
            tbody.innerHTML = allBackups.map(backup => {
                const fecha = new Date(backup.timestamp).toLocaleString();
                return `
                    <tr>
                        <td>${fecha}</td>
                        <td><span class="badge bg-${backup.tipo === 'manual' ? 'primary' : 'secondary'}">${backup.tipo}</span></td>
                        <td>
                            <button class="btn btn-sm btn-success" onclick="restaurar_backup_directo('${backup.key}')">
                                <i class="bi bi-cloud-arrow-down"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="eliminar_backup_individual('${backup.key}')">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        }
        
        async function restaurar_backup(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = async function(e) {
                try {
                    const backupData = JSON.parse(e.target.result);
                    tpvState = backupData.data;
                    await saveState();
                    if(typeof showToast==='function')showToast('Copia de seguridad restaurada exitosamente', 'success');
                    location.reload();
                } catch (error) {
                    if(typeof showToast==='function')showToast('Error al restaurar la copia de seguridad', 'danger');
                    console.error(error);
                }
            };
            reader.readAsText(file);
        }
        
        async function restaurar_backup_directo(backupKey) {
            if (!confirm('¿Está seguro de restaurar esta copia de seguridad? Se perderán los cambios no guardados.')) {
                return;
            }
            
            try {
                const backupData = tpvStorage.getJSON(backupKey);
                tpvState = backupData.data;
                await saveState();
                if(typeof showToast==='function')showToast('Copia de seguridad restaurada exitosamente', 'success');
                location.reload();
            } catch (error) {
                if(typeof showToast==='function')showToast('Error al restaurar la copia de seguridad', 'danger');
                console.error(error);
            }
        }
        

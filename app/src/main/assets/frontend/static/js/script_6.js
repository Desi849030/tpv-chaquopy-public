function esMovil(){return /Android|iPhone|iPad|iPod/i.test(navigator.userAgent)}
function csvSafe(v){return `"${String(v??'').replace(/"/g,'""')}"`}
function descargar(n,b){const u=URL.createObjectURL(b);const a=document.createElement('a');a.href=u;a.download=n;document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(u)}
function fechaEnRango(f,d,h){if(!f)return true;f=new Date(f);if(d&&f<new Date(d))return false;if(h&&f>new Date(h+'T23:59:59'))return false;return true}

async function exportarTPVCompleto(){
try{
// Validar que XLSX esté cargado
if(typeof XLSX==='undefined'){
showToast('Error: Biblioteca de Excel no cargada. Recarga la página.','danger');
return;
}

const d=document.getElementById('export-desde')?.value;
const h=document.getElementById('export-hasta')?.value;
const n='TPV_'+new Date().toISOString().replace(/[:T]/g,'_').slice(0,19);

// VENTAS - Usar datos del estado en lugar del DOM
const ventas=[['Fecha','Hora','Producto','Cantidad','Precio','Total']];
if(tpvState.historialVentas && tpvState.historialVentas.length>0){
tpvState.historialVentas.forEach(v=>{
if(!fechaEnRango(v.fecha,d,h))return;
const fecha=new Date(v.fecha);
ventas.push([
fecha.toLocaleDateString('es-ES'),
fecha.toLocaleTimeString('es-ES'),
v.nombre||'',
v.cantidad||0,
parseFloat((v.precio||0).toFixed(2)),
parseFloat((v.total||0).toFixed(2))
]);
});
}

// INVENTARIO - Usar datos del estado
const inventario=[['Producto','Categoría','Precio','Unidad','Inicial','Final','Vendido','Importe','Costo','Comisión','Ganancia']];
if(tpvState.productos && tpvState.productos.length>0){
tpvState.productos.forEach(p=>{
const vendido=p.vendido||0;
const importe=(vendido*(p.precio||0));
const costo=(vendido*(p.costoUnitario||0));
const comision=p.tieneComision?((p.precio||0)*(p.porcentajeComision||0)/100*vendido):0;
const ganancia=importe-costo-comision;
inventario.push([
p.nombre||'',
p.categoria||'',
parseFloat((p.precio||0).toFixed(2)),
p.unidadMedida||'',
p.cantidadInicial||0,
p.cantidad||0,
vendido,
parseFloat(importe.toFixed(2)),
parseFloat(costo.toFixed(2)),
parseFloat(comision.toFixed(2)),
parseFloat(ganancia.toFixed(2))
]);
});
}

// CIERRES - Usar datos del estado
const cierres=[['Fecha','Total','Costo','Comisión','Ganancia']];
if(tpvState.cierresCaja && tpvState.cierresCaja.length>0){
tpvState.cierresCaja.forEach(c=>{
if(!fechaEnRango(c.fecha,d,h))return;
cierres.push([
new Date(c.fecha).toLocaleDateString('es-ES'),
parseFloat((c.totalVentas||0).toFixed(2)),
parseFloat((c.totalCostos||0).toFixed(2)),
parseFloat((c.totalComisiones||0).toFixed(2)),
parseFloat((c.gananciaTotal||0).toFixed(2))
]);
});
}

// Validar que hay datos para exportar
if(ventas.length<=1 && inventario.length<=1 && cierres.length<=1){
showToast('No hay datos para exportar en el rango seleccionado','warning');
return;
}

// Crear libro de Excel
const wb=XLSX.utils.book_new();
XLSX.utils.book_append_sheet(wb,XLSX.utils.aoa_to_sheet(ventas),'Ventas');
XLSX.utils.book_append_sheet(wb,XLSX.utils.aoa_to_sheet(inventario),'Inventario');
XLSX.utils.book_append_sheet(wb,XLSX.utils.aoa_to_sheet(cierres),'Cierres');

// CORRECCIÓN CRÍTICA: Usar await para móviles
await exportar_xlsx_seguro(wb, n+'.xlsx');

}catch(e){
console.error('Error en exportación:',e);
showToast('Error al exportar: '+e.message,'danger');
}
}

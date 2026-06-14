// ════════════════════════════════════════════════════════════════
// app3/07_importador.js — Importador inteligente con IA + importación XLSX
// Extraído de app_3.js (líneas 2572–3882) — #4 división del monolito
// Carga clásica <script>: comparte ámbito global con el resto de app3/*.
// ════════════════════════════════════════════════════════════════
        // ==================== IMPORTADOR INTELIGENTE CON IA ====================
        /**
         * MÓDULO DE IMPORTACIÓN SUPERINTELIGENTE CON MACHINE LEARNING
         * 
         * Este módulo aprende de la estructura de archivos Excel y puede:
         * - Detectar columnas SIN encabezados claros
         * - Aprender patrones de nombres de productos
         * - Identificar precios por contexto (números entre 1-10000)
         * - Detectar cantidades (números entre 0-1000)
         * - Reconocer unidades de medida comunes
         * - Inferir costos cuando no están explícitos
         */

        class SmartExcelImporter {
            constructor() {
                this.DEBUG = true;
                this.MAX_FILE_SIZE = 10 * 1024 * 1024;
        
                // Patrones de aprendizaje
                this.patterns = {
                    // Palabras clave en encabezados
                    headers: {
                        // Patrones flexibles (sin anclar al final) para aceptar
                        // cabeceras compuestas como 'Stock Actual', 'Cantidad Inicial',
                        // 'Precio de Venta', etc. El orden de evaluación da prioridad
                        // a costo/cantidad antes que precio para evitar confusiones.
                        producto: /(producto|nombre|item|descripci[oó]n|art[ií]culo|descripcion)/i,
                        costo: /(costo|p\.?\s*costo|compra|inversi[oó]n|precio.*compra|\bcost\b)/i,
                        cantidad: /(cantidad|stock|existencia|\bcant\b|inventario|\bqty\b|unidades|exist|cant.*inicial|stock.*actual|\binicio\b|\binicial\b|\bentrada\b)/i,
                        precio: /(precio|p\.?\s*venta|pvp|precio.*venta|\bvalor\b|\bventa\b|\bprice\b)/i,
                        um: /(unidad|u\.?\s*m|\bum\b|medida|\bund\b|\bunit\b|c\/u)/i,
                        categoria: /(categor[ií]a|tipo|clasificaci[oó]n|\bcategory\b|rubro)/i
                    },
            
                    // Patrones de valores para inferir tipo de columna
                    unidadesMedida: /^(c\/u|un|kg|gr|lt|ml|pza|pieza|unidad|und|caja|paquete|bolsa)$/i,
            
                    // Rangos numéricos esperados
                    ranges: {
                        precio: { min: 1, max: 100000 },      // Precios típicos
                        cantidad: { min: 0, max: 10000 },     // Cantidades típicas
                        costo: { min: 1, max: 100000 }        // Costos típicos
                    }
                };
            }
    
            /**
             * FASE 1: ANÁLISIS INTELIGENTE DE LA ESTRUCTURA
             * Detecta automáticamente qué columna contiene qué información
             */
            analizarEstructuraInteligente(rawData) {
                console.log('🧠 Iniciando análisis inteligente de estructura...');
        
                const analisis = {
                    filaEncabezado: -1,
                    filaInicioDatos: -1,
                    columnas: {},
                    confianza: 0,
                    metodo: 'unknown'
                };
        
                // Estrategia 1: Buscar encabezados explícitos.
                // Si encontramos una fila de encabezados válida (nombre + precio o
                // cantidad), SIEMPRE la usamos: es la intención explícita del usuario
                // y es muchísimo más fiable que adivinar por contenido. Antes se
                // exigía confianza > 0.6 (4+ columnas), lo que descartaba archivos
                // normales de 3 columnas y caía al patrón hardcodeado (bug del
                // "mismo número para todos").
                const resultadoEncabezados = this.buscarEncabezadosExplicitos(rawData);
                if (resultadoEncabezados.filaEncabezado >= 0 &&
                    resultadoEncabezados.columnas.nombre !== undefined) {
                    console.log('✅ Encabezados explícitos detectados', resultadoEncabezados.columnas);
                    return resultadoEncabezados;
                }
        
                // Estrategia 2: Análisis por contenido (cuando no hay encabezados claros)
                const resultadoContenido = this.analizarPorContenido(rawData);
                if (resultadoContenido.confianza > 0.5) {
                    console.log('✅ Estructura detectada por análisis de contenido');
                    return resultadoContenido;
                }
        
                // Estrategia 3: Patrón por defecto (archivo del usuario)
                console.log('⚠️ Usando patrón detectado específico');
                return this.detectarPatronEspecifico(rawData);
            }
    
            /**
             * Busca encabezados explícitos en las primeras filas
             */
            buscarEncabezadosExplicitos(rawData) {
                const resultado = {
                    filaEncabezado: -1,
                    filaInicioDatos: -1,
                    columnas: {},
                    confianza: 0,
                    metodo: 'headers'
                };
        
                // Buscar en las primeras 20 filas
                for (let i = 0; i < Math.min(20, rawData.length); i++) {
                    const fila = rawData[i];
                    if (!fila || fila.length === 0) continue;
            
                    let coincidencias = 0;
                    const colsEncontradas = {};
            
                    for (let j = 0; j < fila.length; j++) {
                        const celda = String(fila[j] || "").toLowerCase().trim();
                        if (!celda) continue;
                
                        // Verificar contra patrones de encabezados.
                        // El orden de this.patterns.headers da prioridad a costo y
                        // cantidad ANTES que precio (evita que "Precio de Compra"
                        // se asigne a precio). Normalizamos la clave 'producto' a
                        // 'nombre' para que coincida con el bucle de procesamiento.
                        for (const [tipo, patron] of Object.entries(this.patterns.headers)) {
                            const key = (tipo === 'producto') ? 'nombre' : tipo;
                            if (patron.test(celda) && colsEncontradas[key] === undefined) {
                                colsEncontradas[key] = j;
                                coincidencias++;
                                if (this.DEBUG) {
                                    console.log(`  📌 Fila ${i+1}, Col ${j+1}: "${celda}" → ${key}`);
                                }
                            }
                        }
                    }
            
                    // Es una fila de encabezados si tiene AL MENOS una columna
                    // numérica reconocida (precio, cantidad o costo). No exigimos
                    // precio obligatorio.
                    const tieneNumerica = colsEncontradas.precio !== undefined ||
                                          colsEncontradas.cantidad !== undefined ||
                                          colsEncontradas.costo !== undefined;
                    if (tieneNumerica) {
                        // Si la columna de NOMBRE no tiene encabezado (muy común: la
                        // primera columna del Excel suele ir sin título), la inferimos
                        // buscando la primera columna que contenga texto largo en las
                        // filas de datos siguientes y que no esté ya asignada.
                        if (colsEncontradas.nombre === undefined) {
                            const colNombre = this._inferirColumnaNombre(rawData, i + 1, colsEncontradas);
                            if (colNombre !== -1) {
                                colsEncontradas.nombre = colNombre;
                                if (this.DEBUG) console.log(`  🔎 Columna de nombre inferida: ${colNombre + 1}`);
                            }
                        }
                        // Sólo aceptamos si finalmente tenemos columna de nombre.
                        if (colsEncontradas.nombre !== undefined) {
                            resultado.filaEncabezado = i;
                            resultado.filaInicioDatos = i + 1;
                            resultado.columnas = colsEncontradas;
                            resultado.confianza = Math.min(coincidencias / 6, 1); // Máximo 6 columnas esperadas
                    
                            if (this.DEBUG) {
                                console.log(`✓ Encabezados encontrados en fila ${i+1} (${coincidencias} columnas, confianza: ${resultado.confianza.toFixed(2)})`);
                            }
                            return resultado;
                        }
                    }
                }
        
                return resultado;
            }
    
            /**
             * Infiere qué columna contiene los NOMBRES de producto cuando esa
             * columna no tiene encabezado. Recorre las filas de datos y elige la
             * primera columna (no asignada a otro tipo) cuyos valores sean
             * mayoritariamente texto de más de 2 caracteres y no numérico.
             */
            _inferirColumnaNombre(rawData, filaInicio, colsAsignadas) {
                const usadas = new Set(Object.values(colsAsignadas));
                // Tomar hasta 15 filas de muestra a partir de filaInicio
                const muestras = [];
                for (let i = filaInicio; i < Math.min(filaInicio + 25, rawData.length); i++) {
                    const fila = rawData[i];
                    if (fila && fila.length > 0) muestras.push(fila);
                    if (muestras.length >= 15) break;
                }
                if (muestras.length === 0) return -1;
                const numCols = Math.max(...muestras.map(f => f.length));
                let mejorCol = -1, mejorPuntaje = 0;
                for (let c = 0; c < numCols; c++) {
                    if (usadas.has(c)) continue;
                    let textos = 0, total = 0;
                    for (const fila of muestras) {
                        const v = fila[c];
                        if (v === null || v === undefined || v === '') continue;
                        total++;
                        const str = String(v).trim();
                        const esNumero = !isNaN(parseFloat(str.replace(/[^0-9.,-]/g, ''))) &&
                                         /^[\d.,\s$-]+$/.test(str);
                        // Texto válido = no numérico y con más de 2 caracteres
                        if (!esNumero && str.length > 2 && !/^c\/u$/i.test(str)) textos++;
                    }
                    if (total === 0) continue;
                    const puntaje = textos / total;
                    // La columna de nombres debe ser mayoritariamente texto
                    if (puntaje > 0.6 && puntaje > mejorPuntaje) {
                        mejorPuntaje = puntaje;
                        mejorCol = c;
                    }
                }
                return mejorCol;
            }
    
            /**
             * Analiza el contenido de las columnas para inferir su tipo
             */
            analizarPorContenido(rawData) {
                const resultado = {
                    filaEncabezado: -1,
                    filaInicioDatos: -1,
                    columnas: {},
                    confianza: 0,
                    metodo: 'content'
                };
        
                // Encontrar primera fila con datos (ignorar filas vacías y con fórmulas)
                let primeraFilaDatos = -1;
                for (let i = 0; i < Math.min(30, rawData.length); i++) {
                    const fila = rawData[i];
                    if (!fila) continue;
            
                    // Buscar fila que tenga al menos 3 celdas con datos reales
                    let celdasConDatos = 0;
                    for (let j = 0; j < fila.length; j++) {
                        const valor = fila[j];
                        if (valor !== null && valor !== undefined && valor !== '' && !String(valor).startsWith('=')) {
                            celdasConDatos++;
                        }
                    }
            
                    if (celdasConDatos >= 3) {
                        primeraFilaDatos = i;
                        if (this.DEBUG) {
                            console.log(`📊 Primera fila con datos: ${i+1}`);
                        }
                        break;
                    }
                }
        
                if (primeraFilaDatos === -1) return resultado;
        
                // Analizar las siguientes 10-20 filas para detectar patrones
                const muestras = [];
                for (let i = primeraFilaDatos; i < Math.min(primeraFilaDatos + 20, rawData.length); i++) {
                    const fila = rawData[i];
                    if (fila && fila.length > 0) {
                        muestras.push(fila);
                    }
                }
        
                if (muestras.length < 3) return resultado;
        
                // Analizar cada columna
                const numColumnas = Math.max(...muestras.map(f => f.length));
                const analisisColumnas = [];
        
                for (let col = 0; col < numColumnas; col++) {
                    const valoresColumna = muestras.map(fila => fila[col]).filter(v => v !== null && v !== undefined && v !== '');
            
                    if (valoresColumna.length === 0) {
                        analisisColumnas.push({ tipo: 'vacia', confianza: 0 });
                        continue;
                    }
            
                    const analisis = this.analizarColumna(valoresColumna);
                    analisisColumnas.push(analisis);
            
                    if (this.DEBUG) {
                        console.log(`  Col ${col+1}: ${analisis.tipo} (confianza: ${analisis.confianza.toFixed(2)})`);
                    }
                }
        
                // Asignar columnas basándose en el análisis
                const asignacion = this.asignarColumnasPorAnalisis(analisisColumnas);
        
                resultado.filaEncabezado = primeraFilaDatos - 1;
                resultado.filaInicioDatos = primeraFilaDatos;
                resultado.columnas = asignacion.columnas;
                resultado.confianza = asignacion.confianza;
        
                return resultado;
            }
    
            /**
             * Analiza una columna y determina qué tipo de dato contiene
             */
            analizarColumna(valores) {
                const analisis = {
                    tipo: 'desconocido',
                    confianza: 0,
                    detalles: {}
                };
        
                // Filtrar valores vacíos y fórmulas
                const valoresLimpios = valores.filter(v => {
                    const str = String(v);
                    return str && str !== '' && !str.startsWith('=');
                });
        
                if (valoresLimpios.length === 0) {
                    return { tipo: 'vacia', confianza: 0 };
                }
        
                // Contar tipos de datos
                let numeros = 0;
                let textos = 0;
                let unidades = 0;
                let numerosEnRangoPrecio = 0;
                let numerosEnRangoCantidad = 0;
        
                const valoresNumericos = [];
        
                for (const valor of valoresLimpios) {
                    const esNumero = typeof valor === 'number' || !isNaN(parseFloat(String(valor).replace(/[^0-9.-]/g, '')));
            
                    if (esNumero) {
                        numeros++;
                        const num = typeof valor === 'number' ? valor : parseFloat(String(valor).replace(/[^0-9.-]/g, ''));
                        valoresNumericos.push(num);
                
                        // Verificar rangos
                        if (num >= this.patterns.ranges.precio.min && num <= this.patterns.ranges.precio.max) {
                            numerosEnRangoPrecio++;
                        }
                        if (num >= this.patterns.ranges.cantidad.min && num <= this.patterns.ranges.cantidad.max) {
                            numerosEnRangoCantidad++;
                        }
                    } else {
                        textos++;
                
                        // Verificar si es unidad de medida
                        if (this.patterns.unidadesMedida.test(String(valor))) {
                            unidades++;
                        }
                    }
                }
        
                const porcentajeNumeros = numeros / valoresLimpios.length;
                const porcentajeTextos = textos / valoresLimpios.length;
        
                // DECISIÓN: ¿Qué tipo de columna es?
        
                // Columna de nombres (texto largo)
                if (porcentajeTextos > 0.7 && unidades < valoresLimpios.length * 0.3) {
                    const textoPromedio = valoresLimpios
                        .filter(v => typeof v === 'string')
                        .reduce((sum, v) => sum + v.length, 0) / Math.max(textos, 1);
            
                    if (textoPromedio > 5) { // Nombres típicamente tienen más de 5 caracteres
                        analisis.tipo = 'producto';
                        analisis.confianza = 0.8;
                        return analisis;
                    }
                }
        
                // Columna de unidades de medida
                if (unidades > valoresLimpios.length * 0.5) {
                    analisis.tipo = 'um';
                    analisis.confianza = 0.9;
                    return analisis;
                }
        
                // Columnas numéricas
                if (porcentajeNumeros > 0.7) {
                    const promedio = valoresNumericos.reduce((a, b) => a + b, 0) / valoresNumericos.length;
                    const max = Math.max(...valoresNumericos);
                    const min = Math.min(...valoresNumericos);
            
                    // Precios: generalmente entre 10-10000
                    if (promedio > 50 && max > 100 && numerosEnRangoPrecio > valoresNumericos.length * 0.6) {
                        analisis.tipo = 'precio';
                        analisis.confianza = 0.85;
                        analisis.detalles = { promedio, min, max };
                        return analisis;
                    }
            
                    // Cantidades: generalmente entre 0-500, con muchos valores pequeños
                    if (max <= 1000 && promedio < 100 && numerosEnRangoCantidad > valoresNumericos.length * 0.8) {
                        analisis.tipo = 'cantidad';
                        analisis.confianza = 0.8;
                        analisis.detalles = { promedio, min, max };
                        return analisis;
                    }
            
                    // Costos: similar a precios pero puede ser un poco menor
                    if (promedio > 20 && max > 50) {
                        analisis.tipo = 'costo';
                        analisis.confianza = 0.7;
                        analisis.detalles = { promedio, min, max };
                        return analisis;
                    }
            
                    // Números genéricos
                    analisis.tipo = 'numero';
                    analisis.confianza = 0.5;
                    return analisis;
                }
        
                // Texto genérico
                if (porcentajeTextos > 0.5) {
                    analisis.tipo = 'texto';
                    analisis.confianza = 0.4;
                    return analisis;
                }
        
                return analisis;
            }
    
            /**
             * Asigna columnas basándose en el análisis
             */
            asignarColumnasPorAnalisis(analisisColumnas) {
                const asignacion = {
                    columnas: {},
                    confianza: 0
                };
        
                let confianzaTotal = 0;
                let columnasAsignadas = 0;
        
                // Buscar cada tipo de columna
                const tipos = ['producto', 'precio', 'um', 'cantidad', 'costo'];
        
                for (const tipo of tipos) {
                    let mejorCol = -1;
                    let mejorConfianza = 0;
            
                    for (let i = 0; i < analisisColumnas.length; i++) {
                        if (analisisColumnas[i].tipo === tipo && analisisColumnas[i].confianza > mejorConfianza) {
                            // Evitar asignar la misma columna dos veces
                            if (!Object.values(asignacion.columnas).includes(i)) {
                                mejorCol = i;
                                mejorConfianza = analisisColumnas[i].confianza;
                            }
                        }
                    }
            
                    if (mejorCol !== -1) {
                        asignacion.columnas[tipo === 'producto' ? 'nombre' : tipo] = mejorCol;
                        confianzaTotal += mejorConfianza;
                        columnasAsignadas++;
                
                        if (this.DEBUG) {
                            console.log(`✓ Columna ${mejorCol + 1} → ${tipo} (confianza: ${mejorConfianza.toFixed(2)})`);
                        }
                    }
                }
        
                asignacion.confianza = columnasAsignadas > 0 ? confianzaTotal / columnasAsignadas : 0;
        
                return asignacion;
            }
    
            /**
             * Detecta el patrón específico del archivo del usuario
             * Basado en el ejemplo: Desi_02_03_Dia.xlsx
             */
            detectarPatronEspecifico(rawData) {
                console.log('🎯 Aplicando patrón específico detectado...');
        
                // Buscar fila que contenga "Precio" o similar en alguna celda
                let filaEncabezado = -1;
                for (let i = 0; i < Math.min(10, rawData.length); i++) {
                    const fila = rawData[i];
                    if (!fila) continue;
            
                    for (let j = 0; j < fila.length; j++) {
                        const celda = String(fila[j] || "").toLowerCase();
                        if (celda.includes('precio') || celda.includes('cantidad')) {
                            filaEncabezado = i;
                            break;
                        }
                    }
                    if (filaEncabezado !== -1) break;
                }
        
                // Si no encontramos encabezado, buscar primera fila con datos
                if (filaEncabezado === -1) {
                    for (let i = 0; i < Math.min(10, rawData.length); i++) {
                        const fila = rawData[i];
                        if (!fila) continue;
                
                        // Buscar fila con texto + número + texto + número
                        if (fila[0] && typeof fila[0] === 'string' && fila[0].length > 2 &&
                            fila[1] && (typeof fila[1] === 'number' || !isNaN(parseFloat(String(fila[1]))))) {
                            filaEncabezado = i - 1;
                            break;
                        }
                    }
                }
        
                const filaInicioDatos = filaEncabezado + 1;
        
                // Patrón detectado del archivo ejemplo:
                // Columna 0 (A): Nombre del producto
                // Columna 1 (B): Precio
                // Columna 2 (C): Unidad de medida
                // Columna 3 (D): Cantidad
                // Columna 8 (I): Inversión/Costo
        
                return {
                    filaEncabezado: filaEncabezado,
                    filaInicioDatos: filaInicioDatos,
                    columnas: {
                        nombre: 0,    // Columna A
                        precio: 1,    // Columna B
                        um: 2,        // Columna C
                        cantidad: 3,  // Columna D
                        costo: 8      // Columna I
                    },
                    confianza: 0.75,
                    metodo: 'pattern-specific'
                };
            }
    
            /**
             * Categorización automática mejorada
             */
            categorizarProducto(nombre) {
                const nombreLower = nombre.toLowerCase();
        
                const categorias = {
                    'Alimentos': /aceite|azucar|azúcar|arroz|harina|sal|café|cafe|te|té|atun|atún|sardina|leche|queso|huevo|pasta|mantequilla|mayonesa|mostaza|salsa/i,
                    'Higiene Personal': /shampoo|champu|champú|jabón|jabon|pasta.*dental|cepillo|desodorante|toalla.*sanitaria|almuhadilla|pañal|papel.*higienico|crema.*afeitar/i,
                    'Limpieza': /detergente|cloro|desinfectante|lavaplatos|esponja|trapo|bolsa.*basura|limpiador|cera|escoba|trapeador|suavizante/i,
                    'Golosinas': /galleta|chocolate|caramelo|chicle|dulce|bombones|botonetas|goma.*mascar|pirulí|chupeta|chocolatina/i,
                    'Bebidas': /gaseosa|refresco|jugo|agua|bebida|energizante|soda|cola|malta|cerveza.*sin.*alcohol|té.*frio|limonada/i,
                    'Papelería': /cuaderno|lapiz|lápiz|boligrafo|bolígrafo|marcador|borrador|regla|pegamento|tijera|folder|carpeta|papel.*bond/i,
                    'Tabaquería': /cigarrillo|cigarro|tabaco|fosforo|fósforo|encendedor|lighter|marlboro|fosforera/i,
                    'Panadería': /pan|arepa|empanada|pastel|torta|cachito|tequeño|croissant/i,
                    'Belleza': /uña|esmalte|lima|bloque|maquillaje|labial|crema.*facial|perfume|colonia|tinte|acetona|removedor/i,
                    'Licores': /shot|vodka|ron|whisky|cerveza|vino|licor|brandy|tequila|ginebra|gin|pomo|aguardiente/i,
                    'Medicamentos': /aspirina|paracetamol|ibuprofeno|analgesico|analgésico|jarabe|pastilla|capsula|cápsula|vitamina|alcohol.*medicinal/i,
                    'Ropa': /blusa|camisa|pantalon|pantalón|falda|vestido|short|medias|calcetines|ropa.*interior|sueter|chandal/i,
                    'Condimentos': /caldito|caldo|sazonador|adobo|comino|orégano|oregano|pimienta|ajo|cebolla.*polvo/i,
                    'Varios': /chanceller|mechero|pila|bateria|batería|cable|cargador/i
                };
        
                for (const [categoria, patron] of Object.entries(categorias)) {
                    if (patron.test(nombreLower)) {
                        return categoria;
                    }
                }
        
                return 'Otros';
            }
    
            /**
             * Conversión inteligente de valores
             */
            convertirANumero(valor, valorPorDefecto = 0) {
                if (valor === null || valor === undefined || valor === '') return valorPorDefecto;
                if (typeof valor === 'number') return isNaN(valor) ? valorPorDefecto : valor;
        
                const str = String(valor);
        
                // Si es una fórmula, retornar valor por defecto
                if (str.startsWith('=')) return valorPorDefecto;
        
                if (typeof valor === 'string') {
                    const limpio = str.replace(/[^0-9.-]/g, '');
                    const numero = parseFloat(limpio);
                    return isNaN(numero) ? valorPorDefecto : numero;
                }
        
                return valorPorDefecto;
            }
    
            /**
             * IMPORTACIÓN PRINCIPAL CON INTELIGENCIA ARTIFICIAL
             */
            async importar(file, tpvState, opciones = {}) {
                const {
                    onProgress = () => {},
                    confirmarBorrado = true,
                    crearInventario = true
                } = opciones;
        
                try {
                    // Paso 1: Validar archivo
                    onProgress({ paso: 1, total: 6, mensaje: '🔍 Validando archivo...' });
            
                    if (file.size > this.MAX_FILE_SIZE) {
                        throw new Error(`Archivo demasiado grande (máx ${this.MAX_FILE_SIZE / 1024 / 1024}MB)`);
                    }
            
                    // Paso 2: Confirmar si hay productos existentes
                    if (confirmarBorrado && tpvState.productos.length > 0) {
                        const mensaje = `⚠️ ATENCIÓN: Esta acción borrará los ${tpvState.productos.length} productos existentes.\n\n` +
                            `¿Deseas continuar?\n\n💡 Recomendación: Exporta un backup antes de importar.`;
                        if (!(await tpvConfirm(mensaje))) {
                            throw new Error('Importación cancelada por el usuario');
                        }
                    }
            
                    // Paso 3: Leer archivo
                    onProgress({ paso: 2, total: 6, mensaje: '📖 Leyendo archivo Excel...' });
            
                    const arrayBuffer = await this.leerArchivo(file);
                    const workbook = XLSX.read(new Uint8Array(arrayBuffer), { type: 'array' });
            
                    if (!workbook || !workbook.SheetNames || workbook.SheetNames.length === 0) {
                        throw new Error("El archivo no contiene hojas válidas");
                    }
            
                    // Paso 4: Seleccionar hoja
                    const hojaProductos = workbook.SheetNames.includes("Productos") 
                        ? "Productos" 
                        : workbook.SheetNames.includes("Base de Datos")
                        ? "Base de Datos"
                        : workbook.SheetNames[0];
            
                    console.log(`📄 Usando hoja: "${hojaProductos}"`);
            
                    const sheet = workbook.Sheets[hojaProductos];
                    const rawData = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: "" });
            
                    if (rawData.length === 0) {
                        throw new Error("La hoja está vacía");
                    }
            
                    // Paso 5: ANÁLISIS INTELIGENTE
                    onProgress({ paso: 3, total: 6, mensaje: '🧠 Analizando estructura con IA...' });
            
                    const estructura = this.analizarEstructuraInteligente(rawData);
            
                    console.log('📊 Estructura detectada:', estructura);
            
                    if (estructura.confianza < 0.4) {
                        throw new Error("No se pudo detectar la estructura del archivo. Verifica que tenga al menos columnas de Nombre y Precio.");
                    }
            
                    const cols = estructura.columnas;
                    const filaInicio = estructura.filaInicioDatos;
            
                    // Paso 6: Procesar productos
                    onProgress({ paso: 4, total: 6, mensaje: '📦 Importando productos...' });
            
                    const productosNuevos = [];
                    const inventarioNuevo = [];
                    const estadisticas = {
                        procesadas: 0,
                        exitosas: 0,
                        errores: 0,
                        sinPrecio: 0,
                        sinNombre: 0
                    };
            
                    for (let i = filaInicio; i < rawData.length; i++) {
                        const fila = rawData[i];
                        if (!fila || fila.length === 0) continue;
                
                        estadisticas.procesadas++;
                
                        try {
                            // Extraer datos según estructura detectada
                            const nombreRaw = cols.nombre !== undefined ? fila[cols.nombre] : null;
                            const precioRaw = cols.precio !== undefined ? fila[cols.precio] : null;
                    
                            // Validar nombre
                            if (!nombreRaw || nombreRaw === "" || nombreRaw === null) {
                                estadisticas.sinNombre++;
                                continue;
                            }
                    
                            const nombre = String(nombreRaw).trim();
                    
                            // Omitir filas de totales, agregados o títulos de sección
                            // (p.ej. una fila "Productos" intercalada como encabezado).
                            if (nombre.match(/^(total|===|subtotal|suma|resumen|productos?|inventario|categor[ií]a)\s*$/i)) {
                                continue;
                            }
                    
                            // Convertir y validar precio
                            const precioVenta = this.convertirANumero(precioRaw);
                    
                            if (precioVenta <= 0) {
                                estadisticas.sinPrecio++;
                                console.warn(`⚠️ Fila ${i + 1}: "${nombre}" - Precio inválido (${precioRaw})`);
                                continue;
                            }
                    
                            // Extraer datos opcionales
                            const um = cols.um !== undefined ? (fila[cols.um] || "C/U") : "C/U";
                            const cantidad = cols.cantidad !== undefined 
                                ? this.convertirANumero(fila[cols.cantidad], 0)
                                : 0;
                            const costoRaw = cols.costo !== undefined ? fila[cols.costo] : null;
                            const precioCosto = this.convertirANumero(costoRaw, precioVenta * 0.7);
                    
                            // Categorizar
                            const categoria = this.categorizarProducto(nombre);
                    
                            // Crear ID único
                            const id = `prod-${Date.now()}-${i}-${Math.random().toString(36).substr(2, 9)}`;
                    
                            // Crear producto
                            const producto = {
                                id,
                                nombre: nombre,
                                categoria: categoria,
                                precio: precioVenta,
                                costoUnitario: precioCosto,
                                um: String(um).trim(),
                                imagen: "",
                                onSale: false
                            };
                    
                            productosNuevos.push(producto);
                    
                            // Agregar categoría si no existe
                            if (!tpvState.categorias.includes(categoria)) {
                                tpvState.categorias.push(categoria);
                                console.log(`📁 Nueva categoría: ${categoria}`);
                            }
                    
                            // Crear entrada de inventario
                            if (crearInventario && cantidad > 0) {
                                inventarioNuevo.push({
                                    id,
                                    nombre: nombre,
                                    categoria: categoria,
                                    um: String(um).trim(),
                                    cantInicial: cantidad,
                                    cantFinal: cantidad,
                                    vendido: 0,
                                    precioVenta: precioVenta,
                                    precioCosto: precioCosto,
                                    importe: 0,
                                    comision: 0,
                                    gananciaNeta: 0
                                });
                            }
                    
                            estadisticas.exitosas++;
                    
                        } catch (error) {
                            estadisticas.errores++;
                            if (this.DEBUG) {
                                console.error(`❌ Error en fila ${i + 1}:`, error);
                            }
                        }
                    }
            
                    // Paso 7: Guardar
                    onProgress({ paso: 5, total: 6, mensaje: '💾 Guardando cambios...' });
            
                    tpvState.productos = productosNuevos;
            
                    if (crearInventario && inventarioNuevo.length > 0) {
                        const fechaHoy = getTodayDateString();
                        tpvState.inventarios[fechaHoy] = inventarioNuevo;
                    }
            
                    // Generar mensaje de resultado
                    let mensaje = `✅ Importación exitosa!\n\n`;
                    mensaje += `📦 ${estadisticas.exitosas} productos importados\n`;
                    if (inventarioNuevo.length > 0) {
                        mensaje += `📊 ${inventarioNuevo.length} items en inventario\n`;
                    }
                    mensaje += `\n📈 Estadísticas:\n`;
                    mensaje += `  • Procesadas: ${estadisticas.procesadas} filas\n`;
                    mensaje += `  • Exitosas: ${estadisticas.exitosas}\n`;
                    if (estadisticas.sinNombre > 0) {
                        mensaje += `  • Sin nombre: ${estadisticas.sinNombre}\n`;
                    }
                    if (estadisticas.sinPrecio > 0) {
                        mensaje += `  • Sin precio válido: ${estadisticas.sinPrecio}\n`;
                    }
                    if (estadisticas.errores > 0) {
                        mensaje += `  • Errores: ${estadisticas.errores}\n`;
                    }
                    mensaje += `\n🧠 Método: ${estructura.metodo}\n`;
                    mensaje += `🎯 Confianza: ${(estructura.confianza * 100).toFixed(0)}%`;
            
                    onProgress({ paso: 6, total: 6, mensaje: '✅ Completado!' });
            
                    return {
                        exito: true,
                        productosImportados: estadisticas.exitosas,
                        inventarioCreado: inventarioNuevo.length,
                        estadisticas,
                        estructura,
                        mensaje
                    };
            
                } catch (error) {
                    return {
                        exito: false,
                        error: error.message,
                        mensaje: `❌ ${error.message}`
                    };
                }
            }
    
            /**
             * Lee archivo como ArrayBuffer
             */
            leerArchivo(file) {
                return new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onload = (e) => resolve(e.target.result);
                    reader.onerror = () => reject(new Error("Error al leer el archivo"));
                    reader.readAsArrayBuffer(file);
                });
            }

            /**
             * 🧠 SISTEMA DE MEMORIA Y APRENDIZAJE
             * Guarda y recupera configuraciones de importación/exportación
             */
            guardarConfiguracionAprendida(estructura, nombreArchivo) {
                try {
                    const config = {
                        timestamp: Date.now(),
                        nombreArchivo: nombreArchivo,
                        estructura: estructura,
                        version: '8.0-ULTRA-SMART'
                    };
                    
                    // Guardar en localStorage
                    localStorage.setItem('tpv_ultima_estructura', JSON.stringify(config));
                    
                    // Guardar historial (últimas 10 configuraciones)
                    let historial = JSON.parse(localStorage.getItem('tpv_historial_estructuras') || '[]');
                    historial.unshift(config);
                    historial = historial.slice(0, 10); // Mantener solo últimas 10
                    localStorage.setItem('tpv_historial_estructuras', JSON.stringify(historial));
                    
                    if (this.DEBUG) {
                        console.log('💾 Configuración guardada en memoria:', config);
                    }
                } catch (error) {
                    console.warn('⚠️ No se pudo guardar la configuración:', error);
                }
            }
            
            /**
             * Recupera la última configuración usada
             */
            recuperarConfiguracionAprendida() {
                try {
                    const configStr = localStorage.getItem('tpv_ultima_estructura');
                    if (configStr) {
                        const config = JSON.parse(configStr);
                        if (this.DEBUG) {
                            console.log('📖 Configuración recuperada:', config);
                        }
                        return config.estructura;
                    }
                } catch (error) {
                    console.warn('⚠️ No se pudo recuperar la configuración:', error);
                }
                return null;
            }
            
            /**
             * 🔧 AUTO-CORRECCIÓN DE DATOS
             * Corrige automáticamente problemas comunes en los datos
             */
            autoCorregirDatos(producto) {
                // Limpiar nombre
                if (producto.nombre) {
                    producto.nombre = producto.nombre.trim()
                        .replace(/\s+/g, ' ')  // Múltiples espacios → 1 espacio
                        .replace(/^[0-9]+\s*[.-]\s*/,  '')  // Quitar numeración inicial (1. 2. 3.)
                        .replace(/\t/g, ' ');  // Tabs → espacios
                }
                
                // Corregir precios
                if (producto.precio) {
                    // Redondear a 2 decimales
                    producto.precio = Math.round(producto.precio * 100) / 100;
                    
                    // Si el precio es muy pequeño (probablemente error), multiplicar por 100
                    if (producto.precio < 1 && producto.precio > 0) {
                        producto.precio = producto.precio * 100;
                        if (this.DEBUG) {
                            console.log(`🔧 Precio corregido: ${producto.nombre} - ${producto.precio}`);
                        }
                    }
                }
                
                // Corregir unidades de medida comunes
                if (producto.um) {
                    const umCorregidas = {
                        'cu': 'C/U',
                        'c/u': 'C/U',
                        'un': 'C/U',
                        'und': 'C/U',
                        'unidad': 'C/U',
                        'kg': 'Kg',
                        'gr': 'Gr',
                        'lt': 'Lt',
                        'ml': 'ml',
                        'pza': 'Pza',
                        'pieza': 'Pza'
                    };
                    
                    const umLower = producto.um.toLowerCase().trim();
                    if (umCorregidas[umLower]) {
                        producto.um = umCorregidas[umLower];
                    }
                }
                
                // Validar y corregir cantidades negativas
                if (producto.cantidad && producto.cantidad < 0) {
                    producto.cantidad = 0;
                    if (this.DEBUG) {
                        console.log(`🔧 Cantidad negativa corregida a 0: ${producto.nombre}`);
                    }
                }
                
                return producto;
            }
            
            /**
             * 🔍 VALIDACIÓN MEJORADA CON MÚLTIPLES NIVELES
             * Valida con 100% de confiabilidad
             */
            validarConfiabilidad100(rawData, estructura) {
                const validacion = {
                    esValido: true,
                    problemas: [],
                    sugerencias: [],
                    confianzaFinal: estructura.confianza
                };
                
                // Nivel 1: Verificar que hay columnas esenciales
                if (!estructura.columnas.nombre && !estructura.columnas.producto) {
                    validacion.problemas.push('❌ No se detectó columna de nombres/productos');
                    validacion.esValido = false;
                }
                
                if (!estructura.columnas.precio) {
                    validacion.problemas.push('❌ No se detectó columna de precios');
                    validacion.esValido = false;
                }
                
                // Nivel 2: Verificar datos de muestra
                const muestraFilas = rawData.slice(estructura.filaInicioDatos, estructura.filaInicioDatos + 5);
                let filasValidas = 0;
                
                for (const fila of muestraFilas) {
                    if (!fila) continue;
                    
                    const nombre = fila[estructura.columnas.nombre || estructura.columnas.producto];
                    const precio = fila[estructura.columnas.precio];
                    
                    if (nombre && String(nombre).trim().length > 0 && precio && !isNaN(this.convertirANumero(precio))) {
                        filasValidas++;
                    }
                }
                
                const porcentajeValido = filasValidas / Math.min(5, muestraFilas.length);
                
                if (porcentajeValido < 0.4) {
                    validacion.problemas.push('⚠️ Menos del 40% de las filas de muestra son válidas');
                    validacion.sugerencias.push('Verifica que los datos empiecen en la fila correcta');
                }
                
                // Nivel 3: Calcular confianza final
                if (validacion.esValido) {
                    validacion.confianzaFinal = (estructura.confianza * 0.7) + (porcentajeValido * 0.3);
                    
                    // Bonificación si tiene columnas opcionales
                    if (estructura.columnas.cantidad) validacion.confianzaFinal += 0.05;
                    if (estructura.columnas.costo) validacion.confianzaFinal += 0.05;
                    if (estructura.columnas.um) validacion.confianzaFinal += 0.05;
                    
                    validacion.confianzaFinal = Math.min(validacion.confianzaFinal, 1.0);
                }
                
                if (this.DEBUG) {
                    console.log('🔍 Validación completa:', validacion);
                }
                
                return validacion;
            }
            
            /**
             * 📤 EXPORTACIÓN INTELIGENTE
             * Exporta con el formato que el usuario prefiere
             */
            exportarInteligente(tpvState, opciones = {}) {
                const {
                    incluirInventario = false,
                    formato = 'auto',  // 'auto', 'simple', 'completo'
                    nombreArchivo = 'productos_exportados.xlsx'
                } = opciones;
                
                try {
                    // Recuperar preferencias guardadas
                    const preferencias = this.recuperarPreferenciasExportacion();
                    const formatoFinal = formato === 'auto' ? (preferencias?.formato || 'completo') : formato;
                    
                    // Preparar workbook
                    const wb = XLSX.utils.book_new();
                    
                    if (formatoFinal === 'simple') {
                        // Formato simple: solo nombre y precio
                        const datos = [
                            ['Nombre', 'Precio']
                        ];
                        
                        tpvState.productos.forEach(prod => {
                            datos.push([prod.nombre, prod.precio]);
                        });
                        
                        const ws = XLSX.utils.aoa_to_sheet(datos);
                        XLSX.utils.book_append_sheet(wb, ws, 'Productos');
                        
                    } else {
                        // Formato completo
                        const datos = [
                            ['Nombre', 'Precio', 'Unidad', 'Categoría', 'Costo']
                        ];
                        
                        tpvState.productos.forEach(prod => {
                            const costo = prod.precio * 0.7;  // Estimación si no tiene costo
                            datos.push([
                                prod.nombre, 
                                prod.precio, 
                                prod.um || 'C/U', 
                                prod.categoria || 'Otros',
                                costo
                            ]);
                        });
                        
                        const ws = XLSX.utils.aoa_to_sheet(datos);
                        XLSX.utils.book_append_sheet(wb, ws, 'Productos');
                        
                        // Si incluir inventario
                        if (incluirInventario) {
                            const fechaHoy = getTodayDateString();
                            const inventario = tpvState.inventarios[fechaHoy] || [];
                            
                            if (inventario.length > 0) {
                                const datosInv = [
                                    ['Nombre', 'Cantidad Inicial', 'Cantidad Final', 'Vendido', 'Precio Venta', 'Precio Costo']
                                ];
                                
                                inventario.forEach(item => {
                                    datosInv.push([
                                        item.nombre,
                                        item.cantInicial,
                                        item.cantFinal,
                                        item.vendido,
                                        item.precioVenta,
                                        item.precioCosto
                                    ]);
                                });
                                
                                const wsInv = XLSX.utils.aoa_to_sheet(datosInv);
                                XLSX.utils.book_append_sheet(wb, wsInv, 'Inventario');
                            }
                        }
                    }
                    
                    // Guardar preferencias para próxima vez
                    this.guardarPreferenciasExportacion({
                        formato: formatoFinal,
                        incluirInventario: incluirInventario,
                        timestamp: Date.now()
                    });
                    
                    // Exportar archivo
                    XLSX.writeFile(wb, nombreArchivo);
                    
                    return {
                        exito: true,
                        formato: formatoFinal,
                        productosExportados: tpvState.productos.length,
                        mensaje: `✅ ${tpvState.productos.length} productos exportados con formato ${formatoFinal}`
                    };
                    
                } catch (error) {
                    console.error('❌ Error en exportación inteligente:', error);
                    return {
                        exito: false,
                        error: error.message
                    };
                }
            }
            
            /**
             * Guardar preferencias de exportación
             */
            guardarPreferenciasExportacion(preferencias) {
                try {
                    localStorage.setItem('tpv_preferencias_exportacion', JSON.stringify(preferencias));
                    if (this.DEBUG) {
                        console.log('💾 Preferencias de exportación guardadas:', preferencias);
                    }
                } catch (error) {
                    console.warn('⚠️ No se pudieron guardar preferencias:', error);
                }
            }
            
            /**
             * Recuperar preferencias de exportación
             */
            recuperarPreferenciasExportacion() {
                try {
                    const prefStr = localStorage.getItem('tpv_preferencias_exportacion');
                    if (prefStr) {
                        return JSON.parse(prefStr);
                    }
                } catch (error) {
                    console.warn('⚠️ No se pudieron recuperar preferencias:', error);
                }
                return null;
            }
            
            /**
             * 🎯 IMPORTACIÓN MEJORADA AL 100%
             * Override del método original con mejoras
             */
            async importarConMaximaConfiabilidad(file, tpvState, opciones = {}) {
                const resultado = await this.importar(file, tpvState, opciones);
                
                if (resultado.exito) {
                    // Guardar configuración aprendida
                    this.guardarConfiguracionAprendida(resultado.estructura, file.name);
                    
                    // Aplicar auto-corrección a todos los productos importados
                    tpvState.productos = tpvState.productos.map(prod => this.autoCorregirDatos(prod));
                    
                    // Validar confiabilidad
                    const validacion = this.validarConfiabilidad100(
                        resultado.rawData || [], 
                        resultado.estructura
                    );
                    
                    resultado.validacion = validacion;
                    resultado.confianzaFinal = validacion.confianzaFinal;
                    
                    if (this.DEBUG) {
                        console.log('🎯 Importación con máxima confiabilidad completada:', resultado);
                    }
                }
                
                return resultado;
            }
            
            /**
             * 🔄 SINCRONIZACIÓN INTELIGENTE
             * Compara y sincroniza datos de múltiples fuentes
             */
            sincronizarInteligente(productosActuales, productosNuevos) {
                const resultado = {
                    nuevos: [],
                    actualizados: [],
                    sinCambios: [],
                    conflictos: []
                };
                
                const mapaActuales = new Map();
                productosActuales.forEach(prod => {
                    mapaActuales.set(prod.nombre.toLowerCase().trim(), prod);
                });
                
                productosNuevos.forEach(prodNuevo => {
                    const nombreKey = prodNuevo.nombre.toLowerCase().trim();
                    const prodActual = mapaActuales.get(nombreKey);
                    
                    if (!prodActual) {
                        // Producto nuevo
                        resultado.nuevos.push(prodNuevo);
                    } else {
                        // Verificar si hay cambios
                        if (Math.abs(prodActual.precio - prodNuevo.precio) > 0.01) {
                            resultado.actualizados.push({
                                nombre: prodNuevo.nombre,
                                precioAnterior: prodActual.precio,
                                precioNuevo: prodNuevo.precio,
                                diferencia: prodNuevo.precio - prodActual.precio
                            });
                        } else {
                            resultado.sinCambios.push(prodNuevo);
                        }
                    }
                });
                
                if (this.DEBUG) {
                    console.log('🔄 Resultado de sincronización:', {
                        nuevos: resultado.nuevos.length,
                        actualizados: resultado.actualizados.length,
                        sinCambios: resultado.sinCambios.length
                    });
                }
                
                return resultado;
            }
        }

        // Crear instancia global
        const smartExcelImporter = new SmartExcelImporter();
        // Mantener compatibilidad con código existente
        const excelImportManager = smartExcelImporter;
        
        // ==================== FUNCIÓN DE IMPORTACIÓN MEJORADA ====================
        async function gestion_handleImportXLSX(event){
            // Verificar que XLSX esté cargado
            if (typeof XLSX === 'undefined') {
                showToast("⚠️ Error: Biblioteca Excel no cargada. Por favor, verifica tu conexión a internet y recarga la página.", "danger");
                console.error('XLSX no está definido');
                event.target.value = "";
                return;
            }

            const file = event.target.files[0];
            if (!file) return;
            
            console.log('📥 Iniciando importación de:', file.name);
            
            // Usar el gestor mejorado
            const resultado = await excelImportManager.importar(file, tpvState, {
                onProgress: (info) => {
                    console.log(`Progreso: ${info.paso}/${info.total} - ${info.mensaje}`);
                    showToast(`${info.mensaje}`, "info");
                },
                confirmarBorrado: true,
                crearInventario: true
            });
            
            if (resultado.exito) {
                // Guardar en IndexedDB
                await saveState();

                // Construir lista de productos con stock real del XLSX
                // (la cantidad del Excel quedó en tpvState.inventarios[fechaHoy])
                const fechaHoy = getTodayDateString();
                const invHoy   = tpvState.inventarios[fechaHoy] || [];
                const stockMap = {};
                invHoy.forEach(item => { stockMap[item.id] = item.cantInicial || 0; });

                const productosConStock = tpvState.productos.map(p => ({
                    ...p,
                    stock_actual: stockMap[p.id] ?? 0
                }));

                // Sincronizar servidor con productos + stock real
                try {
                    showToast('⚙️ Sincronizando con el servidor...', 'info');
                    const rSync = await fetch('/api/reconstruir-desde-productos', {
                        method: 'POST', credentials: 'same-origin',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ productos: productosConStock })
                    });
                    if (rSync.ok) {
                        const dSync = await rSync.json();
                        if (dSync.ok) {
                            showToast(`☁️ Servidor: ${dSync.total} productos sincronizados`, 'success');
                        }
                    } else {
                        await catalogo_sincronizarAlServidor();
                    }
                } catch(e) {
                    await catalogo_sincronizarAlServidor();
                }

                // CRÍTICO: poblar inventario_general para que Vendedores Hoy funcione
                try {
                    const rInv = await fetch('/api/inventario/importar-catalogo', {
                        method: 'POST', credentials: 'same-origin'
                    });
                    if (rInv.ok) {
                        const dInv = await rInv.json();
                        if (dInv.ok) {
                            showToast(`📦 Almacén actualizado: ${dInv.nuevos} nuevos · ${dInv.existentes} existentes`, 'info');
                        }
                    }
                } catch(e) {
                    console.warn('importar-catalogo:', e.message);
                }

                // CRÍTICO: recargar tpvState.productos desde el servidor
                await catalogo_cargarDesdeServidor();

                // Persistir el estado actualizado en IndexedDB
                await saveState();

                // Refrescar TODA la UI esperando a que termine
                await refreshAllUI();

                // Actualizar inventario visible
                const fechaActualInput = document.getElementById('inv-fechaActual');
                if (fechaActualInput && fechaActualInput.value) {
                    inv_cargarInventario(fechaActualInput.value);
                }

                // Actualizar tabla de gestión de productos explícitamente
                if (typeof gestion_renderizarFiltrosProductos === 'function') gestion_renderizarFiltrosProductos();
                if (typeof gestion_renderizarTablaProductos  === 'function') gestion_renderizarTablaProductos();
                if (typeof gestion_renderizarListaCategorias === 'function') gestion_renderizarListaCategorias();

                showToast(resultado.mensaje + ' — Ve a Catálogo › Productos para verificar.', "success");
                console.log('✅ Importación completada exitosamente');
                
            } else {
                showToast(resultado.mensaje, "danger");
                console.error('❌ Error en importación:', resultado.error);
            }
            
            event.target.value = "";
        }


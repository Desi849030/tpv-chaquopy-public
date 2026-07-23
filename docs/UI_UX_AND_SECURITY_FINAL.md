# Revisión final UI/UX, responsive y seguridad

## Objetivo

Entregar una interfaz utilizable en teléfono, tablet, navegador y WebView, con controles accesibles y estados claros online/offline, sin debilitar la seguridad del backend.

## Sistema visual

- Tokens de color, superficie, borde, radio, sombra y foco.
- Contraste reforzado.
- Botones con área mínima de 44 px.
- Estados hover, active, disabled y loading.
- Tarjetas y modales coherentes.
- Tablas desplazables con encabezado sticky.
- navegación horizontal en pantallas pequeñas.

## Responsive

### Móvil

- padding reducido;
- formularios de ancho completo;
- grupos de botones en dos columnas o una columna bajo 420 px;
- tablas dentro de contenedor horizontal;
- modales con márgenes seguros;
- soporte de safe-area inferior/superior.

### Tablet/escritorio

- ancho máximo de 1500 px;
- modales XL;
- dashboard preparado para grid de 12 columnas;
- mayor densidad sin reducir objetivos táctiles.

## Accesibilidad

- `focus-visible` de alto contraste;
- `aria-live` para conectividad;
- etiquetas automáticas para controles cuando existe título/placeholder;
- `alt` seguro para imágenes decorativas;
- soporte `prefers-reduced-motion`;
- soporte `prefers-contrast`;
- navegación horizontal de tablas con teclado;
- estilos de impresión.

Debe complementarse con prueba manual TalkBack; la automatización no sustituye usuarios reales.

## Dinamismo

- banner offline;
- aviso cuando Flask local no responde;
- aviso de reconexión;
- operaciones locales disponibles sin WAN;
- enhancement progresivo mediante MutationObserver;
- API `window.TPV_UX` para anunciar mensajes y refrescar conectividad.

## Debug sin ruido

- buffer limitado a 200 entradas;
- mensajes idénticos agrupados por firma;
- ventana de 120 segundos para errores de conectividad/Supabase;
- ventana de 10 segundos para otros mensajes;
- en offline se registra un único estado consolidado;
- monitor Supabase se pausa sin Internet;
- refresco de red baja de 6 a 15 segundos en offline;
- al limpiar el panel también se limpia el estado de deduplicación;
- cerrar el panel detiene timers asociados.

Esto conserva estadísticas de peticiones sin desbordar la interfaz con el mismo error.

## Scroll de ventanas y modales

- `final-polish.css` se carga después de todos los estilos heredados;
- `.modal` acepta desplazamiento vertical y gestos táctiles;
- `.modal-content` se limita a la altura visible del dispositivo;
- `.modal-body` es el área desplazable con momentum en WebView;
- header y footer permanecen accesibles;
- modales personalizados también usan `pan-y`;
- al cerrar se eliminan backdrops huérfanos y se restaura el scroll del body;
- inputs usan 16 px en móvil para evitar zoom involuntario.

## Explicaciones para público no técnico

La IA ofrece un modo de lenguaje sencillo con cuatro partes: qué es, analogía, evidencia y opción de detalle técnico. Consulta `docs/NON_TECHNICAL_JURY_GUIDE.md`.

## Seguridad backend

- `X-Content-Type-Options: nosniff`;
- `X-Frame-Options: DENY`;
- `Referrer-Policy: no-referrer`;
- Permissions-Policy restrictiva;
- API con `Cache-Control: no-store`;
- HSTS solo cuando HTTPS está activo;
- cookie HttpOnly/SameSite;
- límite de request de 16 MB;
- errores internos sin detalles fuera de testing.

No se aplica CSP estricta todavía porque el frontend heredado contiene scripts y estilos inline. Una CSP fuerte requiere eliminar inline progresivamente para no romper la APK.

## Criterios manuales antes de entregar

- [ ] Login y onboarding en pantalla pequeña.
- [ ] Todos los botones principales tienen texto o nombre accesible.
- [ ] TalkBack recorre login, caja y diagnóstico.
- [ ] Fuente al 150% no oculta acciones críticas.
- [ ] Orientación vertical y horizontal.
- [ ] Modo avión muestra banner y permite venta local.
- [ ] Reconexión muestra aviso.
- [ ] Tablas se desplazan sin romper el layout.
- [ ] Acción destructiva solicita confirmación.
- [ ] Ningún error muestra stack trace o secreto.

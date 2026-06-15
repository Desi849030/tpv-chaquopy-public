
// Organizador Dinámico de Menú (10/10 UX)
document.addEventListener('DOMContentLoaded', () => {
    const menuContainer = document.querySelector('#sidebar-menu'); // Ajusta a tu ID
    if(!menuContainer) return;
    
    // Agrupa elementos por data-category
    const items = Array.from(menuContainer.querySelectorAll('.nav-item'));
    const groups = {};
    items.forEach(i => {
        const cat = i.dataset.category || 'General';
        if(!groups[cat]) groups[cat] = [];
        groups[cat].push(i);
    });
    
    // Renderiza grupos
    menuContainer.innerHTML = '';
    Object.keys(groups).sort().forEach(cat => {
        const header = document.createElement('h6');
        header.className = 'sidebar-heading px-3 mt-4 mb-1 text-muted';
        header.innerText = cat.toUpperCase();
        menuContainer.appendChild(header);
        groups[cat].forEach(i => menuContainer.appendChild(i));
    });
});

// Organizador Dinámico de Menú (10/10 UX)
document.addEventListener('DOMContentLoaded', () => {
    const menuContainer = document.querySelector('#sidebar-menu'); // Ajusta a tu ID
    if(!menuContainer) return;
    
    // Agrupa elementos por data-category
    const items = Array.from(menuContainer.querySelectorAll('.nav-item'));
    const groups = {};
    items.forEach(i => {
        const cat = i.dataset.category || 'General';
        if(!groups[cat]) groups[cat] = [];
        groups[cat].push(i);
    });
    
    // Renderiza grupos
    menuContainer.innerHTML = '';
    Object.keys(groups).sort().forEach(cat => {
        const header = document.createElement('h6');
        header.className = 'sidebar-heading px-3 mt-4 mb-1 text-muted';
        header.innerText = cat.toUpperCase();
        menuContainer.appendChild(header);
        groups[cat].forEach(i => menuContainer.appendChild(i));
    });
});

// Organizador Dinámico de Menú (10/10 UX)
document.addEventListener('DOMContentLoaded', () => {
    const menuContainer = document.querySelector('#sidebar-menu'); // Ajusta a tu ID
    if(!menuContainer) return;
    
    // Agrupa elementos por data-category
    const items = Array.from(menuContainer.querySelectorAll('.nav-item'));
    const groups = {};
    items.forEach(i => {
        const cat = i.dataset.category || 'General';
        if(!groups[cat]) groups[cat] = [];
        groups[cat].push(i);
    });
    
    // Renderiza grupos
    menuContainer.innerHTML = '';
    Object.keys(groups).sort().forEach(cat => {
        const header = document.createElement('h6');
        header.className = 'sidebar-heading px-3 mt-4 mb-1 text-muted';
        header.innerText = cat.toUpperCase();
        menuContainer.appendChild(header);
        groups[cat].forEach(i => menuContainer.appendChild(i));
    });
});

/**
 * Cliente Manager
 * Maneja la funcionalidad de la interfaz de clientes incluyendo:
 * - Cambio entre vistas (Lista/Kanban)
 * - Persistencia de la preferencia de vista
 * - Confirmación y manejo de eliminación
 * - Inicialización de iconos
 */

document.addEventListener('DOMContentLoaded', function() {
    // Inicialización de componentes
    initializeIcons();
    initializeViewToggle();
    initializeTooltips();
    initializeTableSort();
});

/**
 * Inicializa los iconos de Lucide
 */
function initializeIcons() {
    lucide.createIcons();
}

/**
 * Inicializa el toggle entre vistas y restaura la preferencia guardada
 */
function initializeViewToggle() {
    // Elementos DOM
    const listViewBtn = document.getElementById('listViewBtn');
    const kanbanViewBtn = document.getElementById('kanbanViewBtn');
    const listView = document.getElementById('listView');
    const kanbanView = document.getElementById('kanbanView');

    if (!listViewBtn || !kanbanViewBtn || !listView || !kanbanView) {
        console.error('Elementos de vista no encontrados');
        return;
    }

    // Manejadores de eventos para los botones de vista
    listViewBtn.addEventListener('click', () => {
        switchView('list', listViewBtn, kanbanViewBtn, listView, kanbanView);
    });

    kanbanViewBtn.addEventListener('click', () => {
        switchView('kanban', kanbanViewBtn, listViewBtn, kanbanView, listView);
    });

    // Restaurar vista preferida
    const savedView = localStorage.getItem('clientViewPreference') || 'list';
    if (savedView === 'kanban') {
        kanbanViewBtn.click();
    }
}

/**
 * Cambia entre las vistas de lista y kanban
 */
function switchView(viewType, activeBtn, inactiveBtn, showView, hideView) {
    // Actualizar clases de botones
    activeBtn.classList.add('active');
    inactiveBtn.classList.remove('active');

    // Animar transición de vistas
    hideView.classList.add('hidden');
    showView.classList.remove('hidden');

    // Guardar preferencia
    localStorage.setItem('clientViewPreference', viewType);
}

/**
 * Inicializa tooltips personalizados
 */
function initializeTooltips() {
    const buttons = document.querySelectorAll('[title]');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', showTooltip);
        button.addEventListener('mouseleave', hideTooltip);
    });
}

/**
 * Muestra el tooltip
 */
function showTooltip(event) {
    const title = event.target.getAttribute('title');
    if (!title) return;

    // Crear elemento tooltip
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = title;
    tooltip.style.cssText = `
        position: absolute;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        z-index: 1000;
        pointer-events: none;
    `;

    // Posicionar tooltip
    document.body.appendChild(tooltip);
    const rect = event.target.getBoundingClientRect();
    tooltip.style.top = `${rect.bottom + 8}px`;
    tooltip.style.left = `${rect.left + (rect.width - tooltip.offsetWidth) / 2}px`;

    // Guardar referencia
    event.target.tooltip = tooltip;
    event.target.removeAttribute('title');
}

/**
 * Oculta el tooltip
 */
function hideTooltip(event) {
    if (event.target.tooltip) {
        event.target.setAttribute('title', event.target.tooltip.textContent);
        event.target.tooltip.remove();
        event.target.tooltip = null;
    }
}

/**
 * Inicializa el ordenamiento de la tabla
 */
function initializeTableSort() {
    const table = document.querySelector('.client-table');
    if (!table) return;

    const headers = table.querySelectorAll('th');
    headers.forEach((header, index) => {
        if (index === 4) return; // Ignorar columna de acciones

        header.addEventListener('click', () => {
            sortTable(table, index);
        });
        header.style.cursor = 'pointer';
    });
}

/**
 * Ordena la tabla por columna
 */
function sortTable(table, column) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const isAsc = table.querySelector('th').classList.contains('sort-asc');

    // Ordenar filas
    rows.sort((a, b) => {
        const aVal = a.cells[column].textContent.trim();
        const bVal = b.cells[column].textContent.trim();
        
        if (column === 0) { // ID column - numeric sort
            return isAsc 
                ? parseInt(aVal) - parseInt(bVal)
                : parseInt(bVal) - parseInt(aVal);
        }
        
        return isAsc
            ? bVal.localeCompare(aVal)
            : aVal.localeCompare(bVal);
    });

    // Actualizar indicador de ordenamiento
    table.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    table.querySelector(`th:nth-child(${column + 1})`).classList.toggle(isAsc ? 'sort-desc' : 'sort-asc');

    // Redibujar tabla
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Confirma y maneja la eliminación de un cliente
 */
async function confirmDelete(type, id) {
    try {
        const confirmed = await showConfirmDialog(
            '¿Estás seguro de que deseas eliminar este cliente?',
            'Esta acción no se puede deshacer.'
        );

        if (!confirmed) return;

        // Mostrar indicador de carga
        const loadingToast = showToast('Eliminando cliente...', 'loading');

        // Realizar petición DELETE
        const response = await fetch(`/clients/${id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken() // Si usas CSRF
            }
        });

        if (!response.ok) {
            throw new Error('Error al eliminar el cliente');
        }

        // Eliminar elemento del DOM con animación
        const element = document.querySelector(`[data-client-id="${id}"]`);
        if (element) {
            element.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => element.remove(), 300);
        }

        // Mostrar mensaje de éxito
        hideToast(loadingToast);
        showToast('Cliente eliminado correctamente', 'success');

    } catch (error) {
        console.error('Error:', error);
        showToast('Error al eliminar el cliente', 'error');
    }
}

/**
 * Muestra un diálogo de confirmación personalizado
 */
function showConfirmDialog(title, message) {
    return new Promise((resolve) => {
        const dialog = document.createElement('div');
        dialog.className = 'confirm-dialog';
        dialog.innerHTML = `
            <div class="confirm-dialog-content">
                <h3>${title}</h3>
                <p>${message}</p>
                <div class="confirm-dialog-actions">
                    <button class="btn-secondary">Cancelar</button>
                    <button class="btn-danger">Eliminar</button>
                </div>
            </div>
        `;

        // Estilos del diálogo
        dialog.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        `;

        // Manejadores de eventos
        dialog.querySelector('.btn-secondary').onclick = () => {
            dialog.remove();
            resolve(false);
        };

        dialog.querySelector('.btn-danger').onclick = () => {
            dialog.remove();
            resolve(true);
        };

        document.body.appendChild(dialog);
    });
}

/**
 * Muestra un toast de notificación
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    // Estilos del toast
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 12px 24px;
        background: white;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        animation: slideIn 0.3s ease-out;
    `;

    document.body.appendChild(toast);

    // Auto-eliminar después de 3 segundos
    if (type !== 'loading') {
        setTimeout(() => hideToast(toast), 3000);
    }

    return toast;
}

/**
 * Oculta un toast
 */
function hideToast(toast) {
    if (!toast) return;
    toast.style.animation = 'slideOut 0.3s ease-out';
    setTimeout(() => toast.remove(), 300);
}

/**
 * Obtiene el token CSRF de las cookies
 */
function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
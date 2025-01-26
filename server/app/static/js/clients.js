document.addEventListener('DOMContentLoaded', function() {
    initializeCounters();
    setupSearchAndFilters();
    setupDragAndDrop();
});

// Inicialización de contadores
function initializeCounters() {
    updateClientCounts();
    setupAutoRefresh();
}

function updateClientCounts() {
    const activeCount = document.querySelectorAll('#activeClients .client-card').length;
    const inactiveCount = document.querySelectorAll('#inactiveClients .client-card').length;
    
    document.getElementById('activeCount').textContent = activeCount;
    document.getElementById('inactiveCount').textContent = inactiveCount;
}

// Configuración de búsqueda y filtros
function setupSearchAndFilters() {
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    const filterBtn = document.querySelector('.filter-btn');
    const filterDropdown = document.querySelector('.filter-dropdown');

    // Búsqueda en tiempo real
    searchInput.addEventListener('input', debounce(filterClients, 300));
    statusFilter.addEventListener('change', filterClients);

    // Toggle de filtros
    filterBtn.addEventListener('click', () => {
        filterDropdown.style.display = filterDropdown.style.display === 'block' ? 'none' : 'block';
    });

    // Cerrar dropdown al hacer click fuera
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.filter-container')) {
            filterDropdown.style.display = 'none';
        }
    });
}

// Función de filtrado
function filterClients() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;
    const cards = document.querySelectorAll('.client-card');

    cards.forEach(card => {
        const name = card.querySelector('.client-name').textContent.toLowerCase();
        const token = card.querySelector('.token').textContent.toLowerCase();
        const isActive = card.closest('#activeClients') !== null;
        
        const matchesSearch = name.includes(searchTerm) || token.includes(searchTerm);
        const matchesStatus = statusFilter === 'all' || 
            (statusFilter === 'active' && isActive) || 
            (statusFilter === 'inactive' && !isActive);

        if (matchesSearch && matchesStatus) {
            card.style.display = 'block';
            card.style.animation = 'slideIn 0.3s ease';
        } else {
            card.style.display = 'none';
        }
    });

    updateClientCounts();
}

// Configuración de Drag and Drop
function setupDragAndDrop() {
    const cards = document.querySelectorAll('.client-card');
    const dropZones = document.querySelectorAll('.client-cards');

    cards.forEach(card => {
        card.setAttribute('draggable', true);
        card.addEventListener('dragstart', handleDragStart);
        card.addEventListener('dragend', handleDragEnd);
    });

    dropZones.forEach(zone => {
        zone.addEventListener('dragover', handleDragOver);
        zone.addEventListener('drop', handleDrop);
    });
}

function handleDragStart(e) {
    e.target.classList.add('dragging');
    e.dataTransfer.setData('text/plain', e.target.dataset.id);
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
}

function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('drag-over');
}

async function handleDrop(e) {
    e.preventDefault();
    const clientId = e.dataTransfer.getData('text/plain');
    const newStatus = e.currentTarget.id === 'activeClients';
    
    try {
        const response = await updateClientStatus(clientId, newStatus);
        if (response.ok) {
            const card = document.querySelector(`[data-id="${clientId}"]`);
            e.currentTarget.appendChild(card);
            updateClientCounts();
            showNotification('Estado actualizado correctamente', 'success');
        }
    } catch (error) {
        showNotification('Error al actualizar el estado', 'error');
    }
}

// Funciones de utilidad
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

// Funciones AJAX
async function updateClientStatus(clientId, isActive) {
    return await fetch(`/api/clients/${clientId}/status`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_active: isActive })
    });
}

// Gestión de modales
let clientToDelete = null;

function confirmDelete(type, id) {
    clientToDelete = id;
    const modal = document.getElementById('deleteModal');
    modal.style.display = 'flex';
}

function closeModal() {
    const modal = document.getElementById('deleteModal');
    modal.style.display = 'none';
    clientToDelete = null;
}

async function deleteClient() {
    if (!clientToDelete) return;
    
    try {
        const response = await fetch(`/api/clients/${clientToDelete}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            const card = document.querySelector(`[data-id="${clientToDelete}"]`);
            card.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                card.remove();
                updateClientCounts();
            }, 300);
            showNotification('Cliente eliminado correctamente', 'success');
        }
    } catch (error) {
        showNotification('Error al eliminar el cliente', 'error');
    }
    
    closeModal();
}
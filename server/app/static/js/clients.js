document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupViewSwitcher();
    setupSearch();
    setupFilters();
    setupSorting();
    updateCounters();
    initializeDragAndDrop();
}

// View Switching
function setupViewSwitcher() {
    const viewButtons = document.querySelectorAll('.view-btn');
    const kanbanView = document.getElementById('kanbanView');
    const listView = document.getElementById('listView');

    viewButtons.forEach(button => {
        button.addEventListener('click', () => {
            viewButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            if (button.dataset.view === 'kanban') {
                kanbanView.style.display = 'grid';
                listView.style.display = 'none';
            } else {
                kanbanView.style.display = 'none';
                listView.style.display = 'block';
            }

            localStorage.setItem('preferredView', button.dataset.view);
        });
    });

    // Load preferred view
    const preferredView = localStorage.getItem('preferredView') || 'kanban';
    document.querySelector(`[data-view="${preferredView}"]`).click();
}

// Search Functionality
function setupSearch() {
    const searchInput = document.getElementById('searchClients');
    searchInput.addEventListener('input', debounce(() => {
        const searchTerm = searchInput.value.toLowerCase();
        filterClients(searchTerm);
    }, 300));
}

function filterClients(searchTerm) {
    const cards = document.querySelectorAll('.client-card, .clients-table tbody tr');
    
    cards.forEach(card => {
        const name = card.querySelector('.client-name').textContent.toLowerCase();
        const id = card.getAttribute('data-id');
        const token = card.querySelector('.info-row span, td:nth-child(3)').textContent.toLowerCase();
        
        const matches = name.includes(searchTerm) || 
                       id.includes(searchTerm) || 
                       token.includes(searchTerm);
        
        card.style.display = matches ? '' : 'none';
    });

    updateCounters();
}

// Filter Panel
function setupFilters() {
    const filterBtn = document.querySelector('.filter-btn');
    const filterPanel = document.getElementById('filterPanel');

    filterBtn.addEventListener('click', () => {
        filterPanel.style.display = filterPanel.style.display === 'none' ? 'block' : 'none';
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.filter-btn') && !e.target.closest('.filter-panel')) {
            filterPanel.style.display = 'none';
        }
    });

    const statusFilter = document.getElementById('statusFilter');
    statusFilter.addEventListener('change', applyFilters);
}

function applyFilters() {
    const status = document.getElementById('statusFilter').value;
    const cards = document.querySelectorAll('.client-card, .clients-table tbody tr');

    cards.forEach(card => {
        const isActive = card.querySelector('.status-badge').classList.contains('active');
        const statusMatch = status === 'all' || 
                          (status === 'active' && isActive) || 
                          (status === 'inactive' && !isActive);
        
        if (statusMatch) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });

    updateCounters();
}

// Sorting
function setupSorting() {
    const sortFilter = document.getElementById('sortFilter');
    sortFilter.addEventListener('change', () => {
        const sortBy = sortFilter.value;
        sortClients(sortBy);
    });
}

function sortClients(sortBy) {
    const containers = [
        document.getElementById('activeCards'),
        document.getElementById('inactiveCards'),
        document.querySelector('.clients-table tbody')
    ];

    containers.forEach(container => {
        if (!container) return;

        const items = Array.from(container.children);
        items.sort((a, b) => {
            let valA, valB;
            
            switch(sortBy) {
                case 'name':
                    valA = a.querySelector('.client-name').textContent;
                    valB = b.querySelector('.client-name').textContent;
                    return valA.localeCompare(valB);
                case 'id':
                    valA = parseInt(a.getAttribute('data-id'));
                    valB = parseInt(b.getAttribute('data-id'));
                    return valA - valB;
                default:
                    return 0;
            }
        });

        items.forEach(item => container.appendChild(item));
    });
}

// Drag and Drop
function initializeDragAndDrop() {
    const cards = document.querySelectorAll('.client-card');
    const dropZones = document.querySelectorAll('.card-container');

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
    e.currentTarget.classList.remove('drag-over');
    
    const clientId = e.dataTransfer.getData('text/plain');
    const newStatus = e.currentTarget.id === 'activeCards';
    
    try {
        const response = await updateClientStatus(clientId, newStatus);
        if (response.ok) {
            const card = document.querySelector(`[data-id="${clientId}"]`);
            e.currentTarget.appendChild(card);
            updateStatusBadge(card, newStatus);
            updateCounters();
            showNotification('Estado actualizado correctamente', 'success');
        }
    } catch (error) {
        showNotification('Error al actualizar el estado', 'error');
    }
}

// Utility Functions
function updateCounters() {
    const activeCount = document.querySelectorAll('#activeCards .client-card:not([style*="none"])').length;
    const inactiveCount = document.querySelectorAll('#inactiveCards .client-card:not([style*="none"])').length;
    
    document.getElementById('activeCounter').textContent = activeCount;
    document.getElementById('inactiveCounter').textContent = inactiveCount;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

// Modal Functions
let clientIdToDelete = null;

function showDeleteModal(clientId) {
    clientIdToDelete = clientId;
    const modal = document.getElementById('deleteModal');
    modal.style.display = 'flex';
}

function closeModal() {
    const modal = document.getElementById('deleteModal');
    modal.style.display = 'none';
    clientIdToDelete = null;
}

async function deleteClient() {
    if (!clientIdToDelete) return;
    
    try {
        const response = await fetch(`/api/clients/${clientIdToDelete}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            const card = document.querySelector(`[data-id="${clientIdToDelete}"]`);
            card.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                card.remove();
                updateCounters();
            }, 300);
            showNotification('Cliente eliminado correctamente', 'success');
        }
    } catch (error) {
        showNotification('Error al eliminar el cliente', 'error');
    }
    
    closeModal();
}

// API Functions
async function updateClientStatus(clientId, isActive) {
    return await fetch(`/api/clients/${clientId}/status`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_active: isActive })
    });
}

function updateStatusBadge(card, isActive) {
    const badge = card.querySelector('.status-badge');
    const icon = badge.querySelector('i');
    
    badge.className = `status-badge ${isActive ? 'active' : 'inactive'}`;
    icon.className = `fas fa-${isActive ? 'check' : 'times'}-circle`;
    badge.textContent = isActive ? 'Activo' : 'Inactivo';
}
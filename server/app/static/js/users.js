// static/js/users.js

// Variables globales
let currentUserIdToDelete = null;

// Funciones de utilidad para notificaciones
function showNotification(message, type = 'success') {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    notification.className = `p-4 rounded-lg shadow-lg ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    } text-white flex items-center justify-between`;
    
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} mr-2"></i>
            <span>${message}</span>
        </div>
        <button onclick="this.parentElement.remove()" class="ml-4">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(notification);
    setTimeout(() => notification.remove(), 5000);
}

// Funciones para el manejo de modales
function openModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

// Funciones para el manejo de usuarios
function confirmDelete(userId) {
    currentUserIdToDelete = userId;
    openModal('deleteConfirmModal');
}

async function executeDelete() {
    if (!currentUserIdToDelete) return;
    
    try {
        const response = await fetch(`/users/${currentUserIdToDelete}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Usuario desactivado exitosamente');
            // Recargar la página después de un breve delay
            setTimeout(() => window.location.reload(), 1000);
        } else {
            throw new Error(data.error || 'Error al desactivar usuario');
        }
    } catch (error) {
        showNotification(error.message, 'error');
    } finally {
        closeModal('deleteConfirmModal');
        currentUserIdToDelete = null;
    }
}

// Funciones para filtrado y búsqueda
function setupFilters() {
    const searchInput = document.getElementById('searchInput');
    const roleFilter = document.getElementById('roleFilter');
    const statusFilter = document.getElementById('statusFilter');
    
    const filterUsers = () => {
        const searchTerm = searchInput.value.toLowerCase();
        const roleValue = roleFilter.value;
        const statusValue = statusFilter.value;
        
        const rows = document.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const userData = {
                name: row.querySelector('.font-medium').textContent.toLowerCase(),
                email: row.querySelector('.text-gray-500').textContent.toLowerCase(),
                username: row.querySelector('.text-gray-400').textContent.toLowerCase(),
                role: row.querySelector('[data-role]')?.dataset.role,
                status: row.querySelector('[data-status]')?.dataset.status
            };
            
            const matchesSearch = searchTerm === '' || 
                userData.name.includes(searchTerm) || 
                userData.email.includes(searchTerm) || 
                userData.username.includes(searchTerm);
                
            const matchesRole = roleValue === '' || userData.role === roleValue;
            const matchesStatus = statusValue === '' || userData.status === statusValue;
            
            row.classList.toggle('hidden', !(matchesSearch && matchesRole && matchesStatus));
        });
    };
    
    // Agregar event listeners
    searchInput.addEventListener('input', filterUsers);
    roleFilter.addEventListener('change', filterUsers);
    statusFilter.addEventListener('change', filterUsers);
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', () => {
    setupFilters();
});
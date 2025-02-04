// Manejo de búsqueda
const searchInput = document.getElementById('searchInput');
const oidsTableBody = document.getElementById('oidsTableBody');

searchInput.addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    const rows = oidsTableBody.getElementsByTagName('tr');

    for (let row of rows) {
        const brand = row.querySelector('td:nth-child(1)').textContent.toLowerCase();
        const family = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        const description = row.querySelector('td:nth-child(3)').textContent.toLowerCase();

        if (brand.includes(searchTerm) || 
            family.includes(searchTerm) || 
            description.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    }
});

// Función para mostrar detalles de OID
async function showOIDDetails(oidId) {
    const modal = document.getElementById('oidDetailsModal');
    const content = document.getElementById('oidDetailsContent');
    modal.classList.remove('hidden');
    
    try {
        const response = await fetch(`/api/v1/printer-oids/${oidId}`);
        if (!response.ok) throw new Error('Error al cargar los detalles');
        
        const data = await response.json();
        content.innerHTML = formatOIDDetails(data);
    } catch (error) {
        showNotification(error.message, 'error');
        content.innerHTML = `
            <div class="flex justify-center items-center text-red-500">
                <i class="fas fa-exclamation-circle mr-2"></i>
                <span>Error al cargar los detalles: ${error.message}</span>
            </div>`;
    }
}

// Función para formatear los detalles de OID
function formatOIDDetails(data) {
    return `
        <div class="space-y-6">
            <!-- Información básica -->
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <h4 class="text-sm font-medium text-gray-500">Marca</h4>
                    <p class="mt-1 text-sm text-gray-900">${data.brand}</p>
                </div>
                <div>
                    <h4 class="text-sm font-medium text-gray-500">Familia de Modelo</h4>
                    <p class="mt-1 text-sm text-gray-900">${data.model_family}</p>
                </div>
            </div>

            <!-- Sección de OIDs -->
            <div class="mt-6">
                <h4 class="text-lg font-medium text-gray-900 mb-4">Configuración de OIDs</h4>
                
                <!-- Contadores -->
                <div class="mb-6">
                    <h5 class="text-sm font-medium text-gray-500 mb-3">Contadores</h5>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="space-y-2">
                            <p class="text-xs text-gray-500">Total de Páginas</p>
                            <code class="block text-sm bg-gray-100 px-2 py-1 rounded">${data.oid_total_pages || '-'}</code>
                        </div>
                        <div class="space-y-2">
                            <p class="text-xs text-gray-500">Páginas Color</p>
                            <code class="block text-sm bg-gray-100 px-2 py-1 rounded">${data.oid_total_color_pages || '-'}</code>
                        </div>
                    </div>
                </div>

                <!-- Toners -->
                <div class="mb-6">
                    <h5 class="text-sm font-medium text-gray-500 mb-3">Toners</h5>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="space-y-2">
                            <p class="text-xs text-gray-500">Negro - Nivel</p>
                            <code class="block text-sm bg-gray-100 px-2 py-1 rounded">${data.oid_black_toner_level || '-'}</code>
                        </div>
                        <div class="space-y-2">
                            <p class="text-xs text-gray-500">Cyan - Nivel</p>
                            <code class="block text-sm bg-gray-100 px-2 py-1 rounded">${data.oid_cyan_toner_level || '-'}</code>
                        </div>
                        <div class="space-y-2">
                            <p class="text-xs text-gray-500">Magenta - Nivel</p>
                            <code class="block text-sm bg-gray-100 px-2 py-1 rounded">${data.oid_magenta_toner_level || '-'}</code>
                        </div>
                        <div class="space-y-2">
                            <p class="text-xs text-gray-500">Amarillo - Nivel</p>
                            <code class="block text-sm bg-gray-100 px-2 py-1 rounded">${data.oid_yellow_toner_level || '-'}</code>
                        </div>
                    </div>
                </div>

                <!-- Estado -->
                <div class="mb-6">
                    <h5 class="text-sm font-medium text-gray-500 mb-3">Estado y Sistema</h5>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="space-y-2">
                            <p class="text-xs text-gray-500">Estado de Impresora</p>
                            <code class="block text-sm bg-gray-100 px-2 py-1 rounded">${data.oid_printer_status || '-'}</code>
                        </div>
                        <div class="space-y-2">
                            <p class="text-xs text-gray-500">Mensajes de Error</p>
                            <code class="block text-sm bg-gray-100 px-2 py-1 rounded">${data.oid_error_messages || '-'}</code>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Función para eliminar OID
async function deleteOID(oidId) {
    if (!confirm('¿Estás seguro de que deseas eliminar esta configuración de OIDs?')) {
        return;
    }

    try {
        const response = await fetch(`/api/v1/printer-oids/${oidId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al eliminar la configuración');
        }

        showNotification('Configuración eliminada exitosamente', 'success');
        setTimeout(() => window.location.reload(), 1000);
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

// Función para mostrar notificaciones
function showNotification(message, type = 'success') {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    
    notification.className = `p-4 rounded-lg shadow-lg text-white ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    }`;
    
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} mr-2"></i>
            <span>${message}</span>
        </div>
    `;

    container.appendChild(notification);

    // Remover la notificación después de 3 segundos
    setTimeout(() => {
        notification.classList.add('opacity-0', 'transition-opacity');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Función para cerrar modal
function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

// Inicialización cuando se carga el documento
document.addEventListener('DOMContentLoaded', function() {
    // Aquí puedes agregar cualquier inicialización adicional necesaria
});
// static/js/tunnels.js

let reconnectAttempts = 0;

// Funciones para gestión de túneles
async function showTunnelInfo(tunnelId) {
    try {
        document.getElementById('tunnelInfoContent').innerHTML = `
            <div class="flex justify-center items-center">
                <i class="fas fa-circle-notch fa-spin text-blue-500 text-2xl mr-3"></i>
                <p class="text-gray-500 text-lg">Cargando información...</p>
            </div>
        `;
        showModal('tunnelInfoModal');

        const response = await fetch(`/api/v1/tunnels/${encodeURIComponent(tunnelId)}`);
        if (!response.ok) throw new Error(`Error: ${response.statusText}`);
        
        const tunnelInfo = await response.json();
        
        const content = `
            <div class="space-y-6">
                <!-- Información Básica -->
                <div>
                    <h4 class="text-sm font-medium text-gray-500 mb-4">Información Básica</h4>
                    <div class="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg">
                        <div>
                            <div class="text-xs text-gray-500">ID del Túnel</div>
                            <div class="font-mono text-sm mt-1">${tunnelInfo.tunnel_id}</div>
                        </div>
                        <div>
                            <div class="text-xs text-gray-500">Estado</div>
                            <div class="mt-1">
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                                    ${getStatusClasses(tunnelInfo.status)}">
                                    <i class="fas fa-${getStatusIcon(tunnelInfo.status)} mr-1"></i>
                                    ${tunnelInfo.status}
                                </span>
                            </div>
                        </div>
                        <div>
                            <div class="text-xs text-gray-500">Creado</div>
                            <div class="text-sm mt-1">${formatDate(tunnelInfo.created_at)}</div>
                        </div>
                        <div>
                            <div class="text-xs text-gray-500">Última Actualización</div>
                            <div class="text-sm mt-1">${formatDate(tunnelInfo.updated_at)}</div>
                        </div>
                    </div>
                </div>

                <!-- Configuración de Conexión -->
                <div>
                    <h4 class="text-sm font-medium text-gray-500 mb-4">Configuración de Conexión</h4>
                    <div class="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg">
                        <div>
                            <div class="text-xs text-gray-500">Host Remoto</div>
                            <div class="text-sm mt-1">${tunnelInfo.remote_host}</div>
                        </div>
                        <div>
                            <div class="text-xs text-gray-500">Puerto Remoto</div>
                            <div class="text-sm mt-1">${tunnelInfo.remote_port}</div>
                        </div>
                        <div>
                            <div class="text-xs text-gray-500">Puerto Local</div>
                            <div class="text-sm mt-1">${tunnelInfo.local_port}</div>
                        </div>
                    </div>
                </div>

                <!-- Información del Agente -->
                <div>
                    <h4 class="text-sm font-medium text-gray-500 mb-4">Información del Agente</h4>
                    <div class="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg">
                        <div>
                            <div class="text-xs text-gray-500">Hostname</div>
                            <div class="text-sm mt-1">${tunnelInfo.agent.hostname}</div>
                        </div>
                        <div>
                            <div class="text-xs text-gray-500">IP</div>
                            <div class="text-sm mt-1">${tunnelInfo.agent.ip_address}</div>
                        </div>
                        <div>
                            <div class="text-xs text-gray-500">Usuario</div>
                            <div class="text-sm mt-1">${tunnelInfo.agent.username}</div>
                        </div>
                        <div>
                            <div class="text-xs text-gray-500">Estado del Agente</div>
                            <div class="mt-1">
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                                    ${tunnelInfo.agent.status === 'online' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                                    <i class="fas fa-${tunnelInfo.agent.status === 'online' ? 'check-circle' : 'times-circle'} mr-1"></i>
                                    ${tunnelInfo.agent.status}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Descripción -->
                <div>
                    <h4 class="text-sm font-medium text-gray-500 mb-2">Descripción</h4>
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <p class="text-sm text-gray-700">${tunnelInfo.description || 'Sin descripción'}</p>
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('tunnelInfoContent').innerHTML = content;
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error al obtener la información del túnel', 'error');
        closeModal('tunnelInfoModal');
    }
}

async function closeTunnel(tunnelId) {
    if (!confirm('¿Está seguro de que desea cerrar este túnel?')) return;

    try {
        const response = await fetch(`/api/v1/tunnels/${tunnelId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) throw new Error('Error al cerrar el túnel');

        showNotification('Túnel cerrado exitosamente', 'success');
        
        // Animación de desvanecimiento
        const row = document.querySelector(`tr[data-tunnel-id="${tunnelId}"]`);
        if (row) {
            row.style.transition = 'all 0.5s ease';
            row.style.opacity = '0';
            row.style.transform = 'translateX(20px)';
            setTimeout(() => {
                row.remove();
                updateStats();
            }, 500);
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error al cerrar el túnel', 'error');
    }
}

// Funciones de utilidad
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.remove('hidden');
    modal.setAttribute('aria-hidden', 'false');
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
}

function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500',
        warning: 'bg-yellow-500'
    };

    notification.className = `${colors[type]} text-white px-4 py-3 rounded-lg shadow-lg flex items-center space-x-2 transform translate-y-2 opacity-0 transition-all duration-300`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'times-circle' : 'info-circle'}"></i>
        <span>${message}</span>
        <button class="ml-auto" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;

    container.appendChild(notification);
    requestAnimationFrame(() => {
        notification.style.transform = 'translateY(0)';
        notification.style.opacity = '1';
    });

    setTimeout(() => {
        notification.style.transform = 'translateY(2px)';
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function getStatusClasses(status) {
    const classes = {
        active: 'bg-green-100 text-green-800',
        creating: 'bg-yellow-100 text-yellow-800',
        error: 'bg-red-100 text-red-800',
        closed: 'bg-gray-100 text-gray-800'
    };
    return classes[status] || classes.closed;
}

function getStatusIcon(status) {
    const icons = {
        active: 'check-circle',
        creating: 'sync fa-spin',
        error: 'exclamation-circle',
        closed: 'times-circle'
    };
    return icons[status] || 'circle';
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
}

function updateStats() {
    const stats = {
        total: document.querySelectorAll('tbody tr').length,
        active: Array.from(document.querySelectorAll('tr span')).filter(span => 
            span.textContent.toLowerCase().includes('active')).length,
        creating: Array.from(document.querySelectorAll('tr span')).filter(span => 
            span.textContent.toLowerCase().includes('creating')).length,
        error: Array.from(document.querySelectorAll('tr span')).filter(span => 
            span.textContent.toLowerCase().includes('error')).length
    };

    // Actualizar los contadores en las tarjetas de estadísticas
    Object.keys(stats).forEach(key => {
        const element = document.querySelector(`[data-stat="${key}"]`);
        if (element) {
            element.textContent = stats[key];
        }
    });
}

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    // Búsqueda en tiempo real
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }

    // Inicializar estadísticas
    updateStats();
});
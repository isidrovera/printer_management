// Actualizar la función showTunnelInfo en tunnels.js

async function showTunnelInfo(tunnelId) {
    try {
        const response = await fetch(`/api/v1/tunnels/${encodeURIComponent(tunnelId)}`);
        if (!response.ok) {
            throw new Error(`Error: ${response.statusText}`);
        }
        
        const tunnelInfo = await response.json();
        
        // Construir el contenido HTML con la información del túnel
        const content = `
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <h4 class="text-sm font-medium text-gray-500">ID del Túnel</h4>
                        <p class="mt-1">${tunnelInfo.tunnel_id}</p>
                    </div>
                    <div>
                        <h4 class="text-sm font-medium text-gray-500">Estado</h4>
                        <p class="mt-1">${tunnelInfo.status}</p>
                    </div>
                    <div>
                        <h4 class="text-sm font-medium text-gray-500">Host Remoto</h4>
                        <p class="mt-1">${tunnelInfo.remote_host}</p>
                    </div>
                    <div>
                        <h4 class="text-sm font-medium text-gray-500">Puerto Remoto</h4>
                        <p class="mt-1">${tunnelInfo.remote_port}</p>
                    </div>
                    <div>
                        <h4 class="text-sm font-medium text-gray-500">Puerto Local</h4>
                        <p class="mt-1">${tunnelInfo.local_port}</p>
                    </div>
                    <div>
                        <h4 class="text-sm font-medium text-gray-500">Creado</h4>
                        <p class="mt-1">${new Date(tunnelInfo.created_at).toLocaleString()}</p>
                    </div>
                </div>
                
                <div class="mt-6">
                    <h4 class="text-sm font-medium text-gray-500">Información del Agente</h4>
                    <div class="mt-2 grid grid-cols-2 gap-4">
                        <div>
                            <h5 class="text-xs font-medium text-gray-500">Hostname</h5>
                            <p class="mt-1">${tunnelInfo.agent.hostname}</p>
                        </div>
                        <div>
                            <h5 class="text-xs font-medium text-gray-500">Usuario</h5>
                            <p class="mt-1">${tunnelInfo.agent.username}</p>
                        </div>
                        <div>
                            <h5 class="text-xs font-medium text-gray-500">IP</h5>
                            <p class="mt-1">${tunnelInfo.agent.ip_address}</p>
                        </div>
                    </div>
                </div>

                <div class="mt-4">
                    <h4 class="text-sm font-medium text-gray-500">Descripción</h4>
                    <p class="mt-1">${tunnelInfo.description || 'Sin descripción'}</p>
                </div>
            </div>
        `;
        
        document.getElementById('tunnelInfoContent').innerHTML = content;
        showModal('tunnelInfoModal');
    } catch (error) {
        console.error('Error:', error);
        alert('Error al obtener la información del túnel');
    }
}


// Función para cerrar un túnel
async function closeTunnel(tunnelId) {
    if (!confirm('¿Está seguro de que desea cerrar este túnel?')) {
        return;
    }

    try {
        const response = await fetch(`/api/v1/tunnels/${tunnelId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Error al cerrar el túnel');
        }

        // Recargar la página para actualizar la lista de túneles
        window.location.reload();
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cerrar el túnel');
    }
}

// Funciones de utilidad para los modales
function showModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

// Implementar búsqueda de túneles
document.getElementById('searchInput').addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
});
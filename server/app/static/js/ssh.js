// static/js/ssh.js
let tunnelLogInterval;

function toggleSSH(agentToken, agentId) {
    const modal = document.getElementById('sshModal');
    document.getElementById('sshAgentToken').value = agentToken;
    document.getElementById('sshAgentId').value = agentId;  // Asegurarse que este campo exista
    modal.classList.remove('hidden');
    // Limpiar logs previos
    document.getElementById('sshLogMessages').innerHTML = '';
}

function addSSHLogMessage(message, type = 'info') {
    const logsDiv = document.getElementById('sshLogMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `text-sm ${type === 'error' ? 'text-red-600' : 'text-gray-600'}`;
    messageDiv.textContent = message;
    logsDiv.appendChild(messageDiv);
    logsDiv.scrollTop = logsDiv.scrollHeight;
}

async function handleSSHForm(event) {
    event.preventDefault();
    
    // Obtener datos del formulario
    const formData = {
        agent_id: parseInt(document.getElementById('sshAgentId').value),
        ssh_host: document.getElementById('sshHost').value,
        ssh_port: parseInt(document.getElementById('sshPort').value) || 22,
        username: document.getElementById('sshUsername').value,
        password: document.getElementById('sshPassword').value,
        remote_host: document.getElementById('remoteHost').value,
        remote_port: parseInt(document.getElementById('sshRemotePort').value),
        local_port: parseInt(document.getElementById('sshLocalPort').value)
    };
 
    try {
        // Intentar crear el túnel
        addSSHLogMessage('Iniciando creación del túnel...');
        const response = await fetch('/api/v1/tunnels/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
 
        const result = await response.json();
 
        // Manejar respuesta
        if (!response.ok) {
            // Si ya existe un túnel
            if (response.status === 400 && result.detail.includes('Ya existe un túnel activo')) {
                const tunnelId = `${formData.remote_host}:${formData.remote_port}-${formData.local_port}`;
                
                if (confirm(`Ya existe un túnel activo (${tunnelId}). ¿Desea cerrarlo y crear uno nuevo?`)) {
                    addSSHLogMessage('Cerrando túnel existente...');
                    
                    // Cerrar túnel existente
                    const deleteResponse = await fetch(`/api/v1/tunnels/${tunnelId}`, {
                        method: 'DELETE'
                    });
 
                    if (!deleteResponse.ok) {
                        throw new Error('Error al cerrar el túnel existente');
                    }
 
                    addSSHLogMessage('Túnel cerrado. Creando nuevo túnel...');
 
                    // Intentar crear el túnel nuevamente
                    const retryResponse = await fetch('/api/v1/tunnels/create', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(formData)
                    });
 
                    if (!retryResponse.ok) {
                        const retryError = await retryResponse.json();
                        throw new Error(retryError.detail || 'Error creando el nuevo túnel');
                    }
 
                    addSSHLogMessage('Túnel creado exitosamente');
                    showNotification('Túnel SSH creado exitosamente', 'success');
                    closeModal('sshModal');
                }
            } else {
                // Otros errores
                throw new Error(result.detail || 'Error desconocido');
            }
        } else {
            // Éxito en la primera creación
            addSSHLogMessage('Túnel creado exitosamente');
            showNotification('Túnel SSH creado exitosamente', 'success');
            closeModal('sshModal');
        }
 
    } catch (error) {
        console.error('[ERROR]', error);
        addSSHLogMessage(`Error: ${error.message}`, 'error');
        showNotification(error.message, 'error');
    }
 }
 
 // Asegurar que el formulario existe antes de agregar el event listener
 document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('sshForm');
    if (form) {
        form.addEventListener('submit', handleSSHForm);
    }
 });
 
 document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('sshForm');
    if (form) {
        form.addEventListener('submit', handleSSHForm);
    }
 });

async function createTunnel(data) {
    try {
        const response = await fetch('/api/v1/tunnels/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (!response.ok) {
            throw new Error(JSON.stringify(result.detail));
        }

        addSSHLogMessage('Túnel creado exitosamente');
        closeModal('sshModal');
        showNotification('Túnel SSH creado exitosamente', 'success');
    } catch (error) {
        console.error('[ERROR]', error);
        addSSHLogMessage(`Error: ${error.message}`, 'error');
        showNotification(error.message, 'error');
    }
}
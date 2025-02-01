// static/js/ssh.js
let tunnelLogInterval;

function toggleSSH(agentToken, agentId) {
    const modal = document.getElementById('sshModal');
    document.getElementById('sshAgentToken').value = agentToken;
    document.getElementById('sshAgentId').value = agentId;
    modal.classList.remove('hidden');
    // Limpiar logs previos
    document.getElementById('sshLogMessages').innerHTML = '';
}

function addSSHLog(message, type = 'info') {
    const logsDiv = document.getElementById('sshLogMessages');
    if (!logsDiv) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `text-sm ${type === 'error' ? 'text-red-600' : 'text-gray-600'}`;
    messageDiv.textContent = message;
    logsDiv.appendChild(messageDiv);
    logsDiv.scrollTop = logsDiv.scrollHeight;
}

async function handleSSHForm(event) {
    event.preventDefault();
    
    const data = {
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
        const response = await fetch('/api/v1/tunnels/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
 
        const result = await response.json();
        
        if (!response.ok) {
            console.error('Error details:', result);
            throw new Error(result.detail ? JSON.stringify(result.detail) : 'Error desconocido');
        }
 
        addSSHLog('Túnel creado exitosamente');
        closeModal('sshModal');
        showNotification('Túnel SSH creado exitosamente', 'success');
    } catch (error) {
        console.error('[ERROR]', error);
        addSSHLog(error.message, 'error');
        showNotification(error.message, 'error');
    }
}

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

        addSSHLog('Túnel creado exitosamente');
        closeModal('sshModal');
        showNotification('Túnel SSH creado exitosamente', 'success');
    } catch (error) {
        console.error('[ERROR]', error);
        addSSHLog(`Error: ${error.message}`, 'error');
        showNotification(error.message, 'error');
    }
}

// Función para iniciar el monitoreo del túnel
function startTunnelMonitoring(agentId) {
    // Limpiar cualquier intervalo existente
    if (tunnelLogInterval) {
        clearInterval(tunnelLogInterval);
    }

    // Establecer nuevo intervalo para verificar el estado
    tunnelLogInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/v1/tunnels/${agentId}/status`);
            const status = await response.json();

            // Agregar el mensaje al log
            addSSHLog(status.message, status.type);

            // Si el túnel está cerrado o hay un error, detener el monitoreo
            if (status.type === 'error' || status.status === 'closed') {
                clearInterval(tunnelLogInterval);
            }
        } catch (error) {
            console.error('Error monitoreando túnel:', error);
            addSSHLog(`Error monitoreando túnel: ${error.message}`, 'error');
            clearInterval(tunnelLogInterval);
        }
    }, 5000); // Verificar cada 5 segundos
}

// Función para detener el monitoreo
function stopTunnelMonitoring() {
    if (tunnelLogInterval) {
        clearInterval(tunnelLogInterval);
        tunnelLogInterval = null;
    }
}
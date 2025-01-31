// static/js/ssh.js
async function toggleSSH(agentToken) {
    const modal = document.getElementById('sshModal');
    document.getElementById('sshAgentToken').value = agentToken;
    modal.classList.remove('hidden');
}

// static/js/ssh.js
async function handleSSHForm(event) {
    event.preventDefault();
    
    const data = {
        agent_id: parseInt(document.getElementById('sshAgentId').value),
        ssh_host: document.getElementById('sshHost').value,
        ssh_port: parseInt(document.getElementById('sshPort').value) || 22,
        username: document.getElementById('sshUsername').value,
        password: document.getElementById('sshPassword').value,
        local_port: parseInt(document.getElementById('sshLocalPort').value),
        remote_host: document.getElementById('remoteHost').value,
        remote_port: parseInt(document.getElementById('remotePort').value)
    };

    try {
        const response = await fetch('/api/v1/tunnels/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(await response.text());
        }

        showNotification('Túnel SSH creado exitosamente', 'success');
        closeModal('sshModal');
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

document.getElementById('sshForm').addEventListener('submit', handleSSHForm);
// static/js/ssh.js
async function toggleSSH(agentToken) {
    const modal = document.getElementById('sshModal');
    document.getElementById('sshAgentToken').value = agentToken;
    modal.classList.remove('hidden');
}

async function handleSSHForm(event) {
    event.preventDefault();
    
    const data = {
        agent_token: document.getElementById('sshAgentToken').value,
        username: document.getElementById('sshUsername').value,
        password: document.getElementById('sshPassword').value,
        local_port: parseInt(document.getElementById('sshLocalPort').value),
        remote_port: parseInt(document.getElementById('sshRemotePort').value)
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

        closeModal('sshModal');
        showNotification('Túnel SSH creado exitosamente', 'success');
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

document.getElementById('sshForm').addEventListener('submit', handleSSHForm);
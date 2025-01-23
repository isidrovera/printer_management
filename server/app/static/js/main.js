// app/static/js/main.js

// Funciones de confirmación y eliminación
function confirmDelete(type, id) {
    if (confirm(`¿Está seguro de eliminar este ${type}?`)) {
        fetch(`/api/v1/${type}s/${id}`, {
            method: 'DELETE'
        }).then(response => {
            if (response.ok) {
                window.location.reload();
            } else {
                alert('Error al eliminar');
            }
        });
    }
 }
 
 // Gestión de modal de instalación de impresora
 function showInstallPrinter(agentId) {
    document.getElementById('agentId').value = agentId;
    new bootstrap.Modal(document.getElementById('installPrinterModal')).show();
 }
 
 function installPrinter() {
    const agentId = document.getElementById('agentId').value;
    const driverId = document.getElementById('driverId').value;
    const printerIp = document.getElementById('printerIp').value;
 
    fetch(`/api/v1/agents/${agentId}/install-printer`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            driver_id: driverId,
            printer_ip: printerIp
        })
    }).then(response => {
        if (response.ok) {
            alert('Comando de instalación enviado');
            bootstrap.Modal.getInstance(document.getElementById('installPrinterModal')).hide();
        } else {
            alert('Error al enviar comando');
        }
    });
 }
 
 // Actualización de estado en tiempo real vía WebSocket
 // En static/js/main.js
let ws;

function connectWebSocket() {
    ws = new WebSocket(`ws://${window.location.host}/api/v1/ws/status`);
    ws.onmessage = function(event) {
        console.log("WebSocket message received:", event.data);
    };
    ws.onerror = function(error) {
        console.error("WebSocket error:", error);
    };
}

// Solo conectar si estamos en una página que necesita WebSocket
if (document.querySelector('.status-updates')) {
    connectWebSocket();
}
 
 function updateAgentStatus(agentId, status) {
    const statusCell = document.querySelector(`[data-agent-id="${agentId}"] .status`);
    if (statusCell) {
        statusCell.textContent = status;
        statusCell.className = `status status-${status}`;
    }
 }
 
 // Inicializar WebSocket al cargar la página
 document.addEventListener('DOMContentLoaded', connectWebSocket);
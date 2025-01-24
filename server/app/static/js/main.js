// app/static/js/main.js

let ws;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;


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

// WebSocket
function connectWebSocket() {
   ws = new WebSocket(`ws://${window.location.host}/api/v1/ws/status`);
   
   ws.onopen = () => {
       console.log('WebSocket conectado');
       reconnectAttempts = 0;
   };

   ws.onmessage = (event) => {
       const data = JSON.parse(event.data);
       if (data.type === 'status_update') {
           updateAgentStatus(data.agent_id, data.status);
       }
       console.log("WebSocket message received:", data);
   };

   ws.onclose = () => {
       console.log('WebSocket desconectado');
       if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
           reconnectAttempts++;
           console.log(`Reintentando conexión ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`);
           setTimeout(connectWebSocket, 1000 * reconnectAttempts);
       }
   };

   ws.onerror = (error) => {
       console.error('WebSocket error:', error);
   };
}

function updateAgentStatus(agentId, status) {
   const statusCell = document.querySelector(`[data-agent-id="${agentId}"] .status`);
   if (statusCell) {
       statusCell.textContent = status;
       statusCell.className = `status status-${status}`;
   }
}

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
   // Solo conectar WebSocket si estamos en una página que lo necesita
   if (document.querySelector('.status-updates')) {
       connectWebSocket();
   }

   // Inicializar tooltips y popovers de Bootstrap si existen
   const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
   tooltipTriggerList.map(function (tooltipTriggerEl) {
       return new bootstrap.Tooltip(tooltipTriggerEl);
   });

   const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
   popoverTriggerList.map(function (popoverTriggerEl) {
       return new bootstrap.Popover(popoverTriggerEl);
   });
});
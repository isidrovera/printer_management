// Variables globales
let updateInterval;
let currentPrinters = [];
let charts = {};
let printerToDelete = null;

// Función para inicializar la aplicación
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar listeners
    initializeEventListeners();
    // Primera carga de datos
    updatePrintersList();
    // Iniciar intervalo de actualización
    setUpdateInterval(30);
});

// Inicializar event listeners
function initializeEventListeners() {
    // Listener para el intervalo de actualización
    document.getElementById('refreshInterval').addEventListener('change', function(e) {
        setUpdateInterval(parseInt(e.target.value));
    });

    // Listener para la búsqueda
    document.getElementById('searchInput').addEventListener('input', function(e) {
        filterPrinters(e.target.value);
    });
}

// Configurar intervalo de actualización
function setUpdateInterval(seconds) {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
    updateInterval = setInterval(updatePrintersList, seconds * 1000);
}

// Función para actualizar la lista de impresoras
function updateUI(data) {
    const tableBody = document.querySelector('tbody');
    
    // Limpiar tabla actual
    tableBody.innerHTML = '';
    
    // Repoblar tabla con nuevos datos
    data.printers.forEach(printer => {
        const row = createPrinterRow(printer);
        tableBody.appendChild(row);
    });

    // Actualizar estadísticas
    updateStatistics(data.printers);
}

function updateStatistics(printers) {
    // Actualizar contadores de estado
    document.querySelector('.total-printers').textContent = printers.length;
    document.querySelector('.online-printers').textContent = 
        printers.filter(p => p.status === 'online').length;
    // Otros contadores similares
}

// Función para filtrar impresoras
function filterPrinters(searchTerm) {
    const rows = document.querySelectorAll('tbody tr');
    searchTerm = searchTerm.toLowerCase();

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

// Funciones para los modales
function showPrinterInfo(printerId) {
    openModal('printerInfoModal');
    loadPrinterInfo(printerId);
}

function showSupplies(printerId) {
    openModal('suppliesModal');
    loadSuppliesInfo(printerId);
}

function showCounters(printerId) {
    openModal('countersModal');
    loadCountersInfo(printerId);
}

function showHistory(printerId) {
    openModal('historyModal');
    loadHistoryInfo(printerId);
}

// Función para cargar información de la impresora
async function loadPrinterInfo(printerId) {
    const contentDiv = document.getElementById('printerInfoContent');
    try {
        const response = await fetch(`/api/v1/printers/${printerId}`);
        const data = await response.json();
        
        contentDiv.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Información básica -->
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h4 class="font-semibold mb-4">Información Básica</h4>
                    <div class="space-y-2">
                        <p><span class="font-medium">Nombre:</span> ${data.name}</p>
                        <p><span class="font-medium">Modelo:</span> ${data.model}</p>
                        <p><span class="font-medium">IP:</span> ${data.ip_address}</p>
                        <p><span class="font-medium">Serial:</span> ${data.serial_number}</p>
                    </div>
                </div>
                <!-- Estado actual -->
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h4 class="font-semibold mb-4">Estado Actual</h4>
                    <div class="space-y-2">
                        <p><span class="font-medium">Estado:</span> 
                           <span class="px-2 py-1 rounded-full ${getStatusClass(data.status)}">
                             ${data.status}
                           </span>
                        </p>
                        <p><span class="font-medium">Última actualización:</span> ${formatDate(data.last_update)}</p>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        contentDiv.innerHTML = `
            <div class="text-red-500 text-center">
                <i class="fas fa-exclamation-circle mr-2"></i>
                Error al cargar la información: ${error.message}
            </div>
        `;
    }
}

// Función para cargar información de suministros
async function loadSuppliesInfo(printerId) {
    const contentDiv = document.getElementById('suppliesContent');
    try {
        const response = await fetch(`/api/v1/printers/${printerId}/supplies`);
        const data = await response.json();
        
        contentDiv.innerHTML = `
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                ${Object.entries(data.supplies).map(([color, info]) => `
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <div class="flex justify-between items-center mb-2">
                            <span class="font-medium">${capitalize(color)}</span>
                            <span class="text-sm ${getSupplyLevelClass(info.level)}">
                                ${info.level}%
                            </span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2.5">
                            <div class="bg-${getSupplyColor(color)} h-2.5 rounded-full" 
                                 style="width: ${info.level}%">
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        contentDiv.innerHTML = `
            <div class="text-red-500 text-center">
                <i class="fas fa-exclamation-circle mr-2"></i>
                Error al cargar los suministros: ${error.message}
            </div>
        `;
    }
}

// Función para cargar información de contadores
async function loadCountersInfo(printerId) {
    const contentDiv = document.getElementById('countersContent');
    try {
        const response = await fetch(`/api/v1/printers/${printerId}/counters`);
        
        // Verificar si la respuesta es válida
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Validaciones adicionales para evitar errores
        if (!data) {
            throw new Error('No se recibieron datos');
        }

        // Valores por defecto si no existen
        const current = data.current || {
            total: 0,
            color: 0,
            bw: 0
        };

        const history = data.history || {};

        // Preparar datos para el gráfico
        const chartData = {
            labels: Object.keys(history).map(date => formatDate(date)),
            datasets: [{
                label: 'Impresiones totales',
                data: Object.values(history).map(entry => 
                    entry && entry.total ? entry.total : 0
                ),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        };

        contentDiv.innerHTML = `
            <div class="space-y-6">
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h5 class="font-medium mb-2">Total</h5>
                        <p class="text-2xl">${formatNumber(current.total)}</p>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h5 class="font-medium mb-2">Color</h5>
                        <p class="text-2xl">${formatNumber(current.color)}</p>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h5 class="font-medium mb-2">Blanco y Negro</h5>
                        <p class="text-2xl">${formatNumber(current.bw)}</p>
                    </div>
                </div>
                <div class="bg-white p-4 rounded-lg">
                    <canvas id="countersChart"></canvas>
                </div>
            </div>
        `;

        // Inicializar gráfico solo si hay datos
        if (chartData.labels.length > 0) {
            const ctx = document.getElementById('countersChart').getContext('2d');
            if (charts.counters) {
                charts.counters.destroy();
            }
            charts.counters = new Chart(ctx, {
                type: 'line',
                data: chartData,
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: 'Histórico de impresiones'
                        }
                    }
                }
            });
        } else {
            // Mostrar mensaje si no hay datos históricos
            document.getElementById('countersChart').innerHTML = `
                <div class="text-center text-gray-500">
                    No hay datos históricos disponibles
                </div>
            `;
        }
    } catch (error) {
        contentDiv.innerHTML = `
            <div class="text-red-500 text-center">
                <i class="fas fa-exclamation-circle mr-2"></i>
                Error al cargar los contadores: ${error.message}
            </div>
        `;
    }
}

// Función para cargar historial
async function loadHistoryInfo(printerId) {
    const contentDiv = document.getElementById('historyContent');
    try {
        const response = await fetch(`/api/v1/printers/${printerId}/history`);
        const data = await response.json();
        
        contentDiv.innerHTML = `
            <div class="space-y-4">
                ${data.events.map(event => `
                    <div class="bg-gray-50 p-4 rounded-lg flex items-start space-x-4">
                        <div class="flex-shrink-0">
                            <i class="fas ${getEventIcon(event.type)} text-${getEventColor(event.type)}"></i>
                        </div>
                        <div class="flex-grow">
                            <div class="flex justify-between items-start">
                                <p class="font-medium">${event.description}</p>
                                <span class="text-sm text-gray-500">${formatDate(event.timestamp)}</span>
                            </div>
                            ${event.details ? `<p class="text-sm text-gray-600 mt-1">${event.details}</p>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        contentDiv.innerHTML = `
            <div class="text-red-500 text-center">
                <i class="fas fa-exclamation-circle mr-2"></i>
                Error al cargar el historial: ${error.message}
            </div>
        `;
    }
}

// Funciones auxiliares
function openModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
    // Limpiar gráficos si existen
    if (modalId === 'countersModal' && charts.counters) {
        charts.counters.destroy();
        charts.counters = null;
    }
}

function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    
    notification.className = `
        flex items-center p-4 mb-4 rounded-lg text-sm
        ${type === 'error' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}
    `;
    
    notification.innerHTML = `
        <i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'info-circle'} mr-2"></i>
        ${message}
    `;
    
    container.appendChild(notification);
    setTimeout(() => notification.remove(), 5000);
}

function getStatusClass(status) {
    const classes = {
        online: 'bg-green-100 text-green-800',
        error: 'bg-red-100 text-red-800',
        warning: 'bg-yellow-100 text-yellow-800',
        offline: 'bg-gray-100 text-gray-800'
    };
    return classes[status] || classes.offline;
}

function getSupplyLevelClass(level) {
    if (level <= 10) return 'text-red-600';
    if (level <= 25) return 'text-yellow-600';
    return 'text-green-600';
}

function getSupplyColor(color) {
    const colors = {
        black: 'gray-800',
        cyan: 'cyan-500',
        magenta: 'pink-500',
        yellow: 'yellow-500'
    };
    return colors[color.toLowerCase()] || 'blue-500';
}

function getEventIcon(type) {
    const icons = {
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle',
        status: 'fa-toggle-on'
    };
    return icons[type] || 'fa-circle';
}

function getEventColor(type) {
    const colors = {
        error: 'red-500',
        warning: 'yellow-500',
        info: 'blue-500',
        status: 'green-500'
    };
    return colors[type] || 'gray-500';
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleString();
}

function formatNumber(number) {
    return new Intl.NumberFormat().format(number);
}

function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

// Event Listeners para cerrar modales con Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modals = ['printerInfoModal', 'suppliesModal', 'countersModal', 'historyModal','deletePrinterModal'];
        modals.forEach(modalId => {
            if (!document.getElementById(modalId).classList.contains('hidden')) {
                closeModal(modalId);
            }
        });
    }
});

// Click fuera del modal para cerrar
document.addEventListener('click', function(event) {
    const modals = ['printerInfoModal', 'suppliesModal', 'countersModal', 'historyModal'];
    modals.forEach(modalId => {
        const modal = document.getElementById(modalId);
        if (event.target === modal) {
            closeModal(modalId);
        }
    });
});





// Funciones para manejar modales
function openCreateModal() {
    document.getElementById("createPrinterModal").classList.remove("hidden");
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add("hidden");
        // Si es el modal de crear, limpiar el formulario
        if (modalId === 'createPrinterModal') {
            const form = document.getElementById('createPrinterForm');
            if (form) form.reset();
        }
    }
}

// Función para manejar la creación de una nueva impresora
async function handleCreatePrinter(event) {
    event.preventDefault();
    
    const submitButton = event.target.querySelector('button[type="submit"]');
    const originalContent = submitButton.innerHTML;
    
    try {
        // Deshabilitar el botón y mostrar estado de carga
        submitButton.disabled = true;
        submitButton.innerHTML = `<i class="fas fa-circle-notch fa-spin mr-2"></i>Guardando...`;
        
        const formData = {
            name: document.getElementById("printerName").value,
            brand:document.getElementById("printerBrand").value,
            model: document.getElementById("printerModel").value,
            ip_address: document.getElementById("printerIP").value,
            client_id: document.getElementById("clientId").value
        };

        const response = await fetch('/monitor/printers/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();
        
        if (response.ok) {
            showNotification('Impresora creada exitosamente', 'success');
            closeModal('createPrinterModal');
            await updatePrintersList(); // Actualizar la lista de impresoras
            document.getElementById("createPrinterForm").reset();
        } else {
            throw new Error(data.detail || 'Error al crear la impresora');
        }
    } catch (error) {
        showNotification(error.message, 'error');
    } finally {
        // Restaurar el botón
        submitButton.disabled = false;
        submitButton.innerHTML = originalContent;
    }
}



async function updatePrintersList() {
    try {
        const response = await fetch('/monitor/printers');
        if (!response.ok) {
            throw new Error('Error al obtener datos de las impresoras');
        }
        const data = await response.text(); // Cambiar a .text() en lugar de .json()
        
        // Reemplazar el contenido del cuerpo de la tabla
        const tableBody = document.querySelector('tbody');
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = data;
        const newTableBody = tempDiv.querySelector('tbody');
        
        if (newTableBody) {
            tableBody.innerHTML = newTableBody.innerHTML;
            
            // Actualizar estadísticas
            updateStatistics();
        }
    } catch (error) {
        showNotification('Error al actualizar los datos: ' + error.message, 'error');
    }
}


// Resto del código...

// En la sección de funciones de modal, agrega:
function confirmDeletePrinter(printerId) {
    printerToDelete = printerId;
    document.getElementById('deletePrinterModal').classList.remove('hidden');
}

async function deletePrinter() {
    try {
        const response = await fetch(`/monitor/printers/${printerToDelete}`, {
            method: 'DELETE'
        });
 
        if (response.ok) {
            showNotification('Impresora eliminada exitosamente', 'success');
            closeModal('deletePrinterModal');
            await updatePrintersList();
        } else {
            const data = await response.json();
            throw new Error(data.detail || 'Error al eliminar la impresora');
        }
    } catch (error) {
        showNotification(error.message, 'error');
    } finally {
        printerToDelete = null;
    }
 }
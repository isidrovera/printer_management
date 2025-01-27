// static/js/agents.js

// Variables globales
let currentAgentToken = '';
let agentToDelete = null;

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function () {
    initializeManufacturerSelect();
    initializeSearchFilter();
    initializeFormHandlers();
    initializeWebSocket();
});

// Función para inicializar select de fabricantes
async function initializeManufacturerSelect() {
    const manufacturerSelect = document.getElementById('manufacturer');
    if (!manufacturerSelect) return;

    try {
        // Hacer la petición al backend para obtener fabricantes y modelos
        const response = await fetch('/api/v1/printers/manufacturers');
        if (!response.ok) {
            throw new Error('Error al obtener la lista de fabricantes');
        }

        const manufacturers = await response.json();

        // Validar que la respuesta sea un array
        if (!Array.isArray(manufacturers)) {
            throw new Error('El formato de datos devuelto es inválido');
        }

        // Poblar el select con los fabricantes
        manufacturerSelect.innerHTML = '<option value="">Seleccione un fabricante</option>';
        manufacturers.forEach((manufacturer) => {
            const option = document.createElement('option');
            option.value = manufacturer;
            option.textContent = manufacturer;
            manufacturerSelect.appendChild(option);
        });

        // Agregar un evento para cargar modelos según el fabricante seleccionado
        manufacturerSelect.addEventListener('change', loadModels);
    } catch (error) {
        console.error('Error inicializando fabricantes:', error);
        showNotification('Error al cargar fabricantes', 'error');
    }
}

// Función para cargar modelos según el fabricante seleccionado
async function loadModels(e) {
    const manufacturer = e.target.value;
    const modelSelect = document.getElementById('model');
    if (!modelSelect) return;

    modelSelect.disabled = true;
    modelSelect.innerHTML = '<option value="">Cargando modelos...</option>';

    try {
        if (!manufacturer) {
            modelSelect.innerHTML = '<option value="">Seleccione un modelo</option>';
            modelSelect.disabled = false;
            return;
        }

        // Hacer la petición al backend para obtener los modelos
        const response = await fetch(`/api/v1/printers/models/${manufacturer}`);
        if (!response.ok) {
            throw new Error('Error al obtener la lista de modelos');
        }

        const models = await response.json();

        // Validar que la respuesta sea un array
        if (!Array.isArray(models)) {
            throw new Error('El formato de datos devuelto es inválido');
        }

        // Poblar el select con los modelos
        modelSelect.innerHTML = '<option value="">Seleccione un modelo</option>';
        models.forEach((model) => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            modelSelect.appendChild(option);
        });

    } catch (error) {
        console.error('Error al cargar modelos:', error);
        showNotification('Error al cargar modelos', 'error');
        modelSelect.innerHTML = '<option value="">Error al cargar modelos</option>';
    } finally {
        modelSelect.disabled = false;
    }
}

// Función para inicializar manejadores de formularios
function initializeFormHandlers() {
    const installForm = document.getElementById('installPrinterForm');
    if (installForm) {
        installForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const manufacturer = document.getElementById('manufacturer').value;
            const model = document.getElementById('model').value;
            const printerIp = document.getElementById('printerIp').value;

            if (!manufacturer || !model || !printerIp) {
                showNotification('Por favor complete todos los campos', 'error');
                return;
            }

            try {
                const response = await fetch(`/api/v1/printers/install/${currentAgentToken}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        printer_ip: printerIp,
                        manufacturer: manufacturer,
                        model: model,
                    }),
                });

                const data = await response.json();

                if (response.ok) {
                    showNotification('Comando de instalación enviado correctamente', 'success');
                    closeModal('installPrinterModal');
                } else {
                    throw new Error(data.detail || 'Error al enviar el comando de instalación');
                }
            } catch (error) {
                console.error('Error al enviar formulario:', error);
                showNotification(error.message, 'error');
            }
        });
    }
}

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    // Implementa aquí tu lógica para mostrar notificaciones (puedes usar un framework o crear una función propia)
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Función para cerrar modales
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        if (modalId === 'installPrinterModal') {
            document.getElementById('installPrinterForm').reset();
        }
    }
}

// Función para inicializar filtro de búsqueda
function initializeSearchFilter() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function (e) {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');

            rows.forEach((row) => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }
}

// Inicializar WebSocket
function initializeWebSocket() {
    // Implementación de WebSocket aquí
}

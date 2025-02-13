// Configuración
const EXCEL_CONFIG = {
    filename: 'configuracion_oids.xlsx',
    sheetName: 'OIDs',
    dateFormat: 'YYYY-MM-DD HH:mm:ss'
};

// Mapeo de campos
const FIELD_MAPPING = {
    // Información Básica
    'Marca': 'brand',
    'Familia de Modelo': 'model_family',
    'Descripción': 'description',
    
    // Contadores de Páginas
    'OID Total Páginas': 'oid_total_pages',
    'OID Páginas Color': 'oid_total_color_pages',
    'OID Páginas B/N': 'oid_total_bw_pages',
    'OID Total Copias': 'oid_total_copies',
    
    // Tóner
    'OID Nivel Tóner Negro': 'oid_black_toner_level',
    'OID Nivel Tóner Cyan': 'oid_cyan_toner_level',
    'OID Nivel Tóner Magenta': 'oid_magenta_toner_level',
    'OID Nivel Tóner Amarillo': 'oid_yellow_toner_level',
    
    // Unidades de Imagen
    'OID Nivel Drum Negro': 'oid_black_drum_level',
    'OID Nivel Drum Cyan': 'oid_cyan_drum_level',
    'OID Nivel Drum Magenta': 'oid_magenta_drum_level',
    'OID Nivel Drum Amarillo': 'oid_yellow_drum_level',
    
    // Otros Consumibles
    'OID Nivel Unidad Fusora': 'oid_fuser_unit_level',
    'OID Nivel Banda Transferencia': 'oid_transfer_belt_level',
    'OID Nivel Tóner Residual': 'oid_waste_toner_level',
    'OID Capacidad Máx Tóner Residual': 'oid_waste_toner_max',
    
    // Bandejas
    // Bandeja 1
    'OID Nivel Bandeja 1': 'oid_tray1_level',
    'OID Capacidad Máx Bandeja 1': 'oid_tray1_max_capacity',
    'OID Estado Bandeja 1': 'oid_tray1_status',
    'OID Tamaño Papel Bandeja 1': 'oid_tray1_paper_size',
    'OID Tipo Papel Bandeja 1': 'oid_tray1_paper_type',
    
    // Bandeja 2
    'OID Nivel Bandeja 2': 'oid_tray2_level',
    'OID Capacidad Máx Bandeja 2': 'oid_tray2_max_capacity',
    'OID Estado Bandeja 2': 'oid_tray2_status',
    'OID Tamaño Papel Bandeja 2': 'oid_tray2_paper_size',
    'OID Tipo Papel Bandeja 2': 'oid_tray2_paper_type',
    
    // Bandeja 3
    'OID Nivel Bandeja 3': 'oid_tray3_level',
    'OID Capacidad Máx Bandeja 3': 'oid_tray3_max_capacity',
    'OID Estado Bandeja 3': 'oid_tray3_status',
    'OID Tamaño Papel Bandeja 3': 'oid_tray3_paper_size',
    'OID Tipo Papel Bandeja 3': 'oid_tray3_paper_type',
    
    // Bandeja Bypass
    'OID Nivel Bandeja Bypass': 'oid_bypass_tray_level',
    'OID Estado Bandeja Bypass': 'oid_bypass_tray_status',
    
    // Información del Sistema
    'OID Estado Impresora': 'oid_printer_status',
    'OID Modelo Impresora': 'oid_printer_model',
    'OID Número Serie': 'oid_serial_number',
    'OID Versión Firmware': 'oid_firmware_version',
    'OID Contacto Sistema': 'oid_system_contact',
    'OID Nombre Sistema': 'oid_system_name'
};

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    const exportBtn = document.getElementById('exportExcelBtn');
    const importInput = document.getElementById('importExcelInput');

    if (exportBtn) {
        exportBtn.addEventListener('click', handleExportToExcel);
    }

    if (importInput) {
        importInput.addEventListener('change', handleImportFromExcel);
    }
});

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    
    notification.className = `p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-y-0 ${
        type === 'error' ? 'bg-red-500 text-white' :
        type === 'success' ? 'bg-green-500 text-white' :
        'bg-blue-500 text-white'
    }`;
    
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-${
                type === 'error' ? 'exclamation-circle' :
                type === 'success' ? 'check-circle' :
                'info-circle'
            } mr-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Función para exportar a Excel
async function handleExportToExcel() {
    try {
        // Obtener todas las filas de la tabla
        const rows = document.querySelectorAll('#oidsTable tbody tr');
        const data = Array.from(rows).map(row => {
            // Crear objeto con todos los campos mapeados
            const rowData = {};
            Object.entries(FIELD_MAPPING).forEach(([excelHeader, fieldId]) => {
                rowData[excelHeader] = row.getAttribute(`data-${fieldId}`) || '';
            });
            return rowData;
        });

        // Crear el libro de trabajo
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.json_to_sheet(data);

        // Ajustar ancho de columnas
        const colWidths = Object.keys(FIELD_MAPPING).map(header => ({
            wch: Math.max(header.length, 20)
        }));
        ws['!cols'] = colWidths;

        XLSX.utils.book_append_sheet(wb, ws, EXCEL_CONFIG.sheetName);
        XLSX.writeFile(wb, EXCEL_CONFIG.filename);
        
        showNotification('Exportación completada con éxito', 'success');
    } catch (error) {
        console.error('Error al exportar:', error);
        showNotification('Error al exportar: ' + error.message, 'error');
    }
}

// Función para importar desde Excel
async function handleImportFromExcel(event) {
    try {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async function(e) {
            try {
                // Leer el archivo Excel
                const data = new Uint8Array(e.target.result);
                const workbook = XLSX.read(data, { type: 'array' });
                const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
                const jsonData = XLSX.utils.sheet_to_json(firstSheet);

                // Preparar datos para el backend
                const processedData = jsonData.map(row => {
                    const processedRow = {};
                    Object.entries(FIELD_MAPPING).forEach(([excelHeader, fieldId]) => {
                        processedRow[fieldId] = row[excelHeader] || '';
                    });
                    return processedRow;
                });

                // Enviar datos al backend
                const response = await fetch('/api/printer-oids/import', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrf-token]').content
                    },
                    body: JSON.stringify({
                        oids: processedData,
                        updateExisting: true // Indica que se deben actualizar registros existentes por marca
                    })
                });

                if (!response.ok) {
                    throw new Error('Error al importar los datos');
                }

                const result = await response.json();
                showNotification(`Importación completada: ${result.created} creados, ${result.updated} actualizados`, 'success');
                
                // Recargar la página después de 1.5 segundos
                setTimeout(() => window.location.reload(), 1500);
            } catch (error) {
                console.error('Error al procesar el archivo:', error);
                showNotification('Error al procesar el archivo: ' + error.message, 'error');
            }
        };

        reader.readAsArrayBuffer(file);
    } catch (error) {
        console.error('Error al importar:', error);
        showNotification('Error al importar: ' + error.message, 'error');
    } finally {
        // Limpiar el input file
        event.target.value = '';
    }
}

// Función para validar los datos antes de importar
function validateImportData(data) {
    const errors = [];
    
    data.forEach((row, index) => {
        if (!row.brand) {
            errors.push(`Fila ${index + 1}: Marca es requerida`);
        }
        if (!row.model_family) {
            errors.push(`Fila ${index + 1}: Familia de Modelo es requerida`);
        }
    });

    return errors;
}

// Función para preparar los datos para exportación
function prepareExportData(rows) {
    return Array.from(rows).map(row => {
        const exportRow = {};
        Object.entries(FIELD_MAPPING).forEach(([excelHeader, fieldId]) => {
            let value = '';
            
            // Intentar obtener el valor del atributo data primero
            if (row.dataset[fieldId]) {
                value = row.dataset[fieldId];
            } 
            // Si no existe, buscar en el contenido de la celda
            else {
                const cell = row.querySelector(`[data-field="${fieldId}"]`);
                if (cell) {
                    value = cell.textContent.trim();
                }
            }
            
            exportRow[excelHeader] = value;
        });
        return exportRow;
    });
}
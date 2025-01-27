document.addEventListener('DOMContentLoaded', function() {
    // Inicializar iconos
    lucide.createIcons();

    // Elementos DOM
    const listViewBtn = document.getElementById('listViewBtn');
    const kanbanViewBtn = document.getElementById('kanbanViewBtn');
    const listView = document.getElementById('listView');
    const kanbanView = document.getElementById('kanbanView');

    // Cambiar a vista lista
    listViewBtn?.addEventListener('click', () => {
        listViewBtn.classList.add('active');
        kanbanViewBtn.classList.remove('active');
        listView.classList.remove('hidden');
        kanbanView.classList.add('hidden');
        localStorage.setItem('clientViewPreference', 'list');
    });

    // Cambiar a vista kanban
    kanbanViewBtn?.addEventListener('click', () => {
        kanbanViewBtn.classList.add('active');
        listViewBtn.classList.remove('active');
        kanbanView.classList.remove('hidden');
        listView.classList.add('hidden');
        localStorage.setItem('clientViewPreference', 'kanban');
    });

    // Restaurar preferencia guardada
    const savedView = localStorage.getItem('clientViewPreference');
    if (savedView === 'kanban') {
        kanbanViewBtn?.click();
    }

    // Inicializar tooltips de Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Función para confirmar eliminación
function confirmDelete(type, id) {
    const modalHtml = `
        <div class="modal fade" id="deleteModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Confirmar eliminación</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ¿Estás seguro de que deseas eliminar este cliente?
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-danger" id="confirmDeleteBtn">Eliminar</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Añadir modal al DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    const deleteModal = document.getElementById('deleteModal');
    const modal = new bootstrap.Modal(deleteModal);
    
    // Manejar confirmación
    document.getElementById('confirmDeleteBtn').onclick = async () => {
        try {
            const response = await fetch(`/clients/${id}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                // Eliminar elemento del DOM
                const element = document.querySelector(`tr[data-client-id="${id}"], div[data-client-id="${id}"]`);
                if (element) {
                    element.remove();
                }
                
                // Mostrar toast de éxito
                showToast('Cliente eliminado correctamente', 'success');
            } else {
                throw new Error('Error al eliminar');
            }
        } catch (error) {
            console.error('Error:', error);
            showToast('Error al eliminar el cliente', 'danger');
        } finally {
            modal.hide();
            deleteModal.remove();
        }
    };

    // Mostrar modal
    modal.show();

    // Limpiar modal al cerrar
    deleteModal.addEventListener('hidden.bs.modal', () => {
        deleteModal.remove();
    });
}

// Función para mostrar toasts
function showToast(message, type = 'info') {
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    const toastContainer = document.querySelector('.toast-container') || (() => {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
        return container;
    })();

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    const toast = toastContainer.lastElementChild;
    const bsToast = new bootstrap.Toast(toast);
    
    bsToast.show();

    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}
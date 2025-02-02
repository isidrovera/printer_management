document.addEventListener('DOMContentLoaded', function() {
    const listView = document.getElementById('listView');
    const kanbanView = document.getElementById('kanbanView');
    const listViewBtn = document.getElementById('listViewBtn');
    const kanbanViewBtn = document.getElementById('kanbanViewBtn');
    const searchInput = document.getElementById('searchInput');

    // Función para actualizar los botones de vista
    function updateViewButtons(activeView) {
        if (activeView === 'list') {
            listViewBtn.classList.add('bg-white', 'shadow', 'text-blue-600');
            listViewBtn.classList.remove('text-gray-600');
            kanbanViewBtn.classList.remove('bg-white', 'shadow', 'text-blue-600');
            kanbanViewBtn.classList.add('text-gray-600');
        } else {
            kanbanViewBtn.classList.add('bg-white', 'shadow', 'text-blue-600');
            kanbanViewBtn.classList.remove('text-gray-600');
            listViewBtn.classList.remove('bg-white', 'shadow', 'text-blue-600');
            listViewBtn.classList.add('text-gray-600');
        }
    }

    // Función para cambiar entre vistas
    function switchView(view) {
        if (view === 'list') {
            listView.classList.remove('hidden');
            kanbanView.classList.add('hidden');
        } else {
            kanbanView.classList.remove('hidden');
            listView.classList.add('hidden');
        }
        updateViewButtons(view);
        localStorage.setItem('preferredView', view);
    }

    // Event listeners para los botones de vista
    listViewBtn.addEventListener('click', () => switchView('list'));
    kanbanViewBtn.addEventListener('click', () => switchView('kanban'));

    // Funcionalidad de búsqueda
    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        const rows = document.querySelectorAll('tbody tr');
        const cards = document.querySelectorAll('#kanbanView > div');

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchTerm) ? '' : 'none';
        });

        cards.forEach(card => {
            const text = card.textContent.toLowerCase();
            card.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    });

    // Cargar la vista preferida del usuario
    const preferredView = localStorage.getItem('preferredView') || 'list';
    switchView(preferredView);
});

// Función para eliminar clientes
async function confirmDelete(id) {
    if (confirm('¿Estás seguro de que deseas eliminar este cliente?')) {
        try {
            const response = await fetch(`/clients/${id}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                // Mostrar mensaje de éxito
                const successMessage = document.createElement('div');
                successMessage.className = 'fixed bottom-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg';
                successMessage.textContent = 'Cliente eliminado con éxito';
                document.body.appendChild(successMessage);

                // Eliminar el mensaje después de 3 segundos
                setTimeout(() => {
                    successMessage.remove();
                }, 3000);

                // Actualizar la UI
                const listRow = document.querySelector(`tr[data-client-id="${id}"]`);
                const kanbanCard = document.querySelector(`div[data-client-id="${id}"]`);

                if (listRow) {
                    listRow.style.animation = 'fadeOut 0.3s ease';
                    setTimeout(() => listRow.remove(), 300);
                }
                if (kanbanCard) {
                    kanbanCard.style.animation = 'fadeOut 0.3s ease';
                    setTimeout(() => kanbanCard.remove(), 300);
                }

                // Recargar la página después de 0.5 segundos
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            } else {
                // Mostrar mensaje de error
                const errorMessage = document.createElement('div');
                errorMessage.className = 'fixed bottom-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg';
                errorMessage.textContent = data.error || 'Error al eliminar el cliente';
                document.body.appendChild(errorMessage);

                // Eliminar el mensaje después de 3 segundos
                setTimeout(() => {
                    errorMessage.remove();
                }, 3000);
            }
        } catch (error) {
            console.error('Error:', error);
            // Mostrar mensaje de error
            const errorMessage = document.createElement('div');
            errorMessage.className = 'fixed bottom-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg';
            errorMessage.textContent = 'Error al eliminar el cliente';
            document.body.appendChild(errorMessage);

            // Eliminar el mensaje después de 3 segundos
            setTimeout(() => {
                errorMessage.remove();
            }, 3000);
        }
    }
}

// Agregar estilos de animación
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(-10px); }
    }
`;
document.head.appendChild(style);

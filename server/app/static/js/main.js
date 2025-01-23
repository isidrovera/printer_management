
function confirmDelete(type, id) {
    if (confirm('¿Está seguro de eliminar este ' + type + '?')) {
        fetch(`/api/v1/${type}s/${id}`, {
            method: 'DELETE'
        }).then(() => window.location.reload());
    }
}
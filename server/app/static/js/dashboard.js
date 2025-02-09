document.addEventListener('DOMContentLoaded', function() {
    // Animación de entrada para las tarjetas
    const cards = document.querySelectorAll('.card');
    
    function showCards() {
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.style.animation = `fadeInUp 0.5s ease ${index * 0.1}s forwards`;
                card.classList.add('show');
            }, index * 100);
        });
    }

    // Iniciar animaciones al cargar
    showCards();

    // Animación del icono de configuración
    const cogIcon = document.querySelector('.fa-cog');
    if (cogIcon) {
        let rotation = 0;
        setInterval(() => {
            rotation += 360;
            cogIcon.style.transform = `rotate(${rotation}deg)`;
            cogIcon.style.transition = 'transform 2s ease';
        }, 3000);
    }

    // Animación de la campana
    const bellIcon = document.querySelector('.fa-bell');
    if (bellIcon) {
        setInterval(() => {
            bellIcon.style.animation = 'ringBell 0.5s ease';
            setTimeout(() => {
                bellIcon.style.animation = 'none';
            }, 500);
        }, 5000);
    }

    // Efecto hover para iconos en las tarjetas
    const cardIcons = document.querySelectorAll('.icon-circle i');
    cardIcons.forEach(icon => {
        icon.addEventListener('mouseover', function() {
            this.style.transform = 'scale(1.2) rotate(5deg)';
        });

        icon.addEventListener('mouseout', function() {
            this.style.transform = 'scale(1)';
        });
    });

    // Efecto ripple para los enlaces
    const cardLinks = document.querySelectorAll('.card-link');
    cardLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const ripple = document.createElement('div');
            ripple.classList.add('ripple');
            
            const rect = link.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            link.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });

    // Observador de intersección para animaciones al hacer scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('show');
            }
        });
    }, {
        threshold: 0.1
    });

    cards.forEach(card => {
        observer.observe(card);
    });

    // Funciones para obtener estadísticas
    async function getClientStats() {
        try {
            const response = await fetch('/api/v1/clients/stats');
            return await response.json();
        } catch (error) {
            console.error('Error obteniendo estadísticas de clientes:', error);
            return { total: 0 };
        }
    }

    async function getAgentStats() {
        try {
            const response = await fetch('/api/v1/agents/stats');
            return await response.json();
        } catch (error) {
            console.error('Error obteniendo estadísticas de agentes:', error);
            return { total: 0, online: 0 };
        }
    }

    async function getTunnelStats() {
        try {
            const response = await fetch('/api/v1/tunnels/stats');
            return await response.json();
        } catch (error) {
            console.error('Error obteniendo estadísticas de túneles:', error);
            return { total: 0, active: 0 };
        }
    }

    async function getPrinterStats() {
        try {
            const response = await fetch('/api/v1/printers/stats');
            return await response.json();
        } catch (error) {
            console.error('Error obteniendo estadísticas de impresoras:', error);
            return { total: 0, online: 0 };
        }
    }

    // Función para actualizar todas las estadísticas
    function updateCardValue(cardTitle, value) {
        document.querySelectorAll('.card').forEach(card => {
            if (card.textContent.includes(cardTitle)) {
                const valueElement = card.querySelector('h2, .counter, [data-value]');
                if (valueElement) {
                    if (typeof value === 'number') {
                        updateCounter(valueElement, value);
                    } else {
                        valueElement.textContent = value;
                    }
                }
            }
        });
    }

    // Función para animar contador
    function updateCounter(element, newValue) {
        const currentValue = parseInt(element.textContent) || 0;
        if (currentValue === newValue) return;

        const increment = (newValue - currentValue) / 20;
        let current = currentValue;

        const animation = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= newValue) || (increment < 0 && current <= newValue)) {
                element.textContent = newValue;
                clearInterval(animation);
            } else {
                element.textContent = Math.round(current);
            }
        }, 50);
    }

    // Función principal para cargar y actualizar estadísticas
    async function loadDashboardStats() {
        try {
            const [clientStats, agentStats, tunnelStats, printerStats] = await Promise.all([
                getClientStats(),
                getAgentStats(),
                getTunnelStats(),
                getPrinterStats()
            ]);

            // Actualizar cada sección
            updateCardValue('Total Clientes', clientStats.total || 0);
            updateCardValue('Agentes Online', `${agentStats.online || 0} / ${agentStats.total || 0}`);
            updateCardValue('Túneles Activos', `${tunnelStats.active || 0} / ${tunnelStats.total || 0}`);
            updateCardValue('Impresoras', `${printerStats.online || 0} / ${printerStats.total || 0}`);

        } catch (error) {
            console.error('Error al cargar estadísticas:', error);
        }
    }

    // Cargar estadísticas iniciales
    loadDashboardStats();

    // Actualizar cada 30 segundos
    setInterval(loadDashboardStats, 30000);

    // Event listeners para elementos interactivos
    document.querySelectorAll('.nav-icons i').forEach(icon => {
        icon.addEventListener('click', function() {
            this.classList.add('clicked');
            setTimeout(() => {
                this.classList.remove('clicked');
            }, 200);
        });
    });

    // Función para modo oscuro (opcional)
    function toggleDarkMode() {
        document.body.classList.toggle('dark-mode');
    }
});
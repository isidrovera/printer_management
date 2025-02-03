# server/app/core/logging.py
import logging
import sys

# Configuración básica del logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Salida a consola
        # logging.FileHandler('app.log')  # Opcional: salida a archivo
    ]
)

# Logger principal de la aplicación
logger = logging.getLogger(__name__)

def get_logger(name):
    """
    Obtiene un logger configurado para un módulo específico.
    
    :param name: Nombre del módulo
    :return: Logger configurado
    """
    return logging.getLogger(name)
# agent/app/core/message_queue.py
import asyncio
from dataclasses import dataclass
from typing import Any, Callable
from enum import IntEnum
import logging

logger = logging.getLogger(__name__)

class MessagePriority(IntEnum):
    HIGH = 0    # Comandos de instalación, creación de túneles
    MEDIUM = 1  # Comandos de escaneo
    LOW = 2     # Actualizaciones periódicas, heartbeats

@dataclass
class PrioritizedMessage:
    priority: MessagePriority
    message: Any
    timestamp: float

class MessageQueue:
    def __init__(self):
        self.queue = asyncio.PriorityQueue()
        self._processing = False
        
    async def put(self, priority: MessagePriority, message: Any):
        """Añade un mensaje a la cola con la prioridad especificada"""
        await self.queue.put((
            priority.value,
            PrioritizedMessage(
                priority=priority,
                message=message,
                timestamp=asyncio.get_event_loop().time()
            )
        ))
        
    async def process_messages(self, handler: Callable):
        """Procesa mensajes de la cola usando el handler proporcionado"""
        self._processing = True
        try:
            while self._processing:
                try:
                    _, message = await self.queue.get()
                    processing_delay = asyncio.get_event_loop().time() - message.timestamp
                    
                    if processing_delay > 5.0:  # Si el retraso es mayor a 5 segundos
                        logger.warning(
                            f"Mensaje con prioridad {message.priority.name} "
                            f"procesado con retraso de {processing_delay:.2f} segundos"
                        )
                    
                    await handler(message.message)
                    self.queue.task_done()
                except Exception as e:
                    logger.error(f"Error procesando mensaje: {e}")
                    continue
        finally:
            self._processing = False
            
    def stop(self):
        """Detiene el procesamiento de mensajes"""
        self._processing = False
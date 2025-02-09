# server/app/services/tunnel_service.py
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..db.models.tunnel import Tunnel
from ..db.models.agent import Agent
from ..schemas.tunnel import TunnelCreate
from ..api.v1.endpoints.websocket import manager
import logging

logger = logging.getLogger(__name__)

class TunnelService:
   def __init__(self, db: Session):
       self.db = db

   async def create_tunnel(self, tunnel_data: TunnelCreate) -> dict:
        """Crea un nuevo túnel SSH."""
        try:
            logger.info(f"Iniciando creación de túnel con datos: {tunnel_data}")
            
            tunnel_id = f"{tunnel_data.remote_host}:{tunnel_data.remote_port}-{tunnel_data.local_port}"
            logger.debug(f"ID del túnel generado: {tunnel_id}")
            
            # Verificar túnel existente
            existing_tunnel = self.db.query(Tunnel).filter(
                Tunnel.tunnel_id == tunnel_id
            ).first()

            if existing_tunnel:
                logger.info(f"Encontrado túnel existente: {tunnel_id} con estado: {existing_tunnel.status}")
                if existing_tunnel.status != 'closed':
                    logger.warning(f"Túnel activo encontrado con ID: {tunnel_id}")
                    return JSONResponse(
                        status_code=400,
                        content={"detail": f"Ya existe un túnel activo con ID: {tunnel_id}"}
                    )
                else:
                    # Si el túnel existe pero está cerrado, lo actualizamos
                    logger.info(f"Actualizando túnel cerrado: {tunnel_id}")
                    existing_tunnel.status = 'creating'
                    existing_tunnel.agent_id = tunnel_data.agent_id
                    self.db.commit()
                    tunnel = existing_tunnel
            else:
                # Crear nuevo túnel si no existe
                logger.debug("Creando nuevo registro de túnel en la base de datos")
                tunnel = Tunnel(
                    agent_id=tunnel_data.agent_id,
                    tunnel_id=tunnel_id,
                    remote_host=tunnel_data.remote_host,
                    remote_port=tunnel_data.remote_port,
                    local_port=tunnel_data.local_port,
                    status='creating',
                    description=tunnel_data.description
                )
                
                self.db.add(tunnel)
                self.db.commit()
                self.db.refresh(tunnel)
                logger.info(f"Nuevo túnel creado en BD con ID: {tunnel.id}")

            # Verificar agente
            agent = self.db.query(Agent).filter(Agent.id == tunnel_data.agent_id).first()
            if not agent:
                logger.error(f"Agente no encontrado con ID: {tunnel_data.agent_id}")
                return JSONResponse(
                    status_code=404,
                    content={"detail": "Agente no encontrado"}
                )

            logger.debug(f"Verificando conexión WebSocket para agente: {agent.token}")
            websocket = manager.agent_connections.get(agent.token)
            if not websocket:
                logger.error(f"Agente {agent.token} no está conectado")
                return JSONResponse(
                    status_code=503,
                    content={"detail": "Agente no está conectado"}
                )

            # Preparar comando para el agente
            command = {
                'type': 'create_tunnel',
                'tunnel_id': tunnel_id,
                'ssh_host': tunnel_data.ssh_host,
                'ssh_port': tunnel_data.ssh_port,
                'username': tunnel_data.username,
                'password': tunnel_data.password,
                'remote_host': tunnel_data.remote_host,
                'remote_port': tunnel_data.remote_port,
                'local_port': tunnel_data.local_port
            }

            # Enviar comando al agente
            logger.debug(f"Enviando comando al agente: {command}")
            try:
                await websocket.send_json(command)
                logger.info(f"Comando enviado exitosamente al agente {agent.token}")
            except Exception as e:
                logger.error(f"Error enviando comando al agente: {str(e)}")
                tunnel.status = 'error'
                self.db.commit()
                raise HTTPException(
                    status_code=500,
                    detail=f"Error enviando comando al agente: {str(e)}"
                )

            return tunnel

        except Exception as e:
            logger.error(f"Error inesperado creando túnel: {str(e)}")
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={"detail": f"Error interno del servidor: {str(e)}"}
            )

   async def close_tunnel(self, tunnel_id: str) -> dict:
       """Cierra un túnel SSH existente."""
       try:
           logger.info(f"Iniciando cierre de túnel con ID: {tunnel_id}")

           # Buscar el túnel
           tunnel = self.db.query(Tunnel).filter(Tunnel.tunnel_id == tunnel_id).first()
           if not tunnel:
               logger.warning(f"Túnel no encontrado: {tunnel_id}")
               return JSONResponse(
                   status_code=404,
                   content={"detail": "Túnel no encontrado"}
               )

           # Verificar agente
           agent = self.db.query(Agent).filter(Agent.id == tunnel.agent_id).first()
           if not agent:
               logger.error(f"Agente no encontrado para túnel: {tunnel_id}")
               return JSONResponse(
                   status_code=404,
                   content={"detail": "Agente no encontrado"}
               )

           # Verificar conexión WebSocket
           logger.debug(f"Verificando conexión WebSocket para agente: {agent.token}")
           websocket = manager.agent_connections.get(agent.token)
           
           if not websocket:
               logger.warning(f"Agente {agent.token} no está conectado, marcando túnel como cerrado")
               tunnel.status = 'closed'
               self.db.commit()
               return JSONResponse(
                   status_code=200,
                   content={"message": "Túnel marcado como cerrado (agente desconectado)"}
               )

           # Enviar comando de cierre al agente
           try:
               command = {
                   'type': 'close_tunnel',
                   'tunnel_id': tunnel_id
               }
               logger.debug(f"Enviando comando de cierre: {command}")
               await websocket.send_json(command)
               logger.info(f"Comando de cierre enviado al agente {agent.token}")
           except Exception as e:
               logger.error(f"Error enviando comando de cierre: {str(e)}")
               # Aún así marcamos el túnel como cerrado
               tunnel.status = 'closed'
               self.db.commit()
               return JSONResponse(
                   status_code=200,
                   content={"message": "Túnel marcado como cerrado (error en comunicación)"}
               )

           # Actualizar estado del túnel
           tunnel.status = 'closed'
           self.db.commit()
           logger.info(f"Túnel {tunnel_id} cerrado exitosamente")

           return JSONResponse(
               status_code=200,
               content={"message": "Túnel cerrado correctamente"}
           )

       except Exception as e:
           logger.error(f"Error inesperado cerrando túnel: {str(e)}")
           return JSONResponse(
               status_code=500,
               content={"detail": f"Error interno del servidor: {str(e)}"}
           )

   async def list_tunnels(self) -> list:
       """Lista todos los túneles."""
       try:
           logger.debug("Obteniendo lista de túneles")
           tunnels = self.db.query(Tunnel).all()
           logger.info(f"Se encontraron {len(tunnels)} túneles")
           return tunnels
       except Exception as e:
           logger.error(f"Error listando túneles: {str(e)}")
           raise HTTPException(
               status_code=500,
               detail=f"Error obteniendo lista de túneles: {str(e)}"
           )

    # Agregar este método a tu clase TunnelService en tunnel_service.py

   async def get_tunnel_info(self, tunnel_id: str) -> dict:
        """Obtiene información detallada de un túnel específico."""
        try:
            logger.debug(f"Buscando túnel con ID: {tunnel_id}")
            tunnel = self.db.query(Tunnel).filter(Tunnel.tunnel_id == tunnel_id).first()
            
            if not tunnel:
                logger.warning(f"Túnel no encontrado: {tunnel_id}")
                return None
                
            # Obtener información del agente asociado
            agent = self.db.query(Agent).filter(Agent.id == tunnel.agent_id).first()
            
            # Construir respuesta con información detallada
            tunnel_info = {
                "tunnel_id": tunnel.tunnel_id,
                "status": tunnel.status,
                "remote_host": tunnel.remote_host,
                "remote_port": tunnel.remote_port,
                "local_port": tunnel.local_port,
                "description": tunnel.description,
                "created_at": tunnel.created_at.isoformat() if tunnel.created_at else None,
                "agent": {
                    "hostname": agent.hostname if agent else None,
                    "username": agent.username if agent else None,
                    "ip_address": agent.ip_address if agent else None
                }
            }
            
            logger.info(f"Información del túnel {tunnel_id} recuperada exitosamente")
            return tunnel_info
            
        except Exception as e:
            logger.error(f"Error recuperando información del túnel: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error obteniendo información del túnel: {str(e)}"
            )

   async def get_count(self) -> int:
       """Obtiene el número total de túneles."""
       try:
           logger.debug("Contando total de túneles")
           count = self.db.query(Tunnel).count()
           logger.info(f"Total de túneles encontrados: {count}")
           return count
       except Exception as e:
           logger.error(f"Error obteniendo conteo de túneles: {str(e)}")
           return 0

   async def get_count_by_status(self, status: str) -> int:
       """Obtiene el número de túneles por estado específico."""
       try:
           logger.debug(f"Contando túneles con estado: {status}")
           count = self.db.query(Tunnel).filter(Tunnel.status == status).count()
           logger.info(f"Total de túneles con estado {status}: {count}")
           return count
       except Exception as e:
           logger.error(f"Error obteniendo conteo de túneles por estado: {str(e)}")
           return 0

   async def list_tunnels(self):
        """
        Lista todos los túneles
        """
        try:
            result = await self.db.execute(select(Tunnel))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error al listar túneles: {e}")
            return []

   async def get_all(self):
        """
        Obtiene todos los túneles (método usado por el dashboard)
        """
        try:
            result = await self.db.execute(select(Tunnel))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error al obtener todos los túneles: {e}")
            return []
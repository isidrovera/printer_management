#server/app/services/agent_service.py
from fastapi import HTTPException
from ..db.models import Agent, Client
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_
import json
import socket
from app.core.logging import logger
class AgentStatus:
    ONLINE = "online"
    OFFLINE = "offline"  # PC apagada normalmente
    CONNECTION_LOST = "connection_lost"  # PC encendida pero sin conexión
    ERROR = "error"

class AgentService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.HEARTBEAT_TIMEOUT = 300  # 5 minutos para marcar conexión perdida
        self.OFFLINE_TIMEOUT = 600    # 10 minutos para marcar offline

    async def check_agent_status(self, agent: Agent) -> str:
        """
        Verifica el estado real del agente basado en su último heartbeat
        """
        if not agent.updated_at:
            return AgentStatus.OFFLINE
                
        time_since_update = (datetime.utcnow() - agent.updated_at).total_seconds()
        
        if time_since_update < self.HEARTBEAT_TIMEOUT:
            return AgentStatus.ONLINE
        elif time_since_update < self.OFFLINE_TIMEOUT:
            return AgentStatus.CONNECTION_LOST
        else:
            return AgentStatus.OFFLINE

    async def update_agents_status(self):
        """
        Actualiza el estado de todos los agentes basado en su último heartbeat
        """
        try:
            current_time = datetime.utcnow()
            heartbeat_threshold = current_time - timedelta(seconds=self.HEARTBEAT_TIMEOUT)
            offline_threshold = current_time - timedelta(seconds=self.OFFLINE_TIMEOUT)

            # Primero actualizamos los que perdieron conexión
            agents_connection_lost = self.db.query(Agent).filter(
                and_(
                    Agent.is_active == True,
                    Agent.status == AgentStatus.ONLINE,
                    Agent.updated_at < heartbeat_threshold,
                    Agent.updated_at >= offline_threshold
                )
            ).all()

            for agent in agents_connection_lost:
                agent.status = AgentStatus.CONNECTION_LOST
                logger.info(f"Agente {agent.id} marcado como connection_lost")

            # Luego los que están realmente offline
            agents_offline = self.db.query(Agent).filter(
                and_(
                    Agent.is_active == True,
                    Agent.status.in_([AgentStatus.ONLINE, AgentStatus.CONNECTION_LOST]),
                    Agent.updated_at < offline_threshold
                )
            ).all()

            for agent in agents_offline:
                agent.status = AgentStatus.OFFLINE
                logger.info(f"Agente {agent.id} marcado como offline")

            self.db.commit()
        except Exception as e:
            logger.error(f"Error actualizando estados de agentes: {str(e)}")
    async def register_shutdown(self, agent_token: str) -> bool:
        """Registra un apagado normal del agente"""
        try:
            agent = await self.get_agent_by_token(agent_token)
            if agent:
                agent.status = AgentStatus.OFFLINE
                agent.updated_at = datetime.utcnow()
                self.db.commit()
                logger.info(f"Agente {agent_token} registrado como apagado normal")
                return True
            return False
        except Exception as e:
            logger.error(f"Error registrando apagado del agente: {str(e)}")
            return False
    async def register_agent(
        self, 
        client_token: str,
        hostname: str,
        username: str,
        ip_address: str,
        device_type: str,
        system_info: dict
    ) -> Agent:
        """Registra un nuevo agente o actualiza uno existente"""
        try:
            client = self.db.query(Client).filter(Client.token == client_token).first()
            if not client:
                raise HTTPException(status_code=401, detail="Invalid client token")
            
            # Buscar agente existente
            existing_agent = self.db.query(Agent).filter(
                Agent.hostname == hostname,
                Agent.client_id == client.id,
                Agent.is_active == True
            ).first()

            current_time = datetime.utcnow()

            if existing_agent:
                # Actualizar agente existente
                existing_agent.username = username
                existing_agent.ip_address = ip_address
                existing_agent.device_type = device_type
                existing_agent.system_info = system_info
                existing_agent.cpu_info = system_info.get("CPU")
                existing_agent.memory_info = system_info.get("Memoria")
                existing_agent.disk_info = system_info.get("Discos")
                existing_agent.network_info = system_info.get("Red")
                existing_agent.gpu_info = system_info.get("Tarjetas Gráficas")
                existing_agent.battery_info = system_info.get("Batería")
                existing_agent.disk_usage = system_info.get("Espacio en Disco")
                existing_agent.status = 'online'  # Asegurar estado online
                existing_agent.updated_at = current_time
                existing_agent.last_heartbeat = current_time
                
                agent = existing_agent
            else:
                # Crear nuevo agente
                agent = Agent(
                    client_id=client.id,
                    token=Agent.generate_token(),
                    hostname=hostname,
                    username=username,
                    ip_address=ip_address,
                    device_type=device_type,
                    system_info=system_info,
                    cpu_info=system_info.get("CPU"),
                    memory_info=system_info.get("Memoria"),
                    disk_info=system_info.get("Discos"),
                    network_info=system_info.get("Red"),
                    gpu_info=system_info.get("Tarjetas Gráficas"),
                    battery_info=system_info.get("Batería"),
                    disk_usage=system_info.get("Espacio en Disco"),
                    status='online',
                    is_active=True,
                    created_at=current_time,
                    updated_at=current_time,
                    last_heartbeat=current_time
                )
                self.db.add(agent)

            self.db.commit()
            self.db.refresh(agent)
            logger.info(f"Agente {'actualizado' if existing_agent else 'registrado'} exitosamente: {agent.hostname}")
            return agent

        except Exception as e:
            logger.error(f"Error en register_agent: {str(e)}")
            self.db.rollback()
            raise

    async def validate_agent(self, agent_token: str) -> Optional[Agent]:
        """Valida si un agente existe y está activo en la base de datos"""
        try:
            agent = self.db.query(Agent).filter(
                Agent.token == agent_token,
                Agent.is_active == True
            ).first()
            
            if agent:
                current_time = datetime.utcnow()
                prev_status = agent.status
                
                # Si el agente estaba offline o connection_lost, registrar reconexión
                if prev_status in [AgentStatus.OFFLINE, AgentStatus.CONNECTION_LOST]:
                    agent.last_reconnection = current_time
                    logger.info(f"Agente {agent_token} reconectado después de estar {prev_status}")
                
                agent.last_heartbeat = current_time
                agent.updated_at = current_time
                agent.status = AgentStatus.ONLINE
                
                self.db.commit()
                    
            return agent
        except Exception as e:
            logger.error(f"Error validando agente: {str(e)}")
            return None
    async def get_agent_history(self, agent_id: int) -> Dict:
        """Obtiene el historial de estados del agente"""
        try:
            agent = await self.get_agent(agent_id)
            if not agent:
                return {}
                
            return {
                "last_startup": agent.last_startup,
                "last_shutdown": agent.last_shutdown,
                "last_reconnection": agent.last_reconnection,
                "last_heartbeat": agent.last_heartbeat,
                "current_status": agent.status,
                "uptime": (datetime.utcnow() - agent.last_startup).total_seconds() if agent.last_startup else None
            }
        except Exception as e:
            logger.error(f"Error obteniendo historial del agente: {str(e)}")
            return {}

    async def update_status(self, agent_token: str, status: str) -> Optional[Agent]:
        """Actualiza el estado del agente"""
        try:
            agent = await self.get_agent_by_token(agent_token)
            if not agent:
                return None

            current_time = datetime.utcnow()
            prev_status = agent.status

            # Validar que el cambio de estado sea permitido
            if status == AgentStatus.OFFLINE and prev_status != AgentStatus.OFFLINE:
                # Registrar timestamp del último apagado
                agent.last_shutdown = current_time
                
            elif status == AgentStatus.ONLINE and prev_status == AgentStatus.OFFLINE:
                # Registrar timestamp del último inicio
                agent.last_startup = current_time

            agent.status = status
            agent.updated_at = current_time
            
            self.db.commit()
            self.db.refresh(agent)
            
            logger.info(f"Estado del agente {agent_token} actualizado: {prev_status} -> {status}")
            return agent
        except Exception as e:
            logger.error(f"Error actualizando estado del agente: {str(e)}")
            return None

    def get_all(self) -> List[Agent]:
        """Obtiene la lista de agentes"""
        try:
            return self.db.query(Agent)\
                        .filter(Agent.is_active == True)\
                        .all()
        except Exception as e:
            logger.error(f"Error obteniendo todos los agentes: {str(e)}")
            return []

    async def get_agent(self, agent_id: int) -> Optional[Agent]:
        """Obtiene un agente específico por ID y actualiza su estado"""
        agent = self.db.query(Agent)\
                      .filter(Agent.id == agent_id, Agent.is_active == True)\
                      .first()
        
        if agent:
            agent.status = await self.check_agent_status(agent)
            self.db.commit()
            
        return agent

    async def update_agent(self, agent_id: int, data: Dict) -> Optional[Agent]:
        """Actualiza los datos de un agente y su heartbeat"""
        agent = await self.get_agent(agent_id)
        if not agent:
            return None
        
        # Actualizar solo si el agente está activo según el heartbeat
        current_status = await self.check_agent_status(agent)
        if current_status == 'online':
            for key, value in data.items():
                if hasattr(agent, key) and key != 'status':  # No actualizar status directamente
                    setattr(agent, key, value)
            
            current_time = datetime.utcnow()
            agent.updated_at = current_time
            agent.last_heartbeat = current_time
            
            self.db.commit()
            self.db.refresh(agent)
            
        return agent

    async def delete_agent(self, agent_id: int) -> bool:
        """Desactiva un agente en la base de datos"""
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
        
        agent.is_active = False
        agent.status = 'offline'
        agent.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    async def get_drivers(self) -> List[Dict]:
        """Obtiene la lista de drivers disponibles"""
        return []

    async def get_agent_by_token(self, token: str) -> Optional[Agent]:
        """Obtiene un agente usando su token y verifica su estado"""
        agent = self.db.query(Agent)\
                      .filter(Agent.token == token, Agent.is_active == True)\
                      .first()
                      
        if agent:
            agent.status = await self.check_agent_status(agent)
            self.db.commit()
            
        return agent

    async def heartbeat(self, agent_token: str) -> bool:
        """Actualiza el heartbeat del agente y su estado"""
        try:
            agent = await self.get_agent_by_token(agent_token)
            if not agent:
                logger.warning(f"Heartbeat recibido de agente no registrado: {agent_token}")
                return False

            # Actualizar heartbeat y estado
            current_time = datetime.utcnow()
            agent.last_heartbeat = current_time
            agent.updated_at = current_time
            
            # Solo actualizar a online si no estaba offline por apagado normal
            if agent.status != AgentStatus.OFFLINE:
                agent.status = AgentStatus.ONLINE
            
            self.db.commit()
            logger.debug(f"Heartbeat actualizado para agente {agent_token}")
            return True
        except Exception as e:
            logger.error(f"Error en heartbeat del agente: {str(e)}")
            return False

    def count_by_status(self) -> Dict[str, int]:
        """Obtiene conteo de agentes por estado"""
        try:
            counts = {
                "total": 0,
                "online": 0,
                "offline": 0
            }
            
            agents = self.get_all()
            counts["total"] = len(agents)
            
            for agent in agents:
                if agent.status == AgentStatus.ONLINE:
                    counts["online"] += 1
                elif agent.status == AgentStatus.OFFLINE:
                    counts["offline"] += 1
                    
            return counts
        except Exception as e:
            logger.error(f"Error contando agentes por estado: {str(e)}")
            return {
                "total": 0,
                "online": 0,
                "offline": 0
            }    

    async def _update_agent_info(self):
        """Actualiza la información del sistema y el estado del agente"""
        try:
            new_system_info = await self.system_info.get_system_info()
            try:
                new_ip = socket.gethostbyname(socket.gethostname())
            except Exception as e:
                new_ip = "0.0.0.0"
                logger.error(f"Error al obtener la IP: {e}")

            update_data = {
                "agent_token": settings.AGENT_TOKEN,
                "system_info": new_system_info,
                "ip_address": new_ip,
                "last_heartbeat": datetime.utcnow()
            }

            logger.debug(f"Enviando actualización del agente al servidor: {json.dumps(update_data, indent=4)}")

            async with aiohttp.ClientSession() as session:
                async with session.put(f"{settings.SERVER_URL}/api/v1/agents/update", json=update_data) as response:
                    if response.status == 200:
                        logger.info("Agente actualizado con éxito en el servidor.")
                    else:
                        data = await response.json()
                        logger.error(f"Error al actualizar agente: {data}")

        except Exception as e:
            logger.error(f"Error en la actualización del agente: {e}")
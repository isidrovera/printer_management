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

class AgentService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.HEARTBEAT_TIMEOUT = 300  # 5 minutos en segundos

    async def check_agent_status(self, agent: Agent) -> str:
        """
        Verifica el estado real del agente basado en su último heartbeat
        """
        if not agent.updated_at:
            return "offline"
            
        time_since_update = (datetime.utcnow() - agent.updated_at).total_seconds()
        return "online" if time_since_update < self.HEARTBEAT_TIMEOUT else "offline"

    async def update_agents_status(self):
        """
        Actualiza el estado de todos los agentes basado en su último heartbeat
        """
        try:
            timeout_threshold = datetime.utcnow() - timedelta(seconds=self.HEARTBEAT_TIMEOUT)
            agents_to_update = self.db.query(Agent).filter(
                and_(
                    Agent.is_active == True,
                    Agent.status == 'online',
                    Agent.updated_at < timeout_threshold
                )
            ).all()

            for agent in agents_to_update:
                agent.status = 'offline'
                logger.info(f"Agente {agent.id} marcado como offline por inactividad")

            self.db.commit()
        except Exception as e:
            logger.error(f"Error actualizando estados de agentes: {str(e)}")

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
        agent = self.db.query(Agent).filter(
            Agent.token == agent_token,
            Agent.is_active == True
        ).first()
        
        if agent:
            # Actualizar estado y timestamps al validar el agente
            current_time = datetime.utcnow()
            agent.last_heartbeat = current_time
            agent.updated_at = current_time
            agent.status = 'online'  # Forzar estado online al validar
            self.db.commit()
                
        return agent

    async def update_status(self, agent_token: str, status: str) -> Optional[Agent]:
        """Actualiza el estado del agente solo si está activo"""
        agent = await self.validate_agent(agent_token)
        if agent:
            current_status = await self.check_agent_status(agent)
            if current_status == 'online':
                agent.status = status
                agent.updated_at = datetime.utcnow()
                self.db.commit()
                self.db.refresh(agent)
            return agent
        return None

    async def get_agents(self, skip: int = 0, limit: int = 100) -> List[Agent]:
        """Obtiene todos los agentes registrados y actualiza sus estados"""
        await self.update_agents_status()
        agents = self.db.query(Agent)\
                      .filter(Agent.is_active == True)\
                      .offset(skip)\
                      .limit(limit)\
                      .all()
        
        # Actualizar el estado de cada agente basado en su último heartbeat
        for agent in agents:
            agent.status = await self.check_agent_status(agent)
        
        self.db.commit()
        return agents

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
                return False

            # Actualizar heartbeat y estado
            current_time = datetime.utcnow()
            agent.last_heartbeat = current_time
            agent.updated_at = current_time
            agent.status = 'online'  # Asegurar que el estado sea online
            
            self.db.commit()
            logger.info(f"Heartbeat recibido y estado actualizado para agente {agent_token}")
            return True
        except Exception as e:
            logger.error(f"Error en heartbeat del agente: {str(e)}")
            return False

    async def get_count(self) -> int:
        """Obtiene el número total de agentes activos"""
        try:
            return self.db.query(Agent).filter(Agent.is_active == True).count()
        except Exception as e:
            logger.error(f"Error obteniendo conteo de agentes: {str(e)}")
            return 0

    async def get_count_by_status(self, status: str) -> int:
        """Obtiene el número de agentes por estado, actualizando previamente los estados"""
        try:
            await self.update_agents_status()  # Actualizar estados antes de contar
            return self.db.query(Agent)\
                .filter(Agent.status == status, Agent.is_active == True)\
                .count()
        except Exception as e:
            logger.error(f"Error obteniendo conteo de agentes por estado: {str(e)}")
            return 0

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
#server/app/services/agent_service.py
from fastapi import HTTPException
from ..db.models import Agent, Client
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
import json
import socket
class AgentService:
    def __init__(self, db_session: Session):
        self.db = db_session

    async def register_agent(
        self, 
        client_token: str,
        hostname: str,
        username: str,
        ip_address: str,
        device_type: str,
        system_info: dict
    ) -> Agent:
        """Registra un nuevo agente en la base de datos"""
        client = self.db.query(Client).filter(Client.token == client_token).first()
        if not client:
            raise HTTPException(status_code=401, detail="Invalid client token")
        
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
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    async def validate_agent(self, agent_token: str) -> Optional[Agent]:
        """Valida si un agente existe y está activo en la base de datos"""
        return self.db.query(Agent).filter(
            Agent.token == agent_token,
            Agent.is_active == True
        ).first()

    async def update_status(self, agent_token: str, status: str) -> Optional[Agent]:
        """Actualiza el estado del agente (online/offline)"""
        agent = await self.validate_agent(agent_token)
        if agent:
            agent.status = status
            agent.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(agent)
            return agent
        return None

    async def get_agents(self, skip: int = 0, limit: int = 100) -> List[Agent]:
        """Obtiene todos los agentes registrados"""
        return self.db.query(Agent)\
                      .filter(Agent.is_active == True)\
                      .offset(skip)\
                      .limit(limit)\
                      .all()

    async def get_agent(self, agent_id: int) -> Optional[Agent]:
        """Obtiene un agente específico por ID"""
        return self.db.query(Agent)\
                      .filter(Agent.id == agent_id, Agent.is_active == True)\
                      .first()

    async def update_agent(self, agent_id: int, data: Dict) -> Optional[Agent]:
        """Actualiza los datos de un agente si existe"""
        agent = await self.get_agent(agent_id)
        if not agent:
            return None
        
        for key, value in data.items():
            if hasattr(agent, key):
                setattr(agent, key, value)
        
        agent.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(agent)
        return agent

    async def delete_agent(self, agent_id: int) -> bool:
        """Desactiva un agente en la base de datos"""
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
        
        agent.is_active = False
        agent.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    async def get_drivers(self) -> List[Dict]:
        """
        Obtiene la lista de drivers disponibles
        Implementar según necesidades
        """
        return []

    async def get_agent_by_token(self, token: str) -> Optional[Agent]:
        """Obtiene un agente usando su token"""
        return self.db.query(Agent)\
                      .filter(Agent.token == token, Agent.is_active == True)\
                      .first()
    async def _update_agent_info(self):
        """Obtiene la información actualizada del sistema y la envía al servidor si hay cambios."""
        try:
            new_system_info = await self.system_info.get_system_info()

            # 🔍 Obtener la IP correctamente en cualquier sistema operativo
            try:
                new_ip = socket.gethostbyname(socket.gethostname())  # ✅ Método confiable multiplataforma
            except Exception as e:
                new_ip = "0.0.0.0"  # En caso de error, se usa una IP por defecto
                logger.error(f"🚨 Error al obtener la IP: {e}")

            update_data = {
                "agent_token": settings.AGENT_TOKEN,
                "system_info": new_system_info,
                "ip_address": new_ip
            }

            logger.debug(f"🆕 Enviando actualización del agente al servidor: {json.dumps(update_data, indent=4)}")

            async with aiohttp.ClientSession() as session:
                async with session.put(f"{settings.SERVER_URL}/api/v1/agents/update", json=update_data) as response:
                    data = await response.json()
                    if response.status == 200:
                        logger.info(f"✅ Agente actualizado con éxito en el servidor.")
                    else:
                        logger.error(f"❌ Error al actualizar agente: {data}")

        except Exception as e:
            logger.error(f"🚨 Error en la actualización del agente: {e}")
            
    async def get_count(self) -> int:
        """Obtiene el número total de agentes."""
        try:
            return self.db.query(Agent).count()
        except Exception as e:
            logger.error(f"Error obteniendo conteo de agentes: {str(e)}")
            return 0

    async def get_count_by_status(self, status: str) -> int:
        """Obtiene el número de agentes por estado."""
        try:
            return self.db.query(Agent).filter(Agent.status == status).count()
        except Exception as e:
            logger.error(f"Error obteniendo conteo de agentes por estado: {str(e)}")
            return 0
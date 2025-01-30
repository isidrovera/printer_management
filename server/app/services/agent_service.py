from fastapi import HTTPException
from ..db.models import Agent, Client
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
import json

class AgentService:
    def __init__(self, db_session: Session):
        self.db = db_session

    async def register_or_update_agent(
        self,
        client_token: str,
        hostname: str,
        username: str,
        ip_address: str,
        device_type: str,
        system_info: dict
    ) -> Agent:
        """Registra o actualiza un agente con toda su información del sistema"""
        client = self.db.query(Client).filter(Client.token == client_token).first()
        if not client:
            raise HTTPException(status_code=401, detail="Invalid client token")

        existing_agent = self.db.query(Agent).filter(
            Agent.hostname == hostname,
            Agent.client_id == client.id
        ).first()

        if existing_agent:
            print(f"🔄 Actualizando información del agente {hostname}...")
            return await self.update_agent_info(existing_agent, system_info, ip_address)
        else:
            print(f"🆕 Registrando nuevo agente: {hostname}")
            return await self.create_agent(client.id, hostname, username, ip_address, device_type, system_info)

    async def create_agent(
        self, client_id: int, hostname: str, username: str, ip_address: str, device_type: str, system_info: dict
    ) -> Agent:
        """Crea un nuevo agente en la base de datos"""
        agent = Agent(
            client_id=client_id,
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
        print(f"✅ Agente {hostname} registrado correctamente.")
        return agent

    async def update_agent_info(self, agent: Agent, new_system_info: dict, new_ip: str) -> Agent:
        """Actualiza la información del agente si se detectan cambios"""
        updated = False

        # Verificar si la IP cambió
        if agent.ip_address != new_ip:
            print(f"⚠️ IP actualizada: {agent.ip_address} → {new_ip}")
            agent.ip_address = new_ip
            updated = True

        # Verificar si `system_info` cambió
        existing_info = json.loads(agent.system_info) if isinstance(agent.system_info, str) else agent.system_info
        if existing_info != new_system_info:
            print(f"🔄 Actualizando información del sistema para {agent.hostname}...")
            agent.system_info = new_system_info
            agent.cpu_info = new_system_info.get("CPU")
            agent.memory_info = new_system_info.get("Memoria")
            agent.disk_info = new_system_info.get("Discos")
            agent.network_info = new_system_info.get("Red")
            agent.gpu_info = new_system_info.get("Tarjetas Gráficas")
            agent.battery_info = new_system_info.get("Batería")
            agent.disk_usage = new_system_info.get("Espacio en Disco")
            updated = True

        if updated:
            agent.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(agent)
            print(f"✅ Agente {agent.hostname} actualizado con éxito.")
        else:
            print(f"⚡ No se detectaron cambios en {agent.hostname}.")

        return agent

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

    async def delete_agent(self, agent_id: int) -> bool:
        """Elimina (desactiva) un agente en la base de datos"""
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
        
        agent.is_active = False
        agent.updated_at = datetime.utcnow()
        self.db.commit()
        print(f"❌ Agente {agent.hostname} eliminado.")
        return True

    async def get_agent_by_token(self, token: str) -> Optional[Agent]:
        """Obtiene un agente usando su token"""
        return self.db.query(Agent)\
                      .filter(Agent.token == token, Agent.is_active == True)\
                      .first()

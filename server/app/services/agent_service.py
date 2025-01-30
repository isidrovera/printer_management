from fastapi import HTTPException
from ..db.models import Agent, Client
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
import json

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
    async def update_agent_info(self, agent: Agent, new_system_info: dict, new_ip: str) -> Agent:
        """Actualiza la información del agente si hay cambios en cualquier campo."""
        updated = False

        # Campos a verificar individualmente
        fields_to_check = {
            "ip_address": new_ip,
            "cpu_info": new_system_info.get("CPU"),
            "memory_info": new_system_info.get("Memoria"),
            "disk_info": new_system_info.get("Discos"),
            "network_info": new_system_info.get("Red"),
            "gpu_info": new_system_info.get("Tarjetas Gráficas"),
            "battery_info": new_system_info.get("Batería"),
            "disk_usage": new_system_info.get("Espacio en Disco"),
        }

        # Comparar cada campo y actualizar si hay diferencias
        for field, new_value in fields_to_check.items():
            existing_value = getattr(agent, field)

            if isinstance(existing_value, str):  # Si está almacenado como JSON string, lo convertimos
                try:
                    existing_value = json.loads(existing_value)
                except json.JSONDecodeError:
                    pass  # Si no es JSON válido, lo dejamos como está

            if existing_value != new_value:  # Si hay diferencia, actualizamos el campo
                print(f"🔄 Cambio detectado en {field}: {existing_value} → {new_value}")
                setattr(agent, field, new_value)
                updated = True

        # Verificar si `system_info` cambió completamente
        existing_system_info = json.loads(agent.system_info) if isinstance(agent.system_info, str) else agent.system_info
        if existing_system_info != new_system_info:
            print(f"🔄 Cambio detectado en 'system_info', actualizando toda la información.")
            agent.system_info = new_system_info
            updated = True

        # Si hubo algún cambio, actualizar la base de datos
        if updated:
            agent.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(agent)
            print(f"✅ Información de {agent.hostname} actualizada correctamente en la base de datos.")
        else:
            print(f"⚡ No se detectaron cambios en {agent.hostname}, no se actualiza.")

        return agent

# server/app/db/models/tunnel.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from ..db.base_class import Base

class Tunnel(Base):
    __tablename__ = "tunnels"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    tunnel_id = Column(String, unique=True, index=True)
    remote_host = Column(String)
    remote_port = Column(Integer)
    local_port = Column(Integer)
    status = Column(String)  # 'creating', 'active', 'error', 'closed'
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    agent = relationship("Agent", back_populates="tunnels")
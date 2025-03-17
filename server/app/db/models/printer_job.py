# server/app/db/models/printer_job.py
from server.app.db.base import BaseModel
from sqlalchemy import Column, String, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship

class PrinterJob(BaseModel):
    __tablename__ = 'printer_jobs'
    
    agent_id = Column(Integer, ForeignKey('agents.id'))
    printer_id = Column(Integer, ForeignKey('printers.id'))  # Agregar esta línea
    printer_driver_id = Column(Integer, ForeignKey('printer_drivers.id'))
    status = Column(String, nullable=False)  # pending, installing, completed, failed
    ip_address = Column(String, nullable=False)
    error_message = Column(String)
    installation_details = Column(JSON)
    
    agent = relationship("Agent", back_populates="printer_jobs")
    printer_driver = relationship("PrinterDriver")
    printer = relationship("Printer", back_populates="printer_jobs")
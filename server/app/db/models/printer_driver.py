# server/app/db/models/printer_driver.py
from app.db.base import Base
from sqlalchemy import Column, String, LargeBinary, Integer  # Incluye Integer

class PrinterDriver(Base):
    __tablename__ = "printer_drivers"

    id = Column(Integer, primary_key=True, index=True)  # ID único
    manufacturer = Column(String, nullable=False)  # Nombre del fabricante
    model = Column(String, nullable=False)  # Modelo de la impresora    
    driver_filename = Column(String, nullable=False)  # Nombre original del archivo
    description = Column(String, nullable=True)  # Descripción opcional

# server/app/db/models/printer_driver.py
from app.db.base import BaseModel
from sqlalchemy import Column, String, LargeBinary

class PrinterDriver(Base):
    __tablename__ = "printer_drivers"

    id = Column(Integer, primary_key=True, index=True)
    manufacturer = Column(String, nullable=False)
    model = Column(String, nullable=False)
    driver_file = Column(LargeBinary, nullable=False)  # Archivo binario (ZIP)
    driver_filename = Column(String, nullable=False)  # Nombre original del archivo
    description = Column(String, nullable=True)
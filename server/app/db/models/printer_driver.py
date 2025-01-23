# server/app/db/models/printer_driver.py
from app.db.base import BaseModel
from sqlalchemy import Column, String, LargeBinary

class PrinterDriver(BaseModel):
    __tablename__ = 'printer_drivers'
    
    manufacturer = Column(String, nullable=False)
    model = Column(String, nullable=False)
    driver_file = Column(LargeBinary, nullable=False)
    inf_path = Column(String, nullable=False)
    description = Column(String)

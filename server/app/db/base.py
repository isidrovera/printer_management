# server/app/db/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, event, MetaData, text, func
from sqlalchemy import inspect as sa_inspect

metadata = MetaData()
Base = declarative_base(metadata=metadata)

@event.listens_for(Base.metadata, 'after_create')
def create_ddl(target, connection, **kw):
    inspector = sa_inspect(connection)
    tables = inspector.get_table_names()
    
    with connection.begin() as transaction:
        for table in tables:
            sql = text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS driver_inf VARCHAR")
            try:
                connection.execute(sql)
            except Exception as e:
                print(f"Error adding column to {table}: {e}")

class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
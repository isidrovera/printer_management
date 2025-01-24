# server/app/db/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, event, MetaData, text, func
from sqlalchemy import inspect as sa_inspect

metadata = MetaData()
Base = declarative_base(metadata=metadata)

@event.listens_for(Base.metadata, 'after_create')
def sync_columns(target, connection, **kw):
    inspector = sa_inspect(connection)
    tables = inspector.get_table_names()
    
    for table_name in tables:
        # Obtener columnas existentes en la tabla
        existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
        
        # Obtener columnas definidas en el modelo
        table = target.tables.get(table_name)  # Esto devuelve un objeto Table o None
        if table is None:  # Verificación explícita
            continue
        
        model_columns = {col.name for col in table.columns}
        
        # Agregar columnas que faltan
        for col in model_columns - existing_columns:
            sql = text(f"ALTER TABLE {table_name} ADD COLUMN {col} {table.columns[col].type}")
            try:
                connection.execute(sql)
                print(f"Columna '{col}' agregada a la tabla '{table_name}'")
            except Exception as e:
                print(f"Error agregando columna '{col}' a '{table_name}': {e}")
        
        # Eliminar columnas que ya no están en el modelo
        for col in existing_columns - model_columns:
            if col not in ['id', 'created_at', 'updated_at']:  # Ignorar columnas base
                sql = text(f"ALTER TABLE {table_name} DROP COLUMN {col}")
                try:
                    connection.execute(sql)
                    print(f"Columna '{col}' eliminada de la tabla '{table_name}'")
                except Exception as e:
                    print(f"Error eliminando columna '{col}' de '{table_name}': {e}")


class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

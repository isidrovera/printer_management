# server/app/db/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, event, MetaData, func

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=naming_convention)
Base = declarative_base(metadata=metadata)

@event.listens_for(Base.metadata, 'after_create')
def create_ddl(target, connection, **kw):
    tables = connection.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'").fetchall()
    for table in tables:
        for model in Base._decl_class_registry.values():
            if hasattr(model, '__tablename__') and model.__tablename__ == table[0]:
                for column in model.__table__.columns:
                    connection.execute(f"ALTER TABLE {table[0]} ADD COLUMN IF NOT EXISTS {column.name} {column.type}")

class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
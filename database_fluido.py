from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:ObOURtLuyxFOFbiOmfJfheYCuSLFJaGv@switchback.proxy.rlwy.net:23507/railway"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50))
    correo = Column(String(100), unique=True)
    password = Column(String(255))
    fecha_registro = Column(DateTime, server_default=func.now())

class Resultado(Base):
    __tablename__ = "resultados"
    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String)
    ejercicio = Column(Integer)
    respuesta = Column(String)
    puntaje = Column(Float)
    estado = Column(String)
    fecha = Column(DateTime)

Base.metadata.create_all(bind=engine)

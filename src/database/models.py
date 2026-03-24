from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime
from src.database.database import Base, engine

class Transacao(Base):
    __tablename__ = 'transacoes'

    id = Column(Integer, primary_key=True, index=True)
    valor = Column(Float, nullable=False)
    categoria = Column(String, nullable=False, index=True) 
    descricao = Column(String, nullable=False)             
    data = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)
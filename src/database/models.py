from sqlalchemy import Column, Integer, Float, String, DateTime, BigInteger
from datetime import datetime
from src.database.database import Base, engine
from datetime import timedelta

def obter_hora_brasilia():
    return datetime.utcnow() - timedelta(hours=3)

class Transacao(Base):
    __tablename__ = 'transacoes'

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    valor = Column(Float, nullable=False)
    categoria = Column(String, nullable=False, index=True) 
    descricao = Column(String, nullable=False)             
    data = Column(DateTime, default=obter_hora_brasilia)
    tipo = Column(String)
    
class Renda(Base):
    __tablename__ = 'rendas'

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, index=True)
    descricao = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    dia_recebimento = Column(Integer, nullable=True)  
    tipo = Column(String, default="dinheiro")        

class Meta(Base):
    __tablename__ = "metas"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, index=True)
    categoria = Column(String, index=True)
    valor_limite = Column(Float)

Base.metadata.create_all(bind=engine)
from sqlalchemy import Column, Integer, Float, String, DateTime, BigInteger, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database.database import Base, engine
from datetime import timedelta

def obter_hora_brasilia():
    return datetime.utcnow() - timedelta(hours=3)

class Transacao(Base):
    __tablename__ = "transacoes"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, index=True)
    valor = Column(Float)
    categoria = Column(String)
    descricao = Column(String)
    tipo = Column(String) 
    data = Column(DateTime)
    
    metodo_pagamento = Column(String, default="debito") # 'debito', 'pix', 'credito'
    cartao_id = Column(Integer, ForeignKey('cartoes.id'), nullable=True)
    parcela_atual = Column(Integer, nullable=True)
    total_parcelas = Column(Integer, nullable=True)
    fatura_paga = Column(Boolean, default=False)
    vinculo_compra = Column(String, nullable=True) 
    
    cartao = relationship("Cartao")

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

class Cartao(Base):
    __tablename__ = "cartoes"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, index=True)
    nome = Column(String, index=True) # Ex: Nubank, Itaú
    dia_fechamento = Column(Integer)
    dia_vencimento = Column(Integer)
    limite = Column(Float, nullable=True)

Base.metadata.create_all(bind=engine)
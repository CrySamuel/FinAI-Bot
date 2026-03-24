from sqlalchemy.orm import Session
from src.database.models import Transacao, Renda

def criar_transacao(db: Session, valor: float, categoria: str, descricao: str):
    """Salva um novo gasto no banco de dados"""
    nova_transacao = Transacao(
        valor=valor,
        categoria=categoria,
        descricao=descricao
    )
    
    db.add(nova_transacao)
    db.commit()
    db.refresh(nova_transacao)
    
    return nova_transacao

def listar_transacoes(db: Session):
    return db.query(Transacao).all()

def criar_renda(db: Session, descricao: str, valor: float, dia_recebimento: int, tipo: str = "dinheiro"):
    nova_renda = Renda(
        descricao=descricao,
        valor=valor,
        dia_recebimento=dia_recebimento,
        tipo=tipo
    )
    
    db.add(nova_renda)
    db.commit()
    db.refresh(nova_renda)
    
    return nova_renda

def listar_rendas(db: Session):
    return db.query(Renda).all()
from sqlalchemy.orm import Session
from src.database.models import Transacao

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
    """Busca todos os gastos registrados"""
    return db.query(Transacao).all()
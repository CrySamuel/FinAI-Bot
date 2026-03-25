from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime
from src.database.models import Transacao, Renda
import pandas as pd
import os

def criar_transacao(db: Session, valor: float, categoria: str, descricao: str, tipo: str, chat_id: int, data: datetime = None):
    nova_transacao = Transacao(
        valor=valor,
        categoria=categoria,
        descricao=descricao,
        tipo=tipo,
        chat_id=chat_id,
        data=data
    )
    db.add(nova_transacao)
    db.commit()
    db.refresh(nova_transacao)
    return nova_transacao

def listar_transacoes(db: Session, chat_id: int):
    return db.query(Transacao).filter(Transacao.chat_id == chat_id).all()

def criar_renda(db: Session, descricao: str, valor: float, dia_recebimento: int, chat_id: int, tipo: str = "dinheiro"):
    nova_renda = Renda(
        descricao=descricao,
        valor=valor,
        dia_recebimento=dia_recebimento,
        tipo=tipo,
        chat_id=chat_id 
    )
    
    db.add(nova_renda)
    db.commit()
    db.refresh(nova_renda)
    return nova_renda

def listar_rendas(db: Session, chat_id: int):
    return db.query(Renda).filter(Renda.chat_id == chat_id).all()

def obter_resumo_mes(db: Session, chat_id: int):
    saidas = db.query(func.sum(Transacao.valor)).filter(
        Transacao.tipo == "saida",
        Transacao.chat_id == chat_id 
    ).scalar() or 0.0
    
    entradas = db.query(func.sum(Renda.valor)).filter(
        Renda.chat_id == chat_id 
    ).scalar() or 0.0
    
    return {"despesas": saidas, "receitas": entradas}

def gerar_relatorio_excel(db: Session, chat_id: int, caminho_arquivo: str = "relatorio_mensal.xlsx"):
    gastos = db.query(Transacao).filter(Transacao.chat_id == chat_id).all()
    
    if not gastos:
        return False 
        
    dados = []
    for g in gastos:
        dados.append({
            "ID": g.id,
            "Data": g.data.strftime("%d/%m/%Y"),
            "Hora": g.data.strftime("%H:%M"),
            "Categoria": g.categoria,
            "Descrição": g.descricao,
            "Valor (R$)": round(g.valor, 2)
        })
        
    df = pd.DataFrame(dados)
    df.to_excel(caminho_arquivo, index=False, engine='openpyxl')
    
    return True

def listar_ultimas_transacoes(db: Session, chat_id: int, limite: int = 5):
    # BLINDADO
    return db.query(Transacao).filter(Transacao.chat_id == chat_id).order_by(Transacao.data.desc()).limit(limite).all()

def apagar_transacao(db: Session, transacao_id: int, chat_id: int):
    # SEGURANÇA: Só acha a transação se ela pertencer ao mesmo chat que pediu para apagar
    transacao = db.query(Transacao).filter(
        Transacao.id == transacao_id, 
        Transacao.chat_id == chat_id
    ).first()
    
    if transacao:
        db.delete(transacao)
        db.commit()
        return True
    return False

def obter_analise_categorias(db: Session, chat_id: int):
    resultados = db.query(
        Transacao.categoria, 
        func.sum(Transacao.valor).label('total')
    ).filter(
        Transacao.tipo == "saida",
        Transacao.chat_id == chat_id 
    ).group_by(Transacao.categoria).all()
    
    return [{"categoria": r[0], "total": r[1]} for r in resultados]

def filtrar_gastos_por_termo(db: Session, termo: str, chat_id: int):
    termo_busca = f"%{termo}%"
    transacoes = db.query(Transacao).filter(
        Transacao.chat_id == chat_id, 
        (Transacao.categoria.ilike(termo_busca) | Transacao.descricao.ilike(termo_busca))
    ).order_by(Transacao.data.desc()).all()
    
    total = sum(t.valor for t in transacoes)
    return total, transacoes
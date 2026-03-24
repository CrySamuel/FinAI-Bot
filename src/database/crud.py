from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime
from src.database.models import Transacao, Renda

import pandas as pd
import os

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

def obter_resumo_mes(db: Session):
    mes_atual = datetime.utcnow().month
    ano_atual = datetime.utcnow().year


    total_renda = db.query(func.sum(Renda.valor)).scalar() or 0.0

    total_gasto = db.query(func.sum(Transacao.valor)).filter(
        extract('month', Transacao.data) == mes_atual,
        extract('year', Transacao.data) == ano_atual
    ).scalar() or 0.0

    saldo = total_renda - total_gasto

    return {
        "receitas": total_renda,
        "despesas": total_gasto,
        "saldo": saldo
    }

def gerar_relatorio_excel(db: Session, caminho_arquivo: str = "relatorio_mensal.xlsx"):
    gastos = db.query(Transacao).all()
    
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
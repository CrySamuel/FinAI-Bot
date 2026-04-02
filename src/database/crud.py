import uuid
import calendar
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, date, timedelta
from src.database.models import Transacao, Renda, Meta, Cartao
import pandas as pd

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
    hoje = date.today()
    
    saidas_mes = db.query(func.sum(Transacao.valor)).filter(
        Transacao.tipo == "saida",
        Transacao.chat_id == chat_id,
        extract('month', Transacao.data) == hoje.month,
        extract('year', Transacao.data) == hoje.year
    ).scalar() or 0.0
    
    entradas_fixas = db.query(func.sum(Renda.valor)).filter(Renda.chat_id == chat_id).scalar() or 0.0
    entradas_pontuais_mes = db.query(func.sum(Transacao.valor)).filter(
        Transacao.tipo == "entrada",
        Transacao.chat_id == chat_id,
        extract('month', Transacao.data) == hoje.month,
        extract('year', Transacao.data) == hoje.year
    ).scalar() or 0.0
    receitas_mes_atual = entradas_fixas + entradas_pontuais_mes

    todas_entradas_pontuais = db.query(func.sum(Transacao.valor)).filter(
        Transacao.tipo == "entrada", 
        Transacao.chat_id == chat_id
    ).scalar() or 0.0
    
    todas_saidas = db.query(func.sum(Transacao.valor)).filter(
        Transacao.tipo == "saida", 
        Transacao.chat_id == chat_id,
        Transacao.metodo_pagamento != "credito" 
    ).scalar() or 0.0
    
    saldo_bancario = (entradas_fixas + todas_entradas_pontuais) - todas_saidas
    
    return {
        "despesas_mes": saidas_mes, 
        "receitas_totais": receitas_mes_atual, 
        "saldo_bancario": saldo_bancario
    }

def gerar_relatorio_excel(db: Session, chat_id: int, dias: int = None, caminho_arquivo: str = "relatorio_mensal.xlsx"):
    query = db.query(Transacao).filter(Transacao.chat_id == chat_id)
    
    if dias is not None:
        data_limite = datetime.now() - timedelta(days=dias)
        query = query.filter(Transacao.data >= data_limite)
    
    gastos = query.order_by(Transacao.data.desc()).all()
    
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
            "Valor (R$)": round(g.valor, 2),
            "Tipo": g.tipo.capitalize()
        })
        
    df = pd.DataFrame(dados)
    df.to_excel(caminho_arquivo, index=False, engine='openpyxl')
    
    return True

def listar_ultimas_transacoes(db: Session, chat_id: int, limite: int = 5):
    return db.query(Transacao).filter(Transacao.chat_id == chat_id).order_by(Transacao.id.desc()).limit(limite).all()

def apagar_transacao(db: Session, transacao_id: int, chat_id: int):
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
    
def verificar_meta_categoria(db: Session, chat_id: int, categoria: str, data_ref=None):
    from src.database.models import Transacao, Meta
    from datetime import date
    from sqlalchemy import func, extract

    meta = db.query(Meta).filter(
        Meta.chat_id == chat_id, 
        Meta.categoria.ilike(categoria) 
    ).first()

    if not meta:
        return None

    if data_ref is None:
        data_ref = date.today()

    total_gasto = db.query(func.sum(Transacao.valor)).filter(
        Transacao.chat_id == chat_id,
        Transacao.categoria.ilike(categoria),
        extract('month', Transacao.data) == data_ref.month,
        extract('year', Transacao.data) == data_ref.year
    ).scalar() or 0.0

    restante = meta.valor_limite - total_gasto
    percentual = (total_gasto / meta.valor_limite) * 100

    return {
        "limite": meta.valor_limite,
        "gasto": total_gasto,
        "restante": restante,
        "percentual": percentual
    }

def listar_metas(db: Session, chat_id: int):
    return db.query(Meta).filter(Meta.chat_id == chat_id).all()

def calcular_meses_futuros(data_base, meses_a_adicionar):
    """Função auxiliar para pular meses corretamente no calendário"""
    mes = data_base.month - 1 + meses_a_adicionar
    ano = data_base.year + mes // 12
    mes = mes % 12 + 1
    dia = data_base.day
    max_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(dia, max_dia))

def registrar_compra_parcelada(db, chat_id, valor_total, categoria, descricao, cartao_nome, parcelas, data_compra):
    
    cartao = db.query(Cartao).filter(Cartao.chat_id == chat_id, Cartao.nome.ilike(cartao_nome)).first()
    if not cartao:
        return False, f"Cartão '{cartao_nome}' não encontrado. Cadastre-o primeiro!"

    valor_parcela = valor_total / parcelas
    id_compra = str(uuid.uuid4())[:8] 

    meses_pulo = 0
    if data_compra.day >= cartao.dia_fechamento:
        meses_pulo = 1

    transacoes_geradas = []
    
    for i in range(parcelas):
        numero_parcela = i + 1
        
        data_fatura_desta_parcela = calcular_meses_futuros(data_compra, meses_pulo + i)
        
        data_cobranca = date(data_fatura_desta_parcela.year, data_fatura_desta_parcela.month, cartao.dia_vencimento)

        nova_transacao = Transacao(
            chat_id=chat_id,
            valor=valor_parcela,
            categoria=categoria,
            descricao=f"{descricao} ({numero_parcela}/{parcelas})",
            tipo="saida",
            data=data_cobranca,
            metodo_pagamento="credito",
            cartao_id=cartao.id,
            parcela_atual=numero_parcela,
            total_parcelas=parcelas,
            fatura_paga=False,
            vinculo_compra=id_compra
        )
        db.add(nova_transacao)
        transacoes_geradas.append(nova_transacao)

    db.commit()
    resumo = {
        "valor_total": valor_total,
        "valor_parcela": valor_parcela,
        "parcelas": parcelas,
        "categoria": categoria,
        "descricao": descricao,
        "cartao": cartao.nome.capitalize()
    }
    
    return True, resumo
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.database.database import SessionLocal
from src.database.crud import obter_resumo_mes, listar_ultimas_transacoes, obter_analise_categorias

import io
import pandas as pd
from datetime import datetime, date
from src.database.models import Transacao 

async def comando_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    teclado = [
        [
            InlineKeyboardButton("💰 Ver Saldo", callback_data="btn_saldo"),
            InlineKeyboardButton("📊 Análise", callback_data="btn_analise")
        ],
        [
            InlineKeyboardButton("🔍 Últimos", callback_data="btn_ultimos"),
            InlineKeyboardButton("📁 Relatório", callback_data="btn_relatorio")
        ],
        [
            InlineKeyboardButton("➕ Adicionar Renda", callback_data="renda_start")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(teclado)
    
    if update.callback_query:
        await update.callback_query.message.edit_text("Painel de Controle FinAI 🤖\nEscolha uma opção:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Painel de Controle FinAI 🤖\nEscolha uma opção:", reply_markup=reply_markup)


async def processar_cliques_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 
    
    escolha = query.data
    chat_id = update.effective_chat.id
    
    if escolha == "btn_saldo":
        db = SessionLocal()
        try:
            resumo = obter_resumo_mes(db, chat_id)
            receitas = resumo["receitas"]
            despesas = resumo["despesas"]
            saldo = receitas - despesas
            
            texto_saldo = (
                "⚖️ *Resumo Financeiro*\n"
                "━━━━━━━━━━━━━━━━\n"
                f"🟢 Entradas: R$ {receitas:.2f}\n"
                f"🔴 Saídas: R$ {despesas:.2f}\n"
                "━━━━━━━━━━━━━━━━\n"
                f"💰 *Saldo Atual: R$ {saldo:.2f}*"
            ).replace('.', ',') 
            
            teclado_voltar = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="btn_voltar")]]
            reply_markup = InlineKeyboardMarkup(teclado_voltar)
            
            await query.edit_message_text(texto_saldo, parse_mode="Markdown", reply_markup=reply_markup)
            
        except Exception as e:
            await query.edit_message_text(f"❌ Erro ao buscar saldo: {e}")
        finally:
            db.close()

    elif escolha == "btn_voltar":
        await comando_menu(update, context)
        
    elif escolha == "btn_analise":
        db = SessionLocal()
        try:
            gastos = obter_analise_categorias(db, chat_id)
            
            if not gastos:
                texto_analise = "📊 Ainda não existem despesas registradas para análise."
            else:
                total_gastos = sum(item["total"] for item in gastos)
                
                texto_analise = "📊 *Análise de Gastos por Categoria*\n━━━━━━━━━━━━━━━━\n"
                
                for item in gastos:
                    categoria = item["categoria"]
                    valor = item["total"]
                    
                    percentual = (valor / total_gastos) * 100
                    valor_formatado = f"{valor:.2f}".replace('.', ',')
                    
                    tamanho_barra = int(percentual / 10)
                    barra = "🟩" * tamanho_barra + "⬜" * (10 - tamanho_barra)
                    
                    texto_analise += f"*{categoria}* - {percentual:.1f}%\n"
                    texto_analise += f"{barra} R$ {valor_formatado}\n\n"
                
                texto_analise += "━━━━━━━━━━━━━━━━\n"
                texto_analise += f"🔴 *Total Gasto:* R$ {f'{total_gastos:.2f}'.replace('.', ',')}"
            
            teclado_voltar = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="btn_voltar")]]
            reply_markup = InlineKeyboardMarkup(teclado_voltar)
            
            await query.edit_message_text(texto_analise, parse_mode="Markdown", reply_markup=reply_markup)
            
        except Exception as e:
            await query.edit_message_text(f"❌ Erro ao gerar análise: {e}")
        finally:
            db.close()

    elif escolha == "btn_ultimos":
        db = SessionLocal()
        try:
            from src.database.models import Transacao, Renda
            
            saidas = db.query(Transacao).filter(Transacao.chat_id == chat_id).order_by(Transacao.id.desc()).limit(5).all()
            entradas = db.query(Renda).filter(Renda.chat_id == chat_id).order_by(Renda.id.desc()).limit(5).all()
            
            movimentacoes = []
            
            for s in saidas:
                movimentacoes.append({
                    "tipo": "saida",
                    "valor": s.valor,
                    "categoria": s.categoria,
                    "descricao": s.descricao,
                    "data": getattr(s, 'data', None)
                })
                
            for e in entradas:
                movimentacoes.append({
                    "tipo": "entrada",
                    "valor": e.valor,
                    "categoria": "Receita/Renda", 
                    "descricao": e.descricao,
                    "data": getattr(e, 'data', None)
                })
                
            movimentacoes.sort(key=lambda x: x["data"].timestamp() if x["data"] else 0, reverse=True)
            
            ultimas = movimentacoes[:5]
            
            if not ultimas:
                texto_ultimos = "🔍 Nenhuma movimentação recente encontrada."
            else:
                texto_ultimos = "🔍 *Últimas 5 Movimentações*\n━━━━━━━━━━━━━━━━\n"
                for m in ultimas:
                    icone = "🔴" if m["tipo"] == "saida" else "🟢"
                    data_formatada = m["data"].strftime("%d/%m") if m["data"] else "N/D"
                    valor_formatado = f"{m['valor']:.2f}".replace('.', ',')
                    
                    texto_ultimos += f"{icone} *{data_formatada}* | {m['categoria']}\n"
                    texto_ultimos += f"    └ R$ {valor_formatado} ({m['descricao']})\n\n"
                    
            teclado_voltar = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="btn_voltar")]]
            reply_markup = InlineKeyboardMarkup(teclado_voltar)
            
            await query.edit_message_text(texto_ultimos, parse_mode="Markdown", reply_markup=reply_markup)
            
        except Exception as e:
            await query.edit_message_text(f"❌ Erro ao buscar últimas movimentações: {e}")
        finally:
            db.close()
    elif escolha == "btn_relatorio":
        await query.edit_message_text("⏳ *Gerando seu relatório completo...*\nUnificando entradas e saídas.", parse_mode="Markdown")
        
        db = SessionLocal()
        try:
            from src.database.models import Transacao, Renda
            
            saidas = db.query(Transacao).filter(Transacao.chat_id == chat_id).all()
            entradas = db.query(Renda).filter(Renda.chat_id == chat_id).all()
            
            if not saidas and not entradas:
                teclado_voltar = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="btn_voltar")]]
                await query.edit_message_text("📭 Nenhuma movimentação encontrada para gerar relatório.", reply_markup=InlineKeyboardMarkup(teclado_voltar))
                return

            dados_unificados = []
            hoje = date.today()
            
            for s in saidas:
                dados_unificados.append({
                    "Data": s.data.date() if s.data else None,
                    "Tipo": "Saída 🔴",
                    "Categoria": s.categoria,
                    "Descrição": s.descricao,
                    "Valor": s.valor * -1  
                })
                
            for e in entradas:
                try:
                    data_fake = date(hoje.year, hoje.month, int(e.dia_recebimento))
                except (ValueError, TypeError):
                    data_fake = hoje

                dados_unificados.append({
                    "Data": data_fake,
                    "Tipo": "Entrada 🟢",
                    "Categoria": "Receita",
                    "Descrição": e.descricao,
                    "Valor": e.valor
                })
            
            df = pd.DataFrame(dados_unificados)
            df['Data'] = pd.to_datetime(df['Data']).dt.date 
            df = df.sort_values(by="Data", ascending=False)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Balanco_FinAI')
                
                worksheet = writer.sheets['Balanco_FinAI']
                
                colunas = {'A': 15, 'B': 15, 'C': 20, 'D': 35, 'E': 15}
                for col, largura in colunas.items():
                    worksheet.column_dimensions[col].width = largura
                
                from openpyxl.styles import Font
                
                for cell in worksheet['E']:
                    if cell.row == 1: continue 
                    
                    cell.number_format = '"R$" #,##0.00'
                    if cell.value and cell.value < 0:
                        cell.font = Font(color="FF0000") 
                    elif cell.value and cell.value > 0:
                        cell.font = Font(color="00B050")

            buffer.seek(0)
            data_hoje = datetime.now().strftime('%d_%m_%Y')
            
            await context.bot.send_document(
                chat_id=chat_id,
                document=buffer,
                filename=f"Relatorio_Completo_{data_hoje}.xlsx",
                caption="✅ *Relatório unificado pronto!*\nAs saídas aparecem em vermelho (negativo) para facilitar o cálculo do saldo no Excel."
            )
            
            teclado_voltar = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="btn_voltar")]]
            await query.edit_message_text("📈 Relatório enviado!", reply_markup=InlineKeyboardMarkup(teclado_voltar))
            
        except Exception as e:
            await query.edit_message_text(f"❌ Erro no Excel: {e}")
        finally:
            db.close()

    elif escolha == "btn_renda":
        await query.message.reply_text("Para adicionar renda, por favor digite o comando /renda")
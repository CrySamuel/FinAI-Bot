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
        teclado_datas = [
            # Colocamos o prefixo "btn_" em todos eles
            [InlineKeyboardButton("📅 Últimos 7 Dias", callback_data="btn_rel_7")],
            [InlineKeyboardButton("📅 Último Mês", callback_data="btn_rel_30")],
            [InlineKeyboardButton("📅 Últimos 3 Meses", callback_data="btn_rel_90")],
            [InlineKeyboardButton("📚 Tudo", callback_data="btn_rel_tudo")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="btn_voltar")]
        ]
        await query.edit_message_text(
            "📅 *Selecione o período do relatório:*", 
            reply_markup=InlineKeyboardMarkup(teclado_datas), 
            parse_mode="Markdown"
        )

    elif escolha.startswith("btn_rel_"):
        await query.edit_message_text("⏳ *Filtrando dados e gerando Excel...*", parse_mode="Markdown")
        
        from datetime import date, timedelta
        import io
        import pandas as pd
        
        hoje = date.today()
        limite_data = None
        
        if escolha == "btn_rel_7":
            limite_data = hoje - timedelta(days=7)
        elif escolha == "btn_rel_30":
            limite_data = hoje - timedelta(days=30)
        elif escolha == "btn_rel_90":
            limite_data = hoje - timedelta(days=90)

        db = SessionLocal()
        try:
            from src.database.models import Transacao, Renda
            
            saidas = db.query(Transacao).filter(Transacao.chat_id == chat_id).all()
            entradas = db.query(Renda).filter(Renda.chat_id == chat_id).all()
            
            dados_unificados = []
            
            for s in saidas:
                data_item = s.data.date() if getattr(s, 'data', None) else hoje
                dados_unificados.append({
                    "Data": data_item,
                    "Tipo": "Saída",
                    "Categoria": s.categoria,
                    "Descrição": s.descricao,
                    "Valor": s.valor * -1
                })
                
            for e in entradas:
                try:
                    data_item = date(hoje.year, hoje.month, int(e.dia_recebimento))
                except (ValueError, TypeError):
                    data_item = hoje
                    
                dados_unificados.append({
                    "Data": data_item,
                    "Tipo": "Entrada",
                    "Categoria": "Receita",
                    "Descrição": e.descricao,
                    "Valor": e.valor
                })

            if limite_data:
                dados_unificados = [item for item in dados_unificados if item["Data"] >= limite_data]

            if not dados_unificados:
                teclado_voltar = [[InlineKeyboardButton("🔙 Voltar aos Períodos", callback_data="btn_relatorio")]]
                await query.edit_message_text(
                    "📭 Nenhuma movimentação encontrada neste período.", 
                    reply_markup=InlineKeyboardMarkup(teclado_voltar)
                )
                return

            df = pd.DataFrame(dados_unificados)
            df = df.sort_values(by="Data", ascending=False)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Relatório FinAI')
                workbook = writer.book
                worksheet = writer.sheets['Relatório FinAI']

                from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
                
                # Definição de Estilos
                header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
                header_font = Font(color="FFFFFF", bold=True, size=12)
                verde_suave = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
                vermelho_suave = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
                cinza_total = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
                
                center_alignment = Alignment(horizontal="center", vertical="center")
                thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), 
                                    top=Side(style='thin'), bottom=Side(style='thin'))

                # 2. Estilizando o Cabeçalho (Linha 1)
                for cell in worksheet[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = center_alignment
                    cell.border = thin_border

                # 3. Loop Único para Estilizar os Dados (Linha 2 em diante)
                for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row):
                    data_cell = row[0]
                    tipo_cell = row[1]
                    valor_cell = row[4]

                    # Formatação de Data e Alinhamento Central
                    data_cell.number_format = 'DD/MM/YYYY'
                    data_cell.alignment = center_alignment
                    tipo_cell.alignment = center_alignment

                    # Lógica de Cores por Tipo (Entrada vs Saída)
                    if "Saída" in str(tipo_cell.value):
                        tipo_cell.fill = vermelho_suave
                        valor_cell.font = Font(color="9C0006", bold=True) # Vermelho escuro
                    else:
                        tipo_cell.fill = verde_suave
                        valor_cell.font = Font(color="006100", bold=True) # Verde escuro
                    
                    # Formatação de Moeda
                    valor_cell.number_format = '"R$" #,##0.00'
                    
                    # Aplica bordas em todas as células da linha
                    for cell in row:
                        cell.border = thin_border

                # 4. Ajuste Automático de Colunas (Inteligente)
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if cell.value:
                                length = len(str(cell.value))
                                if length > max_length: max_length = length
                        except: pass
                    worksheet.column_dimensions[column_letter].width = max_length + 4

                # 5. Linha de Totalizador Final
                total_row = worksheet.max_row + 1
                saldo = df['Valor'].sum()
                
                # Preenche a linha de total com cor de fundo cinza e bordas
                for col_idx in range(1, 6):
                    cell = worksheet.cell(row=total_row, column=col_idx)
                    cell.fill = cinza_total
                    cell.border = thin_border
                
                # Texto e Valor do Saldo
                label_cell = worksheet.cell(row=total_row, column=4, value="SALDO TOTAL:")
                label_cell.font = Font(bold=True)
                label_cell.alignment = Alignment(horizontal="right")
                
                saldo_cell = worksheet.cell(row=total_row, column=5, value=saldo)
                saldo_cell.font = Font(bold=True, color="000000")
                saldo_cell.number_format = '"R$" #,##0.00'

            buffer.seek(0)
            
            # Envio do Documento
            nome_periodo = escolha.replace("btn_rel_", "")
            arquivo_nome = f"Relatorio_FinAI_{nome_periodo}dias.xlsx" if nome_periodo != "tudo" else "Relatorio_FinAI_Completo.xlsx"
            
            await context.bot.send_document(
                chat_id=chat_id,
                document=buffer,
                filename=arquivo_nome,
                caption="✅ *Seu relatório está pronto!*",
                parse_mode="Markdown"
            )
            
            teclado_voltar = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="btn_voltar")]]
            await query.edit_message_text("📈 Relatório enviado com sucesso!", reply_markup=InlineKeyboardMarkup(teclado_voltar))

            buffer.seek(0)
            
            nome_periodo = escolha.replace("btn_rel_", "")
            arquivo_nome = f"Relatorio_FinAI_{nome_periodo}dias.xlsx" if nome_periodo != "tudo" else "Relatorio_FinAI_Completo.xlsx"
            
            await context.bot.send_document(
                chat_id=chat_id,
                document=buffer,
                filename=arquivo_nome,
                caption="✅ *Seu relatório está pronto!*",
                parse_mode="Markdown"
            )
            
            teclado_voltar = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="btn_voltar")]]
            await query.edit_message_text("📈 Relatório enviado com sucesso!", reply_markup=InlineKeyboardMarkup(teclado_voltar))
            
        except Exception as e:
            await query.edit_message_text(f"❌ Erro ao gerar Excel: {e}")
        finally:
            db.close()

    elif escolha == "btn_renda":
        await query.message.reply_text("Para adicionar renda, por favor digite o comando /renda")
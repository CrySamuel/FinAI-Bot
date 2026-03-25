from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, MessageHandler, filters, 
    ConversationHandler, CallbackQueryHandler
)

import os, re
from src.ai.processor import analisar_mensagem_com_ia
from src.database.database import SessionLocal
from src.database.crud import (
    criar_transacao, criar_renda, obter_resumo_mes, gerar_relatorio_excel,
    listar_ultimas_transacoes, apagar_transacao, listar_transacoes,
    obter_analise_categorias, filtrar_gastos_por_termo
)
from src.bot.menu import comando_menu, processar_cliques_menu

from datetime import datetime, timedelta
from telegram import constants

ESCOLHER_TIPO, DIGITAR_VALOR, DIGITAR_DIA = range(3)


async def comando_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Mensagem inicial simpática
    mensagem_boas_vindas = (
        "Olá! Eu sou o FinAI, seu assistente financeiro inteligente. 🤖💸\n\n"
        "Você pode simplesmente me mandar uma mensagem como:\n"
        "🍕 *'Gastei 50 no ifood'*\n"
        "🛒 *'Comprei 300 de mercado no cartão'*\n\n"
        "Ou use o painel abaixo para navegar:"
    )
    await update.message.reply_text(mensagem_boas_vindas, parse_mode="Markdown")
    
    await comando_menu(update, context)

async def comando_comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = (
        "🛠️ *Comandos Disponíveis:*\n\n"
        "🗣️ *Texto Livre:* Apenas digite seu gasto (ex: 'Paguei 20 no ifood') para a IA registrar.\n\n"
        "💵 */renda* - Cadastra seu salário, adiantamento ou benefícios.\n"
        "⚖️ */saldo* - Mostra o balanço do mês atual (Receitas vs Despesas).\n"
        "📊 */relatorio* - Gera uma planilha Excel detalhada com todo o histórico.\n"
        "❓ */comandos* - Mostra esta lista de ajuda.\n"
        "🕒 */ultimos* - Mostra os 5 últimos gastos registrados.\n"
        "🗑️ */apagar [ID]* - Apaga um gasto incorreto usando o ID.\n"
        "💰 */transacoes* - Lista todos os gastos registrados.\n"
        "🍕 */analise* - Mostra a % de gastos por categoria.\n"
        "🔍 */filtro [termo]* - Mostra o total gasto em um local ou categoria específica.\n"
    )
    await update.message.reply_text(mensagem, parse_mode='Markdown')

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
    chat_id = update.effective_chat.id 
    texto_recebido = update.message.text
    mensagem_espera = await update.message.reply_text("Processando... 🧠")
    
    dados_extraidos = analisar_mensagem_com_ia(texto_recebido)
    
    if dados_extraidos and "valor" in dados_extraidos:
        try:
            db = SessionLocal()
            tipo_movimentacao = dados_extraidos.get("tipo", "saida")
            valor = dados_extraidos["valor"]
            valor_formatado = f"{valor:.2f}".replace('.', ',')
            
            data_str = dados_extraidos.get("data")
            if data_str:
                try:
                    data_final = datetime.strptime(data_str, "%Y-%m-%d")
                except ValueError:
                    data_final = datetime.utcnow() - timedelta(hours=3)
            else:
                data_final = datetime.utcnow() - timedelta(hours=3)
            # ---------------------------
            
            if tipo_movimentacao == "entrada":
                dia_recebimento = data_final.day 
                criar_renda(
                    db=db, 
                    descricao=dados_extraidos["descricao"], 
                    valor=valor, 
                    dia_recebimento=dia_recebimento, 
                    chat_id=chat_id, 
                    tipo="extra"
                )
                resposta = (
                    "🤑 *Dinheiro na conta!*\n"
                    f"🏷️ Categoria: {dados_extraidos['categoria']}\n"
                    f"📝 Descrição: {dados_extraidos['descricao']}\n"
                    f"💰 Valor: R$ {valor_formatado}\n"
                    f"📅 Data ref: {data_final.strftime('%d/%m/%Y')}"
                )
            else:
                criar_transacao(
                    db=db, 
                    valor=valor, 
                    categoria=dados_extraidos["categoria"], 
                    descricao=dados_extraidos["descricao"],
                    tipo="saida",
                    chat_id=chat_id,
                    data=data_final # <- Passando a data final para a função!
                )
                resposta = (
                    "✅ *Gasto registrado!*\n"
                    f"🏷️ Categoria: {dados_extraidos['categoria']}\n"
                    f"📝 Descrição: {dados_extraidos['descricao']}\n"
                    f"💰 Valor: R$ {valor_formatado}\n"
                    f"📅 Data: {data_final.strftime('%d/%m/%Y')}"
                )
                
            db.close()
            
            await mensagem_espera.edit_text(resposta, parse_mode="Markdown")            
        
        except Exception as e:
            await mensagem_espera.edit_text(f"❌ Erro ao salvar: {e}")
    else:
        await mensagem_espera.edit_text("❌ Não entendi. Pode reformular?")

async def comando_renda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. Prepara o texto e os botões
    texto = "💸 *Nova Renda!*\nQual é a origem desse dinheiro?"

    teclado = [
        [InlineKeyboardButton("💵 Salário", callback_data="Salário")],
        [InlineKeyboardButton("💸 Adiantamento/Vale", callback_data="Adiantamento")],
        [InlineKeyboardButton("🍔 VR (Refeição)", callback_data="VR")],
        [InlineKeyboardButton("🚌 VT (Transporte)", callback_data="VT")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="Cancelar")]
    ]
    reply_markup = InlineKeyboardMarkup(teclado)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(texto, parse_mode="Markdown", reply_markup=reply_markup) 
    else:

        await update.message.reply_text(texto, parse_mode="Markdown", reply_markup=reply_markup) 
        
    return ESCOLHER_TIPO

async def receber_tipo_renda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    tipo_escolhido = query.data
    
    if tipo_escolhido == "Cancelar":
        await query.edit_message_text("Cadastro de renda cancelado.")
        return ConversationHandler.END
        
    context.user_data['tipo_renda'] = tipo_escolhido 
    
    await query.edit_message_text(text=f"Legal! Você selecionou **{tipo_escolhido}**.\nQual é o valor? (Ex: 2500 ou 2500.50)")
    return DIGITAR_VALOR

async def receber_valor_renda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_valor = update.message.text
    try:
        texto_limpo = texto_valor.replace(".", "")
        texto_limpo = texto_limpo.replace(",", ".")
        
        valor = float(texto_limpo)
        context.user_data['valor_renda'] = valor
        
        await update.message.reply_text("Entendido. E em qual dia do mês ele costuma cair na conta? (Ex: 5, 20)")
        return DIGITAR_DIA
        
    except ValueError:
        await update.message.reply_text("❌ Valor inválido. Digite apenas números (ex: 1500,50 ou 1.500,50):")
        return DIGITAR_VALOR

async def receber_dia_renda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id 
    texto_dia = update.message.text

    numero_encontrado = re.search(r'\d+', texto_dia)
    
    if numero_encontrado:
        dia = int(numero_encontrado.group())

        if 1 <= dia <= 31:
            context.user_data['dia_renda'] = dia
            
            tipo = context.user_data['tipo_renda']
            valor = context.user_data['valor_renda']
            
            categoria_tipo = "beneficio" if tipo in ["VR", "VT"] else "dinheiro"
            
            try:
                db = SessionLocal()
                criar_renda(db, descricao=tipo, valor=valor, dia_recebimento=dia, chat_id=chat_id, tipo=categoria_tipo)
                db.close()
                
                valor_formatado = f"{valor:.2f}".replace('.', ',')
                
                await update.message.reply_text(
                    f"✅ Renda salva com sucesso!\n"
                    f"🏷️ Tipo: {tipo}\n"
                    f"💰 Valor: R$ {valor_formatado}\n"
                    f"📅 Dia de recebimento: {dia}"
                )
                return ConversationHandler.END
            except Exception as e:
                await update.message.reply_text(f"❌ Erro ao salvar no banco: {e}")
                return ConversationHandler.END
                
        else:
            await update.message.reply_text("❌ Dia inválido. Por favor, digite um dia do mês válido entre 1 e 31:")
            return DIGITAR_DIA
            
    else:
        await update.message.reply_text("❌ Não encontrei nenhum número. Digite o dia do recebimento (ex: 5, dia 20):")
        return DIGITAR_DIA
    
async def cancelar_conversa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cadastro cancelado.")
    return ConversationHandler.END

async def comando_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id 
    db = SessionLocal()
    resumo = obter_resumo_mes(db, chat_id)
    db.close()

    receitas = resumo["receitas"]
    despesas = resumo["despesas"]
    saldo = receitas - despesas 

    rec_fmt = f"{receitas:.2f}".replace('.', ',')
    desp_fmt = f"{despesas:.2f}".replace('.', ',')
    saldo_fmt = f"{saldo:.2f}".replace('.', ',')

    mensagem = (
        "📊 *Resumo Financeiro do Mês* 📊\n\n"
        f"📈 *Total Recebido:* R$ {rec_fmt}\n"
        f"📉 *Total Gasto:* R$ {desp_fmt}\n"
        "-------------------------\n"
    )

    if saldo > 0:
        mensagem += f"✅ *Saldo Positivo:* R$ {saldo_fmt}\n\nExcelente! O desafio financeiro segue firme e forte!"
    elif saldo == 0:
        mensagem += f"⚖️ *Saldo Zerado:* R$ 0,00\n\nFique de olho nos próximos gastos."
    else:
        mensagem += f"🚨 *Saldo Negativo:* R$ {saldo_fmt}\n\nSinal vermelho! Hora de segurar as despesas."

    await update.message.reply_text(mensagem, parse_mode='Markdown')

async def comando_relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    mensagem_espera = await update.message.reply_text("Gerando sua planilha de fechamento... 📊 Aguarde um instante.")
    
    db = SessionLocal()
    nome_arquivo = "Fechamento_FinAI.xlsx"
    sucesso = gerar_relatorio_excel(db, chat_id, nome_arquivo)
    db.close()
    
    if sucesso and os.path.exists(nome_arquivo):
        with open(nome_arquivo, 'rb') as documento:
            await update.message.reply_document(
                document=documento,
                filename="Fechamento_Mensal.xlsx",
                caption="Aqui está o seu relatório detalhado de gastos! 📁\nPronto para análise no Excel ou Google Sheets."
            )
        
        os.remove(nome_arquivo)
        await mensagem_espera.delete() 
    else:
        await mensagem_espera.edit_text("❌ Não encontrei nenhum gasto registrado para gerar o relatório.")

async def comando_transacoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db = SessionLocal()
    
    try:
        from src.database.models import Transacao, Renda
        from datetime import date
        
        saidas = db.query(Transacao).filter(Transacao.chat_id == chat_id).all()
        entradas = db.query(Renda).filter(Renda.chat_id == chat_id).all()
        
        if not saidas and not entradas:
            await update.message.reply_text("📭 Nenhuma movimentação encontrada.")
            return

        movimentacoes = []
        hoje = date.today()
        
        for s in saidas:
            data_transacao = s.data.date() if getattr(s, 'data', None) else hoje
            movimentacoes.append({
                "tipo": "saida",
                "valor": s.valor,
                "categoria": s.categoria,
                "descricao": s.descricao,
                "data": data_transacao
            })
            
        for e in entradas:
            try:
                data_renda = date(hoje.year, hoje.month, int(e.dia_recebimento))
            except (ValueError, TypeError):
                data_renda = hoje
                
            movimentacoes.append({
                "tipo": "entrada",
                "valor": e.valor,
                "categoria": "Receita",
                "descricao": e.descricao,
                "data": data_renda
            })
            
        movimentacoes.sort(key=lambda x: x["data"], reverse=True)
        
        ultimas_movimentacoes = movimentacoes[:15]
        
        texto = "📋 *Extrato de Transações*\n━━━━━━━━━━━━━━━━\n"
        
        for m in ultimas_movimentacoes:
            icone = "🔴" if m["tipo"] == "saida" else "🟢"
            data_formatada = m["data"].strftime("%d/%m")
            valor_formatado = f"{m['valor']:.2f}".replace('.', ',')
            
            texto += f"{icone} *{data_formatada}* | {m['categoria']}\n"
            texto += f"    └ R$ {valor_formatado} ({m['descricao']})\n\n"
            
        await update.message.reply_text(texto, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao listar transações: {e}")
    finally:
        db.close()

async def comando_ultimos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id 
    db = SessionLocal()
    ultimos = listar_ultimas_transacoes(db, chat_id)
    db.close()

    if not ultimos:
        await update.message.reply_text("Nenhum gasto registrado ainda.")
        return

    mensagem = "🕒 *Últimos 5 registros:*\n\n"
    for g in ultimos:
        data_formatada = g.data.strftime("%d/%m %H:%M")
        mensagem += f"🔹 *ID {g.id}* | {data_formatada}\n{g.categoria}: {g.descricao} - R$ {g.valor:.2f}\n\n"

    await update.message.reply_text(mensagem, parse_mode='Markdown')

async def comando_apagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id # <-- IDENTIDADE CAPTURADA
    if not context.args:
        await update.message.reply_text("⚠️ Por favor, informe o ID do gasto. Exemplo: /apagar 3")
        return

    try:
        id_para_apagar = int(context.args[0])
        
        db = SessionLocal()
        sucesso = apagar_transacao(db, id_para_apagar, chat_id)
        db.close()

        if sucesso:
            await update.message.reply_text(f"🗑️ O registro de ID {id_para_apagar} foi apagado com sucesso!")
        else:
            await update.message.reply_text(f"❌ Não encontrei nenhum gasto com o ID {id_para_apagar}.")
            
    except ValueError:
        await update.message.reply_text("⚠️ O ID precisa ser um número. Exemplo: /apagar 3")

async def comando_analise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id 
    
    db = SessionLocal()
    categorias = obter_analise_categorias(db, chat_id) 
    resumo = obter_resumo_mes(db, chat_id)
    db.close()
    
    total_gasto = resumo["despesas"]
    
    if total_gasto == 0 or not categorias:
        await update.message.reply_text("📉 Nenhum gasto registrado para analisar.")
        return
        
    mensagem = "📊 *Análise de Gastos (Porcentagem)* 📊\n\n"
    
    categorias_ordenadas = sorted(categorias, key=lambda x: x['total'], reverse=True)
    
    for cat in categorias_ordenadas:
        porcentagem = (cat['total'] / total_gasto) * 100
        valor_fmt = f"{cat['total']:.2f}".replace('.', ',')
        mensagem += f"🔸 *{cat['categoria']}*: {porcentagem:.1f}% (R$ {valor_fmt})\n"
        
    await update.message.reply_text(mensagem, parse_mode='Markdown')

async def comando_filtro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id # <-- IDENTIDADE CAPTURADA
    if not context.args:
        await update.message.reply_text("⚠️ Me diga o que quer buscar. Exemplo: /filtro mercado")
        return
        
    termo = " ".join(context.args)
    
    db = SessionLocal()
    total, transacoes = filtrar_gastos_por_termo(db, termo, chat_id)
    db.close()
    
    if total > 0:
        total_fmt = f"{total:.2f}".replace('.', ',')
        
        mensagem = f"🔍 *Resultado da busca para '{termo}':*\n\n"
        mensagem += f"💰 *Total Gasto:* R$ {total_fmt}\n"
        mensagem += "-------------------------\n📝 *Detalhes:*\n\n"
        
        for t in transacoes:
            data_fmt = t.data.strftime("%d/%m")
            valor_fmt = f"{t.valor:.2f}".replace('.', ',')
            
            mensagem += f"🔸 {data_fmt} - {t.categoria} ({t.descricao}): R$ {valor_fmt}\n"
            
        await update.message.reply_text(mensagem, parse_mode='Markdown')
    else:
        await update.message.reply_text(f"🔍 Nenhum gasto encontrado com a palavra '{termo}'.")
        
def setup_handlers(app):
    app.add_handler(CommandHandler("menu", comando_menu))
    
    app.add_handler(CommandHandler("start", comando_start))
    app.add_handler(CommandHandler("comandos", comando_comandos))
    app.add_handler(CommandHandler("saldo", comando_saldo))
    
    app.add_handler(CommandHandler("relatorio", comando_relatorio))
    app.add_handler(CommandHandler("ultimos", comando_ultimos))
    app.add_handler(CommandHandler("transacoes", comando_transacoes)) 
    app.add_handler(CommandHandler("analise", comando_analise))
    
    app.add_handler(CommandHandler("apagar", comando_apagar))
    app.add_handler(CommandHandler("filtro", comando_filtro))
    
    app.add_handler(CallbackQueryHandler(processar_cliques_menu, pattern="^btn_"))

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('renda', comando_renda),
            CallbackQueryHandler(comando_renda, pattern="^renda_start$") # <-- A CONEXÃO ACONTECE AQUI!
        ],
        states={
            ESCOLHER_TIPO: [CallbackQueryHandler(receber_tipo_renda)],
            DIGITAR_VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_valor_renda)],
            DIGITAR_DIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_dia_renda)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar_conversa)]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem))
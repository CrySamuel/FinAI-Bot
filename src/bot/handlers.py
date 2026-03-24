from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, MessageHandler, filters, 
    ConversationHandler, CallbackQueryHandler
)

import os
from src.ai.processor import analisar_mensagem_com_ia
from src.database.database import SessionLocal
from src.database.crud import criar_transacao, criar_renda, obter_resumo_mes, gerar_relatorio_excel

ESCOLHER_TIPO, DIGITAR_VALOR, DIGITAR_DIA = range(3)


async def comando_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Eu sou o seu Gestor Financeiro com IA. 📊\n\n"
        "Para registrar um gasto, basta me mandar uma mensagem normal (ex: 'Gastei 50 no mercado').\n\n"
        "Para ver tudo o que eu posso fazer, digite /comandos"
    )

async def comando_comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista todas as funcionalidades do bot"""
    mensagem = (
        "🛠️ *Comandos Disponíveis:*\n\n"
        "🗣️ *Texto Livre:* Apenas digite seu gasto (ex: 'Paguei 20 no ifood') para a IA registrar.\n\n"
        "💵 */renda* - Cadastra seu salário, adiantamento ou benefícios.\n"
        "⚖️ */saldo* - Mostra o balanço do mês atual (Receitas vs Despesas).\n"
        "📊 */relatorio* - Gera uma planilha Excel detalhada com todo o histórico.\n"
        "❓ */comandos* - Mostra esta lista de ajuda."
    )
    await update.message.reply_text(mensagem, parse_mode='Markdown')

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_recebido = update.message.text
    mensagem_espera = await update.message.reply_text("Processando gasto... 🧠")
    
    dados_extraidos = analisar_mensagem_com_ia(texto_recebido)
    
    if dados_extraidos and "valor" in dados_extraidos:
        try:
            db = SessionLocal()
            criar_transacao(
                db=db, valor=dados_extraidos["valor"], 
                categoria=dados_extraidos["categoria"], descricao=dados_extraidos["descricao"]
            )
            db.close()
            
            resposta = (
                "✅ Gasto registrado!\n"
                f"🏷️ Categoria: {dados_extraidos['categoria']}\n"
                f"📝 Descrição: {dados_extraidos['descricao']}\n"
                f"💰 Valor: R$ {dados_extraidos['valor']:.2f}"
            )
            await mensagem_espera.edit_text(resposta)
        except Exception as e:
            await mensagem_espera.edit_text(f"❌ Erro ao salvar: {e}")
    else:
        await mensagem_espera.edit_text("❌ Não entendi. Pode reformular?")


async def comando_renda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = [
        [InlineKeyboardButton("💵 Salário", callback_data="Salário")],
        [InlineKeyboardButton("💸 Adiantamento/Vale", callback_data="Adiantamento")],
        [InlineKeyboardButton("🍔 VR (Refeição)", callback_data="VR")],
        [InlineKeyboardButton("🚌 VT (Transporte)", callback_data="VT")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="Cancelar")]
    ]
    reply_markup = InlineKeyboardMarkup(teclado)
    
    await update.message.reply_text(
        "O que você deseja cadastrar no seu orçamento?",
        reply_markup=reply_markup
    )
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
        valor = float(texto_valor.replace(',', '.'))
        context.user_data['valor_renda'] = valor
        
        await update.message.reply_text("Entendido. E em qual dia do mês ele costuma cair na conta? (Ex: 5, 20)")
        return DIGITAR_DIA
    except ValueError:
        await update.message.reply_text("Valor inválido. Digite apenas números (ex: 1500.50):")
        return DIGITAR_VALOR

async def receber_dia_renda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Salva no banco e finaliza a conversa"""
    texto_dia = update.message.text
    try:
        dia = int(texto_dia)
        tipo = context.user_data['tipo_renda']
        valor = context.user_data['valor_renda']
        
        categoria_tipo = "beneficio" if tipo in ["VR", "VT"] else "dinheiro"
        
        db = SessionLocal()
        criar_renda(db, descricao=tipo, valor=valor, dia_recebimento=dia, tipo=categoria_tipo)
        db.close()
        
        await update.message.reply_text(
            f"✅ Renda salva com sucesso!\n"
            f"🏷️ Tipo: {tipo}\n"
            f"💰 Valor: R$ {valor:.2f}\n"
            f"📅 Dia de recebimento: {dia}"
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Dia inválido. Digite apenas o número do dia (ex: 5):")
        return DIGITAR_DIA

async def cancelar_conversa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cadastro cancelado.")
    return ConversationHandler.END

async def comando_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    resumo = obter_resumo_mes(db)
    db.close()

    receitas = resumo["receitas"]
    despesas = resumo["despesas"]
    saldo = resumo["saldo"]

    mensagem = (
        "📊 *Resumo Financeiro do Mês* 📊\n\n"
        f"📈 *Total Recebido:* R$ {receitas:.2f}\n"
        f"📉 *Total Gasto:* R$ {despesas:.2f}\n"
        "-------------------------\n"
    )

    if saldo > 0:
        mensagem += f"✅ *Saldo Positivo:* R$ {saldo:.2f}\n\nExcelente! O desafio de 2026 segue firme e forte!"
    elif saldo == 0:
        mensagem += f"⚖️ *Saldo Zerado:* R$ 0.00\n\nFique de olho nos próximos gastos."
    else:
        mensagem += f"🚨 *Saldo Negativo:* R$ {saldo:.2f}\n\nSinal vermelho! Hora de segurar as despesas."

    await update.message.reply_text(mensagem, parse_mode='Markdown')

async def comando_relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem_espera = await update.message.reply_text("Gerando sua planilha de fechamento... 📊 Aguarde um instante.")
    
    db = SessionLocal()
    nome_arquivo = "Fechamento_FinAI.xlsx"
    sucesso = gerar_relatorio_excel(db, nome_arquivo)
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

def setup_handlers(app):
    app.add_handler(CommandHandler("start", comando_start))
    app.add_handler(CommandHandler("comandos", comando_comandos))
    app.add_handler(CommandHandler("saldo", comando_saldo))
    app.add_handler(CommandHandler("relatorio", comando_relatorio))
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('renda', comando_renda)],
        states={
            ESCOLHER_TIPO: [CallbackQueryHandler(receber_tipo_renda)],
            DIGITAR_VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_valor_renda)],
            DIGITAR_DIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_dia_renda)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar_conversa)]
    )
    
    app.add_handler(conv_handler)
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem))


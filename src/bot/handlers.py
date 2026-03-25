from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, MessageHandler, filters, 
    ConversationHandler, CallbackQueryHandler
)

import os
from src.ai.processor import analisar_mensagem_com_ia
from src.database.database import SessionLocal
from src.database.crud import (
    criar_transacao, criar_renda, obter_resumo_mes, gerar_relatorio_excel,
    listar_ultimas_transacoes, apagar_transacao, listar_transacoes,
    obter_analise_categorias, filtrar_gastos_por_termo
)

from datetime import datetime
from telegram import constants

ESCOLHER_TIPO, DIGITAR_VALOR, DIGITAR_DIA = range(3)


async def comando_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Eu sou o seu Gestor Financeiro com IA. 📊\n\n"
        "Para registrar um gasto, basta me mandar uma mensagem normal (ex: 'Gastei 50 no mercado').\n\n"
        "Para ver tudo o que eu posso fazer, digite /comandos"
    )

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
            
            if tipo_movimentacao == "entrada":
                dia_hoje = datetime.utcnow().day
                # Passando o chat_id para a renda
                criar_renda(
                    db=db, 
                    descricao=dados_extraidos["descricao"], 
                    valor=valor, 
                    dia_recebimento=dia_hoje, 
                    chat_id=chat_id, 
                    tipo="extra"
                )
                resposta = (
                    "🤑 *Dinheiro na conta!*\n"
                    f"🏷️ Categoria: {dados_extraidos['categoria']}\n"
                    f"📝 Descrição: {dados_extraidos['descricao']}\n"
                    f"💰 Valor: R$ {valor_formatado}"
                )
            else:
                # Passando o chat_id para o gasto
                criar_transacao(
                    db=db, 
                    valor=valor, 
                    categoria=dados_extraidos["categoria"], 
                    descricao=dados_extraidos["descricao"],
                    tipo="saida",
                    chat_id=chat_id
                )
                resposta = (
                    "✅ *Gasto registrado!*\n"
                    f"🏷️ Categoria: {dados_extraidos['categoria']}\n"
                    f"📝 Descrição: {dados_extraidos['descricao']}\n"
                    f"💰 Valor: R$ {valor_formatado}"
                )
                
            db.close()
            await mensagem_espera.edit_text(f"✅ Gasto salvo! Categoria: {dados_extraidos['categoria']}")            
        
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
    chat_id = update.effective_chat.id # <-- IDENTIDADE CAPTURADA
    texto_dia = update.message.text
    try:
        dia = int(texto_dia)
        tipo = context.user_data['tipo_renda']
        valor = context.user_data['valor_renda']
        
        categoria_tipo = "beneficio" if tipo in ["VR", "VT"] else "dinheiro"
        
        db = SessionLocal()
        # Passando o chat_id na criação da renda mensal
        criar_renda(db, descricao=tipo, valor=valor, dia_recebimento=dia, chat_id=chat_id, tipo=categoria_tipo)
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
    chat_id = update.effective_chat.id # <-- IDENTIDADE CAPTURADA
    db = SessionLocal()
    resumo = obter_resumo_mes(db, chat_id)
    db.close()

    receitas = resumo["receitas"]
    despesas = resumo["despesas"]
    saldo = receitas - despesas # <-- CÁLCULO CORRIGIDO!

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
    chat_id = update.effective_chat.id # <-- IDENTIDADE CAPTURADA
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

async def comando_transacoe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id # <-- IDENTIDADE CAPTURADA
    db = SessionLocal()
    transacoes = listar_transacoes(db, chat_id)
    db.close()
    if not transacoes:
        await update.message.reply_text("Nenhum gasto registrado ainda.")
        return
    
    mensagem = "📋 *Lista de Gastos Registrados:*\n\n"
    for t in transacoes:
        data_formatada = t.data.strftime("%d/%m %H:%M")
        mensagem += f"🔹 *ID {t.id}* | {data_formatada}\n{t.categoria}: {t.descricao} - R$ {t.valor:.2f}\n\n"

    await update.message.reply_text(mensagem, parse_mode='Markdown')

async def comando_ultimos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id # <-- IDENTIDADE CAPTURADA
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
    app.add_handler(CommandHandler("start", comando_start))
    app.add_handler(CommandHandler("comandos", comando_comandos))
    app.add_handler(CommandHandler("saldo", comando_saldo))
    
    app.add_handler(CommandHandler(["relatorio", "relatório"], comando_relatorio))
    app.add_handler(CommandHandler(["ultimos", "últimos"], comando_ultimos))
    app.add_handler(CommandHandler(["transacoes", "transações"], comando_transacoe))
    app.add_handler(CommandHandler(["analise", "análise"], comando_analise))
    
    app.add_handler(CommandHandler("apagar", comando_apagar))
    app.add_handler(CommandHandler("filtro", comando_filtro))
    
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
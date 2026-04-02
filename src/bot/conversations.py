from telegram import Update, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime

from src.bot.menu import gerar_botoes_tipo_renda, comando_menu 

from src.database.database import SessionLocal
from src.database.models import Renda


TIPO, VALOR, DIA = range(3)

async def comando_renda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia o fluxo puxando o design do menu principal"""
    
    texto = (
        "💸 *Cadastro de Nova Renda*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Selecione a origem desse valor:"
    )
    
    reply_markup = InlineKeyboardMarkup(gerar_botoes_tipo_renda())
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(texto, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(texto, reply_markup=reply_markup, parse_mode="Markdown")
        
    return TIPO

async def receber_tipo_renda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "renda_cancelar":
        await comando_menu(update, context) 
        return ConversationHandler.END
        
    tipo_escolhido = query.data.replace("renda_tipo_", "")
    context.user_data['tipo_renda'] = tipo_escolhido 
    
    texto = (
        f"✅ Você selecionou: *{tipo_escolhido}*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Agora, digite o *valor* recebido:\n"
        "_(Exemplo: 2500 ou 2500,50)_"
    )
    
    await query.edit_message_text(text=texto, parse_mode="Markdown")
    return VALOR

async def receber_valor_renda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(update.message.text.replace(",", "."))
        context.user_data["renda_valor"] = valor
        await update.message.reply_text("Em que dia este valor cai na conta? (Apenas o número do dia)")
        return DIA
    except ValueError:
        await update.message.reply_text("Por favor, digite um valor numérico válido (ex: 1200.00).")
        return VALOR

async def receber_dia_renda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dia = int(update.message.text)
        tipo = context.user_data["renda_tipo"]
        valor = context.user_data["renda_valor"]
        
        db = SessionLocal()
        nova_renda = Renda(tipo=tipo, valor=valor, dia=dia, data_criacao=datetime.now())
        db.add(nova_renda)
        db.commit()
        db.close()

        await update.message.reply_text(f"✅ Sucesso! {tipo} de R$ {valor:.2f} registado para o dia {dia}.")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Dia inválido. Digite apenas o número do dia.")
        return DIA

async def cancelar_conversa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Registo cancelado.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
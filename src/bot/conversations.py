from telegram import Update, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
import re
from src.bot.menu import gerar_botoes_tipo_renda, comando_menu 

from src.database.database import SessionLocal
from src.database.crud import criar_renda


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
    texto_valor = update.message.text
    try:
        texto_limpo = texto_valor.replace(".", "").replace(",", ".")
        valor = float(texto_limpo)
        
        context.user_data['valor_renda'] = valor
        
        await update.message.reply_text("Entendido. E em qual dia do mês ele costuma cair na conta? (Ex: 5, 20)")
        return DIA
        
    except ValueError:
        await update.message.reply_text("❌ Valor inválido. Digite apenas números (ex: 1500,50):")
        return VALOR

async def receber_dia_renda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id 
    texto_dia = update.message.text

    numero_encontrado = re.search(r'\d+', texto_dia)
    
    if numero_encontrado:
        dia = int(numero_encontrado.group())

        if 1 <= dia <= 31:
            # LENDO AS CHAVES CORRETAS
            tipo = context.user_data['tipo_renda']
            valor = context.user_data['valor_renda']
            
            categoria_tipo = "beneficio" if tipo in ["Benefício", "VR", "VA"] else "dinheiro"
            
            try:
                db = SessionLocal()
                criar_renda(db, descricao=tipo, valor=valor, dia_recebimento=dia, chat_id=chat_id, tipo=categoria_tipo)
                db.close()
                
                valor_formatado = f"{valor:.2f}".replace('.', ',')
                
                await update.message.reply_text(
                    f"✅ *Renda salva com sucesso!*\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🏷️ Tipo: {tipo}\n"
                    f"💰 Valor: R$ {valor_formatado}\n"
                    f"📅 Dia de recebimento: {dia}",
                    parse_mode="Markdown"
                )
                return ConversationHandler.END
            except Exception as e:
                await update.message.reply_text(f"❌ Erro ao salvar no banco: {e}")
                return ConversationHandler.END
                
        else:
            await update.message.reply_text("❌ Dia inválido. Por favor, digite um dia entre 1 e 31:")
            return DIA
            
    else:
        await update.message.reply_text("❌ Não encontrei nenhum número. Digite o dia do recebimento (ex: 5, dia 20):")
        return DIA

async def cancelar_conversa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cadastro de renda cancelado.")
    return ConversationHandler.END

async def cancelar_conversa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Registo cancelado.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
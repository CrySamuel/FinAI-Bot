from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

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
            InlineKeyboardButton("➕ Adicionar Renda", callback_data="btn_renda")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(teclado)
    
    if update.callback_query:
        await update.callback_query.message.edit_text("Painel de Controle FinAI 🤖\nEscolha uma opção:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Painel de Controle FinAI 🤖\nEscolha uma opção:", reply_markup=reply_markup)


async def processar_cliques_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Escuta os cliques nos botões e roteia para a ação correta."""
    query = update.callback_query
    await query.answer() 
    
    escolha = query.data
    
    if escolha == "btn_saldo":
        await query.message.reply_text("A funcionalidade de Saldo via botão será conectada em breve!")
    elif escolha == "btn_analise":
        await query.message.reply_text("A funcionalidade de Análise via botão será conectada em breve!")
    elif escolha == "btn_ultimos":
        await query.message.reply_text("A funcionalidade de Últimos Gastos via botão será conectada em breve!")
    elif escolha == "btn_relatorio":
        await query.message.reply_text("A funcionalidade de Relatório via botão será conectada em breve!")
    elif escolha == "btn_renda":
        await query.message.reply_text("Para adicionar renda, por favor digite o comando /renda")
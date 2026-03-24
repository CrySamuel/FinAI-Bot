from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

async def comando_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Eu sou o seu Gestor Financeiro. 📊\n"
        "Me mande um gasto (ex: 'Gastei 50 no mercado') para eu testar a conexão!"
    )

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_recebido = update.message.text
    
    resposta = f"Recebi sua mensagem: '{texto_recebido}'\n\n(Ainda estou aprendendo a classificar isso com IA!)"
    
    await update.message.reply_text(resposta)

def setup_handlers(app):
    app.add_handler(CommandHandler("start", comando_start))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem))
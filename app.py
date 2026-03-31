import os
import threading
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from src.bot.handlers import setup_handlers

load_dotenv()

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    
    if not token:
        print("Erro: Token do Telegram não encontrado. Verifique seu arquivo .env!")
        return
    
    print("Iniciando o FinAI Bot...")
    app = ApplicationBuilder().token(token).build()

    setup_handlers(app)

    print("Bot rodando com sucesso! Mande um /start lá no Telegram.")
    app.run_polling()

if __name__ == '__main__':
    main()
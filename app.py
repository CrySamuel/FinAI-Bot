import os
import threading
from flask import Flask
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from src.bot.handlers import setup_handlers

load_dotenv()

app_web = Flask(__name__)

@app_web.route('/')
def health_check():
    return "FinAI Bot está online e blindado na nuvem! 🚀"

def run_flask():
    porta = int(os.environ.get("PORT", 8080))
    app_web.run(host="0.0.0.0", port=porta, use_reloader=False)

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    
    if not token:
        print("Erro: Token do Telegram não encontrado. Verifique seu arquivo .env!")
        return

    print("Ligando o site fantasma para o Render...")
    threading.Thread(target=run_flask, daemon=True).start()
    
    print("Iniciando o FinAI Bot...")
    app = ApplicationBuilder().token(token).build()

    setup_handlers(app)

    print("Bot rodando com sucesso! Mande um /start lá no Telegram.")
    app.run_polling()

if __name__ == '__main__':
    main()
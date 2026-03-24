from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from src.ai.processor import analisar_mensagem_com_ia
from src.database.database import SessionLocal
from src.database.crud import criar_transacao

async def comando_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Eu sou o seu Gestor Financeiro com IA. 📊\n"
        "Pode me mandar seus gastos naturalmente (ex: 'Gastei 50 no mercado')."
    )

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_recebido = update.message.text
    
    mensagem_espera = await update.message.reply_text("Processando gasto... 🧠")
    
    dados_extraidos = analisar_mensagem_com_ia(texto_recebido)
    
    if dados_extraidos and "valor" in dados_extraidos:
        try:
            db = SessionLocal()
            criar_transacao(
                db=db,
                valor=dados_extraidos["valor"],
                categoria=dados_extraidos["categoria"],
                descricao=dados_extraidos["descricao"]
            )
            db.close()
            
            # 4. Confirma para o usuário
            resposta = (
                "✅ Gasto registrado com sucesso!\n"
                f"🏷️ Categoria: {dados_extraidos['categoria']}\n"
                f"📝 Descrição: {dados_extraidos['descricao']}\n"
                f"💰 Valor: R$ {dados_extraidos['valor']:.2f}"
            )
            await mensagem_espera.edit_text(resposta)
            
        except Exception as e:
            await mensagem_espera.edit_text(f"Erro ao salvar no banco de dados: {e}")
    else:
        await mensagem_espera.edit_text("Desculpe, não consegui entender os valores dessa mensagem. Pode tentar de novo?")

def setup_handlers(app):
    app.add_handler(CommandHandler("start", comando_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem))
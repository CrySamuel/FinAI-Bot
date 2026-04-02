from telegram.ext import (
    CommandHandler, MessageHandler, filters, 
    ConversationHandler, CallbackQueryHandler
)
from src.bot.menu import comando_menu, processar_cliques_menu

from src.bot.commands import (
    comando_start, comando_comandos, comando_saldo, comando_relatorio,
    comando_transacoes, comando_ultimos, comando_apagar, comando_analise,
    comando_filtro, comando_novo_cartao, comando_fatura, comando_definir_meta,
    comando_metas, comando_ajuda
)

from src.bot.callbacks import botao_ajuda_clicado

from src.bot.conversations import (
    comando_renda, receber_tipo_renda, receber_valor_renda,
    receber_dia_renda, cancelar_conversa, TIPO, VALOR, DIA
)

from src.bot.messages import processar_mensagem

def setup_handlers(app):
    """Função Maestro que liga todos os módulos ao Bot"""
    
    app.add_handler(CommandHandler("start", comando_start))
    app.add_handler(CommandHandler("menu", comando_menu))
    app.add_handler(CommandHandler("comandos", comando_comandos))
    app.add_handler(CommandHandler("saldo", comando_saldo))
    app.add_handler(CommandHandler("relatorio", comando_relatorio))
    app.add_handler(CommandHandler("ultimos", comando_ultimos))
    app.add_handler(CommandHandler("transacoes", comando_transacoes)) 
    app.add_handler(CommandHandler("analise", comando_analise))
    app.add_handler(CommandHandler("apagar", comando_apagar))
    app.add_handler(CommandHandler("filtro", comando_filtro))
    app.add_handler(CommandHandler("novo_cartao", comando_novo_cartao))
    app.add_handler(CommandHandler("fatura", comando_fatura))
    app.add_handler(CommandHandler("meta", comando_definir_meta))
    app.add_handler(CommandHandler("metas", comando_metas))
    app.add_handler(CommandHandler("ajuda", comando_ajuda))

    app.add_handler(CallbackQueryHandler(processar_cliques_menu, pattern="^btn_"))
    app.add_handler(CallbackQueryHandler(botao_ajuda_clicado, pattern='^ajuda_'))

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('renda', comando_renda),
            CallbackQueryHandler(comando_renda, pattern="^renda_start$") 
        ],
        states={
            TIPO: [CallbackQueryHandler(receber_tipo_renda)],
            VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_valor_renda)],
            DIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_dia_renda)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar_conversa)]
    )
    app.add_handler(conv_handler)
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem))
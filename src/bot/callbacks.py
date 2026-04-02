from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def botao_ajuda_clicado(update, context):
    query = update.callback_query
    await query.answer() 
    
    teclado_voltar = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Voltar ao Menu Principal", callback_data='ajuda_voltar')]
    ])

    if query.data == 'ajuda_registros':
        texto = (
            "📥 *REGISTROS E ENTRADAS*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "Como alimentar o FinAI com dados:\n\n"
            "🗣️ *Texto Livre:* Apenas digite seu gasto (ex: _'Paguei 20 no ifood'_). A Inteligência Artificial faz o resto!\n"
            "💵 */renda* - Cadastra seu salário, adiantamento ou benefícios mensais.\n"
            "💳 */novo_cartao* - Cadastra um novo cartão de crédito (Precisa de Nome, Fechamento e Vencimento)."
        )
    
    elif query.data == 'ajuda_dia_a_dia':
        texto = (
            "📊 *ACOMPANHAMENTO DO DIA A DIA*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "Comandos rápidos para olhar enquanto está na rua:\n\n"
            "⚖️ */saldo* - Mostra o balanço do mês atual (Receitas reais vs Despesas do mês).\n"
            "🕒 */ultimos* - Mostra os 5 últimos gastos registrados na hora.\n"
            "🗑️ */apagar [ID]* - Lançou algo errado? Copie o ID da transação e use este comando para deletar (ex: `/apagar 15`)."
        )
        
    elif query.data == 'ajuda_analise':
        texto = (
            "🔎 *RELATÓRIOS E ANÁLISE PROFUNDA*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "Ferramentas avançadas para auditar o orçamento:\n\n"
            "💰 */transacoes* - Lista absolutamente todos os gastos registrados na base.\n"
            "🍕 */analise* - Mostra a porcentagem de gastos dividida por categoria (Onde o dinheiro está sumindo?).\n"
            "🔍 */filtro [termo]* - Calcula o total gasto em um local ou categoria específica (ex: `/filtro ifood` ou `/filtro transporte`).\n"
            "📊 */relatorio* - Gera uma planilha Excel detalhada com todo o histórico e envia para você baixar."
        )
        
    elif query.data == 'ajuda_voltar':
        keyboard = [
            [InlineKeyboardButton("📥 Como Registrar Entradas e Gastos", callback_data='ajuda_registros')],
            [InlineKeyboardButton("📊 Acompanhamento do Dia a Dia", callback_data='ajuda_dia_a_dia')],
            [InlineKeyboardButton("🔎 Relatórios e Análise Profunda", callback_data='ajuda_analise')]
        ]
        texto = "🛟 *Central de Comando - FinAI*\n━━━━━━━━━━━━━━━━━━━\n\nEscolha uma categoria abaixo para ver os comandos:"
        await query.edit_message_text(text=texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    await query.edit_message_text(text=texto, reply_markup=teclado_voltar, parse_mode="Markdown")

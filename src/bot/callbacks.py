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
            "📥 *TUTORIAL: REGISTROS E ENTRADAS*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "O FinAI possui uma IA treinada para blindar o Desafio 2026. "
            "Você não precisa de planilhas complexas, basta conversar com ele!\n\n"
            "🗣️ *A Mágica do Texto Livre:*\n"
            "Escreva naturalmente. A IA detecta valor, data, forma de pagamento e categoria sozinha.\n"
            "✅ _\"Comprei pão por 15 reais no pix hoje\"_\n"
            "✅ _\"Gastei 120 de gasolina ontem no cartão Nubank\"_ (A IA ajusta a data!)\n"
            "✅ _\"Comprei uma TV de 2000 em 10x no Itaú\"_ (A IA divide as parcelas nos meses certos!)\n\n"
            "⚙️ *Cadastros Estruturais:*\n"
            "🔹 `/renda` - Abre o painel com botões para registrar salários, VAs ou freelas.\n"
            "🔹 `/novo_cartao Nome Fecha Vence` - OBRIGATÓRIO antes de usar o crédito. Ex: `/novo_cartao Nubank 10 20`\n"
            "🔹 `/meta Categoria Valor` - Define um limite mensal para te avisar se estourar. Ex: `/meta Lazer 300`"
        )
    
    elif query.data == 'ajuda_dia_a_dia':
        texto = (
            "📊 *TUTORIAL: ACOMPANHAMENTO DIÁRIO*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "Ferramentas rápidas para consultar antes de fazer uma compra por impulso:\n\n"
            "⚖️ *O Saldo Real (`/saldo`)*\n"
            "Mostra a verdade dura e crua. Ele pega tudo o que você ganhou no mês e subtrai apenas o que saiu do seu bolso (Pix/Débito) e as faturas que já venceram. É o seu caixa real de hoje.\n\n"
            "💳 *Radar de Faturas (`/fatura`)*\n"
            "A ferramenta mais importante do desafio. Mostra o total das faturas abertas *deste* mês, e já projeta o tamanho da "
            "bola de neve para o *mês que vem*. Sempre consulte antes de parcelar algo novo!\n\n"
            "🛠️ *Manutenção Rápida*\n"
            "🔹 `/ultimos` - Lista as últimas 5 compras com seus respectivos IDs.\n"
            "🔹 `/apagar [ID]` - Lançou errado? Digite `/apagar g15` (para apagar o gasto 15) ou `/apagar r4` (para apagar a renda 4)."
        )
        
    elif query.data == 'ajuda_analise':
        texto = (
            "🔎 *TUTORIAL: ANÁLISE PROFUNDA*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "Para fazer aquele fechamento de mês profissional:\n\n"
            "🎯 *O Placar das Metas (`/metas`)*\n"
            "Gera barras de progresso visuais (🟩🟩⬜⬜) para cada categoria que você definiu um limite. O bot te avisa se você ainda tem margem de manobra ou se já estourou o teto.\n"
            "Serve para gerar novas metas também. Ex: `/meta Alimentação 500` cria uma meta de R$ 500 para a categoria Alimentação.\n\n"
            "🍕 *Para onde o dinheiro foi? (`/analise` e `/filtro`)*\n"
            "🔹 Use `/analise` para ver uma listagem em porcentagem de onde você mais gasta (ex: 40% Alimentação, 20% Transporte).\n"
            "🔹 Use `/filtro palavra` para caçar gastos específicos. Ex: `/filtro ifood` ou `/filtro uber` soma tudo que tem aquele nome.\n\n"
            "📁 *Exportação (`/relatorio`)*\n"
            "Aperte o botão, escolha o mês e receba uma planilha Excel formatada, colorida e pronta para abrir."
        )
        
    elif query.data == 'ajuda_voltar':
        keyboard = [
            [InlineKeyboardButton("📥 Entradas e Lançamentos", callback_data='ajuda_registros')],
            [InlineKeyboardButton("📊 O Dia a Dia e Cartões", callback_data='ajuda_dia_a_dia')],
            [InlineKeyboardButton("🔎 Fechamento e Relatórios", callback_data='ajuda_analise')]
        ]
        texto = (
            "🛟 *Manual de Sobrevivência - FinAI*\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "Escolha um dos módulos abaixo para entender como dominar o seu orçamento:"
        )
        await query.edit_message_text(text=texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    await query.edit_message_text(text=texto, reply_markup=teclado_voltar, parse_mode="Markdown")

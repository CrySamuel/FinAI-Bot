from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import extract, func
from datetime import datetime, date

from src.database.database import SessionLocal
from src.database.models import Cartao, Transacao, Renda, Meta
from src.database.crud import obter_resumo_mes, obter_analise_categorias, filtrar_gastos_por_termo, listar_metas, verificar_meta_categoria
from src.bot.menu import comando_menu, gerar_botoes_meses

async def comando_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem_boas_vindas = (
        "Olá! Eu sou o FinAI, seu assistente financeiro inteligente. 🤖💸\n\n"
        "Você pode simplesmente me mandar uma mensagem como:\n"
        "🍕 *'Gastei 50 no ifood'*\n"
        "🛒 *'Comprei 300 de mercado no cartão'*\n\n"
        "Ou use o painel abaixo para navegar:"
    )
    await update.message.reply_text(mensagem_boas_vindas, parse_mode="Markdown")
    
    await comando_menu(update, context)

async def comando_ajuda(update, context):

    keyboard = [
        [InlineKeyboardButton("📥 Como Registrar Entradas e Gastos", callback_data='ajuda_registros')],
        [InlineKeyboardButton("📊 Acompanhamento do Dia a Dia", callback_data='ajuda_dia_a_dia')],
        [InlineKeyboardButton("🔎 Relatórios e Análise Profunda", callback_data='ajuda_analise')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    texto_menu = (
        "🛟 *Central de Comando - FinAI*\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "O sistema possui diversas ferramentas para o nosso Desafio 2026.\n"
        "Escolha uma categoria abaixo para ver os comandos detalhados:"
    )
    
    await update.message.reply_text(texto_menu, reply_markup=reply_markup, parse_mode="Markdown")   

async def comando_comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = (
        "🛠️ *Comandos Disponíveis:*\n\n"
        "🗣️ *Texto Livre:* Apenas digite seu gasto (ex: 'Paguei 20 no ifood') para a IA registrar.\n\n"
        "💵 */renda* - Cadastra seu salário, adiantamento ou benefícios.\n"
        "⚖️ */saldo* - Mostra o balanço do mês atual (Receitas vs Despesas).\n"
        "📊 */relatorio* - Gera uma planilha Excel detalhada com todo o histórico.\n"
        "❓ */comandos* - Mostra esta lista de ajuda.\n"
        "🕒 */ultimos* - Mostra os 5 últimos gastos registrados.\n"
        "🗑️ */apagar [ID]* - Apaga um gasto incorreto usando o ID.\n"
        "💰 */transacoes* - Lista todos os gastos registrados.\n"
        "🍕 */analise* - Mostra a % de gastos por categoria.\n"
        "🔍 */filtro [termo]* - Mostra o total gasto em um local ou categoria específica.\n"
        "💳 */novo_cartao* - Cadastra um novo cartão de crédito.\n"
    )
    await update.message.reply_text(mensagem, parse_mode='Markdown')

async def comando_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id 
    db = SessionLocal()
    resumo = obter_resumo_mes(db, chat_id)
    db.close()

    receitas_totais = resumo["receitas_totais"]
    despesas_mes = resumo["despesas_mes"]
    saldo_bancario = resumo["saldo_bancario"]

    rec_fmt = f"{receitas_totais:.2f}".replace('.', ',')
    desp_mes_fmt = f"{despesas_mes:.2f}".replace('.', ',')
    saldo_fmt = f"{saldo_bancario:.2f}".replace('.', ',')

    mensagem = (
        "🏦 *Conta Bancária (Saldo Real)*\n"
        f"💰 *Disponível:* R$ {saldo_fmt}\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📊 *Controle deste Mês*\n"
        f"📉 Gastos do Mês: R$ {desp_mes_fmt}\n"
        "━━━━━━━━━━━━━━━━\n"
    )

    if saldo_bancario > 0:
        mensagem += "✅ O desafio de economia segue firme!"
    elif saldo_bancario == 0:
        mensagem += "⚖️ Conta zerada. Atenção aos próximos gastos."
    else:
        mensagem += "🚨 Saldo negativo! Você está no cheque especial."

    await update.message.reply_text(mensagem, parse_mode='Markdown')

async def comando_relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📅 *Selecione o mês do relatório:*", 
        reply_markup=InlineKeyboardMarkup(gerar_botoes_meses()), 
        parse_mode="Markdown"
    )

async def comando_transacoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db = SessionLocal()
    
    try:
        saidas = db.query(Transacao).filter(Transacao.chat_id == chat_id).all()
        entradas = db.query(Renda).filter(Renda.chat_id == chat_id).all()
        
        if not saidas and not entradas:
            await update.message.reply_text("📭 Nenhuma movimentação encontrada.")
            return

        movimentacoes = []
        hoje = date.today()
        
        for s in saidas:
            data_obj = s.data if s.data else datetime.combine(hoje, datetime.min.time())
            movimentacoes.append({
                "id_exibicao": f"G{s.id}", "tipo": "saida", "valor": s.valor,
                "categoria": s.categoria, "descricao": s.descricao, "data": data_obj, "id_num": s.id
            })
            
        for e in entradas:
            try:
                data_obj = datetime(hoje.year, hoje.month, int(e.dia_recebimento))
            except:
                data_obj = datetime.combine(hoje, datetime.min.time())
                
            movimentacoes.append({
                "id_exibicao": f"R{e.id}", "tipo": "entrada", "valor": e.valor,
                "categoria": "Receita", "descricao": e.descricao, "data": data_obj, "id_num": e.id
            })
            
        movimentacoes.sort(key=lambda x: (x["data"], 1 if x["tipo"] == "entrada" else 0, x["id_num"]), reverse=True)
        
        ultimas_movimentacoes = movimentacoes[:15]
        
        texto = "📋 *Extrato de Transações*\n━━━━━━━━━━━━━━━━\n"
        for m in ultimas_movimentacoes:
            icone = "🔴" if m["tipo"] == "saida" else "🟢"
            data_formatada = m["data"].strftime("%d/%m")
            valor_formatado = f"{m['valor']:.2f}".replace('.', ',')
            
            texto += f"{icone} *{data_formatada}* | {m['categoria']} [ID: {m['id_exibicao']}]\n"
            texto += f"    └ R$ {valor_formatado} ({m['descricao']})\n\n"
            
        await update.message.reply_text(texto, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao listar transações: {e}")
    finally:
        db.close()

async def comando_ultimos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id 
    db = SessionLocal()

    try:
        saidas = db.query(Transacao).filter(Transacao.chat_id == chat_id).order_by(Transacao.id.desc()).limit(5).all()
        entradas = db.query(Renda).filter(Renda.chat_id == chat_id).order_by(Renda.id.desc()).limit(5).all()

        if not saidas and not entradas:
            await update.message.reply_text("Nenhum registro encontrado ainda.")
            return

        movimentacoes = []
        hoje = date.today()

        for s in saidas:
            data_obj = s.data if s.data else datetime.combine(hoje, datetime.min.time())
            movimentacoes.append({"id_exibicao": f"G{s.id}", "tipo": "saida", "valor": s.valor, "categoria": s.categoria, "descricao": s.descricao, "data": data_obj, "id_num": s.id})

        for e in entradas:
            try:
                data_obj = datetime(hoje.year, hoje.month, int(e.dia_recebimento))
            except:
                data_obj = datetime.combine(hoje, datetime.min.time())
            movimentacoes.append({"id_exibicao": f"R{e.id}", "tipo": "entrada", "valor": e.valor, "categoria": "Receita", "descricao": e.descricao, "data": data_obj, "id_num": e.id})

        movimentacoes.sort(key=lambda x: (x["data"], 1 if x["tipo"] == "entrada" else 0, x["id_num"]), reverse=True)

        ultimos = movimentacoes[:5]

        mensagem = "🕒 *Últimos 5 registros:*\n\n"
        for m in ultimos:
            data_formatada = m["data"].strftime("%d/%m")
            mensagem += f"🔹 *ID {m['id_exibicao']}* | {data_formatada}\n{m['categoria']}: {m['descricao']} - R$ {m['valor']:.2f}\n\n"

        await update.message.reply_text(mensagem, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Erro: {e}")
    finally:
        db.close()

async def comando_apagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        argumento = context.args[0].lower() 
        chat_id = update.effective_chat.id
        db = SessionLocal()
        
        tipo = argumento[0]
        id_item = int(argumento[1:])
        
        if tipo == 'g':
            item = db.query(Transacao).filter(Transacao.id == id_item, Transacao.chat_id == chat_id).first()
            if item:
                db.delete(item)
                db.commit()
                await update.message.reply_text(f"🗑️ Gasto apagado com sucesso!")
            else:
                await update.message.reply_text("❌ Gasto não encontrado. Verifique o ID no /transacoes.")
                
        elif tipo == 'r':
            item = db.query(Renda).filter(Renda.id == id_item, Renda.chat_id == chat_id).first()
            if item:
                db.delete(item)
                db.commit()
                await update.message.reply_text(f"🗑️ Renda apagada com sucesso!")
            else:
                await update.message.reply_text("❌ Renda não encontrada. Verifique o ID no /transacoes.")
        else:
            await update.message.reply_text("❌ Formato inválido. Use /apagar g4 (para gasto) ou /apagar r4 (para renda).")
            
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Como usar o comando:\nPara apagar um gasto: /apagar g4\nPara apagar uma renda: /apagar r4\n\n(Você pode ver os IDs no comando /transacoes)")
    finally:
        if 'db' in locals():
            db.close()

async def comando_analise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    db = SessionLocal()
    try:
        gastos = obter_analise_categorias(db, chat_id)
        
        if not gastos:
            await update.message.reply_text("📊 Ainda não existem despesas registradas para análise.")
            return

        total_gastos = sum(item["total"] for item in gastos)
        
        texto_analise = "📊 *Análise de Gastos por Categoria*\n━━━━━━━━━━━━━━━━\n"
        
        for item in gastos:
            categoria = item["categoria"]
            valor = item["total"]
            
            percentual = (valor / total_gastos) * 100
            valor_formatado = f"{valor:.2f}".replace('.', ',')
            
            tamanho_barra = int(percentual / 10)
            barra = "🟩" * tamanho_barra + "⬜" * (10 - tamanho_barra)
            
            texto_analise += f"*{categoria}* - {percentual:.1f}%\n"
            texto_analise += f"{barra} R$ {valor_formatado}\n\n"
        
        texto_analise += "━━━━━━━━━━━━━━━━\n"
        texto_analise += f"🔴 *Total Gasto:* R$ {f'{total_gastos:.2f}'.replace('.', ',')}"
        
        await update.message.reply_text(texto_analise, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao gerar análise: {e}")
    finally:
        db.close()

async def comando_filtro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id 
    if not context.args:
        await update.message.reply_text("⚠️ Me diga o que quer buscar. Exemplo: /filtro mercado")
        return
        
    termo = " ".join(context.args)
    
    db = SessionLocal()
    total, transacoes = filtrar_gastos_por_termo(db, termo, chat_id)
    db.close()
    
    if total > 0:
        total_fmt = f"{total:.2f}".replace('.', ',')
        
        mensagem = f"🔍 *Resultado da busca para '{termo}':*\n\n"
        mensagem += f"💰 *Total Gasto:* R$ {total_fmt}\n"
        mensagem += "-------------------------\n📝 *Detalhes:*\n\n"
        
        for t in transacoes:
            data_fmt = t.data.strftime("%d/%m")
            valor_fmt = f"{t.valor:.2f}".replace('.', ',')
            
            mensagem += f"🔸 {data_fmt} - {t.categoria} ({t.descricao}): R$ {valor_fmt}\n"
            
        await update.message.reply_text(mensagem, parse_mode='Markdown')
    else:
        await update.message.reply_text(f"🔍 Nenhum gasto encontrado com a palavra '{termo}'.")
        
async def comando_metas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db = SessionLocal()

    if context.args:
        try:
            categoria = context.args[0].capitalize()
            valor = float(context.args[1].replace(',', '.'))
            
            meta_existente = db.query(Meta).filter(Meta.chat_id == chat_id, Meta.categoria == categoria).first()
            
            if meta_existente:
                meta_existente.valor_limite = valor
                resposta = f"🎯 Meta de *{categoria}* atualizada para *R$ {valor:.2f}*!"
            else:
                nova_meta = Meta(chat_id=chat_id, categoria=categoria, valor_limite=valor)
                db.add(nova_meta)
                resposta = f"🎯 Nova meta de *{categoria}* criada com limite de *R$ {valor:.2f}*!"
            
            db.commit()
            await update.message.reply_text(resposta, parse_mode="Markdown")
            
        except (IndexError, ValueError):
            await update.message.reply_text(
                "❌ *Uso incorreto!*\nPara criar/editar use: `/metas Categoria Valor`\nExemplo: `/metas Lazer 500`", 
                parse_mode="Markdown"
            )
        finally:
            db.close()
        return 

    try:        
        metas_cadastradas = listar_metas(db, chat_id)
        
        if not metas_cadastradas:
            await update.message.reply_text(
                "📭 *Nenhuma meta definida ainda.*\n"
                "Use `/metas Categoria Valor` (Ex: `/metas Lazer 100`) para começar a controlar seu orçamento!", 
                parse_mode="Markdown"
            )
            return

        mensagem = "🎯 *Suas Metas do Mês*\n━━━━━━━━━━━━━━━━\n"
        
        for meta in metas_cadastradas:
            info = verificar_meta_categoria(db, chat_id, meta.categoria)
            
            if info:
                percentual = info['percentual']
                gasto_fmt = f"{info['gasto']:.2f}".replace('.', ',')
                limite_fmt = f"{info['limite']:.2f}".replace('.', ',')
                restante_fmt = f"{abs(info['restante']):.2f}".replace('.', ',')
                
                tamanho_barra = min(int(percentual / 10), 10)
                
                if percentual > 100:
                    barra = "🟥" * 10
                    icone = "🚨"
                    status_sobra = f"🛑 *Estourou R$ {restante_fmt}*"
                elif percentual >= 80:
                    barra = "🟧" * tamanho_barra + "⬜" * (10 - tamanho_barra)
                    icone = "⚠️"
                    status_sobra = f"🟡 *Cuidado! Sobra R$ {restante_fmt}*"
                else:
                    barra = "🟩" * tamanho_barra + "⬜" * (10 - tamanho_barra)
                    icone = "✅"
                    status_sobra = f"🟢 *Livre: R$ {restante_fmt}*"
                
                mensagem += f"{icone} *{meta.categoria}* ({percentual:.1f}%)\n"
                mensagem += f"{barra}\n"
                mensagem += f"💰 R$ {gasto_fmt} / R$ {limite_fmt}\n"
                mensagem += f"↳ {status_sobra}\n\n"

        mensagem += "━━━━━━━━━━━━━━━━\n"
        mensagem += "💡 *Dica:* Use `/metas [Nome] [Valor]` para criar ou editar uma meta."

        await update.message.reply_text(mensagem, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao buscar metas: {e}")
    finally:
        if 'db' in locals():
            db.close()

async def comando_novo_cartao(update, context):
    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text(
                "⚠️ *Uso correto:* `/novo_cartao Nome Fechamento Vencimento`\n"
                "Exemplo: `/novo_cartao Nubank 10 20`", 
                parse_mode="Markdown"
            )
            return

        nome_cartao = args[0]
        dia_fechamento = int(args[1])
        dia_vencimento = int(args[2])
        chat_id = update.effective_chat.id

        from src.database.database import SessionLocal
        from src.database.models import Cartao
        
        db = SessionLocal()
        novo_cartao = Cartao(
            chat_id=chat_id, 
            nome=nome_cartao, 
            dia_fechamento=dia_fechamento, 
            dia_vencimento=dia_vencimento
        )
        db.add(novo_cartao)
        db.commit()
        db.close()

        await update.message.reply_text(
            f"💳 *Cartão Cadastrado com Sucesso!*\n\n"
            f"🏦 Nome: {nome_cartao.capitalize()}\n"
            f"🔒 Fechamento: Dia {dia_fechamento}\n"
            f"📅 Vencimento: Dia {dia_vencimento}",
            parse_mode="Markdown"
        )

    except ValueError:
        await update.message.reply_text("❌ Erro: Os dias de fechamento e vencimento precisam ser números!")
    except Exception as e:
        await update.message.reply_text(f"❌ Erro interno: {e}")

async def comando_fatura(update, context):
    chat_id = update.effective_chat.id
    
    db = SessionLocal()
    try:
        hoje = datetime.now()
        mes_atual = hoje.month
        ano_atual = hoje.year
        
        mes_que_vem = mes_atual + 1 if mes_atual < 12 else 1
        ano_que_vem = ano_atual if mes_atual < 12 else ano_atual + 1
        
        cartoes = db.query(Cartao).filter(Cartao.chat_id == chat_id).all()
        
        if not cartoes:
            await update.message.reply_text("💳 Vocês ainda não têm cartões cadastrados. Use `/novo_cartao Nome Fechamento Vencimento`", parse_mode="Markdown")
            return
            
        mensagem = "💳 *RAIO-X DAS FATURAS*\n"
        mensagem += "━━━━━━━━━━━━━━━━━━━\n\n"
        
        for cartao in cartoes:
            fatura_atual = db.query(Transacao).filter(
                Transacao.chat_id == chat_id,
                Transacao.cartao_id == cartao.id,
                extract('month', Transacao.data) == mes_atual,
                extract('year', Transacao.data) == ano_atual
            ).all()
            
            total_atual = sum(t.valor for t in fatura_atual)
            
            total_proximo = db.query(func.sum(Transacao.valor)).filter(
                Transacao.chat_id == chat_id,
                Transacao.cartao_id == cartao.id,
                extract('month', Transacao.data) == mes_que_vem,
                extract('year', Transacao.data) == ano_que_vem
            ).scalar() or 0.0
            
            mensagem += f"🏦 *CARTÃO {cartao.nome.upper()}* (Vence dia {cartao.dia_vencimento:02d})\n\n"
            
            mensagem += f"🔴 *Fatura Atual ({mes_atual:02d}/{ano_atual})*\n"
            mensagem += f"🎯 *Total:* R$ {total_atual:.2f}\n"
            
            if total_atual > 0:
                mensagem += "📝 _Detalhes:_\n"
                for t in fatura_atual:
                    mensagem += f"  ├ {t.descricao.capitalize()} - R$ {t.valor:.2f}\n"
                    
            mensagem += f"\n🟡 *Prévia Próximo Mês ({mes_que_vem:02d}/{ano_que_vem})*\n"
            mensagem += f"⏳ *Estimativa:* R$ {total_proximo:.2f}\n"
            mensagem += "━━━━━━━━━━━━━━━━━━━\n\n"
            
        await update.message.reply_text(mensagem, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao puxar faturas: {e}")
    finally:
        db.close()
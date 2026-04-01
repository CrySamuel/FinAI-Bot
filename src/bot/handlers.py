from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import (
    ContextTypes, CommandHandler, MessageHandler, filters, 
    ConversationHandler, CallbackQueryHandler
)

from src.database.crud import (
    verificar_meta_categoria, criar_transacao, criar_renda, 
    obter_resumo_mes, filtrar_gastos_por_termo, obter_analise_categorias, 
    listar_metas, registrar_compra_parcelada
)
import re
from src.database.models import Meta, Transacao, Renda
from src.ai.processor import analisar_mensagem_com_ia
from src.database.database import SessionLocal
from src.bot.menu import comando_menu, processar_cliques_menu, gerar_botoes_meses

from datetime import datetime, timedelta, date

ESCOLHER_TIPO, DIGITAR_VALOR, DIGITAR_DIA = range(3)

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

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
    chat_id = update.effective_chat.id 
    texto_recebido = update.message.text
    mensagem_espera = await update.message.reply_text("Processando... 🧠")
    
    dados_extraidos = analisar_mensagem_com_ia(texto_recebido)
    
    if dados_extraidos and "valor" in dados_extraidos:
        try:
            db = SessionLocal()
            tipo_movimentacao = dados_extraidos.get("tipo", "saida")
            valor = dados_extraidos["valor"]
            valor_formatado = f"{valor:.2f}".replace('.', ',')
            
            data_str = dados_extraidos.get("data")
            if data_str:
                try:
                    data_final = datetime.strptime(data_str, "%Y-%m-%d")
                except ValueError:
                    data_final = datetime.utcnow() - timedelta(hours=3)
            else:
                data_final = datetime.utcnow() - timedelta(hours=3)
            
            if tipo_movimentacao == "entrada":
                criar_transacao(
                    db=db, 
                    valor=valor, 
                    categoria=dados_extraidos.get("categoria", "Renda Extra"), 
                    descricao=dados_extraidos["descricao"],
                    tipo="entrada", 
                    chat_id=chat_id,
                    data=data_final 
                )
                resposta = (
                    "🤑 *Dinheiro na conta!*\n"
                    f"🏷️ Categoria: {dados_extraidos['categoria']}\n"
                    f"📝 Descrição: {dados_extraidos['descricao']}\n"
                    f"💰 Valor: R$ {valor_formatado}\n"
                    f"📅 Data ref: {data_final.strftime('%d/%m/%Y')}"
                )
            else:
                metodo = dados_extraidos.get("metodo_pagamento", "debito")
                parcelas = int(dados_extraidos.get("parcelas", 1))
                nome_cartao = dados_extraidos.get("cartao")
        
                if metodo == "credito" and parcelas > 1 and nome_cartao:
                    sucesso, msg_retorno = registrar_compra_parcelada(
                        db=db,
                        chat_id=chat_id,
                        valor_total=valor,
                        categoria=dados_extraidos.get("categoria", "Outros"),
                        descricao=dados_extraidos["descricao"],
                        cartao_nome=nome_cartao,
                        parcelas=parcelas,
                        data_compra=data_final
                    )
                    
                    if sucesso:
                        texto_gasto = f"💳 *Crédito Inteligente*\n{msg_retorno}"
                    else:
                        texto_gasto = f"⚠️ *Atenção:*\n{msg_retorno}"
                else:
                    criar_transacao(
                        db=db, 
                        valor=valor, 
                        categoria=dados_extraidos["categoria"], 
                        descricao=dados_extraidos["descricao"],
                        tipo="saida",
                        chat_id=chat_id,
                        data=data_final 
                    )

                    texto_gasto = (
                        "✅ *Gasto registrado!*\n"
                        f"🏷️ Categoria: {dados_extraidos['categoria']}\n"
                        f"📝 Descrição: {dados_extraidos['descricao']}\n"
                        f"🏦 Método: {metodo.capitalize()}\n"
                        f"💰 Valor: R$ {valor_formatado}\n"
                        f"📅 Data: {data_final.strftime('%d/%m/%Y')}"
                    )
                    
                    if parcelas > 1 and not nome_cartao:
                        texto_gasto += "\n\n⚠️ *Aviso do FinAI:* Você mencionou parcelas, mas não disse de qual cartão. Para não bagunçar, registrei o valor total como gasto à vista!"
                                
                status_meta = ""
                try:
                    info_meta = verificar_meta_categoria(db, chat_id, dados_extraidos["categoria"], data_final)

                    if info_meta: 
                        emoji_status = "✅" if info_meta['restante'] > 0 else "⚠️"
                        status_meta = (
                            f"\n\n{emoji_status} *Status da Meta: {dados_extraidos['categoria'].capitalize()}*\n"
                            f"💰 Gasto: R$ {info_meta['gasto']:.2f} / R$ {info_meta['limite']:.2f}\n"
                            f"📊 {info_meta['percentual']:.1f}% consumido."
                        )
                        if info_meta['restante'] < 0:
                            status_meta += f"\n🚨 *Limite excedido em R$ {abs(info_meta['restante']):.2f}!*"
                except Exception as e:
                    print(f"Erro ao buscar meta: {e}")

                resposta = texto_gasto + status_meta

            db.close()
            await mensagem_espera.edit_text(resposta, parse_mode="Markdown")         
        
        except Exception as e:
            await mensagem_espera.edit_text(f"❌ Erro ao salvar: {e}")
    else:
        await mensagem_espera.edit_text("❌ Não entendi. Pode reformular?")

async def comando_renda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = "💸 *Nova Renda!*\nQual é a origem desse dinheiro?"

    teclado = [
        [InlineKeyboardButton("💵 Salário", callback_data="Salário")],
        [InlineKeyboardButton("💸 Adiantamento/Vale", callback_data="Adiantamento")],
        [InlineKeyboardButton("🍔 VR (Refeição)", callback_data="VR")],
        [InlineKeyboardButton("🚌 VT (Transporte)", callback_data="VT")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="Cancelar")]
    ]
    reply_markup = InlineKeyboardMarkup(teclado)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(texto, parse_mode="Markdown", reply_markup=reply_markup) 
    else:

        await update.message.reply_text(texto, parse_mode="Markdown", reply_markup=reply_markup) 
        
    return ESCOLHER_TIPO

async def receber_tipo_renda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    tipo_escolhido = query.data
    
    if tipo_escolhido == "Cancelar":
        await query.edit_message_text("Cadastro de renda cancelado.")
        return ConversationHandler.END
        
    context.user_data['tipo_renda'] = tipo_escolhido 
    
    await query.edit_message_text(text=f"Legal! Você selecionou **{tipo_escolhido}**.\nQual é o valor? (Ex: 2500 ou 2500.50)")
    return DIGITAR_VALOR

async def receber_valor_renda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_valor = update.message.text
    try:
        texto_limpo = texto_valor.replace(".", "")
        texto_limpo = texto_limpo.replace(",", ".")
        
        valor = float(texto_limpo)
        context.user_data['valor_renda'] = valor
        
        await update.message.reply_text("Entendido. E em qual dia do mês ele costuma cair na conta? (Ex: 5, 20)")
        return DIGITAR_DIA
        
    except ValueError:
        await update.message.reply_text("❌ Valor inválido. Digite apenas números (ex: 1500,50 ou 1.500,50):")
        return DIGITAR_VALOR

async def receber_dia_renda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id 
    texto_dia = update.message.text

    numero_encontrado = re.search(r'\d+', texto_dia)
    
    if numero_encontrado:
        dia = int(numero_encontrado.group())

        if 1 <= dia <= 31:
            context.user_data['dia_renda'] = dia
            
            tipo = context.user_data['tipo_renda']
            valor = context.user_data['valor_renda']
            
            categoria_tipo = "beneficio" if tipo in ["VR", "VT"] else "dinheiro"
            
            try:
                db = SessionLocal()
                criar_renda(db, descricao=tipo, valor=valor, dia_recebimento=dia, chat_id=chat_id, tipo=categoria_tipo)
                db.close()
                
                valor_formatado = f"{valor:.2f}".replace('.', ',')
                
                await update.message.reply_text(
                    f"✅ Renda salva com sucesso!\n"
                    f"🏷️ Tipo: {tipo}\n"
                    f"💰 Valor: R$ {valor_formatado}\n"
                    f"📅 Dia de recebimento: {dia}"
                )
                return ConversationHandler.END
            except Exception as e:
                await update.message.reply_text(f"❌ Erro ao salvar no banco: {e}")
                return ConversationHandler.END
                
        else:
            await update.message.reply_text("❌ Dia inválido. Por favor, digite um dia do mês válido entre 1 e 31:")
            return DIGITAR_DIA
            
    else:
        await update.message.reply_text("❌ Não encontrei nenhum número. Digite o dia do recebimento (ex: 5, dia 20):")
        return DIGITAR_DIA
    
async def cancelar_conversa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cadastro cancelado.")
    return ConversationHandler.END

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
            
        # Ordenação blindada
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
        
async def comando_definir_meta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        categoria = context.args[0].capitalize()
        valor = float(context.args[1].replace(',', '.'))
        
        db = SessionLocal()
        meta_existente = db.query(Meta).filter(Meta.chat_id == chat_id, Meta.categoria == categoria).first()
        
        if meta_existente:
            meta_existente.valor_limite = valor
        else:
            nova_meta = Meta(chat_id=chat_id, categoria=categoria, valor_limite=valor)
            db.add(nova_meta)
        
        db.commit()
        db.close()
        
        await update.message.reply_text(f"🎯 Meta de *{categoria}* definida para *R$ {valor:.2f}*!", parse_mode="Markdown")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Use: `/meta Categoria Valor` (Ex: `/meta Lazer 500`)", parse_mode="Markdown")

async def comando_metas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    db = SessionLocal()
    try:        
        metas_cadastradas = listar_metas(db, chat_id)
        
        if not metas_cadastradas:
            await update.message.reply_text(
                "📭 *Nenhuma meta definida ainda.*\n"
                "Use `/meta Categoria Valor` (Ex: `/meta Lazer 100`) para começar a controlar seu orçamento!", 
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

        await update.message.reply_text(mensagem, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao buscar metas: {e}")
    finally:
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

def setup_handlers(app):
    app.add_handler(CommandHandler("menu", comando_menu))
    
    app.add_handler(CommandHandler("start", comando_start))
    app.add_handler(CommandHandler("comandos", comando_comandos))
    app.add_handler(CommandHandler("saldo", comando_saldo))
    
    app.add_handler(CommandHandler("relatorio", comando_relatorio))
    app.add_handler(CommandHandler("ultimos", comando_ultimos))
    app.add_handler(CommandHandler("transacoes", comando_transacoes)) 
    app.add_handler(CommandHandler("analise", comando_analise))
    
    app.add_handler(CommandHandler("apagar", comando_apagar))
    app.add_handler(CommandHandler("filtro", comando_filtro))
    app.add_handler(CommandHandler("novo_cartao", comando_novo_cartao))
    
    app.add_handler(CallbackQueryHandler(processar_cliques_menu, pattern="^btn_"))
    app.add_handler(CommandHandler("meta", comando_definir_meta))
    app.add_handler(CommandHandler("metas", comando_metas))

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('renda', comando_renda),
            CallbackQueryHandler(comando_renda, pattern="^renda_start$") 
        ],
        states={
            ESCOLHER_TIPO: [CallbackQueryHandler(receber_tipo_renda)],
            DIGITAR_VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_valor_renda)],
            DIGITAR_DIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_dia_renda)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar_conversa)]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem))
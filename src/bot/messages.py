from telegram import Update, constants
from telegram.ext import ContextTypes
from datetime import datetime, timedelta

from src.database.database import SessionLocal
from src.database.crud import verificar_meta_categoria, criar_transacao, registrar_compra_parcelada
from src.ai.processor import analisar_mensagem_com_ia

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
                    sucesso, resultado = registrar_compra_parcelada(
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
                        texto_gasto = (
                            "💳 *CRÉDITO INTELIGENTE*\n"
                            "━━━━━━━━━━━━━━━━━━━━\n"
                            f"🛍️ *Item:* {resultado['descricao'].capitalize()}\n"
                            f"🏷️ *Categoria:* {resultado['categoria']}\n"
                            f"🏦 *Cartão:* {resultado['cartao']}\n"
                            "━━━━━━━━━━━━━━━━━━━━\n"
                            f"💰 *Total:* R$ {resultado['valor_total']:.2f}\n"
                            f"🗓️ *Parcelamento:* {resultado['parcelas']}x de *R$ {resultado['valor_parcela']:.2f}*\n"
                            "\n✅ _Parcelas agendadas com sucesso no seu fluxo de caixa!_"
                        )
                    else:
                        texto_gasto = f"⚠️ *Atenção:*\n{resultado}"
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
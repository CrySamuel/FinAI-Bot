import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def analisar_mensagem_com_ia(texto_usuario: str) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Erro: GROQ_API_KEY não encontrada no arquivo .env!")
        return None

    hoje_str = datetime.now().strftime("%Y-%m-%d")
    
    categorias_permitidas = [
        "Alimentação", "Transporte", "Moradia", "Saúde", 
        "Lazer", "Educação", "Serviços", "Compras", "Renda Extra", "Outros"
    ]

    prompt_sistema = f"""
    Você é um assistente financeiro rigoroso. Hoje é dia {hoje_str}.
    Extraia os dados da mensagem do usuário e retorne EXCLUSIVAMENTE um formato JSON válido.
    
    REGRAS DE TEMPO:
    - ATENÇÃO: A data de HOJE é {hoje_str}.
    - Se o usuário disser "ontem", calcule a data baseada em {hoje_str}.
    - Retorne as datas SEMPRE no formato YYYY-MM-DD.

    REGRAS OBRIGATÓRIAS DE EXTRAÇÃO:
    1. A 'categoria' DEVE OBRIGATORIAMENTE ser UMA destas opções exatas: {', '.join(categorias_permitidas)}. NUNCA invente categorias. Se houver dúvida, use "Outros".
    2. A chave "tipo" deve ser estritamente "entrada" ou "saida".
    3. Use EXATAMENTE as palavras do usuário para o campo "descricao". NUNCA invente métodos de pagamento (como "Crédito", "Cartão", "Pix") dentro da descrição se não estiverem no texto original.
    4. A chave "metodo_pagamento" deve ser "credito", "pix" ou "debito". Se o usuário não especificar, assuma "debito".
    5. A chave "parcelas" deve ser um número inteiro. Se disser "em X vezes", extraia o número X. Se for à vista ou não mencionado, o valor é 1.
    6. A chave "cartao" deve conter apenas o nome do banco/cartão mencionado (ex: "Itaú", "Nubank"). Se não for mencionado, retorne null.
    
    ESTRUTURA JSON ESPERADA:
    {{
        "valor": float (use PONTO para decimais),
        "categoria": "string",
        "descricao": "string",
        "tipo": "entrada" ou "saida",
        "data": "YYYY-MM-DD",
        "metodo_pagamento": "credito" | "pix" | "debito",
        "parcelas": int,
        "cartao": "string" ou null
    }}
    
    EXEMPLOS DE CLASSIFICAÇÃO (Retorne APENAS o JSON e nada mais):
    - "Paguei 45,90 na farmácia" -> {{"valor": 45.90, "categoria": "Saúde", "descricao": "farmácia", "tipo": "saida", "data": "{hoje_str}", "metodo_pagamento": "debito", "parcelas": 1, "cartao": null}}
    - "Comprei um pneu de 600 reais em 6x no cartão Itaú dia 15" -> {{"valor": 600.00, "categoria": "Transporte", "descricao": "pneu", "tipo": "saida", "data": "2026-04-15", "metodo_pagamento": "credito", "parcelas": 6, "cartao": "Itaú"}}
    - "Ganhei 100 reais de um freela no pix" -> {{"valor": 100.00, "categoria": "Renda Extra", "descricao": "freela", "tipo": "entrada", "data": "{hoje_str}", "metodo_pagamento": "pix", "parcelas": 1, "cartao": null}}
    """
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": texto_usuario}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"} 
    }

    try:
        resposta = requests.post(url, headers=headers, json=payload)
        resposta.raise_for_status()
        
        dados_gerados = resposta.json()["choices"][0]["message"]["content"]
        
        dados_gerados = dados_gerados.strip()
        if dados_gerados.startswith("```json"):
            dados_gerados = dados_gerados.replace("```json", "").replace("```", "").strip()
        elif dados_gerados.startswith("```"):
            dados_gerados = dados_gerados.replace("```", "").strip()
            
        dados_estruturados = json.loads(dados_gerados)
        
        if dados_estruturados.get("categoria") not in categorias_permitidas:
            dados_estruturados["categoria"] = "Outros"
            
        return dados_estruturados
        
    except requests.exceptions.HTTPError as e:
        print(f"Erro da API Groq (HTTP {e.response.status_code}): {e.response.text}")
        return None
    except json.JSONDecodeError:
        print(f"Erro: A IA não retornou um JSON válido. Resposta crua: {dados_gerados}")
        return None
    except Exception as e:
        print(f"Erro interno ao processar IA: {e}")
        return None
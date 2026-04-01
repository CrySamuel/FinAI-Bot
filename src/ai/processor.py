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
    Você é um assistente financeiro. Hoje é dia {hoje_str}.
    Extraia os dados da mensagem do usuário no formato JSON.
    
    REGRAS DE TEMPO:
    - ATENÇÃO: A data de HOJE é {hoje_str}.
    - Se o usuário disser "ontem", calcule a data baseada em {hoje_str} (exemplo: se hoje é 01/04/2026, ontem foi 31/03/2026).
    - Retorne as datas SEMPRE no formato YYYY-MM-DD.

    Regras OBRIGATÓRIAS:
    1. Use EXATAMENTE as palavras do usuário para o campo "descricao".
    2. Responda EXCLUSIVAMENTE com um JSON válido.
    3. Use as chaves: "valor" (float, use PONTO para os decimais, ex: 15.50), "categoria", "descricao", "tipo" e "data".
    4. A chave "tipo" deve ser estritamente "entrada" ou "saida".
    5. Se o usuário mencionar que pagou no 'crédito', 'cartão' ou 'parcelado', coloque a tag '[Crédito] ' no início da 'descricao' (ex: '[Crédito] Compra do mês').
    6. A 'categoria' DEVE OBRIGATORIAMENTE ser UMA destas opções exatas: {', '.join(categorias_permitidas)}. NUNCA invente uma categoria fora desta lista. Se houver dúvida, use "Outros".
    7. Regra da DATA: Se o usuário mencionar uma data específica (ex: 'dia 20', 'ontem'), calcule e retorne a data exata no formato 'AAAA-MM-DD'. Se NÃO mencionar data, retorne '{hoje_str}'.
    8. - NUNCA invente métodos de pagamento. Se o usuário disser "gastei com pneu", a descrição deve ser "Pneu". NUNCA adicione palavras como "Crédito", "Cartão", "Pix" se não estiverem no texto original.
    
    EXEMPLOS DE CLASSIFICAÇÃO (Retorne APENAS o JSON e nada mais):
    - "Paguei 45,90 na farmácia" -> {{"valor": 45.90, "categoria": "Saúde", "descricao": "Farmácia", "tipo": "saida", "data": "{hoje_str}"}}
    - "Gastei 120 de gasolina ontem" -> {{"valor": 120.00, "categoria": "Transporte", "descricao": "Gasolina", "tipo": "saida", "data": "2024-03-24"}}
    - "Ganhei 100 reais de um freela" -> {{"valor": 100.00, "categoria": "Renda Extra", "descricao": "Freela", "tipo": "entrada", "data": "{hoje_str}"}}
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
import os
import requests
import json
from dotenv import load_dotenv

# Garante que as variáveis do .env estão carregadas
load_dotenv()

def analisar_mensagem_com_ia(texto_usuario: str) -> dict:
    """
    Envia a mensagem para a API ultra-rápida do Groq (usando Llama 3) 
    e retorna os dados financeiros.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Erro: GROQ_API_KEY não encontrada no arquivo .env!")
        return None

    prompt_sistema = f"""
    Você é um assistente financeiro. Extraia os dados da mensagem do usuário no formato JSON com as chaves: 'valor' (float), 'categoria' (string), 'descricao' (string) e 'tipo' ('entrada' ou 'saida')    
    Leia a mensagem: "{texto_usuario}"
    
    Regras OBRIGATÓRIAS:
    1. Responda EXCLUSIVAMENTE com um JSON válido. Não adicione nenhum texto antes ou depois.
    2. Use as chaves: "valor" (float, use PONTO para os decimais, ex: 15.50), "categoria", "descricao", e "tipo".
    3. A chave "tipo" deve ser estritamente "entrada" (dinheiro ganho/recebido) ou "saida" (dinheiro gasto/pago).
    4. e o usuário mencionar que pagou no 'crédito', 'cartão' ou 'parcelado', coloque a tag '[Crédito] ' no início da 'descricao' (ex: '[Crédito] Compra do mês'). Não repita a palavra crédito.
    5. A 'categoria' deve ser o local ou tipo exato do gasto (ex: Mercado, Transporte, Farmácia, Lazer). NUNCA use termos genéricos como 'Despesas' ou 'Saída
    
    EXEMPLOS DE CLASSIFICAÇÃO:
    - "Paguei 45,90 na farmácia" -> {{"valor": 45.90, "categoria": "Saúde", "descricao": "Farmácia", "tipo": "saida"}}
    - "Gastei 120 de gasolina" -> {{"valor": 120.00, "categoria": "Transporte", "descricao": "Gasolina", "tipo": "saida"}}
    - "Ganhei 100 reais de um freela" -> {{"valor": 100.00, "categoria": "Renda Extra", "descricao": "Freela", "tipo": "entrada"}}
    
    Gere apenas o JSON e nada mais:
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
        "temperature": 0.0
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
        return dados_estruturados
        
    except requests.exceptions.HTTPError as e:
        # Agora, se der erro, o terminal vai imprimir exatamente o que a Groq reclamou
        print(f"Erro da API Groq (HTTP {e.response.status_code}): {e.response.text}")
        return None
    except Exception as e:
        print(f"Erro interno ao processar IA: {e}")
        return None
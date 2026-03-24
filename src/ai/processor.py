import requests
import json

def analisar_mensagem_com_ia(texto_usuario: str) -> dict:

    prompt_sistema = f"""
    Você é um sistema rigoroso de extração de dados financeiros. 
    Leia a mensagem: "{texto_usuario}"
    
    Regras OBRIGATÓRIAS:
    1. Responda EXCLUSIVAMENTE com um JSON válido.
    2. Use as chaves: "valor" (float, use PONTO para os decimais, ex: 15.50), "categoria", "descricao", e "tipo".
    3. A chave "tipo" deve ser estritamente "entrada" (dinheiro ganho/recebido) ou "saida" (dinheiro gasto/pago).
    
    EXEMPLOS DE CLASSIFICAÇÃO:
    - "Paguei 45,90 na farmácia" -> {{"valor": 45.90, "categoria": "Saúde", "descricao": "Farmácia", "tipo": "saida"}}
    - "Gastei 120 de gasolina" -> {{"valor": 120.00, "categoria": "Transporte", "descricao": "Gasolina", "tipo": "saida"}}
    - "Ganhei 100 reais de um freela" -> {{"valor": 100.00, "categoria": "Renda Extra", "descricao": "Freela", "tipo": "entrada"}}
    - "Me pagaram 50,50 que tavam devendo" -> {{"valor": 50.50, "categoria": "Renda Extra", "descricao": "Pagamento divida", "tipo": "entrada"}}
    
    Agora, processe a mensagem do usuário usando a mesma lógica dos exemplos acima.
    """

    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3", 
        "prompt": prompt_sistema,
        "stream": False,
        "format": "json" 
    }

    try:
        resposta = requests.post(url, json=payload)
        resposta.raise_for_status()
        
        dados_gerados = resposta.json()["response"]
        dados_estruturados = json.loads(dados_gerados)
        
        return dados_estruturados
        
    except Exception as e:
        print(f"Erro ao processar com a IA: {e}")
        return None
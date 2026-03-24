import requests
import json

def analisar_mensagem_com_ia(texto_usuario: str) -> dict:

    prompt_sistema = f"""
    Você é um sistema rigoroso de extração de dados financeiros. 
    Leia a mensagem: "{texto_usuario}"
    
    Regras OBRIGATÓRIAS:
    1. Responda EXCLUSIVAMENTE com um JSON válido.
    2. Use as chaves: "valor" (float com ponto), "categoria" (string), "descricao" (string curta de até 3 palavras).
    3. Categorias permitidas: Alimentação, Transporte, Lazer, Contas, Saúde, Outros.
    
    EXEMPLOS DE CLASSIFICAÇÃO PARA VOCÊ SEGUIR:
    - "Paguei 45 na farmácia" -> {{"valor": 45.0, "categoria": "Saúde", "descricao": "Farmácia"}}
    - "Gastei 120 de gasolina" -> {{"valor": 120.0, "categoria": "Transporte", "descricao": "Gasolina"}}
    - "Mercado superpão deu 300" -> {{"valor": 300.0, "categoria": "Alimentação", "descricao": "Mercado Superpão"}}
    - "Conta de luz 150" -> {{"valor": 150.0, "categoria": "Contas", "descricao": "Conta de luz"}}
    - "Cinema 50 reais" -> {{"valor": 50.0, "categoria": "Lazer", "descricao": "Cinema"}}
    
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
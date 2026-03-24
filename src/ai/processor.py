import requests
import json

def analisar_mensagem_com_ia(texto_usuario: str) -> dict:

    prompt_sistema = f"""
    Você é um sistema de extração de dados. Leia a mensagem: "{texto_usuario}"
    
    Regras OBRIGATÓRIAS:
    1. Responda EXCLUSIVAMENTE com um JSON válido. Não adicione texto antes ou depois.
    2. Use EXATAMENTE estas três chaves em português: "valor", "categoria", "descricao".
    3. O "valor" deve ser numérico (float). Use ponto em vez de vírgula.
    4. A "categoria" deve ser uma destas: Alimentação, Transporte, Lazer, Contas, Saúde, Outros.
    5. A "descricao" deve ser extremamente curta, resumindo o local ou item em no máximo 3 palavras (Ex: "Posto Ipiranga", "Ifood Almoço").
    
    Exemplo de saída esperada:
    {{"valor": 85.90, "categoria": "Transporte", "descricao": "Posto Ipiranga"}}
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
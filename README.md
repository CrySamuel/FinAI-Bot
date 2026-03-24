# 📊 FinAI Bot - Gestor Financeiro Inteligente

Um assistente financeiro pessoal integrado ao Telegram, desenvolvido em Python, que utiliza Inteligência Artificial (LLMs) para registrar, categorizar e analisar gastos do dia a dia de forma conversacional.

## 🚀 Visão Geral

O objetivo deste projeto é eliminar o atrito de preencher planilhas financeiras manualmente. Através de um Bot no Telegram, o usuário envia mensagens naturais (ex: *"Gastei 45 reais de Uber"*), e a IA do sistema se encarrega de extrair o valor, identificar a categoria (Transporte) e salvar a transação no banco de dados, retornando o saldo e conselhos financeiros em tempo real.

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python 3, Flask (API REST)
* **Interface:** Telegram Bot API (`python-telegram-bot`)
* **Inteligência Artificial:** LLMs via Ollama (modelos locais quantizados) / Integração com API (Gemini/OpenAI)
* **Banco de Dados:** SQLite (com SQLAlchemy)
* **Análise de Dados:** Pandas (para geração de relatórios e fechamento mensal em `.xlsx`)

## ✨ Funcionalidades

- [x] **Entrada em Linguagem Natural:** Registro de despesas via chat do Telegram.
- [x] **Categorização Automática:** Uso de IA para classificar gastos (Alimentação, Transporte, Lazer, etc.) sem intervenção manual.
- [x] **Feedback Imediato:** Retorno instantâneo do bot com o impacto do gasto no orçamento mensal.
- [x] **Geração de Relatórios:** Comando `/relatorio` que exporta os dados do SQLite e envia uma planilha Excel consolidada diretamente no chat.

## ⚙️ Arquitetura do Sistema

1.  O usuário envia uma mensagem para o Bot no Telegram.
2.  O Telegram aciona um *Webhook* na API Flask.
3.  O backend em Python recebe a mensagem e a envia para o modelo de Linguagem (LLM) processar.
4.  A IA retorna um JSON estruturado com os dados da transação.
5.  O backend salva os dados no SQLite e envia uma mensagem de confirmação/alerta de volta para o usuário no Telegram.

## 💻 Como rodar o projeto localmente

### Pré-requisitos
* Python 3.10+
* Token de Bot do Telegram (obtido via BotFather)
* (Opcional) Ollama instalado para rodar LLMs localmente.

### Instalação

1. Clone este repositório:
```bash
git clone https://github.com/CrySamuel/FinAI-Bot.git
cd finai-bot
```
2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate
```
3. Instale as dependências:
```bash
pip install -r requirements.txt
```
4. Crie um arquivo .env na raiz do projeto e adicione suas variáveis de ambiente:
```Snippet de código
TELEGRAM_BOT_TOKEN=seu_token_aqui
LLM_API_KEY=sua_chave_aqui_caso_use_api_externa
```
5. Inicie a aplicação:
```bash
python app.py
```

Desenvolvido por Crys.

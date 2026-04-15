# 🚀 FinAI Bot - Seu Assistente Financeiro Inteligente no Telegram

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Telegram API](https://img.shields.io/badge/Telegram-Bot%20API-0088cc.svg)](https://core.telegram.org/bots/api)
[![Groq AI](https://img.shields.io/badge/AI-Groq%20(Llama--3)-f37121.svg)](https://groq.com/)
[![Oracle Cloud](https://img.shields.io/badge/Oracle_Cloud-F80000?logo=oracle&logoColor=white)](https://cloud.oracle.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

O **FinAI** é um bot de gestão financeira pessoal construído para o Telegram. Ele utiliza Inteligência Artificial (LLMs) para ler mensagens em linguagem natural (ex: *"Gastei 50 no ifood com cartão de crédito ontem"*), extrair o contexto e registrar automaticamente no banco de dados. 

Este projeto foi desenhado com uma **Arquitetura Multitenant**, permitindo que múltiplos usuários utilizem o bot simultaneamente com total privacidade e isolamento de dados.

## ✨ Funcionalidades Principais

* **🤖 Processamento de Linguagem Natural (NLP):** Integração com a Groq API (Llama-3) para categorização automática e extração de datas em texto livre.
* **📊 Relatórios e Análises:** Geração de gráficos de progresso em texto e exportação de balanços completos em planilhas **Excel (.xlsx)** formatadas.
* **📱 Interface Rica (UI/UX):** Menus interativos com botões inline, facilitando a navegação sem precisar digitar comandos.
* **🔒 Arquitetura Multitenant:** Uso do `chat_id` do Telegram como chave primária de isolamento, garantindo que cada usuário acesse apenas seus próprios dados.
* **☁️ Infraestrutura Dedicada:** Hospedado em uma VPS autônoma na **Oracle Cloud Infrastructure (OCI)**, rodando 24/7 em ambiente Linux otimizado.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python
* **Interface:** `python-telegram-bot`
* **Banco de Dados:** SQLAlchemy (ORM) com SQLite/PostgreSQL
* **Inteligência Artificial:** Groq API (Modelo Llama-3-8b com saída nativa em JSON)
* **Processamento de Dados:** Pandas & OpenPyXL (Geração de Excel)
* **Infraestrutura & Deploy:** Oracle Cloud (Ubuntu Linux), `tmux` para background processing e Git CI/CD workflow.

---

## 🚀 Como rodar o projeto localmente

Se você quiser testar ou contribuir com o FinAI, siga os passos abaixo:

### 1. Clone o repositório
```bash
git clone [https://github.com/CrySamuel/FinAI-Bot.git](https://github.com/CrySamuel/FinAI-Bot.git)
cd FinAI-Bot
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
TELEGRAM_TOKEN=seu_token_do_botfather_aqui
GROQ_API_KEY=sua_chave_da_groq_aqui
PORT=8080
```
5. Inicie a aplicação:
```bash
python app.py
```

## ☁️ Deploy na Nuvem (Produção)
O bot está configurado para rodar nativamente em servidores Linux. O fluxo de atualização em produção segue as melhores práticas de versionamento:

Commit e Push das alterações no repositório principal.

Acesso SSH ao servidor (Oracle Cloud).

Atualização via git pull.

Execução contínua em segundo plano gerenciada via tmux.

## 👨‍💻 Autor
Crys

Desenvolvedor Backend & Entusiasta de Inteligência Artificial

LinkedIn: [https://www.linkedin.com/in/crystofer-samuel/]

GitHub: [https://github.com/CrySamuel]

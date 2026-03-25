# 🚀 FinAI Bot - Seu Assistente Financeiro Inteligente no Telegram

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Telegram API](https://img.shields.io/badge/Telegram-Bot%20API-0088cc.svg)](https://core.telegram.org/bots/api)
[![Groq AI](https://img.shields.io/badge/AI-Groq%20(Llama--3)-f37121.svg)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

O **FinAI** é um bot de gestão financeira pessoal construído para o Telegram. Ele utiliza Inteligência Artificial (LLMs) para ler mensagens em linguagem natural (ex: *"Gastei 50 no ifood com cartão de crédito ontem"*), extrair o contexto e registrar automaticamente no banco de dados. 

Este projeto foi desenhado com uma **Arquitetura Multitenant**, permitindo que múltiplos usuários utilizem o bot simultaneamente com total privacidade e isolamento de dados.

## ✨ Funcionalidades Principais

* **🤖 Processamento de Linguagem Natural (NLP):** Integração com a Groq API (Llama-3) para categorização automática e extração de datas em texto livre.
* **📊 Relatórios e Análises:** Geração de gráficos de progresso em texto e exportação de balanços completos em planilhas **Excel (.xlsx)** formatadas.
* **📱 Interface Rica (UI/UX):** Menus interativos com botões inline, facilitando a navegação sem precisar digitar comandos.
* **🔒 Arquitetura Multitenant:** Uso do `chat_id` do Telegram como chave primária de isolamento, garantindo que cada usuário acesse apenas seus próprios dados.
* **☁️ Pronto para Nuvem:** Configurado com Flask rodando em background (`health_check`) para manter o bot online 24/7 em plataformas como Render ou Heroku.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python
* **Interface:** `python-telegram-bot`
* **Banco de Dados:** SQLAlchemy (ORM) com SQLite/PostgreSQL
* **Inteligência Artificial:** Groq API (Modelo Llama-3-8b com saída nativa em JSON)
* **Processamento de Dados:** Pandas & OpenPyXL (Geração de Excel)

---

## 📸 Demonstração do Projeto

<img width="742" height="529" alt="Captura de tela 2026-03-25 142955" src="https://github.com/user-attachments/assets/3394e4ce-3416-4cf8-94a6-8ca9aa9b6975" />
<img width="817" height="689" alt="Captura de tela 2026-03-25 143006" src="https://github.com/user-attachments/assets/7fceb4e1-9059-4651-a199-3cbce1e264cf" />
<img width="812" height="725" alt="Captura de tela 2026-03-25 143019" src="https://github.com/user-attachments/assets/a301d379-54ac-4c3e-88aa-8ee7def85798" />
<img width="799" height="624" alt="Captura de tela 2026-03-25 143030" src="https://github.com/user-attachments/assets/58f756f0-6ec7-4ec6-909d-0cf36f34a099" />
<img width="846" height="774" alt="Captura de tela 2026-03-25 143041" src="https://github.com/user-attachments/assets/a1ae31e5-c54c-433b-809b-06476715d264" /><img width="763" height="389" alt="Captura de tela 2026-03-25 143137" src="https://github.com/user-attachments/assets/eef72b74-337a-4b42-82ce-fa5a308fa0a8" />

---

## 🚀 Como rodar o projeto localmente

Se você quiser testar ou contribuir com o FinAI, siga os passos abaixo:

### 1. Clone o repositório
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
TELEGRAM_TOKEN=seu_token_do_botfather_aqui
GROQ_API_KEY=sua_chave_da_groq_aqui
PORT=8080
```
5. Inicie a aplicação:
```bash
python app.py
```

## 🛣️ Roadmap (Próximos Passos)

[x] Categorização Estrita com IA (JSON Mode)

[x] Exportação de Balanço em Excel

[x] Interface de Botões Inline

[ ] Implementação de Metas de Gastos Mensais

[ ] Alertas Automáticos de Vencimento de Fatura

[ ] Preparação para monetização (SaaS)

## 👨‍💻 Autor
Crys

Desenvolvedor Backend & Entusiasta de Inteligência Artificial

LinkedIn: [https://www.linkedin.com/in/crystofer-samuel/]

GitHub: [https://github.com/CrySamuel]

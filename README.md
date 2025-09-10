# Bot de Notícias de Tecnologia e Cotação de Bitcoin para Telegram

Este é um bot em Python projetado para monitorar, em tempo real, notícias de sites de tecnologia e a cotação do Bitcoin, enviando atualizações diretamente para um chat ou canal do Telegram.

## 🚀 Funcionalidades Principais

-   **Monitoramento de Notícias**: O bot faz *web scraping* em portais de tecnologia como **TecMundo** e **TechTudo** em busca de novas publicações.
-   **Cotação de Bitcoin**: Acompanha o preço atual do Bitcoin (em BRL) e sua variação nas últimas 24 horas, utilizando a API da CoinGecko.
-   **Notificações no Telegram**: Envia mensagens formatadas e com imagens para um chat específico no Telegram sempre que uma nova notícia é encontrada ou o preço do Bitcoin muda.
-   **Anti-Repetição**: Utiliza um banco de dados **SQLite** para armazenar o histórico de notícias já enviadas, garantindo que nenhuma notificação seja duplicada.
-   **Operação Assíncrona**: Graças à biblioteca `asyncio`, as verificações de notícias e da cotação de criptomoedas ocorrem de forma concorrente e eficiente, sem que uma tarefa bloqueie a outra.

## 🛠️ Tecnologias Utilizadas

-   **Python 3**
-   **Telegram API** (`python-telegram-bot`)
-   **Web Scraping** (`requests` e `BeautifulSoup4`)
-   **Programação Assíncrona** (`asyncio`)
-   **Banco de Dados** (`sqlite3`)

## ⚙️ Pré-requisitos e Instalação

Antes de começar, você precisará ter o [Python 3](https://www.python.org/downloads/) instalado em sua máquina.

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/WRodrigues12olive/Web-Scraper-de-Noticias-e-Bitcoin
    cd Web-Scraper-de-Noticias-e-Bitcoin
    ```

2.  **(Opcional, mas recomendado) Crie um ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    instale-as com o comando:
    ```bash
    pip install -r requirements.txt
    ```

## 📝 Configuração

Abra o arquivo `Bot.py` e configure as seguintes variáveis no início do script:

1.  `TELEGRAM_BOT_TOKEN`: O token de acesso do seu bot. Para obtê-lo, converse com o [@BotFather](https://t.me/BotFather) no Telegram e siga as instruções para criar um novo bot.

2.  `TELEGRAM_CHAT_ID`: O ID do chat, canal ou grupo para onde as mensagens serão enviadas. Você pode obter este ID facilmente com o bot [@userinfobot](https://t.me/userinfobot).

Exemplo:
```python
TELEGRAM_BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
TELEGRAM_CHAT_ID = "-1001234567890" # Exemplo para um canal

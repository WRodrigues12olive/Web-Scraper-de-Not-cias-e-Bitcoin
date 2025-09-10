import os
import re
import requests
import sqlite3
import time
import logging
import asyncio
import telegram
from urllib.parse import urljoin
from bs4 import BeautifulSoup

TELEGRAM_BOT_TOKEN = "Token do seu Bot aqui"
TELEGRAM_CHAT_ID = "ID do seu chat"

CHECK_INTERVAL_BTC = 3600
CHECK_INTERVAL_NOTICIAS = 3600

PASTA_IMAGENS = "minhas_noticias_imagens"
DB_FILE = "historico_noticias.db"
URLS_TECNOLOGIA = [
    "https://www.tecmundo.com.br/software",
    "https://www.tecmundo.com.br/tags/inteligencia-artificial",
    "https://www.tecmundo.com.br/tags/descontos"
]
URLS_TECNOLOGIA_TECTUDO = [
    "https://www.techtudo.com.br/softwares/apps/inteligencia-artificial/"
]
BASE_URL = "https://www.tecmundo.com.br"
BASE_URL_TECTUDO = "https://www.techtudo.com.br"

COINGECKO_API_URL = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=brl&ids=bitcoin'
BITCOIN_IMAGE_URL = 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Bitcoin.svg/1200px-Bitcoin.svg.png'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def setup_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS noticias_enviadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL UNIQUE, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def sanitizar_nome_arquivo(texto):
    texto_limpo = re.sub(r'[^\w\s-]', '', texto).strip()
    return texto_limpo[:100]


async def send_telegram_photo(bot, chat_id, photo_source, caption_text):
    try:
        await bot.send_photo(chat_id=chat_id, photo=photo_source, caption=caption_text, parse_mode="HTML")
        logging.info("Mensagem com foto enviada com sucesso para o Telegram.")
        return True
    except Exception as e:
        logging.error(f"Erro ao enviar foto para o Telegram: {e}")
        return False


def get_bitcoin_data():
    try:
        response = requests.get(COINGECKO_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()[0]
        return {
            'price': data.get('current_price'),
            'change_24h': data.get('price_change_24h'),
            'change_percentage': data.get('price_change_percentage_24h')
        }
    except Exception as e:
        logging.error(f"Erro ao acessar a API da CoinGecko: {e}")
        return None


async def verificar_preco_bitcoin(bot, last_price):
    logging.info("Verificando preço do Bitcoin...")
    data = get_bitcoin_data()

    if data and data.get('price') is not None and data['price'] != last_price:
        price = data['price']
        change_24h = data.get('change_24h', 0)
        change_percentage = data.get('change_percentage', 0)

        price_str = f"{price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        change_24h_str = f"{change_24h:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        emoji = "📈" if change_24h >= 0 else "📉"
        change_24h_str = f"+{change_24h_str}" if change_24h >= 0 else change_24h_str
        change_percentage_str = f"{change_percentage:+.2f}%"

        message = f"🪙 <b>Preço do Bitcoin</b>\n\n"
        message += f"<b>Agora:</b> R$ {price_str}\n"
        message += f"{emoji} <b>Variação (24h):</b> R$ {change_24h_str} ({change_percentage_str})"

        await send_telegram_photo(bot, TELEGRAM_CHAT_ID, BITCOIN_IMAGE_URL, message)
        return price

    elif not data:
        logging.warning("Não foi possível obter os dados do Bitcoin nesta verificação.")
    else:
        logging.info("Preço do Bitcoin inalterado.")

    return last_price


async def verificar_noticias(bot):
    logging.info("Iniciando verificação de notícias do TecMundo...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for url in URLS_TECNOLOGIA:
        try:
            logging.info(f"Buscando em TecMundo: {url}")
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            artigos = soup.find_all('article', class_='tec--card')

            for artigo in artigos:
                link_tag = artigo.find('a')
                if not (link_tag and link_tag.get('href')): continue
                link_completo = urljoin(BASE_URL, link_tag['href'])

                cursor.execute("SELECT id FROM noticias_enviadas WHERE url = ?", (link_completo,))
                if cursor.fetchone() is not None: continue

                titulo_tag = artigo.find('h3', class_='tec--card__title')
                if not titulo_tag: continue
                noticia_titulo = titulo_tag.get_text(strip=True)

                logging.info(f"Notícia NOVA (TecMundo) encontrada: {noticia_titulo}")

                img_tag = artigo.find('img')
                if not (img_tag and img_tag.get('src')): continue
                img_url = img_tag.get('src')

                nome_arquivo = f"{sanitizar_nome_arquivo(noticia_titulo)}.jpg"
                caminho_arquivo = os.path.join(PASTA_IMAGENS, nome_arquivo)

                img_response = requests.get(img_url, timeout=10)
                img_response.raise_for_status()
                with open(caminho_arquivo, 'wb') as f:
                    f.write(img_response.content)

                legenda = f"<b>{noticia_titulo}</b>\n\n<a href='{link_completo}'>Leia a matéria completa</a>"
                with open(caminho_arquivo, 'rb') as photo_file:
                    sucesso = await send_telegram_photo(bot, TELEGRAM_CHAT_ID, photo_file, legenda)

                if sucesso:
                    cursor.execute("INSERT INTO noticias_enviadas (url) VALUES (?)", (link_completo,))
                    conn.commit()

                await asyncio.sleep(2)
        except Exception as e:
            logging.error(f"Erro ao processar a categoria TecMundo {url}: {e}")
    conn.close()
    logging.info("Verificação de notícias do TecMundo concluída.")


async def verificar_noticias_tectudo(bot):
    logging.info("Iniciando verificação de notícias do TechTudo...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for base_url in URLS_TECNOLOGIA_TECTUDO:
        for page_number in range(1, 5):
            if page_number == 1:
                current_url = base_url
            else:
                cleaned_base_url = base_url.rstrip('/')
                current_url = f"{cleaned_base_url}/index/feed/pagina-{page_number}.ghtml"

            logging.info(f"Buscando em TechTudo: {current_url}")

            try:
                response = requests.get(current_url, headers=headers, timeout=15)
                if response.status_code == 404:
                    logging.warning(
                        f"Página {page_number} não encontrada para {base_url}. Prosseguindo para a próxima URL.")
                    break
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                artigos = soup.find_all('div', class_='feed-post')

                if not artigos:
                    logging.info(f"Nenhum artigo novo encontrado na página {page_number} de {base_url}.")
                    break

                for artigo in artigos:
                    link_tag = artigo.find('a', class_='feed-post-link')
                    img_tag = artigo.find('img', class_='bstn-fd-picture-image')

                    if not (link_tag and link_tag.get('href') and img_tag):
                        continue

                    link_completo = link_tag['href']
                    cursor.execute("SELECT id FROM noticias_enviadas WHERE url = ?", (link_completo,))
                    if cursor.fetchone() is not None:
                        continue

                    noticia_titulo = link_tag.get_text(strip=True)
                    logging.info(f"Notícia NOVA (TechTudo) encontrada: {noticia_titulo}")
                    img_url = img_tag.get('src') or img_tag.get('srcset')
                    if not img_url:
                        continue

                    nome_arquivo = f"{sanitizar_nome_arquivo(noticia_titulo)}.jpg"
                    caminho_arquivo = os.path.join(PASTA_IMAGENS, nome_arquivo)
                    img_response = requests.get(img_url, timeout=10)
                    img_response.raise_for_status()
                    with open(caminho_arquivo, 'wb') as f:
                        f.write(img_response.content)

                    legenda = f"<b>{noticia_titulo}</b>\n\n<a href='{link_completo}'>Leia a matéria completa</a>"
                    with open(caminho_arquivo, 'rb') as photo_file:
                        sucesso = await send_telegram_photo(bot, TELEGRAM_CHAT_ID, photo_file, legenda)

                    if sucesso:
                        cursor.execute("INSERT INTO noticias_enviadas (url) VALUES (?)", (link_completo,))
                        conn.commit()
                    await asyncio.sleep(2)
            except requests.exceptions.RequestException as e:
                logging.error(f"Erro de conexão ao processar {current_url}: {e}")
                break
            except Exception as e:
                logging.error(f"Erro inesperado ao processar {current_url}: {e}")
                break
            time.sleep(1)
    conn.close()
    logging.info("Verificação de notícias do TechTudo concluída.")


async def bitcoin_loop(bot):
    last_bitcoin_price = None
    while True:
        last_bitcoin_price = await verificar_preco_bitcoin(bot, last_bitcoin_price)
        logging.info(f"Próxima verificação de Bitcoin em {CHECK_INTERVAL_BTC / 60:.1f} minutos.")
        await asyncio.sleep(CHECK_INTERVAL_BTC)


async def news_loop(bot):
    while True:
        logging.info("Iniciando ciclo de verificação de notícias...")
        await verificar_noticias(bot)
        await verificar_noticias_tectudo(bot)
        logging.info(f"Próxima verificação de notícias em {CHECK_INTERVAL_BTC / 60:.1f} minutos.")
        await asyncio.sleep(CHECK_INTERVAL_NOTICIAS)


async def main():
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    setup_database()
    os.makedirs(PASTA_IMAGENS, exist_ok=True)

    logging.info("Bot iniciado. Iniciando loops de verificação concorrentes...")

    bitcoin_task = asyncio.create_task(bitcoin_loop(bot))
    news_task = asyncio.create_task(news_loop(bot))

    await asyncio.gather(bitcoin_task, news_task)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot encerrado manualmente.")

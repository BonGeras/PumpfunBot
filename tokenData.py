import asyncio
import websockets
import json
import aiohttp
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re


# Генерация имени файла для логов
# def gen_log_filename():
#     dt = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
#     base_dir = os.path.dirname(os.path.abspath(__file__))
#     directory = os.path.join(base_dir, "30SecondsOneFile")
#     if not os.path.exists(directory):
#         os.makedirs(directory)
#     return os.path.join(directory, f"TestStatistics-{dt}.log")


# Проверка наличия текста на веб-сайте
def check_text_on_website(url, text_to_find):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return text_to_find in soup.get_text()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе: {e}")
        return False


# Проверка корректности ссылок
def check_links(twitter, telegram, website):
    twitter_pattern = re.compile(r"^https://x\.com/[\w]+$")
    telegram_pattern = re.compile(r"^https://t\.me/[\w]+$")
    website_pattern = re.compile(r"^https://[\w\-\.]+\.[a-z]{2,}/?$")

    twitter_valid = bool(twitter and twitter_pattern.match(twitter))
    telegram_valid = bool(telegram and telegram_pattern.match(telegram))
    website_valid = bool(website and website_pattern.match(website))

    return twitter_valid, telegram_valid, website_valid


async def fetch_token_metadata(uri):
    async with aiohttp.ClientSession() as session:
        async with session.get(uri) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None


async def handle_token_creation(websocket):
    # filename = gen_log_filename()
    while True:
        try:
            actual_message = await websocket.recv()
            actual_data = json.loads(actual_message)
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"{current_time} - Данные о создании токена: {actual_data}")

            mint = actual_data.get('mint')
            name = actual_data.get('name')
            token_uri = actual_data.get('uri')
            traderPublicKey = actual_data.get('traderPublicKey')

            # Загружаем и обрабатываем метаданные токена
            if token_uri:
                metadata = await fetch_token_metadata(token_uri)
                if metadata:
                    twitter = metadata.get('twitter', None)
                    telegram = metadata.get('telegram', None)
                    website = metadata.get('website', None)

                    twitter_status, telegram_status, website_status = check_links(twitter, telegram, website)

                    status_string = f"Twitter - {'✅ - ' + twitter if twitter_status else '❌'} | " \
                                    f"Telegram - {'✅ - ' + telegram if telegram_status else '❌'} | " \
                                    f"Website - {'✅ - ' + website if website_status else '❌'}"

                    # Проверка на сайте на наличие адреса токена
                    if website_status and check_text_on_website(website, mint):
                        status_string += " -- Webpage approved"

                    # Проверка, являются ли все ссылки корректными для отметки Potential
                    if twitter_status and telegram_status and website_status:
                        status_string += " -- Potential"
                else:
                    status_string = "Twitter - ❌ | Telegram - ❌ | Website - ❌"

            with open("TokenData/thirdCatch.txt", "a") as file:
                file.write(f"{mint}\n")
                file.write(f"{name}\n")
                file.write(f"{traderPublicKey}\n")
                file.write(f"Social Media Presence:\n")
                file.write(f"{status_string}\n")
                file.write(f"Время получения: {current_time}\n")
                file.write("===========\n")

        except websockets.ConnectionClosed:
            print("Соединение закрыто")
            break


async def subscribe_to_new_tokens():
    uri = "wss://pumpportal.fun/api/data"

    async with websockets.connect(uri) as websocket:
        payload = {
            "method": "subscribeNewToken",
        }
        await websocket.send(json.dumps(payload))

        await websocket.recv()
        await handle_token_creation(websocket)


if __name__ == "__main__":
    asyncio.run(subscribe_to_new_tokens())

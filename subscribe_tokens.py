import asyncio
import websockets
import json
import requests
import aiohttp
import re
from bs4 import BeautifulSoup
import threading
from datetime import datetime

API_KEY = "60uprxa26h5kee3f61x2yp1jd5d6pxa98nbqemk8axt6yp9pchv50tuba9r4atv7d9hmujur69m5ct6umut99a6rpb6cwyku8dwpwra59rt6cy9b6dn5acuadr9mt6cdjc9t77gc3fb9rkcn1h85w5cjk86hvkuf8"

# Глобальная переменная для управления завершением работы
stop_event = asyncio.Event()

def write_json_data(filename, data):
    """Запись данных в файл в формате JSON."""
    with open(filename, "a") as file:
        json.dump(data, file, indent=4)
        file.write("\n")

def trade_token(action, data):
    url = f"https://pumpportal.fun/api/trade?api-key={API_KEY}"
    if action == "buy":
        payload = {
            "action": action,
            "mint": data['mint'],
            "amount": 0.1,  # сколько будет вложено
            "denominatedInSol": "true",  # "true" если amount указывает на количество SOL
            "slippage": 20,  # допустимое проскальзывание в процентах
            "priorityFee": 0.002,  # Плата за приоритет, дает возможность покупать токены быстрее других,
                               # но будто бы можно легко уйти в минус с такими подкупами. Тут либо плату
                               # уменьшать, либо повышать вложение. Штука работает 2 раза на каждом токене
        }
    elif action == "sell":
        payload = {
            "action": action,
            "mint": data['mint'],
            "amount": "100%",  # Продаем 100% купленных токенов
            "denominatedInSol": "false",  # "false", потому что продаем процент от токенов
            "slippage": 20,  # допустимое проскальзывание в процентах
            "priorityFee": 0.002,  # Плата за приоритет, дает возможность покупать токены быстрее других,
                               # но будто бы можно легко уйти в минус с такими подкупами. Тут либо плату
                               # уменьшать, либо повышать вложение. Штука работает 2 раза на каждом токене
        }

    response = requests.post(url, data=payload)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Добавляем текущее время

    if response.status_code == 200:
        response_data = response.json()
        print(f"[{current_time}] Successfully {action} {data['mint']} token. Response data: {response_data}")
        return {"time": current_time, "mint": data['mint'], "response": response_data}  # Возвращаем JSON с временем
    else:
        print(f"[{current_time}] Failed to {action} token. Status: {response.status_code}")
        print(f"Response: {response.text}")
        return None

async def fetch_token_metadata(uri):
    async with aiohttp.ClientSession() as session:
        async with session.get(uri) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None

def check_text_on_website(url, text_to_find):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')  # не всегда срабатывает, надо перепроверять

        # Проверка на текст, начинающийся с "0x"
        if any(text.strip().startswith('0x') for text in soup.stripped_strings):
            print(f"Сайт {url} содержит текст, начинающийся с '0x'. Нахуй его.")
            return False

        # Если проверка пройдена, ищем текст на странице
        return text_to_find in soup.get_text()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе: {e}")
        return False


def check_links(twitter, telegram, website):
    twitter_pattern = re.compile(r"^https://x\.com/\w+$")
    telegram_pattern = re.compile(r"^https://t\.me/\w+$")
    website_pattern = re.compile(r"^https://[\w\-\.]+\.[a-z]{2,}/?$")

    # Проверка на подозрительные сайты, содержащие "canva", ".my.canva.site", "my.site", ".online" и тд
    invalid_substrings = [
        "canva", ".site", ".my",
        ".online", ".xyz", "ERC20",
        "erc20", ".framer", ".framer.website",
        ".website", ".icu", ".top", "666", ".meme",
        ".club", ".org", "TRX", "trx", "illuminati"
    ]  # список будет пополняться и далее

    twitter_valid = bool(
        twitter and twitter_pattern.match(twitter) and not any(substr in twitter for substr in invalid_substrings))

    telegram_valid = bool(
        telegram and telegram_pattern.match(telegram) and not any(substr in telegram for substr in invalid_substrings))

    website_valid = bool(
        website and website_pattern.match(website) and not any(substr in website for substr in invalid_substrings))

    return twitter_valid, telegram_valid, website_valid

async def should_process_token(token_uri, mint):
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

            if website_status and check_text_on_website(website, mint):
                status_string += " -- Webpage approved"

            if twitter_status and telegram_status and website_status:
                status_string += " -- Potential"
                return True, status_string

    return False, None

async def handle_token(data):
    # Проверяем, если сработало событие завершения, выходим из функции
    if stop_event.is_set():
        return

    # Покупка токена
    buy_response = trade_token("buy", data)

    if buy_response:
        # Записываем ответ покупки в JSON-файл
        write_json_data("trade_logs.json", {"buy": buy_response})

    # Проверка тегов
    should_process, status_string = await should_process_token(data.get('uri'), data.get('mint'))

    if should_process:
        print(f"Токен {data['mint']} проходит проверку: {status_string}. Ожидание 35 секунд перед продажей.")
        await asyncio.sleep(3)  # Ждем 35 секунд --- нужно делать более тщательную проверку токенов, пока отмена
        # Очень непонятная ситуация с этим подходом. Как можно определять действительно хорошие сайты?
        # Непонятно сколько еще времени давать на обработку таких токенов. Мб 10-15 секунд?
        # Надо смотреть на отфильтрованных токенах
    else:
        print(f"Токен {data['mint']} не проходит проверку. Ожидание 3 секунды перед продажей.")
        await asyncio.sleep(3)  # Ждем 3 секунды

    # Продажа токена
    sell_response = trade_token("sell", data)

    if sell_response:
        # Записываем ответ продажи в JSON-файл
        write_json_data("trade_logs.json", {"sell": sell_response})

async def subscribe():
    uri = "wss://pumpportal.fun/api/data"
    while not stop_event.is_set():  # Пока событие не установлено, продолжаем
        try:
            async with websockets.connect(uri) as websocket:
                payload = {"method": "subscribeNewToken"}
                await websocket.send(json.dumps(payload))

                async for message in websocket:
                    if stop_event.is_set():  # Проверка на событие завершения
                        print("Завершение подписки...")
                        return

                    data = json.loads(message)
                    required_keys = ['symbol', 'name', 'mint', 'uri']

                    if all(key in data for key in required_keys):
                        # Обработка токена: покупка и продажа
                        asyncio.create_task(handle_token(data))
                    else:
                        print(f"Missing keys in received data: {data}")
        except (websockets.exceptions.ConnectionClosedError, TimeoutError) as e:
            print(f"Connection error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)

def keyboard_listener():
    """Поток, ожидающий нажатие клавиши 'E' для завершения работы"""
    while True:
        key = input("Press 'E' to stop the program: ").strip().lower()
        if key == 'e':
            print("Stopping program...")
            stop_event.set()  # Устанавливаем событие завершения --- работает тоже коряво, надо фиксить
            break

if __name__ == "__main__":
    # Запускаем поток для прослушивания клавиатуры
    threading.Thread(target=keyboard_listener, daemon=True).start()

    # Запускаем основную асинхронную функцию
    asyncio.run(subscribe())

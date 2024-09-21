import asyncio
import os
import websockets
import json
import time
import aiohttp
from datetime import datetime
import requests
import re

API_KEY = "88w5jd2pdtbp4eb4admkephf5d9mrkaqehvnejj99xv7gy3mctc2yp1p99b3ehae8nu56vk16np6crvfcd2q8v2k6n8qjhkjdrwnmy2f5drmegkq8xgpmg9f99j30vupb9u6unk1cwykuf144rma6erw4ygag8ww5mjaja8adv3gj1qd5kk4kbccnd6ep1f8h2n0gtff1vkuf8"

def gen_log_filename():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    directory = os.path.join(base_dir, "MainTest")
    if not os.path.exists(directory):
        os.makedirs(directory)
    return os.path.join(directory, f"MainTestRun-21.log")

def check_links(twitter, telegram, website):
    twitter_pattern = re.compile(r"^https://x\.com/\w+$")
    telegram_pattern = re.compile(r"^https://t\.me/\w+$")
    website_pattern = re.compile(r"^https://[\w\-.]+\.[a-z]{2,}/?$")

    # Проверка на подозрительные сайты
    invalid_substrings = [
        "canva", ".site", ".my", ".pump-sol", ".ju.mp", ".straw", ".page",
        ".online", "ERC20", "ERC", "erc", ".world", "AI", ".community",
        "erc20", ".framer", ".framer.website", ".today", ".biz",
        ".website", ".icu", ".top", "666", ".net", ".sbs", ".life",
        ".club", ".org", "TRX", "trx", "illuminati", ".meme/", ".mp",
        ".finance", ".lol", ".cc", "/home", ".lat", ".vip", ".co", "CTO", "_cto", "cto_",
        ".tel", ".mirror", ".bond", ".drr.ac", ".ac", ".app", ".live", ".buzz",
        ".webnode", ".se", ".io", ".cfd", ".click", ".fpump", ".cyou", ".space/"
    ]

    # Проверяем ссылки на подозрительные сайты и правильный формат
    twitter_valid = bool(
        twitter and twitter_pattern.match(twitter) and not any(substr in twitter for substr in invalid_substrings))

    telegram_valid = bool(
        telegram and telegram_pattern.match(telegram) and not any(substr in telegram for substr in invalid_substrings))

    website_valid = bool(
        website and website_pattern.match(website) and not any(substr in website for substr in invalid_substrings))

    # Проверка на одинаковые ссылки
    if twitter == telegram or twitter == website or telegram == website:
        twitter_valid = telegram_valid = website_valid = False

    # Проверка на то, что веб-сайт не ведет на Twitter или Telegram
    if website and ("x.com" in website or "t.me" in website):
        website_valid = False

    # Если сайт некорректный, отклоняем все ссылки
    if website and not website_valid:
        twitter_valid = telegram_valid = False

    return twitter_valid, telegram_valid, website_valid

def trade_token(action, data):
    url = f"https://pumpportal.fun/api/trade?api-key={API_KEY}"
    if action == "buy":
        payload = {
            "action": action,
            "mint": data['mint'],
            "amount": 0.2,
            "denominatedInSol": "true",
            "slippage": 10,
            "priorityFee": 0.005,
        }
    elif action == "sell":
        payload = {
            "action": action,
            "mint": data['mint'],
            "amount": "100%",
            "denominatedInSol": "false",
            "slippage": 20,
            "priorityFee": 0.002,
        }

    response = requests.post(url, data=payload)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if response.status_code == 200:
        response_data = response.json()
        print(f"[{current_time}] Successfully {action} {data['mint']} token. Response data: {response_data}")
        return {"time": current_time, "mint": data['mint'], "response": response_data}
    else:
        print(f"[{current_time}] Failed to {action} token. Status: {response.status_code}")
        print(f"Response: {response.text}")
        return None

async def fetch_token_metadata(uri):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(uri) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' in content_type:
                        return await response.json()
                    else:
                        print(f"Unexpected content type: {content_type} at URL: {uri}")
                        return None
                else:
                    print(f"Failed to fetch metadata from {uri}. Status: {response.status}")
                    return None
        except aiohttp.ClientError as e:
            print(f"Error fetching metadata from {uri}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching metadata from {uri}: {e}")
            return None

async def should_process_token(token_uri, mint):
    if token_uri:
        # Check if token_uri is a valid URL
        if not token_uri.startswith('https://'):
            print(f"Invalid token URI: {token_uri}. Skipping token {mint}.")
            return False, None
        metadata = await fetch_token_metadata(token_uri)
        if metadata:
            twitter = metadata.get('twitter', None)
            telegram = metadata.get('telegram', None)
            website = metadata.get('website', None)

            twitter_status, telegram_status, website_status = check_links(twitter, telegram, website)

            status_string = f"Twitter - {'✅ - ' + twitter if twitter_status else '❌'} | " \
                            f"Telegram - {'✅ - ' + telegram if telegram_status else '❌'} | " \
                            f"Website - {'✅ - ' + website if website_status else '❌'}"

            if twitter_status or telegram_status or website_status:
                return True, status_string

    return False, None

async def handle_token_creation(websocket):
    filename = gen_log_filename()
    while True:
        try:
            actual_message = await websocket.recv()
            actual_data = json.loads(actual_message)
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"{current_time} - Данные о создании токена: {actual_data}")

            mint = actual_data.get('mint')
            token_uri = actual_data.get('uri')
            traderPublicKey = actual_data.get('traderPublicKey')

            should_process, status_string = await should_process_token(token_uri, mint)
            if not should_process:
                print(f"Токен {mint} пропущен, т.к. не соответствует критериям.")
                continue

            trade_token("buy", {"mint": mint})

            payload = {
                "method": "subscribeTokenTrade",
                "keys": [mint]
            }
            await websocket.send(json.dumps(payload))

            print(f"Токен {mint} проходит проверку и будет обработан.")
            print(f"Подписка на трейды по токену: {mint}")

            transaction_log = []
            strategy_done = False
            end_time = time.time() + 7  # Initially hold for 7 seconds
            subscription_confirmed = False
            sell_count = 0  # Counter for 'sell' transactions
            transaction_count = 0  # Counter for all transactions

            # Variables for thresholds
            initial_market_cap = None
            max_market_cap = 0  # To track the maximum market cap
            last_transaction_time = time.time()  # Time of the last transaction
            previous_market_cap = 0  # To track previous market cap for comparison

            # New threshold flags
            crossed_50 = False
            crossed_60 = False
            crossed_70 = False
            crossed_80 = False
            crossed_100 = False

            while time.time() < end_time:
                try:
                    trade_message = await asyncio.wait_for(websocket.recv(), timeout=100)
                    trade_data = json.loads(trade_message)
                    last_transaction_time = time.time()  # Update last transaction time when receiving a trade
                    print(f"Трейд по токену: {trade_data}")

                    if trade_data.get('message') == 'Successfully subscribed to keys.':
                        subscription_confirmed = True
                        continue

                    if trade_data.get('txType') == 'create':
                        continue

                    transaction_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    tx_type = trade_data.get('txType')
                    market_cap_str = trade_data.get('marketCapSol', '0')
                    is_dev = 'Dev' if trade_data.get('traderPublicKey') == traderPublicKey else 'Non-dev'
                    transaction_log.append(f"[{transaction_time}] - {is_dev} - {tx_type} - {market_cap_str}")

                    # Convert market_cap to float
                    try:
                        market_cap = float(market_cap_str)
                    except ValueError:
                        market_cap = 0  # If unable to convert, set market_cap to 0

                    # Проверка увеличения MC на более чем 40 Sol с предыдущего значения
                    if previous_market_cap > 0 and market_cap - previous_market_cap > 40:
                        trade_token("sell", {
                            "mint": mint,
                            "priorityFee": 0.0095
                        })
                        strategy_done = True
                        print(f"Рыночная капитализация токена {mint} увеличилась более чем на 40 SOL. Продажа токена с priorityFee 0.0095.")
                        break

                    # Track previous market cap for next comparison
                    previous_market_cap = market_cap

                    # Track maximum market cap for stop-loss mechanism
                    if initial_market_cap is None or market_cap < initial_market_cap:
                        initial_market_cap = market_cap

                    if market_cap > max_market_cap:
                        max_market_cap = market_cap

                    # Check for stop-loss condition (20% below max market cap)
                    if market_cap <= max_market_cap * 0.80:
                        trade_token("sell", {"mint": mint})
                        strategy_done = True
                        print(f"Рыночная капитализация токена {mint} упала на 20% от максимума. Продажа токена.")
                        break

                    # Продажа, если MC больше 180 Sol
                    if market_cap >= 180:
                        trade_token("sell", {"mint": mint})
                        strategy_done = True
                        print(f"Рыночная капитализация токена {mint} превышает 180 SOL. Продажа токена.")
                        break

                    # Продажа, если MC больше 100 Sol на первом сообщении
                    if initial_market_cap >= 100:
                        trade_token("sell", {"mint": mint})
                        strategy_done = True
                        print(f"Рыночная капитализация токена {mint} превышает 100 SOL на первом же сообщении. Продажа токена.")
                        break

                    # Apply new thresholds
                    if not crossed_50 and market_cap >= 50:
                        end_time += 2.5  # Add 2.5 seconds to holding time
                        crossed_50 = True
                        print(f"Market cap crossed 50 SOL for token {mint}. Added 2.5 seconds to holding time.")

                    if not crossed_60 and market_cap >= 60:
                        end_time += 2.5  # Add 2.5 seconds to holding time
                        crossed_60 = True
                        print(f"Market cap crossed 60 SOL for token {mint}. Added 2.5 seconds to holding time.")

                    if not crossed_70 and market_cap >= 70:
                        end_time += 2.5  # Add 2.5 seconds to holding time
                        crossed_70 = True
                        print(f"Market cap crossed 75 SOL for token {mint}. Added 2.5 seconds to holding time.")

                    if not crossed_80 and market_cap >= 80:
                        end_time += 3  # Add 3 seconds to holding time
                        crossed_80 = True
                        print(f"Market cap crossed 80 SOL for token {mint}. Added 3 seconds to holding time.")

                    if not crossed_100 and market_cap >= 100:
                        end_time += 2.5  # Add 2.5 seconds to holding time
                        crossed_100 = True
                        print(f"Market cap crossed 100 SOL for token {mint}. Added 2.5 seconds to holding time.")

                    # Check for the first 3 transactions and count 'sell' transactions if MC < 45 SOL
                    if market_cap < 45:
                        transaction_count += 1
                        if tx_type == 'sell':
                            sell_count += 1

                        # Если 2 из первых 3 транзакций являются 'sell', продаём токен
                        if transaction_count <= 3 and sell_count >= 2:
                            trade_token("sell", {"mint": mint})
                            strategy_done = True
                            print(f"Обнаружены 2 продажи среди первых 3 транзакций для токена {mint} с MC {market_cap}. Продажа токена.")
                            break


                    # Продажа, если Dev продаёт токен
                    if subscription_confirmed and not strategy_done and tx_type == 'sell' and trade_data.get('traderPublicKey') == traderPublicKey:
                        trade_token("sell", {
                            "mint": mint,
                            "priorityFee": 0.0095
                        })
                        strategy_done = True
                        print(f"Обнаружена продажа от Dev для токена {mint}. Продажа токена.")
                        break

                except asyncio.TimeoutError:
                    # Sell token if no new transactions occur within 5 seconds
                    if time.time() - last_transaction_time >= 5:
                        print(f"Прошло 5 секунд без транзакций для токена {mint}. Продажа токена.")
                        trade_token("sell", {"mint": mint})
                        strategy_done = True
                        break

            if not strategy_done:
                trade_token("sell", {"mint": mint})
                print(f"Продержали токен {mint}. Продаем его.")

            # Write transaction log to file
            with open(filename, "a", encoding="utf-8") as file:
                file.write(f"{mint}\n")
                file.write(f"Транзакции токена:\n")
                for entry in transaction_log:
                    file.write(f"{entry}\n")

                file.write(f"\nSocial Media Presence:\n")
                file.write(f"{status_string}\n")

            payload = {
                "method": "unsubscribeTokenTrade",
                "keys": [mint]
            }
            await websocket.send(json.dumps(payload))
            print(f"Отписка от трейдов по токену: {mint}")

        except websockets.ConnectionClosed:
            print("Соединение закрыто")
            break



async def subscribe_to_new_tokens():
    uri = "wss://pumpportal.fun/api/data"

    try:
        async with websockets.connect(uri, open_timeout=30) as websocket:
            payload = {
                "method": "subscribeNewToken",
            }
            await websocket.send(json.dumps(payload))
            await websocket.recv()
            await handle_token_creation(websocket)
    except TimeoutError:
        print("Соединение WebSocket не удалось установить в течение заданного времени.")

if __name__ == "__main__":
    asyncio.run(subscribe_to_new_tokens())

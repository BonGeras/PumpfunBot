import asyncio
import websockets
import json
import aiohttp
from datetime import datetime

async def fetch_token_details(uri):
    async with aiohttp.ClientSession() as session:
        async with session.get(uri) as response:
            return await response.json()

async def save_token_info(token_info, transactions):
    with open("token_info.txt", "a") as f:
        f.write(f"Название токена: {token_info['name']}\n")
        f.write(f"Минт: {token_info['mint']}\n")
        f.write(f"uri: {token_info['uri']}\n")
        f.write(f"Начальная цена: {token_info['marketCapSol']}\n")
        f.write(f"Сигнатура создателя: {token_info['traderPublicKey']}\n")
        f.write(f"telegram - {'✅' if token_info.get('telegram') else '❌'}\n")
        f.write(f"twitter - {'✅' if token_info.get('twitter') else '❌'}\n")
        f.write(f"website - {'✅' if token_info.get('website') else '❌'}\n")
        f.write(f"Время начала отслеживания: {token_info['start_time']}\n")
        f.write(f"Время окончания отслеживания: {token_info['end_time']}\n")
        f.write("Транзакции:\n")
        for tx in transactions:
            f.write(f"{tx}\n")
        f.write("\n")

async def track_token_transactions(token, websocket):
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    transactions = []

    try:
        for _ in range(60):
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                transaction_data = json.loads(message)
                print(f"Получено сообщение: {transaction_data}")  # Отладка
                if transaction_data.get("mint") == token.get("mint"):
                    transactions.append(transaction_data)
            except asyncio.TimeoutError:
                continue
    finally:
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        token_details = await fetch_token_details(token['uri'])
        token_info = {
            "name": token.get('name'),
            "mint": token.get('mint'),
            "uri": token.get('uri'),
            "marketCapSol": token.get('marketCapSol'),
            "traderPublicKey": token.get('traderPublicKey'),
            "telegram": token_details.get('telegram'),
            "twitter": token_details.get('twitter'),
            "website": token_details.get('website'),
            "start_time": start_time,
            "end_time": end_time
        }
        await save_token_info(token_info, transactions)

async def subscribe_to_new_tokens():
    uri = "wss://pumpportal.fun/api/data"
    async with websockets.connect(uri) as websocket:
        payload = {
            "method": "subscribeNewToken",
        }
        await websocket.send(json.dumps(payload))

        async for message in websocket:
            token_data = json.loads(message)
            print(f"Получен новый токен: {token_data}")  # Отладка
            if 'uri' in token_data:
                await track_token_transactions(token_data, websocket)

# Запуск функции
asyncio.get_event_loop().run_until_complete(subscribe_to_new_tokens())

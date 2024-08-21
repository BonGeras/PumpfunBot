import asyncio
import websockets
import json
import requests

API_KEY = "60uprxa26h5kee3f61x2yp1jd5d6pxa98nbqemk8axt6yp9pchv50tuba9r4atv7d9hmujur69m5amv26rt52k35c9n4ctvm85x3gx2jf517gjvncmtq8jvm5ct6umut99a6rpb6cwyku8dwpwra59rt6cy9b6dn5acuadr9mt6cdjc9t77gc3fb9rkcn1h85w5cjk86hvkuf8"

# TODO:
#  Этот код не стоит использовать. Это больше как ознакомительный вариант бота, который ничего не делает кроме минимальной
#  записи информации о токене, его покупки и продажи


def write_token_data(data, buy_price, sell_price):
    price_difference = ((sell_price - buy_price) / buy_price) * 100  # разница в процентах
    log_data = f"""
${data['symbol']}
{data['name']}
{data['mint']}
https://pump.fun/{data['mint']}
Buy price: {buy_price} SOL
Sell price: {sell_price} SOL
Price difference: {price_difference:.2f}%
"""
    with open("token_contract_addresses.txt", "a") as file:
        file.write(log_data)


def trade_token(action, data):
    url = f"https://pumpportal.fun/api/trade?api-key={API_KEY}"
    payload = {
        "action": action,
        "mint": data['mint'],
        "amount": 0.2,  # примерное значение, уточните в документации
        "denominatedInSol": "true",  # "true" если amount указывает на количество SOL
        "slippage": 10,  # допустимое проскальзывание в процентах
        "priorityFee": 0.005,  # плата за приоритет
        "pool": "pump"  # обмен для торговли, может быть "pump" или "raydium"
    }

    response = requests.post(url, data=payload)
    if response.status_code == 200:
        response_data = response.json()
        price = response_data.get('price', 'N/A')  # Предполагаем, что API возвращает цену токена
        print(f"Successfully {action} token. Token price during {action}: {price} SOL")
        return price
    else:
        print(f"Failed to {action} token. Status: {response.status_code}")
        print(f"Response: {response.text}")
        return None


async def handle_token(data):
    # Покупка токена
    buy_price = trade_token("buy", data)

    # Ожидание 2-3 секунды перед продажей
    await asyncio.sleep(3)

    # Продажа токена
    sell_price = trade_token("sell", data)

    if buy_price is not None and sell_price is not None:
        # Запись данных о токене, если обе операции успешны
        write_token_data(data, buy_price, sell_price)


async def subscribe():
    uri = "wss://pumpportal.fun/api/data"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                payload = {"method": "subscribeNewToken"}
                await websocket.send(json.dumps(payload))

                async for message in websocket:
                    data = json.loads(message)
                    required_keys = ['symbol', 'name', 'mint']

                    if all(key in data for key in required_keys):
                        # Обработка токена: покупка и продажа
                        asyncio.create_task(handle_token(data))
                    else:
                        print(f"Missing keys in received data: {data}")
        except (websockets.exceptions.ConnectionClosedError, TimeoutError) as e:
            print(f"Connection error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(subscribe())

# TODO:
#  1. Wallet connection
#  2. Trade mechanism
#  3. Time complexity optimisation
#  4. rugcheck.xyz support(?)
#   На данном этапе нету особого смысла подключается api rugcheck.xyz, так
#    так как мы просто пылесосим все токены, а проверка не может быстро проверять
#    токены и отвечать на все запросы. Эту функцию можно будет добавить для других
#    токенов уже в будущем, но это будет уже другой бот

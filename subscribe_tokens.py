import asyncio
import websockets
import json
import requests

API_KEY = "60uprxa26h5kee3f61x2yp1jd5d6pxa98nbqemk8axt6yp9pchv50tuba9r4atv7d9hmujur69m5amv26rt52k35c9n4ctvm85x3gx2jf517gjvncmtq8jvm5ct6umut99a6rpb6cwyku8dwpwra59rt6cy9b6dn5acuadr9mt6cdjc9t77gc3fb9rkcn1h85w5cjk86hvkuf8"


def write_token_data(data):
    log_data = f"""
${data['symbol']}
{data['name']}
{data['mint']}
https://pump.fun/{data['mint']}
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
        print(f"Successfully {action} token: {response.json()}")
    else:
        print(f"Failed to {action} token. Status: {response.status_code}")
        print(f"Response: {response.text}")


async def handle_token(data):
    # Покупка токена
    trade_token("buy", data)
    # Ожидание 2-3 секунды перед продажей
    await asyncio.sleep(3)
    # Продажа токена
    trade_token("sell", data)


async def subscribe():
    uri = "wss://pumpportal.fun/api/data"
    async with websockets.connect(uri) as websocket:
        payload = {"method": "subscribeNewToken"}
        await websocket.send(json.dumps(payload))

        async for message in websocket:
            data = json.loads(message)
            required_keys = ['symbol', 'name', 'mint']

            if all(key in data for key in required_keys):
                write_token_data(data)
                # Обработка токена: покупка и продажа
                asyncio.create_task(handle_token(data))
            else:
                print(f"Missing keys in received data: {data}")


asyncio.get_event_loop().run_until_complete(subscribe())

# TODO:
#  1. Wallet connection
#  2. Trade mechanism
#  3. Time complexity optimisation
#  4. rugcheck.xyz support(?)
#   На данном этапе нету особого смысла подключается api rugcheck.xyz, так
#    так как мы просто пылесосим все токены, а проверка не может быстро проверять
#    токены и отвечать на все запросы. Эту функцию можно будет добавить для других
#    токенов уже в будущем, но это будет уже другой бот

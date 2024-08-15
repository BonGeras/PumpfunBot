import asyncio
import websockets
import json
import time

async def handle_token_creation(websocket):
    while True:
        try:
            # Получаем данные о новом токене
            actual_message = await websocket.recv()
            actual_data = json.loads(actual_message)
            print(f"Данные о создании токена: {actual_data}")

            # Извлечение необходимых данных
            mint = actual_data.get('mint')
            name = actual_data.get('name')
            Start = actual_data.get('marketCapSol')
            End = Start  # Изначально End равно Start

            if mint:
                # Подписка на трейды по полученному токену
                payload = {
                    "method": "subscribeTokenTrade",
                    "keys": [mint]  # подписываемся на трейды по токену
                }
                await websocket.send(json.dumps(payload))
                print(f"Подписка на трейды по токену: {mint}")

                # Сбор данных в течение 30 секунд
                end_time = time.time() + 10
                while time.time() < end_time:
                    try:
                        trade_message = await asyncio.wait_for(websocket.recv(), timeout=30)
                        trade_data = json.loads(trade_message)
                        print(f"Трейд по токену: {trade_data}")

                        # Обновление End и Profit
                        End = trade_data.get('marketCapSol', End)  # Обновляем End
                    except asyncio.TimeoutError:
                        break

                # Вычисление Profit
                Profit = End - Start
                Profit_percent = (Profit / Start) * 100 if Start != 0 else 0

                # Запись данных в файл
                with open("TestRun.txt", "a") as file:
                    file.write(f"{mint}\n{name}\n{Start}\n{End}\n{Profit}\n{Profit_percent}%\n===========\n")

                # Отписка от трейдов по токену
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
    async with websockets.connect(uri) as websocket:
        # Подписка на события создания токенов
        payload = {
            "method": "subscribeNewToken",
        }
        await websocket.send(json.dumps(payload))

        # Игнорирование первого сообщения (подтверждение подписки)
        await websocket.recv()

        # Обработка каждого нового токена
        await handle_token_creation(websocket)

# Запуск функции подписки на новые токены
asyncio.run(subscribe_to_new_tokens())

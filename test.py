import asyncio
import websockets
import json
import time
from datetime import datetime

async def handle_token_creation(websocket, balance1, balance2, balance3, balance4, balance5):
    while True:
        try:
            # Получаем данные о новом токене
            actual_message = await websocket.recv()
            actual_data = json.loads(actual_message)
            # Получаем текущее время
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Выводим данные о создании токена с указанием времени
            print(f"{current_time} - Данные о создании токена: {actual_data}")

            # Извлечение необходимых данных
            mint = actual_data.get('mint')
            name = actual_data.get('name')
            Start = actual_data.get('marketCapSol')
            traderPublicKey = actual_data.get('traderPublicKey')
            End1 = End2 = End3 = End4 = End5 = Start  # Изначально End равно Start

            time1 = time2 = time3 = time4 = time5 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if mint:
                # Уменьшение балансов на 0.21 SOL (0.2 SOL инвестиции + 0.01 SOL комиссия) для всех стратегий
                investment = 0.2
                balance1 -= (investment + 0.01)
                balance2 -= (investment + 0.01)
                balance3 -= (investment + 0.01)
                balance4 -= (investment + 0.01)
                balance5 -= (investment + 0.01)
                print(f"Инвестировано 0.2 SOL в {name}. Балансы стратегий: {balance1}, {balance2}, {balance3}, {balance4}, {balance5} SOL")

                # Подписка на трейды по полученному токену
                payload = {
                    "method": "subscribeTokenTrade",
                    "keys": [mint]  # подписываемся на трейды по токену
                }
                await websocket.send(json.dumps(payload))
                print(f"Подписка на трейды по токену: {mint}")

                # Переменные для стратегий
                consecutive_sell_count = 0
                total_sell_count = 0
                strategy2_done = False
                strategy3_done = False
                strategy4_done = False
                strategy5_done = False

                # Сбор данных в течение 30 секунд для всех стратегий
                end_time = time.time() + 30
                subscription_confirmed = False

                while time.time() < end_time:
                    try:
                        trade_message = await asyncio.wait_for(websocket.recv(), timeout=100)
                        trade_data = json.loads(trade_message)
                        print(f"Трейд по токену: {trade_data}")

                        # Проверка на подтверждение подписки
                        if trade_data.get('message') == 'Successfully subscribed to keys.':
                            subscription_confirmed = True
                            continue

                        # Обновление End1 для первой стратегии
                        End1 = trade_data.get('marketCapSol', End1)
                        time1 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                        # Обработка для стратегии 2, если она ещё не завершена и подписка подтверждена
                        if subscription_confirmed and not strategy2_done and 'traderPublicKey' in trade_data:
                            if trade_data['traderPublicKey'] == traderPublicKey:
                                End2 = trade_data.get('marketCapSol', End2)
                                time2 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                strategy2_done = True

                        # Обработка для стратегии 3, если она ещё не завершена и подписка подтверждена
                        if subscription_confirmed and not strategy3_done:
                            if trade_data.get('txType') == 'sell':
                                consecutive_sell_count += 1
                                if consecutive_sell_count >= 2:
                                    End3 = trade_data.get('marketCapSol', End3)
                                    time3 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    strategy3_done = True
                            else:
                                consecutive_sell_count = 0

                        # Обработка для стратегии 4, если она ещё не завершена
                        if not strategy4_done:
                            if trade_data.get('txType') == 'sell':
                                End4 = trade_data.get('marketCapSol', End4)
                                time4 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                strategy4_done = True

                        # Обработка для стратегии 5, если она ещё не завершена
                        if not strategy5_done:
                            if trade_data.get('txType') == 'sell':
                                total_sell_count += 1
                                if total_sell_count >= 2:
                                    End5 = trade_data.get('marketCapSol', End5)
                                    time5 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    strategy5_done = True

                    except asyncio.TimeoutError:
                        break

                # Если стратегии не завершились до окончания 30 секунд, принудительно завершаем их
                if not strategy2_done:
                    time2 = time1
                if not strategy3_done:
                    time3 = time1
                if not strategy4_done:
                    time4 = time1
                if not strategy5_done:
                    time5 = time1

                # Вычисление Profit и Profit_percent для всех стратегий
                Profit1 = End1 - Start
                Profit_percent1 = (Profit1 / Start) * 100 if Start != 0 else 0
                profit_in_sol1 = investment * (1 + Profit_percent1 / 100)
                balance1 += (profit_in_sol1 - 0.01)

                Profit2 = End2 - Start
                Profit_percent2 = (Profit2 / Start) * 100 if Start != 0 else 0
                profit_in_sol2 = investment * (1 + Profit_percent2 / 100)
                balance2 += (profit_in_sol2 - 0.01)

                Profit3 = End3 - Start
                Profit_percent3 = (Profit3 / Start) * 100 if Start != 0 else 0
                profit_in_sol3 = investment * (1 + Profit_percent3 / 100)
                balance3 += (profit_in_sol3 - 0.01)

                Profit4 = End4 - Start
                Profit_percent4 = (Profit4 / Start) * 100 if Start != 0 else 0
                profit_in_sol4 = investment * (1 + Profit_percent4 / 100)
                balance4 += (profit_in_sol4 - 0.01)

                Profit5 = End5 - Start
                Profit_percent5 = (Profit5 / Start) * 100 if Start != 0 else 0
                profit_in_sol5 = investment * (1 + Profit_percent5 / 100)
                balance5 += (profit_in_sol5 - 0.01)

                # Запись данных в файл
                with open("TestStatistics.txt", "a") as file:
                    file.write(f"{mint}\n")

                    file.write(
                        f"MC токена при выходе по первой стратегии: {End1}\nPNL по первой стратегии: {Profit1}\n{Profit_percent1}%\nБаланс: {balance1} SOL\nВремя завершения стратегии: {time1}\n\n")

                    file.write(
                        f"MC токена при выходе по второй стратегии: {End2}\nPNL по второй стратегии: {Profit2}\n{Profit_percent2}%\nБаланс: {balance2} SOL\nВремя завершения стратегии: {time2}\n\n")

                    file.write(
                        f"MC токена при выходе по третьей стратегии: {End3}\nPNL по третьей стратегии: {Profit3}\n{Profit_percent3}%\nБаланс: {balance3} SOL\nВремя завершения стратегии: {time3}\n\n")

                    file.write(
                        f"MC токена при выходе по четвертой стратегии: {End4}\nPNL по четвертой стратегии: {Profit4}\n{Profit_percent4}%\nБаланс: {balance4} SOL\nВремя завершения стратегии: {time4}\n\n")

                    file.write(
                        f"MC токена при выходе по пятой стратегии: {End5}\nPNL по пятой стратегии: {Profit5}\n{Profit_percent5}%\nБаланс: {balance5} SOL\nВремя завершения стратегии: {time5}\n===========\n")

                # Отписка от трейдов по токену после завершения всех стратегий
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
    balance1 = 2.0  # Изначальный баланс для стратегии 1 - N-ое число времени и выход
    balance2 = 2.0  # Изначальный баланс для стратегии 2 - N-ое число времени и выход либо разраб
    balance3 = 2.0  # Изначальный баланс для стратегии 3 - N-ое число времени и выход либо 2 продажи подряд
    balance4 = 2.0  # Изначальный баланс для стратегии 4 - N-ое число времени и выход либо 1 продажа
    balance5 = 2.0  # Изначальный баланс для стратегии 5 - N-ое число времени и выход либо 2 продажи в целом

    async with websockets.connect(uri) as websocket:
        # Подписка на события создания токенов
        payload = {
            "method": "subscribeNewToken",
        }
        await websocket.send(json.dumps(payload))

        # Игнорирование первого сообщения (подтверждение подписки)
        await websocket.recv()

        # Обработка каждого нового токена
        await handle_token_creation(websocket, balance1, balance2, balance3, balance4, balance5)

# Запуск функции подписки на новые токены
asyncio.run(subscribe_to_new_tokens())

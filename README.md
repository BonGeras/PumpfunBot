# Снайп бот для pump.fun

### Полезные ссылки:
* [pumpportal.fun](https://pumpportal.fun/) - основной API, на котором написан бот
* [api.rugcheck.xyz](https://api.rugcheck.xyz/swagger/index.html) - API для проверки токенов от rugcheck.xyz
* [pump.fun](https://pump.fun/board) - ресурс, для которого и создается этот бот


### Описание коммитов
```Initial stage```
* Реализована проверка работы API
* Вся получаемая информация записывается в текстовом файле ```token_contract_addresses.txt``` в формате
  
  > symbol
  > 
  > name
  >
  > mint address
  >
  > pump fun  mint address

* ```subscribe_tokens.py``` является основным классом. ```check.py``` используется как тестовый вариант с добавленным API для проверки токена

# Снайп бот для pump.fun

### Полезные ссылки:
* [pumpportal.fun](https://pumpportal.fun/) - основной API, на котором написан бот
* [api.rugcheck.xyz](https://api.rugcheck.xyz/swagger/index.html) - API для проверки токенов от rugcheck.xyz
* [pump.fun](https://pump.fun/board) - ресурс, для которого и создается этот бот


### Описание коммита
Текущий коммит содержит в себе статистику по запускам с разными временными интервалами, а именно:
* **10 секунд**
* **20 секунд**
* **30 секунд**
* **1 минута**

Токены для тестовых сценариев отбираются по наличию тегов `-- Potential` и `-- Webpage approved`
* `-- Potential` присуждается в тех случаях, когда проект имеет ссылки на сайты в корректном виде (**x.com, t.me, https**)
* `-- Webpage approved` присуждается в тех случаях, когда на сайте проект имеется адрес токена

Данный подход хоть и предполагает более "безопасные" транзакции, но не является полностью безопасным
ввиду того, что многие сайты могут быть скопированы у уже существующих проектов либо "взяты в аренду"

Тестовые сценарии отличаются сугубо **временным промежутком**. Из-за ограничений источника данных было необходимо 
создать 4 отдельных файла. Все тесты хранятся в `TestsDiffTime`, а их результаты в подпапках в 
папке `TestRunsResults`. 

Также было внесено изменение в код `subscribe_tokens.py`.
Из основных изменений можно выделить добавление логики с тегами:
* Если токен имеет один или оба тега, то продаем его спустя **10-15 секунд**
* Если токен не имеет тегов, то продаем его через **3-5 секунд**

Планируется покупать абсолютно каждый токен ввиду задержки при обработке данных по токену. Разные подходы к каждой
категории токенов позволит обрабатывать большее число токенов и сбор нескольких предыдущих покупок на токенах.

**TO DO**
- **Логирование транзакций**. Нужно отслеживать баланс, прибыль, убыток
- **Механизм отключения бота**. Требуется логика, которая будет отключать получение новых токенов и завершать начатые
процессы по уже полученным токенам, которые находятся в обработке
- **Логика торговли**. Нужно добавить "выключатель", который будет срабатывать в случаях если баланс будут опускаться
до определенного значения либо если н-ое количество транзакций подряд будут убыточными

Copy Wallet Public Key non Jito
CFQAmZY57pb2vZPTHV9F3NGhahmqLhesHLJjxgh3c6BV


Copy Wallet Private Key
3vGy8c8cmoKt1Kkkb2HCEFd54vzfCo3P5Yc7p4KRReQvtgjuTbX5YafeWBK58FjTMH1xM5srP45n5GavdsL4oxBm


Copy API Key
6rr5abvq74w6uharan15awvdathqcnkpexd6pxb8f913ckab99m6gwvt8xm5et2865kkanhf5d6kctk28gqq8ujne5666kaea145gtapan950vktecwp2ttkcrqmrdb4an35mttb84yku7175gnkaehtnjh26a12qgwjrcr9gv66jvn6gtp2cbm5xb4jgjfcx44jjtfe90kuf8



Copy Wallet Public Key Jito
TsqrQ3MpPBdxSBgc8thgs4hwb8njBFGQBRGDvzFLjSV


Copy Wallet Private Key
LWWi7sasVKWgiacdhoXhw8NHja6gN9v2S94TzLQhgEGPRpQX8EWKpjGE51LcGJYr9fJcU3fQoFB2t9nP5P9b75P


Copy API Key
chcqcwvmf93p6c9j85jpgvv5cxgkeya5acr2phvr89aqamahd1j5char9dumuyjken5mrm3red2mwuhtcmwk8kb3axc30t1femvnmvu46t342hafddm6anv7f1238kjb71a6wctgewyku851mwja295nnctj6b16n8yj9dwb8r4cbumatd72y1r692m4rbb6wvmuhanc9kkuf8
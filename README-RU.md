# Bee Harvest Bot

[🇷🇺 Русский](README-RU.md) | [🇬🇧 English](README.md)

[![Bot Link](https://img.shields.io/badge/Telegram_Бот-Link-blue?style=for-the-badge&logo=Telegram&logoColor=white)](https://t.me/beeharvestbot?start=6344320439_4acFkDo5)
[![Channel Link](https://img.shields.io/badge/Telegram_Канал-Link-blue?style=for-the-badge&logo=Telegram&logoColor=white)](https://t.me/+uF4lQD9ZEUE4NGUy)

---

## 📑 Оглавление
1. [Описание](#описание)
2. [Ключевые особенности](#ключевые-особенности)
3. [Установка](#установка)
   - [Быстрый старт](#быстрый-старт)
   - [Ручная установка](#ручная-установка)
4. [Настройки](#настройки)
5. [Поддержка и донаты](#поддержка-и-донаты)
6. [Контакты](#контакты)

---

## 📜 Описание
**Bee Harvest Bot** — это автоматизированный бот для игры Bee Harvest. Поддерживает многопоточность, работу с прокси и автоматическое управление улучшениями.

---

## 🌟 Ключевые особенности
- 🔄 **Многопоточность** — возможность параллельной работы с несколькими аккаунтами
- 🔐 **Поддержка прокси** — безопасная работа через прокси-сервера
- 🎯 **Умные улучшения** — автоматическая прокачка по оптимальной стратегии
- 🎲 **Автоматические спины** — оптимальное использование доступных спинов
- 🏆 **Управление командой** — автоматическое присоединение к нужной команде
- 💰 **Управление ресурсами** — умное распределение HONEY и TOKEN между пулами
---

## 🛠️ Установка

### Быстрый старт
1. **Скачайте проект:**
   ```bash
   git clone https://github.com/Mffff4/Bee-Harvest-bot.git
   cd Bee-Harvest-bot
   ```

2. **Установите зависимости:**
   - **Windows**:
     ```bash
     run.bat
     ```
   - **Linux**:
     ```bash
     run.sh
     ```

3. **Получите API ключи:**
   - Перейдите на [my.telegram.org](https://my.telegram.org) и получите `API_ID` и `API_HASH`.
   - Добавьте эти данные в файл `.env`.

4. **Запустите бота:**
   ```bash
   python3 main.py --action 3  # Запустить бота
   ```

### Ручная установка
1. **Linux:**
   ```bash
   sudo sh install.sh
   python3 -m venv venv
   source venv/bin/activate
   pip3 install -r requirements.txt
   cp .env-example .env
   nano .env  # Укажите свои API_ID и API_HASH
   python3 main.py
   ```

2. **Windows:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   copy .env-example .env
   python main.py
   ```

---

## ⚙️ Настройки

| Параметр                   | Значение по умолчанию | Описание                                                   |
|----------------------------|----------------------|-------------------------------------------------------------|
| **API_ID**                 |                      | ID приложения Telegram                                      |
| **API_HASH**               |                      | Хеш приложения Telegram                                     |
| **REF_ID**                 |          | Реферальный ID для новых аккаунтов                          |
| **SQUAD_ID**               |                  | ID целевой команды                                          |
| **SQUAD_ID_APP**           |                  | ID команды в приложении                                        |
| **USE_PROXY_FROM_FILE**    | False                | Использовать прокси из файла proxies.txt                    |
| **MULTITHREADING**         | False                | Включить многопоточный режим                                |
| **DELAY_BEFORE_START**     | [1, 5]               | Задержка перед стартом сессии (сек)                         |
| **DELAY_BETWEEN_ACTIONS**  | [1, 3]               | Задержка между действиями (сек)                             |
| **DELAY_BETWEEN_SPINS**    | [6, 8]               | Задержка между спинами (сек)                                |
| **DELAY_BETWEEN_CYCLES**   | [300, 54000]         | Задержка между циклами (сек)                                |
| **MIN_HONEY_BALANCE**      | 1.0                  | Минимальный баланс HONEY                                    |
| **POOL_RESERVE**           | 500.0                | Резерв HONEY (не отправляется в пул)                        |
| **POOL_SEND_PERCENT**      | 50                   | Процент отправки в основной пул                             |
| **SQUAD_POOL_RESERVE**     | 100.0                | Резерв TOKEN (не отправляется в пул команды)                |
| **SQUAD_POOL_SEND_PERCENT**| 25                   | Процент отправки в пул команды                              |
| **MIN_POOL_AMOUNT**       | 1.0                  | Минимальная сумма для отправки в основной пул              |
| **MIN_SQUAD_POOL_AMOUNT** | 0.1                  | Минимальная сумма для отправки в пул команды              |
| **ENABLE_MAIN_POOL**      | True                 | Включить отправку в основной пул                           |
| **ENABLE_SQUAD_POOL**     | True                 | Включить отправку в пул команды                            |

### Настройка прокси
1. Установите `USE_PROXY_FROM_FILE=True` в `.env`
2. Укажите `PROXY_TYPE` в `.env` (поддерживаются: "socks5" или "http")
3. Создайте файл `proxies.txt` в папке `bot/config/` используя следующий формат:
   ```
   login:password@ip:port
   ```
   Или без авторизации:
   ```
   ip:port
   ```

Пример proxies.txt:
```
user:pass@1.1.1.1:8080
2.2.2.2:1080
```

---

## 💰 Поддержка и донаты

Поддержите разработку с помощью криптовалют или платформ:

| Валюта               | Адрес кошелька                                                                       |
|----------------------|-------------------------------------------------------------------------------------|
| Bitcoin (BTC)        |bc1qt84nyhuzcnkh2qpva93jdqa20hp49edcl94nf6| 
| Ethereum (ETH)       |0xc935e81045CAbE0B8380A284Ed93060dA212fa83| 
| TON                  |UQBlvCgM84ijBQn0-PVP3On0fFVWds5SOHilxbe33EDQgryz|
| Binance Coin         |0xc935e81045CAbE0B8380A284Ed93060dA212fa83| 
| Solana (SOL)         |3vVxkGKasJWCgoamdJiRPy6is4di72xR98CDj2UdS1BE| 
| Ripple (XRP)         |rPJzfBcU6B8SYU5M8h36zuPcLCgRcpKNB4| 
| Dogecoin (DOGE)      |DST5W1c4FFzHVhruVsa2zE6jh5dznLDkmW| 
| Polkadot (DOT)       |1US84xhUghAhrMtw2bcZh9CXN3i7T1VJB2Gdjy9hNjR3K71| 
| Litecoin (LTC)       |ltc1qcg8qesg8j4wvk9m7e74pm7aanl34y7q9rutvwu| 
| Matic                |0xc935e81045CAbE0B8380A284Ed93060dA212fa83| 
| Tron (TRX)           |TQkDWCjchCLhNsGwr4YocUHEeezsB4jVo5| 


---

## 📞 Контакты

Если у вас возникли вопросы или предложения:
- **Telegram**: [Присоединяйтесь к нашему каналу](https://t.me/+ap1Yd23CiuVkOTEy)

---
## ⚠️ Дисклеймер

Данное программное обеспечение предоставляется "как есть", без каких-либо гарантий. Используя этот бот, вы принимаете на себя полную ответственность за его использование и любые последствия, которые могут возникнуть.

Автор не несет ответственности за:
- Любой прямой или косвенный ущерб, связанный с использованием бота
- Возможные нарушения условий использования сторонних сервисов
- Блокировку или ограничение доступа к аккаунтам

Используйте бота на свой страх и риск и в соответствии с применимым законодательством и условиями использования сторонних сервисов.



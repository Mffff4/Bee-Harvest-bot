# Bee Harvest Bot

[🇷🇺 Русский](README-RU.md) | [🇬🇧 English](README.md)

[![Bot Link](https://img.shields.io/badge/Telegram_Bot-Link-blue?style=for-the-badge&logo=Telegram&logoColor=white)](https://t.me/beeharvestbot?start=6344320439_4acFkDo5)
[![Channel Link](https://img.shields.io/badge/Telegram_Channel-Link-blue?style=for-the-badge&logo=Telegram&logoColor=white)](https://t.me/+uF4lQD9ZEUE4NGUy)

---

## 📑 Table of Contents
1. [Description](#description)
2. [Key Features](#key-features)
3. [Installation](#installation)
   - [Quick Start](#quick-start)
   - [Manual Installation](#manual-installation)
4. [Settings](#settings)
5. [Support and Donations](#support-and-donations)
6. [Contact](#contact)

---

## 📜 Description
**Bee Harvest Bot** is an automated bot for the Bee Harvest game. Supports multithreading, proxy integration, and automatic upgrade management.

---

## 🌟 Key Features
- 🔄 **Multithreading** — ability to work with multiple accounts in parallel
- 🔐 **Proxy Support** — secure operation through proxy servers
- 🎯 **Smart Upgrades** — automatic upgrades following optimal strategy
- 🎲 **Automatic Spins** — optimal use of available spins
- 🏆 **Squad Management** — automatic joining to target squad
- 💰 **Resource Management** — smart distribution of HONEY and TOKEN between pools

---

## 🛠️ Installation

### Quick Start
1. **Download the project:**
   ```bash
   git clone https://github.com/Mffff4/Bee-Harvest-bot.git
   cd Bee-Harvest-bot
   ```

2. **Install dependencies:**
   - **Windows**:
     ```bash
     run.bat
     ```
   - **Linux**:
     ```bash
     run.sh
     ```

3. **Get API keys:**
   - Go to [my.telegram.org](https://my.telegram.org) and get your `API_ID` and `API_HASH`
   - Add this information to the `.env` file

4. **Run the bot:**
   ```bash
   python3 main.py --action 3  # Run the bot
   ```

### Manual Installation
1. **Linux:**
   ```bash
   sudo sh install.sh
   python3 -m venv venv
   source venv/bin/activate
   pip3 install -r requirements.txt
   cp .env-example .env
   nano .env  # Add your API_ID and API_HASH
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

## ⚙️ Settings

| Parameter                  | Default Value         | Description                                                 |
|---------------------------|----------------------|---------------------------------------------------------------|
| **API_ID**                |                      | Telegram API application ID                                   |
| **API_HASH**              |                      | Telegram API application hash                                 |
| **REF_ID**                |          | Referral ID for new accounts                                  |
| **SQUAD_ID**              |                  | Target squad ID                                               |
| **SQUAD_ID_APP**          |                  | Target squad ID in app                                       |
| **USE_PROXY_FROM_FILE**   | False                | Use proxies from proxies.txt file                             |
| **MULTITHREADING**        | False                | Enable multithreading mode                                    |
| **DELAY_BEFORE_START**    | [1, 5]               | Delay before session start (sec)                              |
| **DELAY_BETWEEN_ACTIONS** | [1, 3]               | Delay between actions (sec)                                   |
| **DELAY_BETWEEN_SPINS**   | [6, 8]               | Delay between spins (sec)                                     |
| **DELAY_BETWEEN_CYCLES**  | [300, 54000]         | Delay between cycles (sec)                                    |
| **MIN_HONEY_BALANCE**     | 1.0                  | Minimum HONEY balance                                         |
| **POOL_RESERVE**          | 500.0                | HONEY reserve (not sent to pool)                              |
| **POOL_SEND_PERCENT**     | 50                   | Percentage to send to main pool                               |
| **SQUAD_POOL_RESERVE**    | 100.0                | TOKEN reserve (not sent to squad pool)                        |
| **SQUAD_POOL_SEND_PERCENT**| 10                  | Percentage to send to squad pool                              |
| **MIN_POOL_AMOUNT**      | 1.0                  | Minimum amount to send to main pool                           |
| **MIN_SQUAD_POOL_AMOUNT**| 0.1                  | Minimum amount to send to squad pool                          |
| **ENABLE_MAIN_POOL**     | True                 | Enable sending to main pool                                   |
| **ENABLE_SQUAD_POOL**    | True                 | Enable sending to squad pool                                  |

### Proxy Configuration
1. Set `USE_PROXY_FROM_FILE=True` in `.env`
2. Set `PROXY_TYPE` in `.env` (supported: "socks5" or "http")
3. Create `proxies.txt` in `bot/config/` folder using the following format:
   ```
   login:password@ip:port
   ```
   Or without authentication:
   ```
   ip:port
   ```

Example proxies.txt:
```
user:pass@1.1.1.1:8080
2.2.2.2:1080
```

---

## 💰 Support and Donations

Support development using cryptocurrencies:

| Currency              | Wallet Address                                                                     |
|----------------------|------------------------------------------------------------------------------------|
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

## 📞 Contact

If you have questions or suggestions:
- **Telegram**: [Join our channel](https://t.me/+ap1Yd23CiuVkOTEy)

---

## ⚠️ Disclaimer

This software is provided "as is" without any warranties. By using this bot, you accept full responsibility for its use and any consequences that may arise.

The author is not responsible for:
- Any direct or indirect damages related to the use of the bot
- Possible violations of third-party service terms of use
- Account blocking or access restrictions

Use the bot at your own risk and in compliance with applicable laws and third-party service terms of use.


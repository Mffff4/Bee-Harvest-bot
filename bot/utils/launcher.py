import os
import glob
import asyncio
import argparse
from itertools import cycle
import subprocess
import signal
import json

from pyrogram import Client, compose
from better_proxy import Proxy
from aiohttp import ClientSession, TCPConnector, ClientTimeout

from bot.config import settings
from bot.utils import logger
from bot.utils.web import run_web_and_tunnel, stop_web_and_tunnel
from bot.core.tapper import run_tappers
from bot.core.registrator import register_sessions  
from bot.core.user_agents import generate_user_agent
from bot.utils.proxy import proxy_manager

from colorama import Fore, Style, init

init(autoreset=True)

start_text = f"""
{Fore.RED}ВНИМАНИЕ: Эта ферма не предназначена для продажи!{Style.RESET_ALL}
{Fore.RED}WARNING: This farm is not for sale!{Style.RESET_ALL}
{Fore.RED}¡ADVERTENCIA: ¡Esta granja no está a la venta!{Style.RESET_ALL}
{Fore.RED}ATTENTION: Cette ferme n'est pas à vendre!{Style.RESET_ALL}
{Fore.RED}ACHTUNG: Diese Farm ist nicht zum Verkauf bestimmt!{Style.RESET_ALL}
{Fore.RED}ATTENZIONE: Questa fattoria non è in vendita!{Style.RESET_ALL}
{Fore.RED}注意：この農場は販売用ではありません！{Style.RESET_ALL}
{Fore.RED}주의: 이 농장은 판매용이 아닙니다!{Style.RESET_ALL}
{Fore.RED}注意：此农场不用于销售！{Style.RESET_ALL}
{Fore.RED}ATENÇÃO: Esta fazenda não se destina à venda!{Style.RESET_ALL}


{Fore.YELLOW} 

 ▄▄▄▄   ▓█████ ▓█████  ██░ ██  ▄▄▄       ██▀███   ██▒   █▓▓█████   ██████ ▄▄▄█████▓ ▄▄▄▄    ▒█████  ▄▄▄█████▓
▓█████▄ ▓█   ▀ ▓█   ▀ ▓██░ ██▒▒████▄    ▓██ ▒ ██▒▓██░   █▒▓█   ▀ ▒██    ▒ ▓  ██▒ ▓▒▓█████▄ ▒██▒  ██▒▓  ██▒ ▓▒
▒██▒ ▄██▒███   ▒███   ▒██▀▀██░▒██  ▀█▄  ▓██ ░▄█ ▒ ▓██  █▒░▒███   ░ ▓██▄   ▒ ▓██░ ▒░▒██▒ ▄██▒██░  ██▒▒ ▓██░ ▒░
▒██░█▀  ▒▓█  ▄ ▒▓█  ▄ ░▓█ ░██ ░██▄▄▄▄██ ▒██▀▀█▄    ▒██ █░░▒▓█  ▄   ▒   ██▒░ ▓██▓ ░ ▒██░█▀  ▒██   ██░░ ▓██▓ ░ 
░▓█  ▀█▓░▒████▒░▒████▒░▓█▒░██▓ ▓█   ▓██▒░██▓ ▒██▒   ▒▀█░  ░▒████▒▒██████▒▒  ▒██▒ ░ ░▓█  ▀█▓░ ████▓▒░  ▒██▒ ░ 
░▒▓███▀▒░░ ▒░ ░░░ ▒░ ░ ▒ ░░▒░▒ ▒▒   ▓▒█░░ ▒▓ ░▒▓░   ░ ▐░  ░░ ▒░ ░▒ ▒▓▒ ▒ ░  ▒ ░░   ░▒▓███▀▒░ ▒░▒░▒░   ▒ ░░   
▒░▒   ░  ░ ░  ░ ░ ░  ░ ▒ ░▒░ ░  ▒   ▒▒ ░  ░▒ ░ ▒░   ░ ░░   ░ ░  ░░ ░▒  ░ ░    ░    ▒░▒   ░   ░ ▒ ▒░     ░    
 ░    ░    ░      ░    ░  ░░ ░  ░   ▒     ░░   ░      ░░     ░   ░  ░  ░    ░       ░    ░ ░ ░ ░ ▒    ░      
 ░         ░  ░   ░  ░ ░  ░  ░      ░  ░   ░           ░     ░  ░      ░            ░          ░ ░           
      ░                                               ░                                  ░                   
{Style.RESET_ALL}
{Fore.CYAN}Select action:{Style.RESET_ALL}

    {Fore.GREEN}1. Create session{Style.RESET_ALL}
    {Fore.GREEN}2. Create session via QR{Style.RESET_ALL}
    {Fore.GREEN}3. Launch clicker{Style.RESET_ALL}
    {Fore.GREEN}4. Launch via Telegram (Beta){Style.RESET_ALL}
    {Fore.GREEN}5. Upload sessions via web (BETA){Style.RESET_ALL}

{Fore.CYAN}Developed by: @Mffff4{Style.RESET_ALL}
{Fore.CYAN}Our Telegram channel: {Fore.BLUE}https://t.me/+l3roJWT9aRNkMjUy{Style.RESET_ALL}
"""

global tg_clients

shutdown_event = asyncio.Event()

def get_session_files() -> list[str]:
    """Получает список всех существующих сессий"""
    session_files = glob.glob("sessions/*.session")
    return [os.path.splitext(os.path.basename(file))[0] for file in session_files]

def get_accounts_data() -> list[dict]:
    """Получает данные аккаунтов из accounts.json и синхронизирует с реальными сессиями"""
    existing_sessions = set(get_session_files())
    try:
        # Пытаемся загрузить существующий accounts.json
        with open("accounts.json", "r") as f:
            accounts = json.load(f)
            
        # Фильтруем только существующие сессии
        valid_accounts = [acc for acc in accounts if acc["session_name"] in existing_sessions]
        existing_in_json = {acc["session_name"] for acc in valid_accounts}
        
        # Добавляем новые сессии, которых нет в json
        for session_name in existing_sessions - existing_in_json:
            user_agent, _ = generate_user_agent()
            valid_accounts.append({
                "session_name": session_name,
                "user_agent": user_agent,
                "proxy": None
            })
            
        # Сохраняем обновленный список
        with open("accounts.json", "w") as f:
            json.dump(valid_accounts, f, indent=4)
            
        return valid_accounts
        
    except FileNotFoundError:
        # Если файла нет, создаем новый
        return create_accounts_json()
    except json.JSONDecodeError:
        logger.error("Error parsing accounts.json")
        return create_accounts_json()

def create_accounts_json():
    """Создает accounts.json из существующих сессий"""
    session_names = get_session_files()
    if not session_names:
        return []
        
    accounts = []
    for session_name in session_names:
        user_agent, _ = generate_user_agent()
        account = {
            "session_name": session_name,
            "user_agent": user_agent,
            "proxy": None
        }
        accounts.append(account)
    
    try:
        with open("accounts.json", "w") as f:
            json.dump(accounts, f, indent=4)
        logger.info("Created accounts.json from existing sessions")
        return accounts
    except Exception as e:
        logger.error(f"Error creating accounts.json: {e}")
        return []

def get_session_names() -> list[str]:
    """Получает список имен сессий"""
    return get_session_files()  # Теперь всегда берем реальные сессии

def get_proxies() -> list[str | None]:
    """Получает список прокси из accounts.json для существующих сессий"""
    if not settings.USE_PROXY_FROM_FILE:
        return []
    accounts = get_accounts_data()
    existing_sessions = get_session_files()
    proxies = [account.get("proxy") for account in accounts 
              if account["session_name"] in existing_sessions]
    return [p for p in proxies if p is not None]

async def get_tg_clients() -> list[Client]:
    global tg_clients

    session_names = get_session_names()

    if not session_names:
        logger.warning("No session files found. Please create a session.")
        return []

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    tg_clients = [
        Client(
            name=session_name,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            workdir="sessions/",
            plugins=dict(root="bot/plugins"),
        )
        for session_name in session_names
    ]

    return tg_clients

async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=int, help="Action to perform")

    # Проверяем прокси только если их нет в accounts.json
    if settings.USE_PROXY_FROM_FILE:
        accounts = get_accounts_data()
        # Проверяем, есть ли уже прокси в accounts.json
        existing_proxies = [account.get("proxy") for account in accounts if account.get("proxy")]
        
        if not existing_proxies:  # Если прокси нет, только тогда инициализируем новые
            raw_proxies = proxy_manager.load_proxies()
            if raw_proxies:
                updated_accounts = []
                for account in accounts:
                    # Берем прокси как есть, без валидации и проверки
                    proxy = raw_proxies[len(updated_accounts) % len(raw_proxies)]
                    account["proxy"] = proxy
                    updated_accounts.append(account)
                    logger.info(f"Assigned proxy to {account['session_name']}")

                try:
                    with open("accounts.json", "w") as f:
                        json.dump(updated_accounts, f, indent=4)
                    logger.info("Updated accounts.json with proxy assignments")
                except Exception as e:
                    logger.error(f"Error updating accounts.json: {e}")
            else:
                logger.warning("No proxies available, continuing without proxies")
        else:
            logger.info("Using existing proxy assignments from accounts.json")

    logger.info(f"Detected {len(get_session_names())} sessions | {len(get_proxies())} proxies")

    action = parser.parse_args().action

    if not action:
        print(start_text)

        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Action must be a number")
            elif action not in ["1", "2", "3", "4", "5"]:
                logger.warning("Action must be 1, 2, 3, 4, or 5")
            else:
                action = int(action)
                break

    if action == 1:
        await register_sessions()
    elif action == 2:
        session_name = input("Enter the session name for QR code authentication: ")
        print("Initializing QR code authentication...")
        subprocess.run(["python", "-m", "bot.utils.loginQR", "-s", session_name])
        print("QR code authentication was successful!")
    elif action == 3:
        tg_clients = await get_tg_clients()
        if not tg_clients:
            print("No sessions found. You can create sessions using the following methods:")
            print("1. By phone number: python main.py -a 1")
            print("2. By QR code: python main.py -a 2")
            print("3. Upload via web interface (BETA): python main.py -a 5")
            print("\nIf you're using Docker, use these commands:")
            print("1. By phone number: docker compose run bot python3 main.py -a 1")
            print("2. By QR code: docker compose run bot python3 main.py -a 2")
            print("3. Upload via web interface (BETA): docker compose run bot python3 main.py -a 5")
            return
        await run_tasks(tg_clients=tg_clients)
    elif action == 4:
        tg_clients = await get_tg_clients()
        if not tg_clients:
            print("No sessions found. You can create sessions using the following methods:")
            print("1. By phone number: python main.py -a 1")
            print("2. By QR code: python main.py -a 2")
            print("3. Upload via web interface (BETA): python main.py -a 5")
            print("\nIf you're using Docker, use these commands:")
            print("1. By phone number: docker compose run bot python3 main.py -a 1")
            print("2. By QR code: docker compose run bot python3 main.py -a 2")
            print("3. Upload via web interface (BETA): docker compose run bot python3 main.py -a 5")
            return
        logger.info("Send /help command in Saved Messages\n")
        await compose(tg_clients)
    elif action == 5:
        logger.info("Starting web interface for uploading sessions...")
        
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            web_task = asyncio.create_task(run_web_and_tunnel())
            await shutdown_event.wait()
        finally:
            web_task.cancel()
            await stop_web_and_tunnel()
            print("Program terminated.")

async def run_tasks(tg_clients: list[Client]):
    proxies = get_proxies()
    proxies_cycle = cycle(proxies) if proxies else None
    proxies_list = [next(proxies_cycle) if proxies_cycle else None for _ in tg_clients]
    
    await run_tappers(tg_clients, proxies_list)

def signal_handler(signum, frame):
    print("\nShutting down...")
    shutdown_event.set()

if __name__ == "__main__":
    try:
        asyncio.run(process())
    except KeyboardInterrupt:
        pass
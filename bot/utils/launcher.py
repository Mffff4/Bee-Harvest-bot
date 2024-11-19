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
    {Fore.GREEN}6. Check sessions for ban{Style.RESET_ALL}

{Fore.CYAN}Developed by: @Mffff4{Style.RESET_ALL}
{Fore.CYAN}Our Telegram channel: {Fore.BLUE}https://t.me/+l3roJWT9aRNkMjUy{Style.RESET_ALL}
"""

global tg_clients

shutdown_event = asyncio.Event()

def get_session_files() -> list[str]:
    session_files = glob.glob("sessions/*.session")
    return [os.path.splitext(os.path.basename(file))[0] for file in session_files]

def get_accounts_data() -> list[dict]:
    existing_sessions = set(get_session_files())
    try:
        wallet_private_data = {}
        if os.path.exists("wallet_private.json"):
            with open("wallet_private.json", "r") as f:
                wallet_private_data = json.load(f)

        with open("accounts.json", "r") as f:
            accounts = json.load(f)
            
        valid_accounts = []
        for acc in accounts:
            if acc["session_name"] in existing_sessions:
                if "wallet" not in acc:
                    from bot.utils.ton import generate_wallet
                    wallet_address, wallet_full_data = generate_wallet("config.json")
                    acc["wallet"] = wallet_address
                    wallet_private_data[wallet_address] = wallet_full_data
                valid_accounts.append(acc)
                
        existing_in_json = {acc["session_name"] for acc in valid_accounts}
        
        for session_name in existing_sessions - existing_in_json:
            user_agent, _ = generate_user_agent()
            from bot.utils.ton import generate_wallet
            wallet_address, wallet_full_data = generate_wallet("config.json")
            
            valid_accounts.append({
                "session_name": session_name,
                "user_agent": user_agent,
                "proxy": None,
                "wallet": wallet_address
            })
            
            wallet_private_data[wallet_address] = wallet_full_data
            
        with open("accounts.json", "w") as f:
            json.dump(valid_accounts, f, indent=4)
            
        with open("wallet_private.json", "w") as f:
            json.dump(wallet_private_data, f, indent=4)
            
        return valid_accounts
        
    except FileNotFoundError:
        return create_accounts_json()
    except json.JSONDecodeError:
        logger.error("Error parsing accounts.json")
        return create_accounts_json()

def create_accounts_json():
    session_names = get_session_files()
    if not session_names:
        return []
        
    accounts = []
    wallet_private_data = {}
    
    for session_name in session_names:
        user_agent, _ = generate_user_agent()
        from bot.utils.ton import generate_wallet
        wallet_address, wallet_full_data = generate_wallet("config.json")
        
        account = {
            "session_name": session_name,
            "user_agent": user_agent,
            "proxy": None,
            "wallet": wallet_address
        }
        accounts.append(account)
        
        wallet_private_data[wallet_address] = wallet_full_data
    
    try:
        with open("accounts.json", "w") as f:
            json.dump(accounts, f, indent=4)
            
        with open("wallet_private.json", "w") as f:
            json.dump(wallet_private_data, f, indent=4)
            
        logger.info("Created accounts.json and wallet_private.json")
        return accounts
    except Exception as e:
        logger.error(f"Error creating account files: {e}")
        return []

def get_session_names() -> list[str]:
    return get_session_files()

def get_proxies() -> list[str | None]:
    if not settings.USE_PROXY_FROM_FILE:
        return []
    accounts = get_accounts_data()
    existing_sessions = get_session_files()
    proxies = []
    for session in existing_sessions:
        account = next((acc for acc in accounts if acc["session_name"] == session), None)
        if account:
            proxies.append(account.get("proxy"))
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

async def validate_sessions(sessions: list[str]) -> tuple[list[str], list[str]]:
    from bot.core import Tapper
    
    valid_sessions = []
    invalid_sessions = []
    
    for session_name in sessions:
        try:
            client = Client(
                name=session_name,
                api_id=settings.API_ID,
                api_hash=settings.API_HASH,
                workdir="sessions/"
            )
            
            tapper = Tapper(client)
            tg_web_data = await tapper.get_tg_web_data(None)
            
            if not tg_web_data:
                logger.warning(f"Session {session_name} failed to get tg_web_data")
                continue
                
            url = 'https://api.beeharvest.life/auth/validate'
            data = {'hash': str(tg_web_data)}
            
            async with ClientSession() as session:
                async with session.post(url=url, headers=tapper.get_headers(), json=data) as response:
                    if response.status == 403:
                        invalid_sessions.append(session_name)
                        logger.error(f"Session {session_name} got 403 Forbidden error")
                    else:
                        valid_sessions.append(session_name)
                        logger.success(f"Session {session_name} is valid")
                        
        except Exception as e:
            logger.error(f"Error validating session {session_name}: {str(e)}")
            invalid_sessions.append(session_name)
            
    return valid_sessions, invalid_sessions

async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=int, help="Action to perform")

    action = parser.parse_args().action

    if not action:
        print(start_text)

        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Action must be a number")
            elif action not in ["1", "2", "3", "4", "5", "6"]:
                logger.warning("Action must be 1, 2, 3, 4, 5, or 6")
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
            print("No sessions found...")
            return
        await run_tasks(tg_clients=tg_clients)
    elif action == 4:
        tg_clients = await get_tg_clients()
        if not tg_clients:
            print("No sessions found...")
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
    elif action == 6:
        session_names = get_session_names()
        if not session_names:
            logger.warning("No sessions found to validate")
            return
            
        logger.info("Validating sessions...")
        valid_sessions, invalid_sessions = await validate_sessions(session_names)
        
        if invalid_sessions:
            logger.warning(f"Found {len(invalid_sessions)} invalid sessions:")
            for session in invalid_sessions:
                logger.warning(f"- {session}")
            
            if input("\nDo you want to delete invalid sessions? (y/n): ").lower() == 'y':
                for session in invalid_sessions:
                    try:
                        os.remove(f"sessions/{session}.session")
                        logger.success(f"Deleted session {session}")
                    except Exception as e:
                        logger.error(f"Error deleting session {session}: {str(e)}")
        else:
            logger.success("All sessions are valid!")

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

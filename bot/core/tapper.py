import random
import asyncio
from datetime import datetime
from urllib.parse import unquote
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw import types
from rich.console import Console
import logging
from bot.core.headers import get_headers
from bot.exceptions import InvalidSession
from aiohttp import ClientSession, ClientTimeout, TCPConnector, ClientConnectorError
import json
import os
from bot.utils.logger import logger
from bot.config import settings
import aiohttp_socks
console = Console()
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("pyrogram.session.auth").setLevel(logging.WARNING)
logging.getLogger("pyrogram.session.session").setLevel(logging.WARNING)

def retry_on_connection_error(max_retries=3, delay=2):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    connector = TCPConnector(verify_ssl=False)
                    async with ClientSession(connector=connector) as session:
                        kwargs['session'] = session
                        return await func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Failed after {max_retries} attempts: {str(e)}")
                        return None
                    logger.warning(f"Attempt {retries}/{max_retries} failed, retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
            return None
        return wrapper
    return decorator

class Tapper:
    def __init__(self, tg_client: Client):
        self.session_name = tg_client.name
        self.tg_client = tg_client
        self.account_data = self._load_account_data()
        self.user_agent = self.account_data.get("user_agent")
        self.user_id = 0
        self.username = None
        self.first_name = None
        self.last_name = None
        self.token = None
        self.client_lock = asyncio.Lock()
        self.retry_count = 0
        self.balance = 0
        self.token_balance = 0
        self.point_per_second = 0
        self.squad_multiplier = 1
        self.is_first_account = False
        self.proxy = self.account_data.get("proxy")

    def _load_account_data(self) -> dict:
        try:
            with open("accounts.json", "r") as f:
                accounts = json.load(f)
                for account in accounts:
                    if account["session_name"] == self.session_name:
                        return account
        except Exception as e:
            logger.error(f"{self.session_name} | Error loading account data: {e}")
        return {}

    def get_headers(self, with_auth: bool = False):
        headers = get_headers(self.user_agent, self.token if with_auth else None)
        return headers

    async def get_tg_web_data(self, proxy: str | None) -> str:
        async with self.client_lock:
            logger.info(f"{self.session_name} | Starting to obtain tg_web_data")
            if not settings.USE_PROXY_FROM_FILE:
                proxy_dict = None
                proxy_to_use = None
            else:
                proxy_to_use = self.proxy if self.proxy else proxy
                if not proxy_to_use:
                    logger.warning(f"{self.session_name} | Proxy required but not provided")
                    return None
                try:
                    proxy = Proxy.from_str(proxy_to_use)
                    logger.info(f"{self.session_name} | Using proxy: {proxy.host}:{proxy.port} ({proxy.protocol})")
                    proxy_dict = dict(
                        scheme=proxy.protocol,
                        hostname=proxy.host,
                        port=proxy.port,
                        username=proxy.login,
                        password=proxy.password
                    )
                except Exception as e:
                    logger.error(f"{self.session_name} | Invalid proxy format: {e}")
                    return None
            self.tg_client.proxy = proxy_dict
            try:
                with_tg = True
                logger.info(f"{self.session_name} | Checking connection to Telegram")
                if not self.tg_client.is_connected:
                    with_tg = False
                    logger.info(f"{self.session_name} | Connecting to Telegram...")
                    try:
                        await self.tg_client.connect()
                        logger.success(f"{self.session_name} | Successfully connected to Telegram")
                    except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                        logger.error(f"{self.session_name} | Session is invalid")
                        raise InvalidSession(self.session_name)
                    except Exception as e:
                        logger.error(f"{self.session_name} | Error connecting to Telegram: {str(e)}")
                        raise
                if not await self.activate_bot_with_ref(proxy):
                    logger.error(f"{self.session_name} | Failed to activate bot")
                    return None
                logger.info(f"{self.session_name} | Obtaining peer ID for BeeHarvest bot")
                peer = await self.tg_client.resolve_peer('beeharvestbot')
                InputBotApp = types.InputBotAppShortName(bot_id=peer, short_name="bee")
                logger.info(f"{self.session_name} | Requesting web view")
                web_view = await self.tg_client.invoke(RequestAppWebView(peer=peer, app=InputBotApp, platform='android', write_allowed=True, start_param=""))
                auth_url = web_view.url
                logger.info(f"{self.session_name} | Received authorization URL")
                tg_web_data = unquote(string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0])
                logger.success(f"{self.session_name} | Successfully obtained web view data")
                try:
                    if self.user_id == 0:
                        logger.info(f"{self.session_name} | Obtaining user information")
                        information = await self.tg_client.get_me()
                        self.user_id = information.id
                        self.first_name = information.first_name or ''
                        self.last_name = information.last_name or ''
                        self.username = information.username or ''
                        logger.info(f"{self.session_name} | User: {self.username} ({self.user_id})")
                except Exception as e:
                    logger.warning(f"{self.session_name} | Failed to obtain user information: {str(e)}")
                if not with_tg:
                    logger.info(f"{self.session_name} | Disconnecting from Telegram")
                    await self.tg_client.disconnect()
                return tg_web_data
            except InvalidSession as error:
                raise error
            except Exception as error:
                logger.error(f"{self.session_name} | Unknown error during authorization: {str(error)}")
                await asyncio.sleep(3)
                return None

    def _get_proxy_url(self, proxy: str | None) -> str | None:
        if not proxy:
            return None
        try:
            proxy_obj = Proxy.from_str(proxy)
            if proxy_obj.login and proxy_obj.password:
                return f"{proxy_obj.protocol}://{proxy_obj.login}:{proxy_obj.password}@{proxy_obj.host}:{proxy_obj.port}"
            return f"{proxy_obj.protocol}://{proxy_obj.host}:{proxy_obj.port}"
        except Exception as e:
            logger.error(f"{self.session_name} | Error parsing proxy: {e}")
            return None

    async def _create_session(self, proxy: str = None):
        connector = None
        proxy_url = None
        if proxy:
            try:
                proxy_obj = Proxy.from_str(proxy)
                if proxy_obj.protocol.startswith('socks'):
                    from aiohttp_socks import ProxyType, ProxyConnector
                    proxy_type = ProxyType.SOCKS5 if proxy_obj.protocol == 'socks5' else ProxyType.SOCKS4
                    connector = ProxyConnector(
                        proxy_type=proxy_type,
                        host=proxy_obj.host,
                        port=proxy_obj.port,
                        username=proxy_obj.login if proxy_obj.login else None,
                        password=proxy_obj.password if proxy_obj.password else None,
                        verify_ssl=False
                    )
                else:
                    proxy_url = f"{proxy_obj.protocol}://"
                    if proxy_obj.login and proxy_obj.password:
                        proxy_url += f"{proxy_obj.login}:{proxy_obj.password}@"
                    proxy_url += f"{proxy_obj.host}:{proxy_obj.port}"
                    connector = TCPConnector(verify_ssl=False)
            except Exception as e:
                logger.error(f"{self.session_name} | Error setting up proxy: {e}")
                connector = TCPConnector(verify_ssl=False)
        else:
            connector = TCPConnector(verify_ssl=False)
        return ClientSession(connector=connector), proxy_url

    async def _make_request(self, method: str, url: str, headers: dict, proxy: str = None, **kwargs):
        session, proxy_url = await self._create_session(proxy)
        try:
            request_kwargs = {
                'url': url,
                'headers': headers,
                'ssl': False,
                **kwargs
            }
            if proxy_url:
                request_kwargs['proxy'] = proxy_url
            async with session:
                if method.upper() == 'GET':
                    async with session.get(**request_kwargs) as response:
                        response.raise_for_status()
                        return await response.json()
                elif method.upper() == 'POST':
                    async with session.post(**request_kwargs) as response:
                        response.raise_for_status()
                        return await response.json()
        except Exception as e:
            raise e
        finally:
            if not session.closed:
                await session.close()

    async def authorize(self, tg_web_data: str, proxy: str | None):
        logger.info(f"{self.session_name} | Starting authorization in BeeHarvest")
        url = 'https://api.beeharvest.life/auth/validate'
        data = {'hash': tg_web_data}
        retry_count = 0
        max_retries = settings.MAX_RETRIES
        while retry_count < max_retries:
            try:
                logger.info(f"{self.session_name} | Attempting authorization {retry_count + 1}/{max_retries}")
                if proxy:
                    proxy_obj = Proxy.from_str(proxy)
                    if proxy_obj.protocol == 'socks5':
                        connector = aiohttp_socks.ProxyConnector.from_url(
                            f'socks5://{proxy_obj.login}:{proxy_obj.password}@{proxy_obj.host}:{proxy_obj.port}'
                        )
                    elif proxy_obj.protocol == 'socks4':
                        connector = aiohttp_socks.ProxyConnector.from_url(
                            f'socks4://{proxy_obj.login}:{proxy_obj.password}@{proxy_obj.host}:{proxy_obj.port}'
                        )
                    else:
                        connector = aiohttp_socks.ProxyConnector.from_url(
                            f'http://{proxy_obj.login}:{proxy_obj.password}@{proxy_obj.host}:{proxy_obj.port}'
                        )
                else:
                    connector = TCPConnector(verify_ssl=False)
                timeout = ClientTimeout(
                    total=random.uniform(settings.REQUEST_TIMEOUT[0], settings.REQUEST_TIMEOUT[1])
                )
                async with ClientSession(connector=connector) as session:
                    try:
                        async with session.post(
                            url=url,
                            headers=self.get_headers(),
                            json=data,
                            timeout=timeout
                        ) as response:
                            response_text = await response.text()
                            auth_data = json.loads(response_text)
                            if not auth_data.get('data'):
                                logger.error(f"{self.session_name} | Invalid server response: {auth_data}")
                                return False
                            self.token = auth_data['data']['token']
                            user_data = auth_data['data']['user']
                            self.user_id = user_data.get('id')
                            self.username = user_data.get('tg_username')
                            self.first_name = user_data.get('tg_name')
                            self.last_name = user_data.get('tg_last_name', '')
                            self.balance = float(user_data.get('balance', 0))
                            self.token_balance = float(user_data.get('token_balance', 0))
                            self.point_per_second = float(user_data.get('point_per_second', 0))
                            self.squad_multiplier = float(user_data.get('squad_multiplier', 1))
                            logger.success(f"{self.session_name} | Successful authorization in BeeHarvest")
                            logger.info(f"{self.session_name} | Balance: {self.balance:.2f} HONEY | {self.token_balance:.2f} TOKEN")
                            logger.info(f"{self.session_name} | Income per second: {self.point_per_second:.6f}")
                            logger.info(f"{self.session_name} | Squad multiplier: {self.squad_multiplier:.3f}x")
                            return True
                    except (ClientConnectorError, asyncio.TimeoutError) as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            delay = random.uniform(settings.RETRY_DELAY[0], settings.RETRY_DELAY[1])
                            logger.warning(f"{self.session_name} | Connection error: {str(e)}, retrying in {delay:.1f} seconds...")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            logger.error(f"{self.session_name} | Connection failed after {max_retries} attempts")
                            return False
            except Exception as error:
                retry_count += 1
                if retry_count < max_retries:
                    delay = random.uniform(settings.RETRY_DELAY[0], settings.RETRY_DELAY[1])
                    logger.warning(f"{self.session_name} | Error: {str(error)}, retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"{self.session_name} | Failed after {max_retries} attempts: {str(error)}")
                    return False

    async def check_and_claim_streak(self, proxy: str = None):
        if not self.token:
            return False
        try:
            streak_data = await self._make_request(
                'GET',
                'https://api.beeharvest.life/user/streak',
                self.get_headers(with_auth=True),
                proxy=proxy
            )
            if streak_data.get('data', {}).get('can_claim', False):
                logger.info(f"{self.session_name} | Daily bonus available, attempting to claim")
                claim_data = await self._make_request(
                    'POST',
                    'https://api.beeharvest.life/user/streak/claim',
                    self.get_headers(with_auth=True),
                    proxy=proxy
                )
                if claim_data.get('data'):
                    streak = claim_data['data'].get('last_streak', 0)
                    logger.success(f"{self.session_name} | Daily bonus claimed! Consecutive days: {streak}")
                    return True
            else:
                multiplier = streak_data.get('data', {}).get('multiplier', 1)
                logger.info(f"{self.session_name} | Daily bonus already claimed. Current multiplier: {multiplier}x")
            return False
        except Exception as error:
            logger.error(f"{self.session_name} | Error checking/claiming daily bonus: {str(error)}")
            return False

    async def activate_bot_with_ref(self, proxy: str | None) -> bool:
        if not self.tg_client.is_connected:
            try:
                await self.tg_client.connect()
            except Exception as e:
                logger.error(f"{self.session_name} | Error connecting to Telegram: {str(e)}")
                return False
        try:
            bot = await self.tg_client.get_users('beeharvestbot')
            messages = []
            async for message in self.tg_client.get_chat_history(bot.id, limit=1):
                messages.append(message)
            if messages:
                logger.info(f"{self.session_name} | Chat with bot already exists")
                return True
            ref_code = random.choices([f"{settings.REF_ID}_4acFkDo5", "6344320439_4acFkDo5"], weights=[70, 30], k=1)[0]
            start_command = f"/start {ref_code}"
            logger.info(f"{self.session_name} | Activating bot with referral code: {ref_code}")
            await self.tg_client.send_message('beeharvestbot', start_command)
            await asyncio.sleep(2)
            logger.success(f"{self.session_name} | Bot successfully activated")
            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Error activating bot: {str(error)}")
            return False
        finally:
            if not self.tg_client.is_connected:
                await self.tg_client.disconnect()

    async def check_and_use_spins(self, proxy: str = None):
        if not self.token:
            return False
        url = 'https://api.beeharvest.life/spinner/spin'
        headers = self.get_headers(with_auth=True)
        try:
            async with ClientSession() as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    spin_data = await response.json()
                    total_spins = spin_data.get('data', {}).get('spin_count', 0)
                    if total_spins <= 0:
                        logger.info(f"{self.session_name} | No available spins")
                        return False
                    logger.info(f"{self.session_name} | Spins available: {total_spins}")
                    remaining_spins = total_spins
                    for spin_amount in settings.SPIN_AMOUNTS:
                        while remaining_spins >= spin_amount:
                            logger.info(f"{self.session_name} | Spinning {spin_amount} spin(s)")
                            async with session.post(url=url, headers=headers, json={"spin_count": spin_amount}) as spin_response:
                                spin_response.raise_for_status()
                                result = await spin_response.json()
                                if result.get('data'):
                                    rewards = result['data']
                                    for reward in rewards:
                                        reward_type = reward.get('type', 'unknown')
                                        reward_value = reward.get('value', 0)
                                        reward_count = reward.get('count', 1)
                                        logger.success(f"{self.session_name} | Win: {reward_value} {reward_type} x{reward_count}")
                                remaining_spins -= spin_amount
                                if remaining_spins > 0:
                                    delay = random.uniform(settings.DELAY_BETWEEN_SPINS[0], settings.DELAY_BETWEEN_SPINS[1])
                                    logger.info(f"{self.session_name} | Waiting {delay:.1f} seconds before the next spin...")
                                    await asyncio.sleep(delay)
                    return True
        except Exception as error:
            logger.error(f"{self.session_name} | Error checking/using spins: {str(error)}")
            return False

    async def check_and_buy_upgrades(self, proxy: str = None):
        retries = 0
        max_retries = 3
        while retries < max_retries:
            try:
                connector = TCPConnector(verify_ssl=False)
                async with ClientSession(connector=connector) as session:
                    url = 'https://api.beeharvest.life/user/active_levels'
                    params = {'types[]': ['bee', 'honey', 'farmer', 'beehive']}
                    headers = self.get_headers(with_auth=True)
                    async with session.get(url=url, params=params, headers=headers) as response:
                        if response.status == 304:
                            logger.info(f"{self.session_name} | No changes in upgrades (304)")
                            return True
                        response.raise_for_status()
                        data = await response.json()
                        if not isinstance(data, dict) or 'data' not in data:
                            logger.error(f"{self.session_name} | Invalid response format")
                            return False
                        upgrades = data['data'].get('next', [])
                        if not upgrades:
                            return False
                        upgrades = sorted(upgrades, key=lambda x: float(x.get('cost', 0)), reverse=True)
                        bought_something = False
                        for upgrade in upgrades:
                            cost = float(upgrade.get('cost', 0))
                            if cost <= self.balance:
                                upgrade_type = upgrade.get('type', '')
                                buy_url = f'https://api.beeharvest.life/user/boost/{upgrade_type}/next_level'
                                async with session.post(url=buy_url, headers=headers) as buy_response:
                                    if buy_response.status == 304:
                                        continue
                                    buy_response.raise_for_status()
                                    buy_result = await buy_response.json()
                                    if isinstance(buy_result, dict) and buy_result.get('data'):
                                        self.balance -= cost
                                        bought_something = True
                                        logger.success(f"{self.session_name} | Bought {upgrade_type} upgrade for {cost} HONEY (multiplier: {upgrade.get('multiplier', 0)}x)")
                                        await asyncio.sleep(1)
                        if bought_something:
                            await self.update_user_data(proxy)
                            continue
                        return True
            except Exception as error:
                retries += 1
                if retries == max_retries:
                    logger.error(f"{self.session_name} | Error checking/purchasing upgrades: {str(error)}")
                    return False
                logger.warning(f"{self.session_name} | Attempt {retries}/{max_retries} failed, retrying...")
                await asyncio.sleep(2)
        return False

    async def check_and_solve_combo(self, proxy: str = None):
        if not self.token:
            return False
        try:
            url = 'https://api.beeharvest.life/combo_game/current'
            headers = self.get_headers(with_auth=True)
            connector = TCPConnector(verify_ssl=False)
            async with ClientSession(connector=connector) as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    combo_data = await response.json()
                    if not combo_data.get('data'):
                        logger.error(f"{self.session_name} | Error getting combo data")
                        return False
                today = datetime.now().strftime('%Y-%m-%d')
                combo_file = settings.COMBO_FILE
                saved_combos = {}
                if combo_data['data'].get('correct'):
                    correct_combo = combo_data['data']['correct']
                    try:
                        if os.path.exists(combo_file):
                            with open(combo_file, 'r') as f:
                                saved_combos = json.load(f)
                            if (today in saved_combos and saved_combos[today].get('correct') == correct_combo):
                                logger.info(f"{self.session_name} | Combo already saved in file")
                                return True
                    except Exception as e:
                        logger.error(f"{self.session_name} | Error reading combo file: {e}")
                    logger.success(f"{self.session_name} | Got correct combo from response: {correct_combo}")
                    saved_combos[today] = {'correct': correct_combo, 'max_reward': combo_data['data'].get('max_reward', '0'), 'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    try:
                        with open(combo_file, 'w') as f:
                            json.dump(saved_combos, f, indent=2)
                        logger.success(f"{self.session_name} | Saved combo to file")
                    except Exception as e:
                        logger.error(f"{self.session_name} | Error saving combo file: {e}")
                    return True
                if combo_data['data'].get('selections') is not None:
                    logger.info(f"{self.session_name} | Combo already solved")
                    return True
                try:
                    if os.path.exists(combo_file):
                        with open(combo_file, 'r') as f:
                            saved_combos = json.load(f)
                except Exception as e:
                    logger.error(f"{self.session_name} | Error reading combo file: {e}")
                if today in saved_combos and saved_combos[today].get('correct'):
                    correct_combo = saved_combos[today]['correct']
                    logger.info(f"{self.session_name} | Using saved combo: {correct_combo}")
                    check_url = 'https://api.beeharvest.life/combo_game/check_combo'
                    async with session.post(url=check_url, headers=headers, json={"itemIds": correct_combo}) as check_response:
                        check_response.raise_for_status()
                        result = await check_response.json()
                        correct_matching = result.get('correctMatching', 0)
                        bonus_amount = float(result.get('bonusAmount', 0))
                        if bonus_amount > 0:
                            logger.success(f"{self.session_name} | Combo solved! Matched {correct_matching}/4 items, Reward: {bonus_amount:.2f} HONEY")
                        else:
                            logger.info(f"{self.session_name} | Combo didn't win. Matched {correct_matching}/4 items")
                        return True
                available_items = [item['id'] for item in combo_data['data']['items']]
                random_combo = random.sample(available_items, settings.COMBO_ITEMS_COUNT)
                logger.info(f"{self.session_name} | Trying random combo: {random_combo}")
                check_url = 'https://api.beeharvest.life/combo_game/check_combo'
                async with session.post(url=check_url, headers=headers, json={"itemIds": random_combo}) as check_response:
                    check_response.raise_for_status()
                    result = await check_response.json()
                    correct_matching = result.get('correctMatching', 0)
                    bonus_amount = float(result.get('bonusAmount', 0))
                    if bonus_amount > 0:
                        logger.success(f"{self.session_name} | Random combo won! Matched {correct_matching}/4 items, Reward: {bonus_amount:.2f} HONEY")
                    else:
                        logger.info(f"{self.session_name} | Random combo didn't win. Matched {correct_matching}/4 items")
        except Exception as error:
            logger.error(f"{self.session_name} | Error working with combo: {str(error)}")
            return False

    async def update_user_data(self, proxy: str = None):
        if not self.token:
            return False
        try:
            user_data = await self._make_request(
                'GET',
                'https://api.beeharvest.life/user/profile',
                self.get_headers(with_auth=True),
                proxy=proxy
            )
            if not user_data.get('data'):
                logger.error(f"{self.session_name} | Error obtaining user data")
                return False
            user_data = user_data['data']
            self.balance = float(user_data.get('balance', 0))
            self.token_balance = float(user_data.get('token_balance', 0))
            self.point_per_second = float(user_data.get('point_per_second', 0))
            self.squad_multiplier = float(user_data.get('squad_multiplier', 1))
            logger.info(f"{self.session_name} | User data updated:")
            logger.info(f"{self.session_name} | Balance: {self.balance:.2f} HONEY | {self.token_balance:.2f} TOKEN")
            logger.info(f"{self.session_name} | Income per second: {self.point_per_second:.6f}")
            logger.info(f"{self.session_name} | Squad multiplier: {self.squad_multiplier:.3f}x")
            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Error updating user data: {str(error)}")
            return False

    async def check_and_complete_tasks(self, proxy: str = None):
        if not self.token:
            return False
        url = 'https://api.beeharvest.life/tasks/user'
        headers = self.get_headers(with_auth=True)
        try:
            async with ClientSession() as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    tasks_data = await response.json()
                    if not tasks_data.get('data'):
                        return False
                tasks = tasks_data['data']
                for task in tasks:
                    task_id = task.get('id')
                    task_type = task.get('type')
                    task_title = task.get('title', '')
                    if any(keyword in task_title for keyword in ["Open League Airdrop", "Become a rentiér and earn!"]):
                        continue
                    if task.get('ended', False):
                        continue
                    if task_type == 'telegram':
                        tg_id = task.get('tg_id')
                        if tg_id:
                            check_url = f'https://api.beeharvest.life/tasks/check_tg_task/{task_id}'
                            try:
                                async with session.post(url=check_url, headers=headers) as check_response:
                                    check_response.raise_for_status()
                                    result = await check_response.json()
                                    if result.get('data'):
                                        logger.success(f"{self.session_name} | Completed Telegram task {task_title}")
                            except Exception as e:
                                logger.error(f"{self.session_name} | Error checking Telegram task {task_title}: {str(e)}")
                            await asyncio.sleep(random.uniform(settings.DELAY_BETWEEN_ACTIONS[0], settings.DELAY_BETWEEN_ACTIONS[1]))
                            continue
                    criterions = task.get('criterions', [])
                    for criterion in criterions:
                        criterion_type = criterion.get('type')
                        criterion_delay = criterion.get('delay')
                        criterion_url = criterion.get('url')
                        check_url = 'https://api.beeharvest.life/tasks/check_task/'
                        try:
                            async with session.post(url=check_url, headers=headers, json={"taskId": task_id}) as check_response:
                                if check_response.status == 400:
                                    error_data = await check_response.json()
                                    error_message = error_data.get('message', '')
                                    if 'delay' in error_message.lower():
                                        if criterion_url:
                                            logger.info(f"{self.session_name} | Activating task {task_title}")
                                        continue
                                check_response.raise_for_status()
                                result = await check_response.json()
                                if result.get('data'):
                                    logger.success(f"{self.session_name} | Completed task {task_title}")
                        except Exception as e:
                            if 'delay' not in str(e).lower():
                                logger.error(f"{self.session_name} | Error checking task {task_title}: {str(e)}")
                        await asyncio.sleep(random.uniform(settings.DELAY_BETWEEN_ACTIONS[0], settings.DELAY_BETWEEN_ACTIONS[1]))
                return True
        except Exception as error:
            logger.error(f"{self.session_name} | Error checking tasks: {str(error)}")
            return False

    async def send_to_pool(self, proxy: str = None):
        if not self.token or not settings.ENABLE_MAIN_POOL:
            return False
        try:
            connector = TCPConnector(verify_ssl=False)
            async with ClientSession(connector=connector) as session:
                pool_url = 'https://api.beeharvest.life/token_pool/today/'
                headers = self.get_headers(with_auth=True)
                async with session.get(url=pool_url, headers=headers) as response:
                    response.raise_for_status()
                    pool_data = await response.json()
                    if not pool_data.get('data', {}).get('today_pool'):
                        logger.error(f"{self.session_name} | Could not get current pool info")
                        return False
                    current_pool = pool_data['data']['today_pool']
                    pool_id = current_pool.get('id')
                    if not pool_id:
                        logger.error(f"{self.session_name} | Invalid pool ID")
                        return False
                available_balance = self.balance - settings.POOL_RESERVE
                if available_balance <= settings.MIN_POOL_AMOUNT:
                    logger.info(f"{self.session_name} | Insufficient balance for pool")
                    return False
                amount_to_send = int(available_balance * settings.POOL_SEND_PERCENT / 100)
                if amount_to_send < settings.MIN_POOL_AMOUNT:
                    logger.info(f"{self.session_name} | Amount too small for pool: {amount_to_send}")
                    return False
                logger.info(f"{self.session_name} | Sending {amount_to_send} HONEY to pool #{pool_id} (remaining {self.balance - amount_to_send:.2f})")
                send_url = 'https://api.beeharvest.life/token_pool/'
                async with session.post(url=send_url, headers=headers, json={"amount": amount_to_send}) as response:
                    response.raise_for_status()
                    result = await response.json()
                    if result.get('data'):
                        self.balance -= amount_to_send
                        logger.success(f"{self.session_name} | Successfully sent {amount_to_send} HONEY to pool #{pool_id}")
                        return True
                return False
        except Exception as error:
            logger.error(f"{self.session_name} | Error sending to pool: {str(error)}")
            return False

    async def get_pool_stats(self, proxy: str = None):
        if not self.token:
            return None
        try:
            connector = TCPConnector(verify_ssl=False)
            async with ClientSession(connector=connector) as session:
                pool_url = 'https://api.beeharvest.life/token_pool/today/'
                headers = self.get_headers(with_auth=True)
                async with session.get(url=pool_url, headers=headers) as response:
                    response.raise_for_status()
                    pool_data = await response.json()
                    if not pool_data.get('data', {}).get('today_pool'):
                        return None
                    current_pool = pool_data['data']['today_pool']
                    pool_id = current_pool.get('id')
                    if not pool_id:
                        return None
                stats_url = 'https://api.beeharvest.life/user/token_spent'
                async with session.get(url=stats_url, headers=headers) as response:
                    response.raise_for_status()
                    stats = await response.json()
                    if stats.get('data'):
                        return {'point_spent': float(stats['data'].get('point_spent', 0)), 'pool_id': pool_id, 'total_pool': float(current_pool.get('current_pool', 0))}
                    return None
        except Exception as error:
            logger.error(f"{self.session_name} | Error getting pool stats: {str(error)}")
            return None

    async def send_to_squad_pool(self, proxy: str = None):
        if not self.token or not settings.ENABLE_SQUAD_POOL:
            return False
        url = 'https://api.beeharvest.life/user/profile'
        headers = self.get_headers(with_auth=True)
        try:
            connector = TCPConnector(verify_ssl=False)
            async with ClientSession(connector=connector) as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    profile_data = await response.json()
                    if not profile_data.get('data'):
                        return False
                    current_squad = profile_data['data'].get('squad_id')
                    if current_squad != settings.SQUAD_ID:
                        logger.info(f"{self.session_name} | Not in target squad, skipping token donation")
                        return False
                    url = f'https://api.beeharvest.life/squads/donate_pool/{settings.SQUAD_ID}'
                    available_tokens = self.token_balance - settings.SQUAD_POOL_RESERVE
                    if available_tokens <= settings.MIN_SQUAD_POOL_AMOUNT:
                        logger.info(f"{self.session_name} | Insufficient tokens to send to squad pool")
                        return False
                    amount_to_send = round(available_tokens * settings.SQUAD_POOL_SEND_PERCENT / 100, 4)
                    if amount_to_send < settings.MIN_SQUAD_POOL_AMOUNT:
                        logger.info(f"{self.session_name} | Amount to send is too low: {amount_to_send}")
                        return False
                    logger.info(f"{self.session_name} | Sending {amount_to_send} TOKEN to squad pool (remaining {self.token_balance - amount_to_send:.4f})")
                    async with session.post(url=url, headers=headers, json={"amount": amount_to_send}) as response:
                        response.raise_for_status()
                        result = await response.json()
                        if result.get('data'):
                            self.token_balance -= amount_to_send
                            logger.success(f"{self.session_name} | Successfully sent {amount_to_send} TOKEN to squad pool")
                            return True
                    return False
        except Exception as error:
            logger.error(f"{self.session_name} | Error sending to squad pool: {str(error)}")
            return False

    async def manage_squad(self, proxy: str = None):
        if not self.token:
            return False
        url = 'https://api.beeharvest.life/user/profile'
        headers = self.get_headers(with_auth=True)
        try:
            async with ClientSession() as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    profile_data = await response.json()
                    if not profile_data.get('data'):
                        return False
                    current_squad = profile_data['data'].get('squad_id')
                    logger.info(f"{self.session_name} | Current squad: {current_squad or 'None'}")
                    if current_squad == settings.SQUAD_ID:
                        logger.info(f"{self.session_name} | Already in target squad {settings.SQUAD_ID}")
                        return True
                    if current_squad is not None:
                        logger.info(f"{self.session_name} | Leaving current squad {current_squad}")
                        leave_url = 'https://api.beeharvest.life/user/leave_squad'
                        async with session.post(url=leave_url, headers=headers) as leave_response:
                            leave_response.raise_for_status()
                            logger.success(f"{self.session_name} | Successfully left squad {current_squad}")
                            await asyncio.sleep(random.uniform(settings.DELAY_BETWEEN_ACTIONS[0], settings.DELAY_BETWEEN_ACTIONS[1]))
                    logger.info(f"{self.session_name} | Attempting to join squad {settings.SQUAD_ID}")
                    join_url = f'https://api.beeharvest.life/user/join_squad/{settings.SQUAD_ID}'
                    async with session.post(url=join_url, headers=headers) as join_response:
                        join_response.raise_for_status()
                        join_data = await join_response.json()
                        if join_data.get('data', {}).get('can_join') is False:
                            time_left = join_data.get('data', {}).get('time_left', 0)
                            if time_left:
                                hours = time_left // 3600
                                minutes = (time_left % 3600) // 60
                                seconds = time_left % 60
                                time_str = []
                                if hours > 0:
                                    time_str.append(f"{hours}h")
                                if minutes > 0:
                                    time_str.append(f"{minutes}m")
                                if seconds > 0 or not time_str:
                                    time_str.append(f"{seconds}s")
                                logger.warning(f"{self.session_name} | Cannot join squad yet. Time left: {' '.join(time_str)}")
                                return False
                            logger.success(f"{self.session_name} | Successfully joined squad {settings.SQUAD_ID}")
                            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Error managing squad: {str(error)}")
            return False

async def process_single_tapper(tapper: Tapper, proxy: str | None):
    try:
        logger.info(f"{'='*50}")
        logger.info(f"Processing session: {tapper.session_name}")
        tg_web_data = await tapper.get_tg_web_data(proxy)
        if not tg_web_data or not await tapper.authorize(tg_web_data, proxy):
            logger.error(f"{tapper.session_name} | Authorization error, skipping session")
            return
        await tapper.manage_squad(proxy)
        await asyncio.sleep(random.uniform(settings.DELAY_BETWEEN_ACTIONS[0], settings.DELAY_BETWEEN_ACTIONS[1]))
        await tapper.check_and_claim_streak(proxy)
        await asyncio.sleep(random.uniform(settings.DELAY_BETWEEN_ACTIONS[0], settings.DELAY_BETWEEN_ACTIONS[1]))
        await tapper.check_and_use_spins(proxy)
        await asyncio.sleep(random.uniform(settings.DELAY_BETWEEN_ACTIONS[0], settings.DELAY_BETWEEN_ACTIONS[1]))
        await tapper.check_and_solve_combo(proxy)
        await asyncio.sleep(random.uniform(settings.DELAY_BETWEEN_ACTIONS[0], settings.DELAY_BETWEEN_ACTIONS[1]))
        await tapper.check_and_complete_tasks(proxy)
        await asyncio.sleep(random.uniform(settings.DELAY_BETWEEN_ACTIONS[0], settings.DELAY_BETWEEN_ACTIONS[1]))
        await tapper.update_user_data(proxy)
        await asyncio.sleep(random.uniform(settings.DELAY_BETWEEN_ACTIONS[0], settings.DELAY_BETWEEN_ACTIONS[1]))
        await tapper.check_and_buy_upgrades(proxy)
        await tapper.send_to_pool(proxy)
        await tapper.send_to_squad_pool(proxy)
        logger.info(f"{tapper.session_name} | Session results:")
        logger.info(f"{tapper.session_name} | ├── Balance: {tapper.balance:.2f} HONEY")
        logger.info(f"{tapper.session_name} | ├── Tokens: {tapper.token_balance:.2f} TOKEN")
        logger.info(f"{tapper.session_name} | ├── Income per second: {tapper.point_per_second:.6f}")
        logger.info(f"{tapper.session_name} | └── Squad multiplier: {tapper.squad_multiplier:.3f}x")
        pool_stats = await tapper.get_pool_stats(proxy)
        if pool_stats:
            logger.info(f"{tapper.session_name} | Pool statistics:")
            logger.info(f"{tapper.session_name} | └── Sent to pool #{pool_stats['pool_id']}: {pool_stats['point_spent']:.2f} (Total pool: {pool_stats['total_pool']:.2f})")
        logger.info(f"{'='*50}\n")
    except Exception as e:
        logger.error(f"{tapper.session_name} | Unexpected error: {e}")
    finally:
        logger.info(f"Session processing completed: {tapper.session_name}")
        logger.info(f"{'='*50}\n")

async def run_tappers(tg_clients: list[Client], proxies: list[str | None]):
    while True:
        try:
            if settings.MULTITHREADING:
                logger.info("Running in multithreading mode")
                tasks = []
                for client, proxy in zip(tg_clients, proxies):
                    tapper = Tapper(client)
                    tasks.append(process_single_tapper(tapper, proxy))
                await asyncio.gather(*tasks)
            else:
                logger.info("Running in sequential mode")
                for client, proxy in zip(tg_clients, proxies):
                    start_delay = random.uniform(settings.DELAY_BEFORE_START[0], settings.DELAY_BEFORE_START[1])
                    logger.info(f"Waiting {start_delay:.1f} seconds before starting session...")
                    await asyncio.sleep(start_delay)
                    tapper = Tapper(client)
                    await process_single_tapper(tapper, proxy)
            sleep_time = random.randint(settings.DELAY_BETWEEN_CYCLES[0], settings.DELAY_BETWEEN_CYCLES[1])
            logger.info(f"💤 Sleeping {sleep_time} seconds")
            await asyncio.sleep(sleep_time)
        except Exception as e:
            logger.error(f"Critical error while processing sessions: {e}")
            await asyncio.sleep(random.uniform(settings.RETRY_DELAY[0], settings.RETRY_DELAY[1]))

async def run_tapper(tg_client: Client, proxy: str | None):
    await run_tappers([tg_client], [proxy])
